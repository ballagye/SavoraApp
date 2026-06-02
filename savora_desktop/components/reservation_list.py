"""Liste des réservations groupées par créneau horaire (style Zenchef)."""
from itertools import groupby
from typing import Callable, Dict, List, Optional

import customtkinter as ctk

from config import ACCENT, MAX_COVERS

STATUS_COLORS = {
    "pending":   "#F59E0B",
    "confirmed": "#10B981",
    "refused":   "#EF4444",
    "cancelled": "#6B7280",
}
STATUS_ICONS = {
    "pending":   "⏱",
    "confirmed": "✓ ",
    "refused":   "✕ ",
    "cancelled": "◷ ",
}


class ReservationList(ctk.CTkFrame):
    def __init__(self, master, on_select: Callable[[Dict], None], **kwargs):
        super().__init__(master, **kwargs)
        self._on_select = on_select
        self._reservations: List[Dict] = []
        self._date_var   = ctk.StringVar()
        self._period_var = ctk.StringVar(value="")
        self._status_var = ctk.StringVar(value="")
        self._search_var = ctk.StringVar()
        self._build()

    def _build(self):
        # ── Barre de recherche ────────────────────────────────────────────────
        search = ctk.CTkFrame(self, fg_color="#1E1E22", corner_radius=8, height=38)
        search.pack(fill="x", padx=8, pady=(8, 6))
        search.pack_propagate(False)

        ctk.CTkLabel(
            search, text="🔍", font=ctk.CTkFont(size=13), text_color="#555566"
        ).pack(side="left", padx=10)

        ctk.CTkEntry(
            search, textvariable=self._search_var,
            placeholder_text="Rechercher un client…",
            border_width=0, fg_color="transparent",
            font=ctk.CTkFont(size=13),
        ).pack(side="left", fill="x", expand=True, pady=4)

        self._search_var.trace_add("write", lambda *_: self._filter_and_rebuild())

        # ── Zone de défilement ────────────────────────────────────────────────
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    # ── API publique ──────────────────────────────────────────────────────────

    def set_date_filter(self, date_val: str):
        self._date_var.set(date_val)

    def set_period_filter(self, period: Optional[str]):
        self._period_var.set(period or "")

    def set_status_filter(self, status: Optional[str]):
        self._status_var.set(status or "")

    def load(self, reservations: List[Dict]):
        self._reservations = reservations
        self._filter_and_rebuild()

    def get_filters(self) -> dict:
        return {
            "date":        self._date_var.get() or None,
            "meal_period": self._period_var.get() or None,
            "status":      self._status_var.get() or None,
        }

    # ── Filtrage + reconstruction ─────────────────────────────────────────────

    def _filter_and_rebuild(self):
        filtered = self._reservations
        q = self._search_var.get().strip().lower()
        if len(q) >= 2:
            filtered = [
                r for r in filtered
                if q in r["first_name"].lower() or q in r["last_name"].lower()
            ]
        self._rebuild(filtered)

    def _rebuild(self, reservations: List[Dict]):
        # Vider la liste
        for w in self._scroll.winfo_children():
            w.destroy()

        if not reservations:
            ctk.CTkLabel(
                self._scroll,
                text="Aucune réservation",
                text_color="#3D3D4A", font=ctk.CTkFont(size=14),
            ).pack(pady=60)
            return

        # Grouper par créneau horaire
        sorted_r = sorted(reservations, key=lambda r: r["time_slot"])
        for slot, grp in groupby(sorted_r, key=lambda r: r["time_slot"]):
            group = list(grp)
            active_covers = sum(
                r["party_size"] for r in group
                if r["status"] in ("pending", "confirmed")
            )
            self._make_slot_header(slot, len(group), active_covers)
            for r in group:
                self._make_row(r)

    # ── En-tête de créneau ────────────────────────────────────────────────────

    def _make_slot_header(self, slot: str, count: int, covers: int):
        """Ex : 19h30    📋 3    🍴 12 / 15"""
        frame = ctk.CTkFrame(
            self._scroll, fg_color="#212127", height=30, corner_radius=4
        )
        frame.pack(fill="x", pady=(10, 2))
        frame.pack_propagate(False)

        ctk.CTkLabel(
            frame, text=slot.replace(":", "h"),
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left", padx=14)

        ctk.CTkLabel(
            frame, text=f"  📋 {count}",
            text_color="#777788", font=ctk.CTkFont(size=11),
        ).pack(side="left")

        cover_color = "#EF4444" if covers >= MAX_COVERS else ACCENT
        ctk.CTkLabel(
            frame, text=f"  🍴 {covers} / {MAX_COVERS}",
            text_color=cover_color, font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(side="left")

    # ── Ligne de réservation ──────────────────────────────────────────────────

    def _make_row(self, r: Dict):
        color = STATUS_COLORS.get(r["status"], "#6B7280")
        icon  = STATUS_ICONS.get(r["status"], "• ")
        name  = f"{r['first_name']} {r['last_name'].upper()}"

        # Conteneur extérieur (transparent, hauteur fixe)
        outer = ctk.CTkFrame(self._scroll, fg_color="transparent", height=42)
        outer.pack(fill="x", pady=1)
        outer.pack_propagate(False)

        # Barre colorée à gauche (3 px)
        border = ctk.CTkFrame(outer, width=3, fg_color=color, corner_radius=0)
        border.pack(side="left", fill="y")

        # Fond de la ligne
        NORMAL = "#1E1E25"
        HOVER  = "#272733"
        inner = ctk.CTkFrame(outer, fg_color=NORMAL, corner_radius=0)
        inner.pack(side="left", fill="both", expand=True)

        inner.columnconfigure(1, weight=1)

        # Icône statut (colonne 0)
        lbl_icon = ctk.CTkLabel(
            inner, text=icon, text_color=color,
            font=ctk.CTkFont(size=11, weight="bold"), width=26,
        )
        lbl_icon.grid(row=0, column=0, rowspan=2, padx=(8, 2), sticky="ns")

        # Nom (colonne 1, ligne 0)
        lbl_name = ctk.CTkLabel(
            inner, text=name,
            font=ctk.CTkFont(size=12, weight="bold"), anchor="w",
        )
        lbl_name.grid(row=0, column=1, sticky="sw", pady=(2, 0), padx=(2, 0))

        # Téléphone (colonne 1, ligne 1)
        lbl_phone = ctk.CTkLabel(
            inner, text=r.get("phone", ""),
            text_color="#8888AA", font=ctk.CTkFont(size=10), anchor="w",
        )
        lbl_phone.grid(row=1, column=1, sticky="nw", pady=(0, 2), padx=(2, 0))

        # Couverts (colonne 2)
        lbl_pax = ctk.CTkLabel(
            inner, text=f"{r['party_size']} pax",
            text_color="#AAAAAA", font=ctk.CTkFont(size=12, weight="bold"),
            width=60,
        )
        lbl_pax.grid(row=0, column=2, rowspan=2, padx=14, sticky="e")

        # Hover + clic sur tous les widgets de la ligne
        def on_enter(_e): inner.configure(fg_color=HOVER)
        def on_leave(_e):
            # Vérifie qu'on a vraiment quitté la ligne
            inner.after(8, lambda: _check_leave(inner))
        def on_click(_e, res=r): self._on_select(res)

        def _check_leave(f):
            try:
                rx = f.winfo_pointerx() - f.winfo_rootx()
                ry = f.winfo_pointery() - f.winfo_rooty()
                if not (0 <= rx < f.winfo_width() and 0 <= ry < f.winfo_height()):
                    f.configure(fg_color=NORMAL)
            except Exception:
                pass

        for w in (outer, border, inner, lbl_icon, lbl_name, lbl_phone, lbl_pax):
            try:
                w.bind("<Button-1>", on_click)
                w.bind("<Enter>",    on_enter)
                w.bind("<Leave>",    on_leave)
                w.configure(cursor="hand2")
            except Exception:
                pass
