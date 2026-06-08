"""Point d'entrée — application desktop Savora."""
import sys
import os
import threading
from datetime import date, timedelta
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk

import api_client
from api_client import APIError
from components.reservation_list import ReservationList
from components.reservation_detail import ReservationDetail
from components.quota_panel import QuotaPanel
from components.new_reservation_dialog import NewReservationDialog
from components.clients_list import ClientsList
from components.client_detail import ClientDetail
from components.new_client_dialog import NewClientDialog
from config import ACCENT, JOURS_FR, MOIS_FR, MAX_COVERS, REFRESH_MS

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class SavoraApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Savora — Gestion des réservations")
        self.geometry("1440x860")
        self.minsize(1100, 680)

        self._after_id    = None
        self._debounce_id = None          # debounce navigation rapide
        self._current_date = date.today()
        self._showing_all   = False
        self._service_filter: Optional[str] = None
        self._status_filter:  Optional[str] = None
        self._active_view = "reservations"          # "reservations" | "clients"

        self._build()
        self._load()

    # ── Construction ──────────────────────────────────────────────────────────

    def _build(self):
        # ── Ligne 1 : header ──────────────────────────────────────────────────
        header = ctk.CTkFrame(self, height=56, corner_radius=0, fg_color="#18181B")
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="SAVORA",
            font=ctk.CTkFont(size=20, weight="bold"), text_color=ACCENT,
        ).pack(side="left", padx=20)

        ctk.CTkFrame(header, width=1, fg_color="#333333").pack(
            side="left", fill="y", pady=12, padx=6
        )

        # Bouton TOUT (toutes les dates, sans filtre de date)
        self._all_btn = ctk.CTkButton(
            header, text="TOUT", width=58, height=30,
            fg_color="#2A2A2E", text_color="#AAAAAA",
            hover_color="#3A3A3E", corner_radius=6,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._show_all_dates,
        )
        self._all_btn.pack(side="left", padx=(4, 4), pady=13)

        # Navigation date : ‹ MAR. 27 JUIN ›
        self._prev_btn = ctk.CTkButton(
            header, text="‹", width=32, height=30,
            fg_color="#2A2A2E", hover_color="#3A3A3E", corner_radius=6,
            font=ctk.CTkFont(size=18), command=self._prev_day,
        )
        self._prev_btn.pack(side="left", padx=(0, 0), pady=13)

        self._date_lbl = ctk.CTkLabel(
            header, text=self._fmt_date(),
            font=ctk.CTkFont(size=13, weight="bold"), width=170,
        )
        self._date_lbl.pack(side="left", padx=4)

        self._next_btn = ctk.CTkButton(
            header, text="›", width=32, height=30,
            fg_color="#2A2A2E", hover_color="#3A3A3E", corner_radius=6,
            font=ctk.CTkFont(size=18), command=self._next_day,
        )
        self._next_btn.pack(side="left", padx=(0, 10))

        ctk.CTkFrame(header, width=1, fg_color="#333333").pack(
            side="left", fill="y", pady=12, padx=6
        )

        # Tabs service : TOUS / DÉJEUNER / DÎNER
        self._svc_btns = {}
        for label, val in [("TOUS", None), ("DÉJEUNER", "lunch"), ("DÎNER", "dinner")]:
            active = val is None
            btn = ctk.CTkButton(
                header, text=label, width=98, height=30,
                fg_color=ACCENT if active else "#2A2A2E",
                text_color="#18181B" if active else "#AAAAAA",
                hover_color="#B8852A" if active else "#3A3A3E",
                corner_radius=6,
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda l=label, v=val: self._set_service(l, v),
            )
            btn.pack(side="left", padx=2, pady=13)
            self._svc_btns[label] = btn

        ctk.CTkFrame(header, width=1, fg_color="#333333").pack(
            side="left", fill="y", pady=12, padx=6
        )

        # ── Switcher de vues : Réservations / Clients ─────────────────────────
        self._view_btns = {}
        for label, view in [("📋  Réservations", "reservations"),
                             ("👥  Clients",       "clients")]:
            btn = ctk.CTkButton(
                header, text=label, width=130, height=30,
                fg_color=ACCENT if view == "reservations" else "#2A2A2E",
                text_color="#18181B" if view == "reservations" else "#AAAAAA",
                hover_color="#B8852A" if view == "reservations" else "#3A3A3E",
                corner_radius=6, font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda v=view: self._switch_view(v),
            )
            btn.pack(side="left", padx=2, pady=13)
            self._view_btns[view] = btn

        ctk.CTkFrame(header, width=1, fg_color="#333333").pack(
            side="left", fill="y", pady=12, padx=6
        )

        # Bouton Nouvelle réservation (visible en vue Réservations)
        self._btn_new_resa = ctk.CTkButton(
            header, text="＋  Nouvelle réservation", height=30,
            fg_color="#2A2A2E", hover_color="#3A3A3E", corner_radius=6,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._new_reservation,
        )
        self._btn_new_resa.pack(side="left", padx=(4, 0), pady=13)

        # Boutons vue Clients (masqués par défaut)
        self._btn_new_client = ctk.CTkButton(
            header, text="＋  Nouveau client", height=30,
            fg_color="#2A2A2E", hover_color="#3A3A3E", corner_radius=6,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._new_client,
        )
        self._btn_import = ctk.CTkButton(
            header, text="⬇  Importer réservations", height=30,
            fg_color="#2A2A2E", hover_color="#3A3A3E", corner_radius=6,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._import_clients,
        )

        # Refresh + compteur (à droite)
        self._count_lbl = ctk.CTkLabel(
            header, text="", text_color="#9CA3AF", font=ctk.CTkFont(size=12)
        )
        self._count_lbl.pack(side="right", padx=12)

        self._refresh_btn = ctk.CTkButton(
            header, text="↻", width=36, height=30,
            fg_color="#2A2A2E", hover_color="#3A3A3E", corner_radius=6,
            command=self._load,
        )
        self._refresh_btn.pack(side="right", padx=(0, 8), pady=13)

        # ── Ligne 2 : tabs statut avec compteurs ──────────────────────────────
        stat_bar = ctk.CTkFrame(self, height=40, corner_radius=0, fg_color="#111113")
        stat_bar.pack(fill="x", side="top")
        stat_bar.pack_propagate(False)

        self._stat_tab: dict[Optional[str], tuple] = {}
        for key, icon, color in [
            (None,        "TOUS",   "#FFFFFF"),
            ("pending",   "⏱",     "#F59E0B"),
            ("confirmed", "✓",      "#10B981"),
            ("refused",   "✕",      "#EF4444"),
            ("cancelled", "◷",      "#6B7280"),
        ]:
            var = ctk.StringVar(value=f"{icon}  0")
            btn = ctk.CTkButton(
                stat_bar, textvariable=var,
                width=88, height=26,
                fg_color="#1F1F24" if key else "#2A2A2E",
                text_color=color,
                hover_color="#2A2A2E",
                corner_radius=5,
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda k=key: self._set_status(k),
            )
            btn.pack(side="left", padx=(8, 2), pady=7)
            self._stat_tab[key] = (btn, var, icon)

        # ── Quota bar (avant le body pour ne pas être écrasée) ────────────────
        self._quota_panel = QuotaPanel(self, height=48)
        self._quota_panel.pack(fill="x", side="bottom", padx=10, pady=(0, 6))

        # ── Corps : liste (gauche) + détail (droite) ──────────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=10, pady=(8, 4))

        # ── Vue Réservations ──────────────────────────────────────────────────
        self._resas_frame = ctk.CTkFrame(body, fg_color="transparent")
        self._resas_frame.pack(fill="both", expand=True)

        self._list_panel = ReservationList(
            self._resas_frame, on_select=self._on_select, width=760)
        self._list_panel.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self._detail_panel = ReservationDetail(
            self._resas_frame, on_refresh=self._load, width=540)
        self._detail_panel.pack(side="right", fill="both", padx=(5, 0))

        # ── Vue Clients ───────────────────────────────────────────────────────
        self._clients_frame = ctk.CTkFrame(body, fg_color="transparent")
        # (pas packée — affichée uniquement quand on clique sur "Clients")

        self._clients_list = ClientsList(
            self._clients_frame, on_select=self._on_client_select, width=760)
        self._clients_list.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self._client_detail = ClientDetail(
            self._clients_frame, on_refresh=self._load_clients, width=540)
        self._client_detail.pack(side="right", fill="both", padx=(5, 0))

        # Date initiale
        self._list_panel.set_date_filter(self._current_date.isoformat())

    # ── Navigation de date ────────────────────────────────────────────────────

    def _fmt_date(self) -> str:
        d = self._current_date
        return f"{JOURS_FR[d.weekday()]}. {d.day} {MOIS_FR[d.month - 1]}"

    # ── Switcher de vues ──────────────────────────────────────────────────────

    def _switch_view(self, view: str):
        self._active_view = view
        for v, btn in self._view_btns.items():
            if v == view:
                btn.configure(fg_color=ACCENT, text_color="#18181B",
                               hover_color="#B8852A")
            else:
                btn.configure(fg_color="#2A2A2E", text_color="#AAAAAA",
                               hover_color="#3A3A3E")

        if view == "reservations":
            self._clients_frame.pack_forget()
            self._btn_new_client.pack_forget()
            self._btn_import.pack_forget()
            self._resas_frame.pack(fill="both", expand=True)
            self._btn_new_resa.pack(side="left", padx=(4, 0), pady=13)
            self._load()
        else:
            self._resas_frame.pack_forget()
            self._btn_new_resa.pack_forget()
            self._clients_frame.pack(fill="both", expand=True)
            self._btn_new_client.pack(side="left", padx=(4, 2), pady=13)
            self._btn_import.pack(side="left", padx=(0, 4), pady=13)
            self._load_clients()

    def _load_clients(self):
        def fetch():
            try:
                data = api_client.get_clients()
                self.after(0, lambda: self._clients_list.load(data))
                self.after(0, lambda: self._count_lbl.configure(
                    text=f"{len(data)} client{'s' if len(data) != 1 else ''}",
                    text_color="#10B981"))
            except Exception as exc:
                msg = exc.detail if isinstance(exc, APIError) else str(exc)
                self.after(0, lambda: self._count_lbl.configure(
                    text=f"Erreur : {msg}", text_color="#EF4444"))
        threading.Thread(target=fetch, daemon=True).start()

    def _on_client_select(self, client: dict):
        self._client_detail.load(client)

    def _new_client(self):
        NewClientDialog(self, on_created=self._load_clients)

    def _import_clients(self):
        """Crée les fiches clients pour tous les emails de réservations."""
        self._btn_import.configure(state="disabled", text="…")

        def do():
            try:
                result = api_client.import_clients_from_reservations()
                n = result.get("imported", 0)
                self.after(0, lambda: self._count_lbl.configure(
                    text=f"{n} client{'s' if n != 1 else ''} importé{'s' if n != 1 else ''}",
                    text_color="#10B981"))
                self.after(0, self._load_clients)
            except Exception as exc:
                msg = exc.detail if isinstance(exc, APIError) else str(exc)
                self.after(0, lambda: self._count_lbl.configure(
                    text=f"Erreur : {msg}", text_color="#EF4444"))
            finally:
                self.after(0, lambda: self._btn_import.configure(
                    state="normal", text="⬇  Importer réservations"))

        threading.Thread(target=do, daemon=True).start()

    def _new_reservation(self):
        """Ouvre le dialogue de création d'une réservation."""
        NewReservationDialog(self, on_created=self._load)

    def _show_all_dates(self):
        """Désactive le filtre de date → toutes les réservations."""
        self._showing_all = True
        self._all_btn.configure(fg_color=ACCENT, text_color="#18181B", hover_color="#B8852A")
        self._date_lbl.configure(text_color="#555566")
        self._list_panel.set_date_filter("")
        self._load()

    def _activate_date_nav(self):
        """Réactive la navigation par date (sort du mode TOUT)."""
        if self._showing_all:
            self._showing_all = False
            self._all_btn.configure(fg_color="#2A2A2E", text_color="#AAAAAA", hover_color="#3A3A3E")
            self._date_lbl.configure(text_color="#FFFFFF")

    def _prev_day(self):
        self._activate_date_nav()
        self._current_date -= timedelta(days=1)
        self._date_lbl.configure(text=self._fmt_date())
        self._list_panel.set_date_filter(self._current_date.isoformat())
        self._load()

    def _next_day(self):
        self._activate_date_nav()
        self._current_date += timedelta(days=1)
        self._date_lbl.configure(text=self._fmt_date())
        self._list_panel.set_date_filter(self._current_date.isoformat())
        self._load()

    # ── Filtres service / statut ──────────────────────────────────────────────

    def _set_service(self, label: str, val: Optional[str]):
        self._service_filter = val
        for lbl, btn in self._svc_btns.items():
            if lbl == label:
                btn.configure(fg_color=ACCENT, text_color="#18181B", hover_color="#B8852A")
            else:
                btn.configure(fg_color="#2A2A2E", text_color="#AAAAAA", hover_color="#3A3A3E")
        self._list_panel.set_period_filter(val)
        self._load()

    def _set_status(self, key: Optional[str]):
        self._status_filter = key
        for k, (btn, var, icon) in self._stat_tab.items():
            btn.configure(fg_color="#2A2A2E" if k == key else "#1F1F24")
        self._list_panel.set_status_filter(key)
        self._load()

    # ── Chargement (thread) ───────────────────────────────────────────────────

    def _load(self, debounce_ms: int = 80):
        """Lance un chargement après un court délai (debounce).
        Les appels rapides successifs (navigation date, filtres) sont fusionnés
        en un seul appel réseau, évitant les requêtes inutiles."""
        if self._debounce_id is not None:
            self.after_cancel(self._debounce_id)
        self._debounce_id = self.after(debounce_ms, self._do_load)

    def _do_load(self):
        self._debounce_id = None
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None

        self._refresh_btn.configure(state="disabled", text="…")
        filters = {k: v for k, v in self._list_panel.get_filters().items() if v}

        def fetch():
            try:
                data = api_client.get_reservations(**filters)
                self.after(0, lambda: self._apply(data))
            except Exception as exc:
                msg = exc.detail if isinstance(exc, APIError) else str(exc)
                self.after(0, lambda: self._error(msg))

        threading.Thread(target=fetch, daemon=True).start()

    def _apply(self, data: list):
        self._list_panel.load(data)
        self._update_stat_tabs(data)
        n = len(data)
        self._count_lbl.configure(
            text=f"{n} résultat{'s' if n != 1 else ''}",
            text_color="#10B981",
        )
        self._refresh_btn.configure(state="normal", text="↻")
        self._after_id = self.after(REFRESH_MS, self._load)

    def _error(self, msg: str):
        self._count_lbl.configure(text=f"Erreur : {msg}", text_color="#EF4444")
        self._refresh_btn.configure(state="normal", text="↻")
        self._after_id = self.after(REFRESH_MS, self._load)

    def _update_stat_tabs(self, data: list):
        counts: dict[Optional[str], int] = {k: 0 for k in self._stat_tab}
        counts[None] = len(data)
        for r in data:
            s = r.get("status", "")
            if s in counts:
                counts[s] += 1
        for key, (btn, var, icon) in self._stat_tab.items():
            var.set(f"{icon}  {counts.get(key, 0)}")

    def _on_select(self, reservation: dict):
        self._detail_panel.load(reservation)


if __name__ == "__main__":
    app = SavoraApp()
    app.mainloop()
