from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import DailyQuota, MealPeriod, Reservation, ReservationStatus
from schemas import AvailabilityOut, QuotaOut, QuotaSet

router = APIRouter(tags=["Quota & Disponibilité"])

# ── Capacité du restaurant ─────────────────────────────────────────────────────
# Modifier cette valeur pour changer la capacité max par service (midi / soir)
DEFAULT_MAX_COVERS = 15


def _reserved(db: Session, d: date, period: MealPeriod) -> int:
    result = db.query(func.coalesce(func.sum(Reservation.party_size), 0)).filter(
        Reservation.date == d,
        Reservation.meal_period == period,
        Reservation.status.in_([ReservationStatus.pending, ReservationStatus.confirmed]),
    ).scalar()
    return int(result)


def _max_covers(db: Session, d: date, period: MealPeriod) -> int:
    quota = db.query(DailyQuota).filter(
        DailyQuota.date == d, DailyQuota.meal_period == period
    ).first()
    return quota.max_covers if quota else DEFAULT_MAX_COVERS


# ── Quota d'un service ─────────────────────────────────────────────────────────

@router.get("/quota/{date}/{meal_period}", response_model=QuotaOut)
def get_quota(date: date, meal_period: MealPeriod, db: Session = Depends(get_db)):
    max_c = _max_covers(db, date, meal_period)
    reserved = _reserved(db, date, meal_period)
    available = max(0, max_c - reserved)
    return QuotaOut(
        date=date,
        meal_period=meal_period,
        max_covers=max_c,
        reserved_covers=reserved,
        available_covers=available,
        is_full=(available == 0),
    )


@router.put("/quota/{date}/{meal_period}", response_model=QuotaOut)
def set_quota(
    date: date, meal_period: MealPeriod, payload: QuotaSet, db: Session = Depends(get_db)
):
    quota = db.query(DailyQuota).filter(
        DailyQuota.date == date, DailyQuota.meal_period == meal_period
    ).first()
    if quota:
        quota.max_covers = payload.max_covers
    else:
        quota = DailyQuota(date=date, meal_period=meal_period, max_covers=payload.max_covers)
        db.add(quota)
    db.commit()

    reserved = _reserved(db, date, meal_period)
    available = max(0, payload.max_covers - reserved)
    return QuotaOut(
        date=date,
        meal_period=meal_period,
        max_covers=payload.max_covers,
        reserved_covers=reserved,
        available_covers=available,
        is_full=(available == 0),
    )


# ── Disponibilité pour le site SvelteKit ──────────────────────────────────────

@router.get("/availability/{date}", response_model=AvailabilityOut)
def get_availability(date: date, db: Session = Depends(get_db)):
    lunch_max = _max_covers(db, date, MealPeriod.lunch)
    dinner_max = _max_covers(db, date, MealPeriod.dinner)
    lunch_reserved = _reserved(db, date, MealPeriod.lunch)
    dinner_reserved = _reserved(db, date, MealPeriod.dinner)

    return AvailabilityOut(
        date=date,
        lunch_available=(lunch_reserved < lunch_max),
        dinner_available=(dinner_reserved < dinner_max),
        lunch_remaining=max(0, lunch_max - lunch_reserved),
        dinner_remaining=max(0, dinner_max - dinner_reserved),
    )
