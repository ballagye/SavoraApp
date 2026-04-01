"""Barre de quota en bas de la fenêtre principale."""
from typing import Dict
import customtkinter as ctk
from tkinter import messagebox

import api_client
from api_client import APIError


class QuotaPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Gestion des quotas", font=ctk.CTkFont(weight="bold")).pack(
            side="left", padx=(12, 16)
        )

        ctk.CTkLabel(self, text="Date :").pack(side="left")
        self._date_var = ctk.StringVar()
        ctk.CTkEntry(self, textvariable=self._date_var, placeholder_text="AAAA-MM-JJ", width=120).pack(
            side="left", padx=(4, 10)
        )

        ctk.CTkLabel(self, text="Service :").pack(side="left")
        self._period_var = ctk.StringVar(value="lunch")
        ctk.CTkComboBox(
            self, variable=self._period_var, values=["lunch", "dinner"], width=90
        ).pack(side="left", padx=(4, 10))

        ctk.CTkLabel(self, text="Max couverts :").pack(side="left")
        self._max_var = ctk.StringVar()
        ctk.CTkEntry(self, textvariable=self._max_var, width=60).pack(side="left", padx=(4, 10))

        ctk.CTkButton(self, text="Appliquer", width=90, command=self._apply).pack(
            side="left", padx=(0, 16)
        )

        ctk.CTkButton(self, text="Voir quota", width=90, command=self._show).pack(
            side="left", padx=(0, 16)
        )

        self._info_label = ctk.CTkLabel(self, text="", text_color="#9CA3AF")
        self._info_label.pack(side="left")

    def _apply(self):
        date = self._date_var.get().strip()
        period = self._period_var.get()
        try:
            max_c = int(self._max_var.get())
        except ValueError:
            messagebox.showwarning("Valeur invalide", "Entrez un nombre entier pour le quota.")
            return
        try:
            data = api_client.set_quota(date, period, max_c)
            self._info_label.configure(
                text=f"Quota {period} {date} → {data['reserved_covers']}/{data['max_covers']} couverts",
                text_color="#10B981" if not data["is_full"] else "#EF4444",
            )
        except APIError as e:
            messagebox.showerror("Erreur API", str(e))

    def _show(self):
        date = self._date_var.get().strip()
        period = self._period_var.get()
        try:
            data = api_client.get_quota(date, period)
            full_txt = "COMPLET" if data["is_full"] else f"{data['available_covers']} places libres"
            self._info_label.configure(
                text=f"{period.capitalize()} {date} : {data['reserved_covers']}/{data['max_covers']} — {full_txt}",
                text_color="#EF4444" if data["is_full"] else "#10B981",
            )
        except APIError as e:
            messagebox.showerror("Erreur API", str(e))
