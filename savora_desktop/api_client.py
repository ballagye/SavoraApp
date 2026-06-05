"""Client HTTP vers l'API FastAPI Savora."""
from typing import Any, Dict, List, Optional
import requests

BASE_URL = "http://localhost:8000"


class APIError(Exception):
    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


def _handle(response: requests.Response) -> Any:
    if response.status_code in (200, 201):
        return response.json()
    try:
        detail = response.json().get("detail", response.text)
    except Exception:
        detail = response.text
    raise APIError(str(detail))


# ── Réservations ──────────────────────────────────────────────────────────────

def create_reservation(data: Dict) -> Dict:
    """Crée une nouvelle réservation (POST /reservations/)."""
    r = requests.post(f"{BASE_URL}/reservations/", json=data, timeout=10)
    return _handle(r)


def get_reservations(
    date: Optional[str] = None,
    meal_period: Optional[str] = None,
    status: Optional[str] = None,
) -> List[Dict]:
    params = {}
    if date:
        params["date"] = date
    if meal_period:
        params["meal_period"] = meal_period
    if status:
        params["status"] = status
    r = requests.get(f"{BASE_URL}/reservations", params=params, timeout=10)
    return _handle(r)


def get_reservation(reservation_id: int) -> Dict:
    r = requests.get(f"{BASE_URL}/reservations/{reservation_id}", timeout=10)
    return _handle(r)


def update_status(reservation_id: int, status: str, staff_note: str = "") -> Dict:
    payload = {"status": status}
    if staff_note:
        payload["staff_note"] = staff_note
    r = requests.patch(
        f"{BASE_URL}/reservations/{reservation_id}/status",
        json=payload,
        timeout=10,
    )
    return _handle(r)


def update_reservation(reservation_id: int, data: Dict) -> Dict:
    r = requests.patch(
        f"{BASE_URL}/reservations/{reservation_id}",
        json=data,
        timeout=10,
    )
    return _handle(r)


def delete_reservation(reservation_id: int) -> None:
    r = requests.delete(f"{BASE_URL}/reservations/{reservation_id}", timeout=10)
    if r.status_code != 204:
        _handle(r)


# ── Clients ───────────────────────────────────────────────────────────────────

def get_clients() -> List[Dict]:
    r = requests.get(f"{BASE_URL}/clients", timeout=10)
    return _handle(r)


def get_client(client_id: int) -> Dict:
    r = requests.get(f"{BASE_URL}/clients/{client_id}", timeout=10)
    return _handle(r)


def get_client_reservations(client_id: int) -> List[Dict]:
    r = requests.get(f"{BASE_URL}/clients/{client_id}/reservations", timeout=10)
    return _handle(r)


def import_clients_from_reservations() -> Dict:
    """Crée automatiquement les fiches clients depuis les réservations existantes."""
    r = requests.post(f"{BASE_URL}/clients/import-from-reservations", timeout=10)
    return _handle(r)


def create_client(data: Dict) -> Dict:
    r = requests.post(f"{BASE_URL}/clients/", json=data, timeout=10)
    return _handle(r)


def update_client(client_id: int, data: Dict) -> Dict:
    r = requests.patch(f"{BASE_URL}/clients/{client_id}", json=data, timeout=10)
    return _handle(r)


def delete_client(client_id: int) -> None:
    r = requests.delete(f"{BASE_URL}/clients/{client_id}", timeout=10)
    if r.status_code != 204:
        _handle(r)


# ── Quota ──────────────────────────────────────────────────────────────────────

def get_quota(date: str, meal_period: str) -> Dict:
    r = requests.get(f"{BASE_URL}/quota/{date}/{meal_period}", timeout=10)
    return _handle(r)


def set_quota(date: str, meal_period: str, max_covers: int) -> Dict:
    r = requests.put(
        f"{BASE_URL}/quota/{date}/{meal_period}",
        json={"max_covers": max_covers},
        timeout=10,
    )
    return _handle(r)
