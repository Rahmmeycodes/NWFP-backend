import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Food, User
from schemas import FoodResponse
from auth import get_current_user

router = APIRouter(prefix="/api/scanner", tags=["scanner"])

OFF_BARCODE_URL = "https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
OFF_SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"


def _parse_off_product(product: dict) -> dict:
    nutrients = product.get("nutriments", {})
    return {
        "name": product.get("product_name", "Unknown"),
        "brand": product.get("brands"),
        "serving_size": product.get("serving_size", "100g"),
        "calories": nutrients.get("energy-kcal_100g", 0),
        "protein": nutrients.get("proteins_100g", 0),
        "carbs": nutrients.get("carbohydrates_100g", 0),
        "fat": nutrients.get("fat_100g", 0),
        "fiber": nutrients.get("fiber_100g", 0),
        "sugar": nutrients.get("sugars_100g", 0),
        "sodium": nutrients.get("sodium_100g", 0) * 1000,
        "barcode": product.get("code"),
        "image_url": product.get("image_front_small_url"),
    }


@router.get("/barcode/{barcode}")
async def scan_barcode(barcode: str, _: User = Depends(get_current_user)):
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(OFF_BARCODE_URL.format(barcode=barcode))
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to reach food database")

    data = resp.json()
    if data.get("status") != 1:
        raise HTTPException(status_code=404, detail="Product not found for this barcode")

    return _parse_off_product(data["product"])


@router.get("/search")
async def search_off(
    q: str = Query(..., description="Food name to search"),
    limit: int = Query(10, le=25),
    _: User = Depends(get_current_user),
):
    params = {
        "search_terms": q,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": limit,
        "fields": "code,product_name,brands,serving_size,nutriments,image_front_small_url",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(OFF_SEARCH_URL, params=params)
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to reach food database")

    products = resp.json().get("products", [])
    return [_parse_off_product(p) for p in products if p.get("product_name")]


@router.post("/barcode/{barcode}/save", response_model=FoodResponse, status_code=201)
async def save_scanned_food(
    barcode: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Scan a barcode and save the food to the database for easy logging."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(OFF_BARCODE_URL.format(barcode=barcode))
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to reach food database")

    data = resp.json()
    if data.get("status") != 1:
        raise HTTPException(status_code=404, detail="Product not found for this barcode")

    parsed = _parse_off_product(data["product"])
    db_food = Food(
        name=parsed["name"],
        brand=parsed["brand"],
        serving_size=parsed["serving_size"],
        calories=parsed["calories"],
        protein=parsed["protein"],
        carbs=parsed["carbs"],
        fat=parsed["fat"],
        fiber=parsed["fiber"],
        sugar=parsed["sugar"],
        sodium=parsed["sodium"],
        is_custom=0,
        created_by=current_user.id,
    )
    db.add(db_food)
    db.commit()
    db.refresh(db_food)
    return db_food
