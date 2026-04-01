from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
from models import Civility, MealPeriod, ReservationStatus

LUNCH_SLOTS = {"12:00", "12:30", "13:00", "13:30"}
DINNER_SLOTS = {"19:00", "19:30", "20:00", "20:30", "21:00", "21:30"}


# ── Réservation ────────────────────────────────────────────────────────────────

class ReservationCreate(BaseModel):
    party_size: int
    date: date
    time_slot: str
    meal_period: MealPeriod
    civility: Civility
    first_name: str
    last_name: str
    phone: str
    email: EmailStr
    special_requests: Optional[str] = None
    save_data_consent: bool = False
    terms_accepted: bool

    @field_validator("party_size")
    @classmethod
    def check_party_size(cls, v: int) -> int:
        if not 1 <= v <= 6:
            raise ValueError("Le nombre de couverts doit être entre 1 et 6.")
        return v

    @field_validator("time_slot")
    @classmethod
    def check_time_slot(cls, v: str) -> str:
        if v not in LUNCH_SLOTS | DINNER_SLOTS:
            raise ValueError(f"Créneau horaire invalide : {v}")
        return v

    @field_validator("date")
    @classmethod
    def check_date_future(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("La date de réservation ne peut pas être dans le passé.")
        return v

    @field_validator("terms_accepted")
    @classmethod
    def check_terms(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Les conditions générales doivent être acceptées.")
        return v


class ReservationUpdate(BaseModel):
    party_size: Optional[int] = None
    date: Optional[date] = None
    time_slot: Optional[str] = None
    meal_period: Optional[MealPeriod] = None
    civility: Optional[Civility] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    special_requests: Optional[str] = None
    staff_note: Optional[str] = None


class StatusUpdate(BaseModel):
    status: ReservationStatus
    staff_note: Optional[str] = None


class ReservationOut(BaseModel):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    party_size: int
    date: date
    time_slot: str
    meal_period: MealPeriod
    civility: Civility
    first_name: str
    last_name: str
    phone: str
    email: str
    special_requests: Optional[str]
    status: ReservationStatus
    staff_note: Optional[str]

    model_config = {"from_attributes": True}


# ── Quota ──────────────────────────────────────────────────────────────────────

class QuotaSet(BaseModel):
    max_covers: int

    @field_validator("max_covers")
    @classmethod
    def positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Le quota doit être supérieur à 0.")
        return v


class QuotaOut(BaseModel):
    date: date
    meal_period: MealPeriod
    max_covers: int
    reserved_covers: int
    available_covers: int
    is_full: bool

    model_config = {"from_attributes": True}


# ── Disponibilité (utilisé par le site SvelteKit) ──────────────────────────────

class AvailabilityOut(BaseModel):
    date: date
    lunch_available: bool
    dinner_available: bool
    lunch_remaining: int
    dinner_remaining: int
