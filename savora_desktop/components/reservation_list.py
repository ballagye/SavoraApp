"""Panneau gauche : liste filtrée des réservations."""
import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Dict, Optional
import customtkinter as ctk

STATUS_COLORS = {
    "pending":   "#F59E0B",
    "confirmed": "#10B981",
    "refused":   "#EF4444",
    "cancelled": "#6B7280",
}

STATUS_LABELS = {
    "pending":   "En attente",
    "confirmed": "Confirmée",
    "refused":   "Refusée",
    "cancelled": "Annulée",
}


class ReservationList(ctk.CTkFrame):
    def __init__(self, master, on_select: Callable[[Dict], None], **kwargs):
        super().__init__(master, **kwargs)
        self._on_select = on_select
        self._reservations: List[Dict] = []
        self._build()

    def _build(self):
        # ── Filtres ────────────────────────────────────────────────────────────
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", padx=10, pady=(10, 4))

        ctk.CTkLabel(filter_frame, text="Date :").pack(side="left")
        self._date_var = ctk.StringVar()
        self._date_entry = ctk.CTkEntry(
            filter_frame, textvariable=self._date_var, placeholder_text="AAAA-MM-JJ", width=120
        )
        self._date_entry.pack(side="left", padx=(4, 12))

        ctk.CTkLabel(filter_frame, text="Service :").pack(side="left")
        self._period_var = ctk.StringVar(value="Tous")
        self._period_combo = ctk.CTkComboBox(
            filter_frame,
            variable=self._period_var,
            values=["Tous", "lunch", "dinner"],
            width=100,
            command=lambda _: self._on_filter(),
        )
        self._period_combo.pack(side="left", padx=(4, 12))

        ctk.CTkLabel(filter_frame, text="Statut :").pack(side="left")
        self._status_var = ctk.StringVar(value="Tous")
        self._status_combo = ctk.CTkComboBox(
            filter_frame,
            variable=self._status_var,
            values=["Tous", "pending", "confirmed", "refused", "cancelled"],
            width=120,
            command=lambda _: self._on_filter(),
        )
        self._status_combo.pack(side="left", padx=(4, 12))

        ctk.CTkButton(filter_frame, text="Filtrer", width=80, command=self._on_filter).pack(
            side="left"
        )

        # ── Tableau ────────────────────────────────────────────────────────────
        cols = ("id", "date", "service", "heure", "couverts", "client", "statut")
        self._tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="browse")

        for col, label, width in [
            ("id",       "#",         40),
            ("date",     "Date",      100),
            ("service",  "Service",   80),
            ("heure",    "Heure",     60),
            ("couverts", "Cvts",      50),
            ("client",   "Client",    180),
            ("statut",   "Statut",    100),
        ]:
            self._tree.heading(col, text=label)
            self._tree.column(col, width=width, anchor="center" if col != "client" else "w")

        for status, color in STATUS_COLORS.items():
            self._tree.tag_configure(status, foreground=color)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self._tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self._tree.bind("<<TreeviewSelect>>", self._on_tree_select)

    # ── Méthodes publiques ─────────────────────────────────────────────────────

    def load(self, reservations: List[Dict]):
        self._reservations = reservations
        self._refresh_tree(reservations)

    def _on_filter(self):
        """Filtre côté client sur la liste déjà chargée."""
        date_f = self._date_var.get().strip()
        period_f = self._period_var.get()
        status_f = self._status_var.get()

        filtered = self._reservations
        if date_f:
            filtered = [r for r in filtered if r["date"] == date_f]
        if period_f != "Tous":
            filtered = [r for r in filtered if r["meal_period"] == period_f]
        if status_f != "Tous":
            filtered = [r for r in filtered if r["status"] == status_f]

        self._refresh_tree(filtered)

    def _refresh_tree(self, reservations: List[Dict]):
        self._tree.delete(*self._tree.get_children())
        for r in reservations:
            client = f"{r['civility']} {r['first_name']} {r['last_name']}"
            tag = r["status"]
            self._tree.insert(
                "",
                "end",
                iid=str(r["id"]),
                values=(
                    r["id"],
                    r["date"],
                    "Midi" if r["meal_period"] == "lunch" else "Soir",
                    r["time_slot"],
                    r["party_size"],
                    client,
                    STATUS_LABELS.get(r["status"], r["status"]),
                ),
                tags=(tag,),
            )

    def _on_tree_select(self, _event):
        selected = self._tree.selection()
        if not selected:
            return
        rid = int(selected[0])
        match = next((r for r in self._reservations if r["id"] == rid), None)
        if match:
            self._on_select(match)

    def get_filters(self) -> dict:
        return {
            "date": self._date_var.get().strip() or None,
            "meal_period": self._period_var.get() if self._period_var.get() != "Tous" else None,
            "status": self._status_var.get() if self._status_var.get() != "Tous" else None,
        }
