"""Panneau de gestion des quotas (bande inférieure)."""
from datetime import date as Date
import customtkinter as ctk

import api_client
from api_client import APIError
from config import MAX_COVERS


class QuotaPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#18181B", corner_radius=0, **kwargs)
        self._build()

    def _build(self):
        # ── Ligne unique ──────────────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="QUOTAS",
            font=ctk.CTkFont(size=11, weight="bold"), text_color="#C9963A",
        ).pack(side="left", padx=(14, 8))

        ctk.CTkFrame(self, width=1, fg_color="#333333").pack(
            side="left", fill="y", pady=10, padx=4
        )

        # Date
        ctk.CTkLabel(self, text="Date :", text_color="#AAAAAA",
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=(8, 4))
        self._date_var = ctk.StringVar(value=Date.today().isoformat())
        ctk.CTkEntry(self, textvariable=self._date_var,
                     width=108, height=28).pack(side="left", padx=(0, 10))

        # Service
        ctk.CTkLabel(self, text="Service :", text_color="#AAAAAA",
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 4))
        self._period_var = ctk.StringVar(value="lunch")
        ctk.CTkComboBox(self, variable=self._period_var,
                        values=["lunch", "dinner"],
                        width=86, height=28,
                        command=lambda _: None,
                        ).pack(side="left", padx=(0, 10))

        # Max couverts — pré-rempli avec MAX_COVERS
        ctk.CTkLabel(self, text="Max :", text_color="#AAAAAA",
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 4))
        self._max_var = ctk.StringVar(value=str(MAX_COVERS))
        ctk.CTkEntry(self, textvariable=self._max_var,
                     width=50, height=28).pack(side="left", padx=(0, 8))

        # Boutons
        ctk.CTkButton(
            self, text="Appliquer", width=88, height=28,
            command=self._apply,
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            self, text="Voir", width=55, height=28,
            fg_color="#2A2A2E", hover_color="#3A3A3E",
            command=self._show,
        ).pack(side="left", padx=(0, 10))

        # Résultat (label dynamique)
        self._info = ctk.CTkLabel(
            self, text="", text_color="#9CA3AF", font=ctk.CTkFont(size=12)
        )
        self._info.pack(side="left", fill="x", expand=True)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _apply(self):
        d = self._date_var.get().strip()
        period = self._period_var.get()

        if not d:
            self._err("Entrez une date (AAAA-MM-JJ).")
            return
        try:
            max_c = int(self._max_var.get())
        except ValueError:
            self._err("Max doit être un entier.")
            return

        try:
            data = api_client.set_quota(d, period, max_c)
            svc = "Midi" if period == "lunch" else "Soir"
            txt = f"✓  {svc} {d}  —  {data['reserved_covers']} / {data['max_covers']} couverts"
            self._ok(txt, data["is_full"])
        except APIError as e:
            self._err(str(e))
        except Exception as e:
            self._err(f"Erreur : {e}")

    def _show(self):
        d = self._date_var.get().strip()
        period = self._period_var.get()

        if not d:
            self._err("Entrez une date (AAAA-MM-JJ).")
            return
        try:
            data = api_client.get_quota(d, period)
            svc  = "Midi" if period == "lunch" else "Soir"
            dispo = "COMPLET" if data["is_full"] else f"{data['available_covers']} places libres"
            txt = f"{svc}  {d}  —  {data['reserved_covers']} / {data['max_covers']}  —  {dispo}"
            self._ok(txt, data["is_full"])
        except APIError as e:
            self._err(str(e))
        except Exception as e:
            self._err(f"Erreur : {e}")

    def _ok(self, text: str, is_full: bool):
        self._info.configure(
            text=text,
            text_color="#EF4444" if is_full else "#10B981",
        )

    def _err(self, text: str):
        self._info.configure(text=f"⚠  {text}", text_color="#F59E0B")
