from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import User, WeightLog
from schemas import ProfileUpdate, UserResponse
from auth import get_current_user

router = APIRouter(prefix="/api/profile", tags=["profile"])

ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}


def _calculate_tdee(weight_kg: float, height_cm: float, age: int, gender: str, activity_level: str) -> int:
    if gender == "male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.55)
    return round(bmr * multiplier)


def _macro_split(calories: int) -> tuple[float, float, float]:
    protein = round(calories * 0.30 / 4, 1)
    carbs = round(calories * 0.40 / 4, 1)
    fat = round(calories * 0.30 / 9, 1)
    return protein, carbs, fat


@router.put("", response_model=UserResponse)
def update_profile(
    profile: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if profile.height_cm is not None:
        current_user.height_cm = profile.height_cm
    if profile.age is not None:
        current_user.age = profile.age
    if profile.gender is not None:
        current_user.gender = profile.gender
    if profile.activity_level is not None:
        current_user.activity_level = profile.activity_level
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/auto-goals", response_model=dict)
def auto_calculate_goals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not all([current_user.height_cm, current_user.age, current_user.gender]):
        return {"error": "Set height_cm, age, and gender in your profile first."}

    latest_weight = (
        db.query(WeightLog)
        .filter(WeightLog.user_id == current_user.id)
        .order_by(WeightLog.date.desc())
        .first()
    )
    if not latest_weight:
        return {"error": "Log your weight first so we can calculate your goals."}

    tdee = _calculate_tdee(
        latest_weight.weight,
        current_user.height_cm,
        current_user.age,
        current_user.gender,
        current_user.activity_level or "moderate",
    )
    protein, carbs, fat = _macro_split(tdee)

    current_user.calorie_goal = tdee
    current_user.protein_goal = protein
    current_user.carbs_goal = carbs
    current_user.fat_goal = fat
    db.commit()

    return {
        "message": "Goals auto-calculated from your profile",
        "weight_kg": latest_weight.weight,
        "bmr_method": "Mifflin-St Jeor",
        "activity_level": current_user.activity_level,
        "calorie_goal": tdee,
        "protein_goal": protein,
        "carbs_goal": carbs,
        "fat_goal": fat,
    }
