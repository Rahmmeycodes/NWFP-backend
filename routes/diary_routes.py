from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import DiaryEntry, Food, User
from schemas import DiaryEntryCreate, DiaryEntryResponse, DailySummary, GoalsUpdate
from auth import get_current_user

router = APIRouter(prefix="/api/diary", tags=["diary"])


def _entry_to_response(entry: DiaryEntry) -> DiaryEntryResponse:
    return DiaryEntryResponse(
        id=entry.id,
        food=entry.food,
        date=entry.date,
        meal_type=entry.meal_type,
        servings=entry.servings,
        total_calories=entry.food.calories * entry.servings,
        total_protein=entry.food.protein * entry.servings,
        total_carbs=entry.food.carbs * entry.servings,
        total_fat=entry.food.fat * entry.servings,
    )


@router.post("", response_model=DiaryEntryResponse, status_code=201)
def add_entry(
    entry: DiaryEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    food = db.query(Food).filter(Food.id == entry.food_id).first()
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")
    if entry.meal_type not in ("breakfast", "lunch", "dinner", "snack"):
        raise HTTPException(status_code=400, detail="Invalid meal type")

    db_entry = DiaryEntry(
        user_id=current_user.id,
        food_id=entry.food_id,
        date=entry.date,
        meal_type=entry.meal_type,
        servings=entry.servings,
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    db.refresh(db_entry, ["food"])
    return _entry_to_response(db_entry)


@router.get("/day", response_model=DailySummary)
def get_daily_summary(
    day: date = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if day is None:
        day = date.today()

    entries = (
        db.query(DiaryEntry)
        .options(joinedload(DiaryEntry.food))
        .filter(DiaryEntry.user_id == current_user.id, DiaryEntry.date == day)
        .all()
    )

    meals: dict[str, list[DiaryEntryResponse]] = {
        "breakfast": [], "lunch": [], "dinner": [], "snack": []
    }
    total_cal = total_pro = total_carb = total_fat = 0.0

    for e in entries:
        resp = _entry_to_response(e)
        meals.setdefault(e.meal_type, []).append(resp)
        total_cal += resp.total_calories
        total_pro += resp.total_protein
        total_carb += resp.total_carbs
        total_fat += resp.total_fat

    return DailySummary(
        date=day,
        total_calories=round(total_cal, 1),
        total_protein=round(total_pro, 1),
        total_carbs=round(total_carb, 1),
        total_fat=round(total_fat, 1),
        calorie_goal=current_user.calorie_goal,
        protein_goal=current_user.protein_goal,
        carbs_goal=current_user.carbs_goal,
        fat_goal=current_user.fat_goal,
        calories_remaining=round(current_user.calorie_goal - total_cal, 1),
        meals=meals,
    )


@router.delete("/{entry_id}", status_code=204)
def delete_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = db.query(DiaryEntry).filter(
        DiaryEntry.id == entry_id, DiaryEntry.user_id == current_user.id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    db.delete(entry)
    db.commit()


@router.put("/goals", response_model=dict)
def update_goals(
    goals: GoalsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if goals.calorie_goal is not None:
        current_user.calorie_goal = goals.calorie_goal
    if goals.protein_goal is not None:
        current_user.protein_goal = goals.protein_goal
    if goals.carbs_goal is not None:
        current_user.carbs_goal = goals.carbs_goal
    if goals.fat_goal is not None:
        current_user.fat_goal = goals.fat_goal
    db.commit()
    return {"message": "Goals updated"}
