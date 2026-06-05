import enum
from sqlalchemy import Boolean, Column, Date, DateTime, Enum, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func
from database import Base


# ── Enums (définis en premier, utilisés par toutes les tables) ─────────────────

class MealPeriod(str, enum.Enum):
    lunch = "lunch"
    dinner = "dinner"


class ReservationStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    refused = "refused"
    cancelled = "cancelled"


class Civility(str, enum.Enum):
    madame = "Madame"
    monsieur = "Monsieur"
    mx = "Mx."


# ── Table clients ──────────────────────────────────────────────────────────────

class Client(Base):
    """Un client du restaurant (lié aux réservations par email)."""
    __tablename__ = "clients"

    id         = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    civility   = Column(Enum(Civility), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name  = Column(String(100), nullable=False)
    phone      = Column(String(20),  nullable=False)
    email      = Column(String(200), nullable=False, unique=True, index=True)
    notes      = Column(Text, nullable=True)


# ── Table reservations ─────────────────────────────────────────────────────────

class Reservation(Base):
    __tablename__ = "reservations"

    id         = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    party_size  = Column(Integer, nullable=False)
    date        = Column(Date, nullable=False)
    time_slot   = Column(String(5), nullable=False)
    meal_period = Column(Enum(MealPeriod), nullable=False)

    civility   = Column(Enum(Civility), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name  = Column(String(100), nullable=False)
    phone      = Column(String(20),  nullable=False)
    email      = Column(String(200), nullable=False)

    special_requests  = Column(Text, nullable=True)
    save_data_consent = Column(Boolean, default=False)
    terms_accepted    = Column(Boolean, default=False)

    status     = Column(Enum(ReservationStatus), default=ReservationStatus.pending, nullable=False)
    staff_note = Column(Text, nullable=True)


# ── Table daily_quotas ─────────────────────────────────────────────────────────

class DailyQuota(Base):
    """Quota de couverts par service et par jour."""
    __tablename__ = "daily_quotas"
    __table_args__ = (UniqueConstraint("date", "meal_period", name="uq_quota_date_period"),)

    id          = Column(Integer, primary_key=True)
    date        = Column(Date, nullable=False)
    meal_period = Column(Enum(MealPeriod), nullable=False)
    max_covers  = Column(Integer, nullable=False, default=15)
