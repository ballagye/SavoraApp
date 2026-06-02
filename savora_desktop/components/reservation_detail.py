"""Panneau droit : détail + actions d'une réservation."""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Dict, Optional

import customtkinter as ctk

import api_client
from api_client import APIError

STATUS_FR = {
    "pending":   "⏱  En attente",
    "confirmed": "✓  Confirmée",
    "refused":   "✕  Refusée",
    "cancelled": "◷  Annulée",
}
STATUS_COLOR = {
    "pending":   "#F59E0B",
    "confirmed": "#10B981",
    "refused":   "#EF4444",
    "cancelled": "#6B7280",
}
MEAL_FR = {"lunch": "Midi", "dinner": "Soir"}

_BG   = "#1A1A1F"
_CARD = "#212127"


class ReservationDetail(ctk.CTkFrame):
    def __init__(self, master, on_refresh: Callable, **kwargs):
        super().__init__(master, fg_color=_BG, corner_radius=8, **kwargs)
        self._on_refresh = on_refresh
        self._current: Optional[Dict] = None
        self._content_visible = False
        self._build()

    # ── Construction ──────────────────────────────────────────────────────────

    def _build(self):
        # ── Placeholder (rien de sélectionné) ────────────────────────────────
        self._ph = ctk.CTkFrame(self, fg_color="transparent")
        self._ph.pack(fill="both", expand=True)
        ctk.CTkLabel(
            self._ph,
            text="Sélectionnez\nune réservation",
            font=ctk.CTkFont(size=15), text_color="#3D3D4A",
        ).place(relx=0.5, rely=0.5, anchor="center")

        # ── Zone de défilement ────────────────────────────────────────────────
        # On utilise Canvas + Scrollbar natif tkinter : c'est le seul moyen
        # de garantir que les enfants avec fill="x" occupent toute la largeur.
        self._sc = tk.Frame(self, bg=_BG)
        # (packée plus tard via _show_content)

        self._canvas = tk.Canvas(self._sc, bg=_BG, highlightthickness=0, bd=0)
        self._vsb    = ttk.Scrollbar(self._sc, orient="vertical",
                                     command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._vsb.set)
        self._vsb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        # Frame interne à largeur forcée = largeur du canvas
        self._inner  = ctk.CTkFrame(self._canvas, fg_color="transparent",
                                    corner_radius=0)
        self._win_id = self._canvas.create_window((0, 0), window=self._inner,
                                                  anchor="nw")

        self._inner.bind("<Configure>",
                         lambda e: self._canvas.configure(
                             scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>",
                          lambda e: self._canvas.itemconfig(
                              self._win_id, width=e.width))
        # Défilement souris
        self._canvas.bind("<MouseWheel>",
                          lambda e: self._canvas.yview_scroll(
                              int(-1 * (e.delta / 120)), "units"))

        # ── Contenu (tout dans self._inner) ──────────────────────────────────
        C = self._inner   # alias

        # En-tête : ID + badge statut
        hdr = ctk.CTkFrame(C, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(14, 8))

        self._id_lbl = ctk.CTkLabel(hdr, text="",
                                     font=ctk.CTkFont(size=17, weight="bold"))
        self._id_lbl.pack(side="left")

        # Badge : width=130 pour "⏱  En attente" sans troncature
        self._badge = ctk.CTkButton(
            hdr, text="", width=130, height=26,
            fg_color="#6B7280", hover_color="#6B7280", corner_radius=13,
            font=ctk.CTkFont(size=11, weight="bold"), command=lambda: None,
        )
        self._badge.pack(side="right")

        # ── Actions en haut (toujours visibles sans scroll) ───────────────────
        self._sep(C, "Actions")

        pri = ctk.CTkFrame(C, fg_color="transparent")
        pri.pack(fill="x", padx=16, pady=(0, 6))
        pri.columnconfigure((0, 1), weight=1)

        self._btn_confirm = ctk.CTkButton(
            pri, text="✓  Confirmer",
            fg_color="#10B981", hover_color="#059669",
            height=42, font=ctk.CTkFont(size=13, weight="bold"),
            command=self._confirm)
        self._btn_confirm.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        self._btn_refuse = ctk.CTkButton(
            pri, text="✕  Refuser",
            fg_color="#EF4444", hover_color="#DC2626",
            height=42, font=ctk.CTkFont(size=13, weight="bold"),
            command=self._refuse)
        self._btn_refuse.grid(row=0, column=1, padx=(4, 0), sticky="ew")

        sec = ctk.CTkFrame(C, fg_color="transparent")
        sec.pack(fill="x", padx=16, pady=(0, 12))
        sec.columnconfigure((0, 1), weight=1)

        self._btn_cancel = ctk.CTkButton(
            sec, text="Annuler la résa",
            fg_color="#2D2D35", hover_color="#3D3D45",
            height=32, command=self._cancel)
        self._btn_cancel.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        self._btn_delete = ctk.CTkButton(
            sec, text="Supprimer",
            fg_color="#1F1F1F", hover_color="#7F1D1D",
            border_color="#7F1D1D", border_width=1,
            height=32, command=self._delete)
        self._btn_delete.grid(row=0, column=1, padx=(4, 0), sticky="ew")

        # Note interne
        self._sep(C, "Note interne")
        self._note_entry = ctk.CTkTextbox(C, height=52, fg_color=_CARD,
                                           corner_radius=8)
        self._note_entry.pack(fill="x", padx=16, pady=(0, 12))

        # Infos réservation
        self._sep(C, "Réservation")
        self._res_vars: Dict[str, ctk.StringVar] = {}
        rc = self._card(C)
        for lbl, key in [("Date", "date"), ("Service", "meal_period"),
                          ("Heure", "time_slot"), ("Couverts", "party_size")]:
            self._row(rc, lbl, key, self._res_vars)

        # Infos client
        self._sep(C, "Client")
        self._cli_vars: Dict[str, ctk.StringVar] = {}
        cc = self._card(C)
        for lbl, key in [("Civilité", "civility"), ("Prénom", "first_name"),
                          ("Nom", "last_name"), ("Téléphone", "phone"),
                          ("Email", "email")]:
            self._row(cc, lbl, key, self._cli_vars)

        # Demandes spéciales
        self._sep(C, "Demandes spéciales")
        self._special_box = ctk.CTkTextbox(C, height=50, state="disabled",
                                            fg_color=_CARD, corner_radius=8)
        self._special_box.pack(fill="x", padx=16, pady=(0, 12))

        # Modifier couverts
        cr = ctk.CTkFrame(C, fg_color="transparent")
        cr.pack(fill="x", padx=16, pady=(0, 28))
        ctk.CTkLabel(cr, text="Modifier couverts :", text_color="#AAAAAA",
                     font=ctk.CTkFont(size=12)).pack(side="left")
        self._covers_var = ctk.StringVar()
        self._covers_entry = ctk.CTkEntry(
            cr, textvariable=self._covers_var, width=55, height=30)
        self._covers_entry.pack(side="left", padx=8)
        ctk.CTkButton(cr, text="Enregistrer", width=100, height=30,
                      command=self._save_covers).pack(side="left")

        self._set_interactive("disabled")

    # ── Helpers layout ────────────────────────────────────────────────────────

    def _sep(self, parent, title: str):
        ctk.CTkLabel(
            parent, text=title.upper(),
            font=ctk.CTkFont(size=10, weight="bold"), text_color="#555566",
        ).pack(anchor="w", padx=16, pady=(4, 3))

    def _card(self, parent) -> ctk.CTkFrame:
        f = ctk.CTkFrame(parent, fg_color=_CARD, corner_radius=8)
        f.pack(fill="x", padx=16, pady=(0, 12))
        return f

    def _row(self, card: ctk.CTkFrame, label: str, key: str, store: dict):
        """Label + valeur en pack — fill='x' garantit l'absence de troncature."""
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=4, pady=2)

        ctk.CTkLabel(
            row, text=f"{label} :", anchor="e",
            width=90, text_color="#888899", font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=(8, 6))

        var = ctk.StringVar(value="—")
        store[key] = var
        # fill="x" + expand=True → le label prend TOUT l'espace restant
        ctk.CTkLabel(
            row, textvariable=var, anchor="w",
            font=ctk.CTkFont(size=12),
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

    # ── Visibilité ────────────────────────────────────────────────────────────

    def _show_content(self):
        if not self._content_visible:
            self._ph.pack_forget()
            self._sc.pack(fill="both", expand=True)
            self._content_visible = True

    def _show_placeholder(self):
        if self._content_visible:
            self._sc.pack_forget()
            self._ph.pack(fill="both", expand=True)
            self._content_visible = False

    # ── Chargement ────────────────────────────────────────────────────────────

    def load(self, r: Dict):
        self._current = r
        self._show_content()

        self._id_lbl.configure(text=f"Réservation  #{r['id']}")
        color = STATUS_COLOR.get(r["status"], "#6B7280")
        self._badge.configure(
            text=STATUS_FR.get(r["status"], r["status"]),
            fg_color=color, hover_color=color,
        )

        self._res_vars["date"].set(r["date"])
        self._res_vars["meal_period"].set(
            MEAL_FR.get(r["meal_period"], r["meal_period"]))
        self._res_vars["time_slot"].set(r["time_slot"])
        n = r["party_size"]
        self._res_vars["party_size"].set(f"{n} couvert{'s' if n > 1 else ''}")

        self._cli_vars["civility"].set(r["civility"])
        self._cli_vars["first_name"].set(r["first_name"])
        self._cli_vars["last_name"].set(r["last_name"].upper())
        self._cli_vars["phone"].set(r["phone"])
        self._cli_vars["email"].set(r["email"])

        self._special_box.configure(state="normal")
        self._special_box.delete("1.0", "end")
        self._special_box.insert("1.0", r.get("special_requests") or "Aucune")
        self._special_box.configure(state="disabled")

        self._note_entry.delete("1.0", "end")
        if r.get("staff_note"):
            self._note_entry.insert("1.0", r["staff_note"])

        self._covers_var.set(str(r["party_size"]))
        self._set_interactive("normal")

    def _set_interactive(self, state: str):
        for w in (self._btn_confirm, self._btn_refuse,
                  self._btn_cancel, self._btn_delete, self._covers_entry):
            w.configure(state=state)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _note(self) -> str:
        return self._note_entry.get("1.0", "end").strip()

    def _confirm(self): self._change_status("confirmed")
    def _refuse(self):  self._change_status("refused")
    def _cancel(self):  self._change_status("cancelled")

    def _change_status(self, s: str):
        if not self._current:
            return
        try:
            api_client.update_status(self._current["id"], s, staff_note=self._note())
            self._on_refresh()
        except APIError as e:
            messagebox.showerror("Erreur API", str(e))

    def _delete(self):
        if not self._current:
            return
        r = self._current
        if not messagebox.askyesno(
            "Confirmer",
            f"Supprimer la réservation #{r['id']} de "
            f"{r['first_name']} {r['last_name']} ?\nAction irréversible."
        ):
            return
        try:
            api_client.delete_reservation(r["id"])
            self._current = None
            self._show_placeholder()
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
