"""CRUD complet pour la gestion des clients."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Client, Reservation
from schemas import ClientCreate, ClientOut, ClientUpdate, ReservationOut

router = APIRouter(prefix="/clients", tags=["Clients"])


def _with_count(client: Client, db: Session) -> ClientOut:
    """Ajoute le nombre de réservations à la fiche client."""
    count = db.query(Reservation).filter(Reservation.email == client.email).count()
    out = ClientOut.model_validate(client)
    out.reservation_count = count
    return out


# ── Liste ──────────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[ClientOut])
def list_clients(db: Session = Depends(get_db)):
    clients = db.query(Client).order_by(Client.last_name, Client.first_name).all()
    return [_with_count(c, db) for c in clients]


# ── Détail ─────────────────────────────────────────────────────────────────────

@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: int, db: Session = Depends(get_db)):
    c = db.query(Client).filter(Client.id == client_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Client introuvable.")
    return _with_count(c, db)


@router.get("/{client_id}/reservations", response_model=List[ReservationOut])
def get_client_reservations(client_id: int, db: Session = Depends(get_db)):
    """Retourne toutes les réservations liées à cet email client."""
    c = db.query(Client).filter(Client.id == client_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Client introuvable.")
    return (
        db.query(Reservation)
        .filter(Reservation.email == c.email)
        .order_by(Reservation.date.desc(), Reservation.time_slot)
        .all()
    )


# ── Création ───────────────────────────────────────────────────────────────────

@router.post("/", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
def create_client(payload: ClientCreate, db: Session = Depends(get_db)):
    if db.query(Client).filter(Client.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Un client avec cet email existe déjà.")
    client = Client(**payload.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return _with_count(client, db)


# ── Modification ───────────────────────────────────────────────────────────────

@router.patch("/{client_id}", response_model=ClientOut)
def update_client(client_id: int, payload: ClientUpdate, db: Session = Depends(get_db)):
    c = db.query(Client).filter(Client.id == client_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Client introuvable.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(c, field, value)
    db.commit()
    db.refresh(c)
    return _with_count(c, db)


# ── Import depuis les réservations ────────────────────────────────────────────

@router.post("/import-from-reservations", tags=["Clients"])
def import_from_reservations(db: Session = Depends(get_db)):
    """Crée automatiquement un client pour chaque email unique en réservations."""
    reservations = db.query(Reservation).all()
    created = 0
    for r in reservations:
        if not db.query(Client).filter(Client.email == r.email).first():
            db.add(Client(
                civility=r.civility,
                first_name=r.first_name,
                last_name=r.last_name,
                phone=r.phone,
                email=r.email,
            ))
            created += 1
    db.commit()
    return {"imported": created}


# ── Suppression ────────────────────────────────────────────────────────────────

@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: int, db: Session = Depends(get_db)):
    c = db.query(Client).filter(Client.id == client_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Client introuvable.")
    db.delete(c)
    db.commit()
