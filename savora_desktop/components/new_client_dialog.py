"""Dialogue de création d'un client."""
from tkinter import messagebox
from typing import Callable

import customtkinter as ctk

import api_client
from api_client import APIError

CIVILITIES = ["Madame", "Monsieur", "Mx."]


class NewClientDialog(ctk.CTkToplevel):
    def __init__(self, master, on_created: Callable):
        super().__init__(master)
        self.title("Nouveau client")
        self.geometry("420x480")
        self.resizable(False, False)
        self._on_created = on_created
        self._build()
        self.grab_set()
        self.focus_force()

    def _build(self):
        ctk.CTkLabel(self, text="Nouveau client",
                     font=ctk.CTkFont(size=16, weight="bold")
                     ).pack(anchor="w", padx=24, pady=(18, 12))

        form = ctk.CTkScrollableFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=24)

        # Civilité
        ctk.CTkLabel(form, text="Civilité  *", anchor="w",
                     font=ctk.CTkFont(size=12)).pack(fill="x", pady=(0, 2))
        self._civ_var = ctk.StringVar(value="Madame")
        ctk.CTkComboBox(form, variable=self._civ_var, values=CIVILITIES,
                        width=160, height=32, state="readonly").pack(anchor="w")

        self._prenom_var = ctk.StringVar()
        self._field(form, "Prénom  *", self._prenom_var)
        self._nom_var = ctk.StringVar()
        self._field(form, "Nom  *", self._nom_var)
        self._tel_var = ctk.StringVar()
        self._field(form, "Téléphone  *", self._tel_var)
        self._email_var = ctk.StringVar()
        self._field(form, "Email  *", self._email_var)

        ctk.CTkLabel(form, text="Notes internes", anchor="w",
                     font=ctk.CTkFont(size=12)).pack(fill="x", pady=(8, 2))
        self._notes = ctk.CTkTextbox(form, height=60, fg_color="#212127",
                                      corner_radius=6)
        self._notes.pack(fill="x")

        self._err = ctk.CTkLabel(form, text="", text_color="#EF4444",
                                  font=ctk.CTkFont(size=11), anchor="w")
        self._err.pack(fill="x", pady=(8, 0))

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", padx=24, pady=12)

        ctk.CTkButton(btns, text="Annuler", width=100,
                      fg_color="#2A2A2E", hover_color="#3A3A3E",
                      command=self.destroy).pack(side="left")

        self._submit_btn = ctk.CTkButton(
            btns, text="✓  Créer", width=180,
            fg_color="#10B981", hover_color="#059669",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._submit)
        self._submit_btn.pack(side="right")

    def _field(self, parent, label: str, var: ctk.StringVar):
        ctk.CTkLabel(parent, text=label, anchor="w",
                     font=ctk.CTkFont(size=12)).pack(fill="x", pady=(8, 2))
        ctk.CTkEntry(parent, textvariable=var, height=32).pack(fill="x")

    def _submit(self):
        self._err.configure(text="")
        prenom = self._prenom_var.get().strip()
        nom    = self._nom_var.get().strip()
        tel    = self._tel_var.get().strip()
        email  = self._email_var.get().strip()
        if not all([prenom, nom, tel, email]):
            self._err.configure(text="⚠  Tous les champs obligatoires (*) sont requis.")
            return
        try:
            api_client.create_client({
                "civility":   self._civ_var.get(),
                "first_name": prenom,
                "last_name":  nom,
                "phone":      tel,
                "email":      email,
                "notes":      self._notes.get("1.0", "end").strip() or None,
            })
            self._on_created()
            self.destroy()
        except APIError as e:
            self._err.configure(text=f"⚠  {e.detail}")
        except Exception as e:
            self._err.configure(text=f"⚠  Erreur : {e}")
