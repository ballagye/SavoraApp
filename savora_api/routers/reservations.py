from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import Client, DailyQuota, MealPeriod, Reservation, ReservationStatus
from schemas import ReservationCreate, ReservationOut, ReservationUpdate, StatusUpdate

router = APIRouter(prefix="/reservations", tags=["Réservations"])


def _get_reserved_covers(db: Session, date, meal_period: MealPeriod) -> int:
    """Somme des couverts pour les réservations confirmées ou en attente."""
    result = db.query(func.coalesce(func.sum(Reservation.party_size), 0)).filter(
        Reservation.date == date,
        Reservation.meal_period == meal_period,
        Reservation.status.in_([ReservationStatus.pending, ReservationStatus.confirmed]),
    ).scalar()
    return int(result)


def _check_quota(db: Session, date, meal_period: MealPeriod, party_size: int,
                 exclude_id: Optional[int] = None):
    """Lève une 409 si le quota est dépassé."""
    quota = db.query(DailyQuota).filter(
        DailyQuota.date == date,
        DailyQuota.meal_period == meal_period,
    ).first()

    if quota is None:
        return  # Pas de quota configuré → pas de blocage

    reserved = _get_reserved_covers(db, date, meal_period)
    if exclude_id:
        # On soustrait les couverts de la réservation en cours de modification
        existing = db.query(Reservation).filter(Reservation.id == exclude_id).first()
        if existing and existing.status in (ReservationStatus.pending, ReservationStatus.confirmed):
            reserved -= existing.party_size

    if reserved + party_size > quota.max_covers:
        remaining = quota.max_covers - reserved
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Quota atteint pour ce service. Places restantes : {max(0, remaining)}.",
        )


# ── Création (depuis le site web) ─────────────────────────────────────────────

@router.post("/", response_model=ReservationOut, status_code=status.HTTP_201_CREATED)
def create_reservation(payload: ReservationCreate, db: Session = Depends(get_db)):
    _check_quota(db, payload.date, payload.meal_period, payload.party_size)

    # Crée la réservation
    reservation = Reservation(**payload.model_dump())
    db.add(reservation)

    # Auto-crée le client si inexistant (lien par email)
    if not db.query(Client).filter(Client.email == payload.email).first():
        db.add(Client(
            civility=payload.civility,
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone=payload.phone,
            email=payload.email,
        ))

    db.commit()
    db.refresh(reservation)
    return reservation


# ── Lecture ────────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[ReservationOut])
def list_reservations(
    date_filter: Optional[str] = Query(None, alias="date"),
    meal_period: Optional[MealPeriod] = None,
    status_filter: Optional[ReservationStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db),
):
    q = db.query(Reservation)
    if date_filter:
        q = q.filter(Reservation.date == date_filter)
    if meal_period:
        q = q.filter(Reservation.meal_period == meal_period)
    if status_filter:
        q = q.filter(Reservation.status == status_filter)
    return q.order_by(Reservation.date, Reservation.time_slot).all()


@router.get("/{reservation_id}", response_model=ReservationOut)
def get_reservation(reservation_id: int, db: Session = Depends(get_db)):
    r = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Réservation introuvable.")
    return r


# ── Mise à jour (modification par le personnel) ───────────────────────────────

@router.patch("/{reservation_id}", response_model=ReservationOut)
def update_reservation(
    reservation_id: int, payload: ReservationUpdate, db: Session = Depends(get_db)
):
    r = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Réservation introuvable.")

    update_data = payload.model_dump(exclude_unset=True)

    new_date = update_data.get("date", r.date)
    new_period = update_data.get("meal_period", r.meal_period)
    new_size = update_data.get("party_size", r.party_size)

    if "party_size" in update_data or "date" in update_data or "meal_period" in update_data:
        _check_quota(db, new_date, new_period, new_size, exclude_id=reservation_id)

    for field, value in update_data.items():
        setattr(r, field, value)

    db.commit()
    db.refresh(r)
    return r


# ── Changement de statut (valider / refuser) ──────────────────────────────────

@router.patch("/{reservation_id}/status", response_model=ReservationOut)
def update_status(
    reservation_id: int, payload: StatusUpdate, db: Session = Depends(get_db)
):
    r = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Réservation introuvable.")

    # Si on confirme, on revérifie le quota
    if payload.status == ReservationStatus.confirmed:
        _check_quota(db, r.date, r.meal_period, r.party_size, exclude_id=r.id)

    r.status = payload.status
    if payload.staff_note is not None:
        r.staff_note = payload.staff_note

    db.commit()
    db.refresh(r)
    return r


# ── Suppression ───────────────────────────────────────────────────────────────

@router.delete("/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reservation(reservation_id: int, db: Session = Depends(get_db)):
    r = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Réservation introuvable.")
    db.delete(r)
    db.commit()
