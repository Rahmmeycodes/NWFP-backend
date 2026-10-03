from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import SavedMeal, SavedMealItem, Food, DiaryEntry, User
from schemas import SavedMealCreate, SavedMealResponse
from auth import get_current_user

router = APIRouter(prefix="/api/saved-meals", tags=["saved meals"])


def _meal_response(meal: SavedMeal) -> dict:
    total_cal = sum(i.food.calories * i.servings for i in meal.items)
    total_pro = sum(i.food.protein * i.servings for i in meal.items)
    total_carb = sum(i.food.carbs * i.servings for i in meal.items)
    total_fat = sum(i.food.fat * i.servings for i in meal.items)
    return {
        "id": meal.id,
        "name": meal.name,
        "items": meal.items,
        "total_calories": round(total_cal, 1),
        "total_protein": round(total_pro, 1),
        "total_carbs": round(total_carb, 1),
        "total_fat": round(total_fat, 1),
        "created_at": meal.created_at,
    }


@router.post("", response_model=SavedMealResponse, status_code=201)
def create_saved_meal(
    data: SavedMealCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not data.items:
        raise HTTPException(status_code=400, detail="A saved meal needs at least one item")

    food_ids = [i.food_id for i in data.items]
    foods = db.query(Food).filter(Food.id.in_(food_ids)).all()
    found = {f.id for f in foods}
    missing = set(food_ids) - found
    if missing:
        raise HTTPException(status_code=404, detail=f"Food IDs not found: {missing}")

    meal = SavedMeal(user_id=current_user.id, name=data.name)
    db.add(meal)
    db.flush()

    for item in data.items:
        db.add(SavedMealItem(meal_id=meal.id, food_id=item.food_id, servings=item.servings))

    db.commit()
    db.refresh(meal)
    meal = (
        db.query(SavedMeal)
        .options(joinedload(SavedMeal.items).joinedload(SavedMealItem.food))
        .filter(SavedMeal.id == meal.id)
        .first()
    )
    return _meal_response(meal)


@router.get("", response_model=list[SavedMealResponse])
def list_saved_meals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meals = (
        db.query(SavedMeal)
        .options(joinedload(SavedMeal.items).joinedload(SavedMealItem.food))
        .filter(SavedMeal.user_id == current_user.id)
        .order_by(SavedMeal.name)
        .all()
    )
    return [_meal_response(m) for m in meals]


@router.get("/{meal_id}", response_model=SavedMealResponse)
def get_saved_meal(
    meal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meal = (
        db.query(SavedMeal)
        .options(joinedload(SavedMeal.items).joinedload(SavedMealItem.food))
        .filter(SavedMeal.id == meal_id, SavedMeal.user_id == current_user.id)
        .first()
    )
    if not meal:
        raise HTTPException(status_code=404, detail="Saved meal not found")
    return _meal_response(meal)


@router.post("/{meal_id}/log", response_model=dict)
def log_saved_meal(
    meal_id: int,
    meal_type: str = Query(..., description="breakfast, lunch, dinner, or snack"),
    log_date: date = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meal = (
        db.query(SavedMeal)
        .options(joinedload(SavedMeal.items))
        .filter(SavedMeal.id == meal_id, SavedMeal.user_id == current_user.id)
        .first()
    )
    if not meal:
        raise HTTPException(status_code=404, detail="Saved meal not found")

    target_date = log_date or date.today()
    entries = []
    for item in meal.items:
        entry = DiaryEntry(
            user_id=current_user.id,
            food_id=item.food_id,
            date=target_date,
            meal_type=meal_type,
            servings=item.servings,
        )
        db.add(entry)
        entries.append(entry)

    db.commit()
    return {
        "message": f"Logged '{meal.name}' as {meal_type}",
        "entries_created": len(entries),
        "date": str(target_date),
    }


@router.delete("/{meal_id}", status_code=204)
def delete_saved_meal(
    meal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meal = db.query(SavedMeal).filter(
        SavedMeal.id == meal_id, SavedMeal.user_id == current_user.id
    ).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Saved meal not found")
    db.delete(meal)
    db.commit()
