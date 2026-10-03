from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models import WaterLog, User
from schemas import WaterLogCreate, WaterLogResponse, WaterDailySummary
from auth import get_current_user

router = APIRouter(prefix="/api/water", tags=["water"])


@router.post("", response_model=WaterLogResponse, status_code=201)
def log_water(
    entry: WaterLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log = WaterLog(
        user_id=current_user.id,
        amount_ml=entry.amount_ml,
        date=entry.date,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("/today", response_model=WaterDailySummary)
def get_today_water(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = date.today()
    total = (
        db.query(func.coalesce(func.sum(WaterLog.amount_ml), 0.0))
        .filter(WaterLog.user_id == current_user.id, WaterLog.date == today)
        .scalar()
    )
    goal = current_user.water_goal_ml
    return WaterDailySummary(
        date=today,
        total_ml=round(total, 1),
        goal_ml=goal,
        remaining_ml=round(max(goal - total, 0), 1),
        percent=round(total / goal * 100, 1) if goal > 0 else 0,
    )


@router.get("", response_model=list[WaterLogResponse])
def get_water_logs(
    day: date = Query(default=None),
    limit: int = Query(30, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(WaterLog).filter(WaterLog.user_id == current_user.id)
    if day:
        query = query.filter(WaterLog.date == day)
    return query.order_by(WaterLog.date.desc(), WaterLog.id.desc()).limit(limit).all()


@router.put("/goal", response_model=dict)
def set_water_goal(
    goal_ml: float = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_user.water_goal_ml = goal_ml
    db.commit()
    return {"message": "Water goal updated", "water_goal_ml": goal_ml}


@router.delete("/{log_id}", status_code=204)
def delete_water_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log = db.query(WaterLog).filter(
        WaterLog.id == log_id, WaterLog.user_id == current_user.id
    ).first()
    if not log:
        raise HTTPException(status_code=404, detail="Water log not found")
    db.delete(log)
    db.commit()
