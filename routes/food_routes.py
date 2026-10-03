from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import get_db
from models import Food, User
from schemas import FoodCreate, FoodResponse
from auth import get_current_user

router = APIRouter(prefix="/api/foods", tags=["foods"])


@router.get("", response_model=list[FoodResponse])
def search_foods(
    q: str = Query("", description="Search query"),
    limit: int = Query(20, le=100),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Food)
    if q:
        query = query.filter(
            or_(
                Food.name.ilike(f"%{q}%"),
                Food.brand.ilike(f"%{q}%"),
            )
        )
    query = query.filter(
        or_(Food.is_custom == 0, Food.created_by == current_user.id)
    )
    return query.offset(offset).limit(limit).all()


@router.get("/{food_id}", response_model=FoodResponse)
def get_food(food_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    food = db.query(Food).filter(Food.id == food_id).first()
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")
    return food


@router.post("", response_model=FoodResponse, status_code=201)
def create_custom_food(
    food: FoodCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_food = Food(
        **food.model_dump(),
        is_custom=1,
        created_by=current_user.id,
    )
    db.add(db_food)
    db.commit()
    db.refresh(db_food)
    return db_food
