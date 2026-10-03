from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from database import get_db
from models import DiaryEntry, Exercise, WeightLog, User
from schemas import StreakResponse, DailyReport, ProgressReport
from auth import get_current_user

router = APIRouter(prefix="/api/progress", tags=["progress"])


def _compute_streaks(logged_dates: list[date]) -> tuple[int, int]:
    if not logged_dates:
        return 0, 0
    sorted_dates = sorted(set(logged_dates))
    current = 1
    longest = 1
    for i in range(1, len(sorted_dates)):
        if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
            current += 1
            longest = max(longest, current)
        else:
            current = 1
    today = date.today()
    last = sorted_dates[-1]
    if last != today and last != today - timedelta(days=1):
        current = 0
    return current, longest


@router.get("/streaks", response_model=StreakResponse)
def get_streaks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    diary_dates = [
        row[0] for row in
        db.query(DiaryEntry.date)
        .filter(DiaryEntry.user_id == current_user.id)
        .distinct()
        .all()
    ]
    exercise_dates = [
        row[0] for row in
        db.query(Exercise.date)
        .filter(Exercise.user_id == current_user.id)
        .distinct()
        .all()
    ]
    all_dates = list(set(diary_dates + exercise_dates))
    current_streak, longest_streak = _compute_streaks(all_dates)

    return StreakResponse(
        current_streak=current_streak,
        longest_streak=longest_streak,
        total_logged_days=len(set(all_dates)),
        last_logged_date=max(all_dates) if all_dates else None,
    )


@router.get("/report", response_model=ProgressReport)
def get_progress_report(
    days: int = Query(7, le=90, description="Number of days to report on"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    end = date.today()
    start = end - timedelta(days=days - 1)

    diary_entries = (
        db.query(DiaryEntry)
        .options(joinedload(DiaryEntry.food))
        .filter(
            DiaryEntry.user_id == current_user.id,
            DiaryEntry.date >= start,
            DiaryEntry.date <= end,
        )
        .all()
    )

    exercises = (
        db.query(Exercise)
        .filter(
            Exercise.user_id == current_user.id,
            Exercise.date >= start,
            Exercise.date <= end,
        )
        .all()
    )

    daily: dict[date, DailyReport] = {}
    for d in range(days):
        day = start + timedelta(days=d)
        daily[day] = DailyReport(
            date=day, calories_consumed=0, calories_burned=0,
            net_calories=0, protein=0, carbs=0, fat=0, exercise_minutes=0,
        )

    for entry in diary_entries:
        r = daily.get(entry.date)
        if not r:
            continue
        r.calories_consumed += entry.food.calories * entry.servings
        r.protein += entry.food.protein * entry.servings
        r.carbs += entry.food.carbs * entry.servings
        r.fat += entry.food.fat * entry.servings

    for ex in exercises:
        r = daily.get(ex.date)
        if not r:
            continue
        r.calories_burned += ex.calories_burned
        r.exercise_minutes += ex.duration_minutes

    day_list = []
    for day in sorted(daily):
        r = daily[day]
        r.net_calories = round(r.calories_consumed - r.calories_burned, 1)
        r.calories_consumed = round(r.calories_consumed, 1)
        r.calories_burned = round(r.calories_burned, 1)
        r.protein = round(r.protein, 1)
        r.carbs = round(r.carbs, 1)
        r.fat = round(r.fat, 1)
        day_list.append(r)

    days_with_food = [d for d in day_list if d.calories_consumed > 0]
    n = len(days_with_food) or 1

    weights = (
        db.query(WeightLog)
        .filter(
            WeightLog.user_id == current_user.id,
            WeightLog.date >= start,
            WeightLog.date <= end,
        )
        .order_by(WeightLog.date)
        .all()
    )
    weight_change = None
    if len(weights) >= 2:
        weight_change = round(weights[-1].weight - weights[0].weight, 1)

    all_logged_dates = list(set(
        [e.date for e in diary_entries] + [e.date for e in exercises]
    ))
    current_streak, longest_streak = _compute_streaks(all_logged_dates)

    return ProgressReport(
        period_start=start,
        period_end=end,
        days=day_list,
        avg_daily_calories=round(sum(d.calories_consumed for d in days_with_food) / n, 1),
        avg_daily_protein=round(sum(d.protein for d in days_with_food) / n, 1),
        avg_daily_carbs=round(sum(d.carbs for d in days_with_food) / n, 1),
        avg_daily_fat=round(sum(d.fat for d in days_with_food) / n, 1),
        total_exercise_minutes=sum(d.exercise_minutes for d in day_list),
        total_calories_burned=round(sum(d.calories_burned for d in day_list), 1),
        weight_change=weight_change,
        current_streak=current_streak,
        longest_streak=longest_streak,
    )
