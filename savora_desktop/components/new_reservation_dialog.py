"""Dialogue de création d'une réservation (personnel uniquement).
   Couvre le C du CRUD — les autres opérations sont dans reservation_detail.py
"""
from datetime import date as Date
from tkinter import messagebox
from typing import Callable

import customtkinter as ctk

import api_client
from api_client import APIError

# ── Créneaux disponibles (doit correspondre à schemas.py côté API) ─────────────
LUNCH_SLOTS  = ["12:00", "12:30", "13:00", "13:30"]
DINNER_SLOTS = ["19:00", "19:30", "20:00", "20:30", "21:00", "21:30"]
ALL_SLOTS    = LUNCH_SLOTS + DINNER_SLOTS

CIVILITIES = ["Madame", "Monsieur", "Mx."]


class NewReservationDialog(ctk.CTkToplevel):
    """Fenêtre modale de création d'une réservation."""

    def __init__(self, master, on_created: Callable):
        super().__init__(master)
        self.title("Nouvelle réservation")
        self.geometry("460x580")
        self.resizable(False, False)
        self._on_created = on_created
        self._build()
        self.grab_set()           # Bloque la fenêtre principale
        self.focus_force()

    # ── Construction ──────────────────────────────────────────────────────────

    def _build(self):
        # En-tête
        ctk.CTkLabel(
            self, text="Nouvelle réservation",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=24, pady=(18, 4))

        ctk.CTkLabel(
            self, text="Remplissez les champs ci-dessous puis cliquez sur Créer.",
            font=ctk.CTkFont(size=12), text_color="#888899",
        ).pack(anchor="w", padx=24, pady=(0, 12))

        # Formulaire dans un frame scrollable
        form = ctk.CTkScrollableFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=24)

        # ── Date ──────────────────────────────────────────────────────────────
        self._date_var = ctk.StringVar(value=Date.today().isoformat())
        self._field(form, "Date (AAAA-MM-JJ)  *", self._date_var)

        # ── Créneau ───────────────────────────────────────────────────────────
        ctk.CTkLabel(form, text="Créneau  *", anchor="w",
                     font=ctk.CTkFont(size=12)).pack(fill="x", pady=(8, 2))
        self._slot_var = ctk.StringVar(value="12:00")
        ctk.CTkComboBox(
            form, variable=self._slot_var, values=ALL_SLOTS,
            width=200, height=32, state="readonly",
        ).pack(anchor="w")

        # ── Couverts ──────────────────────────────────────────────────────────
        ctk.CTkLabel(form, text="Nombre de couverts  *", anchor="w",
                     font=ctk.CTkFont(size=12)).pack(fill="x", pady=(8, 2))
        self._covers_var = ctk.StringVar(value="2")
        ctk.CTkComboBox(
            form, variable=self._covers_var,
            values=["1", "2", "3", "4", "5", "6"],
            width=100, height=32, state="readonly",
        ).pack(anchor="w")

        # ── Civilité ──────────────────────────────────────────────────────────
        ctk.CTkLabel(form, text="Civilité  *", anchor="w",
                     font=ctk.CTkFont(size=12)).pack(fill="x", pady=(8, 2))
        self._civ_var = ctk.StringVar(value="Madame")
        ctk.CTkComboBox(
            form, variable=self._civ_var, values=CIVILITIES,
            width=160, height=32, state="readonly",
        ).pack(anchor="w")

        # ── Prénom / Nom ──────────────────────────────────────────────────────
        self._prenom_var = ctk.StringVar()
        self._field(form, "Prénom  *", self._prenom_var)

        self._nom_var = ctk.StringVar()
        self._field(form, "Nom  *", self._nom_var)

        # ── Téléphone / Email ─────────────────────────────────────────────────
        self._tel_var = ctk.StringVar()
        self._field(form, "Téléphone  *", self._tel_var)

        self._email_var = ctk.StringVar()
        self._field(form, "Email  *", self._email_var)

        # ── Demandes spéciales ────────────────────────────────────────────────
        ctk.CTkLabel(form, text="Demandes spéciales", anchor="w",
                     font=ctk.CTkFont(size=12)).pack(fill="x", pady=(8, 2))
        self._notes = ctk.CTkTextbox(form, height=60, fg_color="#212127",
                                      corner_radius=6)
        self._notes.pack(fill="x")

        # Message d'erreur inline
        self._err = ctk.CTkLabel(form, text="", text_color="#EF4444",
                                  font=ctk.CTkFont(size=11), anchor="w")
        self._err.pack(fill="x", pady=(8, 0))

        # ── Boutons ───────────────────────────────────────────────────────────
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", padx=24, pady=12)

        ctk.CTkButton(
            btns, text="Annuler", width=110,
            fg_color="#2A2A2E", hover_color="#3A3A3E",
            command=self.destroy,
        ).pack(side="left")

        self._submit_btn = ctk.CTkButton(
            btns, text="✓  Créer la réservation", width=220,
            fg_color="#10B981", hover_color="#059669",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._submit,
        )
        self._submit_btn.pack(side="right")

    # ── Helper de champ ───────────────────────────────────────────────────────

    def _field(self, parent, label: str, var: ctk.StringVar):
        ctk.CTkLabel(parent, text=label, anchor="w",
                     font=ctk.CTkFont(size=12)).pack(fill="x", pady=(8, 2))
        ctk.CTkEntry(parent, textvariable=var, height=32).pack(fill="x")

    # ── Soumission ────────────────────────────────────────────────────────────

    def _submit(self):
        self._err.configure(text="")

        # Validation locale
        date_str  = self._date_var.get().strip()
        slot      = self._slot_var.get()
        prenom    = self._prenom_var.get().strip()
        nom       = self._nom_var.get().strip()
        tel       = self._tel_var.get().strip()
        email     = self._email_var.get().strip()
        civ       = self._civ_var.get()
        notes     = self._notes.get("1.0", "end").strip() or None

        try:
            covers = int(self._covers_var.get())
        except ValueError:
            self._err.configure(text="⚠  Nombre de couverts invalide.")
            return

        if not all([date_str, prenom, nom, tel, email]):
            self._err.configure(text="⚠  Tous les champs obligatoires (*) doivent être remplis.")
            return

        # Détermine le service depuis le créneau
        meal_period = "lunch" if slot in LUNCH_SLOTS else "dinner"

        payload = {
            "party_size":        covers,
            "date":              date_str,
            "time_slot":         slot,
            "meal_period":       meal_period,
            "civility":          civ,
            "first_name":        prenom,
            "last_name":         nom,
            "phone":             tel,
            "email":             email,
            "special_requests":  notes,
            "save_data_consent": False,
            "terms_accepted":    True,   # Le personnel valide pour le client
        }

        self._submit_btn.configure(state="disabled", text="Création…")
        try:
            api_client.create_reservation(payload)
            self._on_created()
            self.destroy()
        except APIError as e:
            self._err.configure(text=f"⚠  {e.detail}")
            self._submit_btn.configure(state="normal", text="✓  Créer la réservation")
        except Exception as e:
            self._err.configure(text=f"⚠  Erreur : {e}")
            self._submit_btn.configure(state="normal", text="✓  Créer la réservation")
