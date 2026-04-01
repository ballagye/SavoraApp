"""Panneau droit : détail d'une réservation + actions du personnel."""
from typing import Callable, Dict, Optional
import customtkinter as ctk
from tkinter import messagebox

import api_client
from api_client import APIError

STATUS_FR = {
    "pending":   "En attente",
    "confirmed": "Confirmée",
    "refused":   "Refusée",
    "cancelled": "Annulée",
}
STATUS_BG = {
    "pending":   "#F59E0B",
    "confirmed": "#10B981",
    "refused":   "#EF4444",
    "cancelled": "#6B7280",
}
MEAL_FR = {"lunch": "Midi (Aube)", "dinner": "Soir (Crépuscule)"}


class ReservationDetail(ctk.CTkFrame):
    def __init__(self, master, on_refresh: Callable, **kwargs):
        super().__init__(master, **kwargs)
        self._on_refresh = on_refresh
        self._current: Optional[Dict] = None
        self._build()

    def _build(self):
        self._title_label = ctk.CTkLabel(
            self, text="Sélectionnez une réservation",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self._title_label.pack(pady=(16, 8))

        # ── Infos ──────────────────────────────────────────────────────────────
        info_frame = ctk.CTkFrame(self)
        info_frame.pack(fill="x", padx=16, pady=4)

        self._info_vars: Dict[str, ctk.StringVar] = {}
        fields = [
            ("Date",      "date"),
            ("Service",   "meal_period"),
            ("Heure",     "time_slot"),
            ("Couverts",  "party_size"),
            ("Civilité",  "civility"),
            ("Prénom",    "first_name"),
            ("Nom",       "last_name"),
            ("Téléphone", "phone"),
            ("Email",     "email"),
            ("Statut",    "status"),
        ]
        for row, (label, key) in enumerate(fields):
            ctk.CTkLabel(info_frame, text=f"{label} :", anchor="e", width=90).grid(
                row=row, column=0, sticky="e", padx=(8, 4), pady=3
            )
            var = ctk.StringVar(value="—")
            self._info_vars[key] = var
            ctk.CTkLabel(info_frame, textvariable=var, anchor="w").grid(
                row=row, column=1, sticky="w", pady=3
            )

        # ── Demandes spéciales ────────────────────────────────────────────────
        ctk.CTkLabel(self, text="Demandes spéciales :", anchor="w").pack(
            fill="x", padx=16, pady=(8, 0)
        )
        self._special_box = ctk.CTkTextbox(self, height=60, state="disabled")
        self._special_box.pack(fill="x", padx=16, pady=(0, 8))

        # ── Note interne ──────────────────────────────────────────────────────
        ctk.CTkLabel(self, text="Note interne (personnel) :", anchor="w").pack(
            fill="x", padx=16
        )
        self._note_entry = ctk.CTkTextbox(self, height=60)
        self._note_entry.pack(fill="x", padx=16, pady=(0, 12))

        # ── Boutons d'action ──────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=(0, 12))

        self._btn_confirm = ctk.CTkButton(
            btn_frame, text="Confirmer", fg_color="#10B981", hover_color="#059669",
            command=self._confirm
        )
        self._btn_confirm.pack(side="left", padx=4, expand=True, fill="x")

        self._btn_refuse = ctk.CTkButton(
            btn_frame, text="Refuser", fg_color="#EF4444", hover_color="#DC2626",
            command=self._refuse
        )
        self._btn_refuse.pack(side="left", padx=4, expand=True, fill="x")

        self._btn_cancel = ctk.CTkButton(
            btn_frame, text="Annuler", fg_color="#6B7280", hover_color="#4B5563",
            command=self._cancel
        )
        self._btn_cancel.pack(side="left", padx=4, expand=True, fill="x")

        # ── Modification rapide du nombre de couverts ─────────────────────────
        edit_frame = ctk.CTkFrame(self, fg_color="transparent")
        edit_frame.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(edit_frame, text="Modifier couverts :").pack(side="left")
        self._covers_var = ctk.StringVar()
        self._covers_entry = ctk.CTkEntry(edit_frame, textvariable=self._covers_var, width=60)
        self._covers_entry.pack(side="left", padx=6)
        ctk.CTkButton(
            edit_frame, text="Enregistrer", width=110, command=self._save_covers
        ).pack(side="left")

        self._set_buttons_state("disabled")

    # ── Chargement d'une réservation ──────────────────────────────────────────

    def load(self, reservation: Dict):
        self._current = reservation
        r = reservation

        self._title_label.configure(text=f"Réservation #{r['id']}")

        self._info_vars["date"].set(r["date"])
        self._info_vars["meal_period"].set(MEAL_FR.get(r["meal_period"], r["meal_period"]))
        self._info_vars["time_slot"].set(r["time_slot"])
        self._info_vars["party_size"].set(str(r["party_size"]))
        self._info_vars["civility"].set(r["civility"])
        self._info_vars["first_name"].set(r["first_name"])
        self._info_vars["last_name"].set(r["last_name"])
        self._info_vars["phone"].set(r["phone"])
        self._info_vars["email"].set(r["email"])
        self._info_vars["status"].set(STATUS_FR.get(r["status"], r["status"]))

        self._special_box.configure(state="normal")
        self._special_box.delete("1.0", "end")
        self._special_box.insert("1.0", r.get("special_requests") or "—")
        self._special_box.configure(state="disabled")

        self._note_entry.delete("1.0", "end")
        if r.get("staff_note"):
            self._note_entry.insert("1.0", r["staff_note"])

        self._covers_var.set(str(r["party_size"]))
        self._set_buttons_state("normal")

    def _set_buttons_state(self, state: str):
        for btn in (self._btn_confirm, self._btn_refuse, self._btn_cancel, self._covers_entry):
            btn.configure(state=state)

    # ── Actions ────────────────────────────────────────────────────────────────

    def _note(self) -> str:
        return self._note_entry.get("1.0", "end").strip()

    def _confirm(self):
        self._change_status("confirmed")

    def _refuse(self):
        self._change_status("refused")

    def _cancel(self):
        self._change_status("cancelled")

    def _change_status(self, new_status: str):
        if not self._current:
            return
        rid = self._current["id"]
        try:
            api_client.update_status(rid, new_status, staff_note=self._note())
            self._on_refresh()
        except APIError as e:
            messagebox.showerror("Erreur API", str(e))

    def _save_covers(self):
        if not self._current:
            return
        try:
            val = int(self._covers_var.get())
        except ValueError:
            messagebox.showwarning("Valeur invalide", "Entrez un nombre entier.")
            return
        try:
            api_client.update_reservation(self._current["id"], {"party_size": val})
            self._on_refresh()
        except APIError as e:
            messagebox.showerror("Erreur API", str(e))
