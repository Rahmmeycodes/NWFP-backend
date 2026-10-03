from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Exercise, User
from schemas import ExerciseCreate, ExerciseResponse
from auth import get_current_user

router = APIRouter(prefix="/api/exercises", tags=["exercises"])

COMMON_EXERCISES = {
    "running": 10.0,
    "walking": 4.0,
    "cycling": 8.0,
    "swimming": 9.0,
    "weightlifting": 5.0,
    "yoga": 3.0,
    "hiit": 12.0,
    "jump rope": 11.0,
    "rowing": 8.5,
    "elliptical": 7.0,
    "dancing": 6.0,
    "hiking": 6.5,
    "pilates": 4.0,
    "stretching": 2.5,
    "boxing": 10.0,
}


@router.get("/suggestions", response_model=list[dict])
def get_exercise_suggestions(_: User = Depends(get_current_user)):
    return [
        {"name": name, "calories_per_minute": cpm, "category": "cardio" if cpm > 5 else "light"}
        for name, cpm in COMMON_EXERCISES.items()
    ]


@router.post("", response_model=ExerciseResponse, status_code=201)
def log_exercise(
    entry: ExerciseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exercise = Exercise(
        user_id=current_user.id,
        name=entry.name,
        category=entry.category,
        duration_minutes=entry.duration_minutes,
        calories_burned=entry.calories_burned,
        date=entry.date,
    )
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return exercise


@router.get("", response_model=list[ExerciseResponse])
def get_exercises(
    day: date = Query(default=None),
    limit: int = Query(30, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Exercise).filter(Exercise.user_id == current_user.id)
    if day:
        query = query.filter(Exercise.date == day)
    return query.order_by(Exercise.date.desc()).limit(limit).all()


@router.delete("/{exercise_id}", status_code=204)
def delete_exercise(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exercise = db.query(Exercise).filter(
        Exercise.id == exercise_id, Exercise.user_id == current_user.id
    ).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    db.delete(exercise)
    db.commit()
