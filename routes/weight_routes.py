from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import WeightLog, User
from schemas import WeightLogCreate, WeightLogResponse
from auth import get_current_user

router = APIRouter(prefix="/api/weight", tags=["weight"])


@router.post("", response_model=WeightLogResponse, status_code=201)
def log_weight(
    entry: WeightLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(WeightLog).filter(
        WeightLog.user_id == current_user.id, WeightLog.date == entry.date
    ).first()
    if existing:
        existing.weight = entry.weight
        db.commit()
        db.refresh(existing)
        return existing

    log = WeightLog(user_id=current_user.id, weight=entry.weight, date=entry.date)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("", response_model=list[WeightLogResponse])
def get_weight_history(
    limit: int = Query(30, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(WeightLog)
        .filter(WeightLog.user_id == current_user.id)
        .order_by(WeightLog.date.desc())
        .limit(limit)
        .all()
    )


@router.delete("/{log_id}", status_code=204)
def delete_weight_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log = db.query(WeightLog).filter(
        WeightLog.id == log_id, WeightLog.user_id == current_user.id
    ).first()
    if not log:
        raise HTTPException(status_code=404, detail="Weight log not found")
    db.delete(log)
    db.commit()
