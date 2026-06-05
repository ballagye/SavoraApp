"""Panneau droit — fiche client + historique des réservations."""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Dict, List, Optional

import customtkinter as ctk

import api_client
from api_client import APIError

_BG   = "#1A1A1F"
_CARD = "#212127"

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


class ClientDetail(ctk.CTkFrame):
    def __init__(self, master, on_refresh: Callable, **kwargs):
        super().__init__(master, fg_color=_BG, corner_radius=8, **kwargs)
        self._on_refresh = on_refresh
        self._current: Optional[Dict] = None
        self._content_visible = False
        self._build()

    def _build(self):
        # Placeholder
        self._ph = ctk.CTkFrame(self, fg_color="transparent")
        self._ph.pack(fill="both", expand=True)
        ctk.CTkLabel(self._ph, text="Sélectionnez\nun client",
                     font=ctk.CTkFont(size=15), text_color="#3D3D4A"
                     ).place(relx=0.5, rely=0.5, anchor="center")

        # Contenu scrollable (Canvas natif)
        self._sc = tk.Frame(self, bg=_BG)
        self._canvas = tk.Canvas(self._sc, bg=_BG, highlightthickness=0, bd=0)
        self._vsb = ttk.Scrollbar(self._sc, orient="vertical",
                                   command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._vsb.set)
        self._vsb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._inner = ctk.CTkFrame(self._canvas, fg_color="transparent",
                                    corner_radius=0)
        self._win = self._canvas.create_window((0, 0), window=self._inner,
                                                anchor="nw")
        self._inner.bind("<Configure>", lambda e: self._canvas.configure(
            scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfig(
            self._win, width=e.width))
        self._canvas.bind("<MouseWheel>", lambda e: self._canvas.yview_scroll(
            int(-1 * (e.delta / 120)), "units"))

        C = self._inner

        # En-tête
        hdr = ctk.CTkFrame(C, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(14, 8))
        self._name_lbl = ctk.CTkLabel(hdr, text="",
                                       font=ctk.CTkFont(size=17, weight="bold"))
        self._name_lbl.pack(side="left")

        # Réservations
        rsv_cnt = ctk.CTkLabel(hdr, text="",
                                text_color="#C9963A",
                                font=ctk.CTkFont(size=12, weight="bold"))
        rsv_cnt.pack(side="right")
        self._rsv_count_lbl = rsv_cnt

        # ── Infos client (éditables) ──────────────────────────────────────────
        self._sep(C, "Informations")
        info_card = ctk.CTkFrame(C, fg_color=_CARD, corner_radius=8)
        info_card.pack(fill="x", padx=16, pady=(0, 12))

        self._vars: Dict[str, ctk.StringVar] = {}
        for lbl, key in [
            ("Civilité",  "civility"),
            ("Prénom",    "first_name"),
            ("Nom",       "last_name"),
            ("Téléphone", "phone"),
            ("Email",     "email"),
        ]:
            self._edit_row(info_card, lbl, key)

        # Notes internes
        self._sep(C, "Notes internes")
        self._notes = ctk.CTkTextbox(C, height=60, fg_color=_CARD, corner_radius=8)
        self._notes.pack(fill="x", padx=16, pady=(0, 12))

        # Boutons
        btns = ctk.CTkFrame(C, fg_color="transparent")
        btns.pack(fill="x", padx=16, pady=(0, 12))
        btns.columnconfigure((0, 1), weight=1)

        self._btn_save = ctk.CTkButton(
            btns, text="💾  Enregistrer",
            fg_color="#10B981", hover_color="#059669",
            height=38, font=ctk.CTkFont(size=12, weight="bold"),
            command=self._save)
        self._btn_save.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        self._btn_delete = ctk.CTkButton(
            btns, text="Supprimer le client",
            fg_color="#1F1F1F", hover_color="#7F1D1D",
            border_color="#7F1D1D", border_width=1,
            height=38, command=self._delete)
        self._btn_delete.grid(row=0, column=1, padx=(4, 0), sticky="ew")

        # ── Historique des réservations ───────────────────────────────────────
        self._sep(C, "Historique des réservations")
        self._history = ctk.CTkScrollableFrame(C, height=200,
                                                fg_color=_CARD, corner_radius=8)
        self._history.pack(fill="x", padx=16, pady=(0, 20))

        self._set_interactive("disabled")

    # ── Helpers de construction ───────────────────────────────────────────────

    def _sep(self, parent, title: str):
        ctk.CTkLabel(parent, text=title.upper(),
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color="#555566").pack(anchor="w", padx=16, pady=(4, 3))

    def _edit_row(self, card, label: str, key: str):
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=4, pady=2)

        ctk.CTkLabel(row, text=f"{label} :", anchor="e",
                     width=90, text_color="#888899",
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=(8, 6))

        var = ctk.StringVar(value="—")
        self._vars[key] = var

        # Champ éditable
        entry = ctk.CTkEntry(row, textvariable=var, height=28,
                              fg_color="transparent", border_width=0,
                              font=ctk.CTkFont(size=12))
        entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

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

    def _set_interactive(self, state: str):
        for w in (self._btn_save, self._btn_delete):
            w.configure(state=state)

    # ── Chargement d'un client ────────────────────────────────────────────────

    def load(self, c: Dict):
        self._current = c
        self._show_content()

        self._name_lbl.configure(
            text=f"{c['first_name']} {c['last_name'].upper()}")
        n = c.get("reservation_count", 0)
        self._rsv_count_lbl.configure(
            text=f"{n} réservation{'s' if n != 1 else ''}")

        for key, var in self._vars.items():
            var.set(c.get(key, ""))

        self._notes.delete("1.0", "end")
        if c.get("notes"):
            self._notes.insert("1.0", c["notes"])

        self._set_interactive("normal")
        self._load_history(c["id"])

    def _load_history(self, client_id: int):
        for w in self._history.winfo_children():
            w.destroy()

        try:
            reservations = api_client.get_client_reservations(client_id)
        except Exception:
            ctk.CTkLabel(self._history, text="Impossible de charger l'historique.",
                         text_color="#EF4444").pack(pady=8)
            return

        if not reservations:
            ctk.CTkLabel(self._history, text="Aucune réservation",
                         text_color="#555566").pack(pady=10)
            return

        for r in reservations:
            color = STATUS_COLORS.get(r["status"], "#6B7280")
            row = ctk.CTkFrame(self._history, fg_color="transparent")
            row.pack(fill="x", pady=1)

            ctk.CTkFrame(row, width=3, fg_color=color,
                         corner_radius=0).pack(side="left", fill="y")

            ctk.CTkLabel(row, text=f"{r['date']}  {r['time_slot']}",
                         font=ctk.CTkFont(size=11), width=130,
                         anchor="w").pack(side="left", padx=8)

            ctk.CTkLabel(row, text=f"{r['party_size']} pax",
                         text_color="#AAAAAA",
                         font=ctk.CTkFont(size=11)).pack(side="left")

            ctk.CTkLabel(row, text=STATUS_LABELS.get(r["status"], r["status"]),
                         text_color=color, font=ctk.CTkFont(size=10),
                         ).pack(side="right", padx=8)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _save(self):
        if not self._current:
            return
        data = {k: v.get() for k, v in self._vars.items()}
        notes = self._notes.get("1.0", "end").strip()
        if notes:
            data["notes"] = notes
        try:
            api_client.update_client(self._current["id"], data)
            self._on_refresh()
        except APIError as e:
            messagebox.showerror("Erreur API", str(e))

    def _delete(self):
        if not self._current:
            return
        c = self._current
        if not messagebox.askyesno(
            "Supprimer le client",
            f"Supprimer {c['first_name']} {c['last_name']} ?\n"
            "Ses réservations ne seront pas supprimées."
        ):
            return
        try:
            api_client.delete_client(c["id"])
            self._current = None
            self._show_placeholder()
            self._on_refresh()
        except APIError as e:
            messagebox.showerror("Erreur API", str(e))
