"""Liste des clients avec recherche."""
from typing import Callable, Dict, List

import customtkinter as ctk


class ClientsList(ctk.CTkFrame):
    def __init__(self, master, on_select: Callable[[Dict], None], **kwargs):
        super().__init__(master, **kwargs)
        self._on_select = on_select
        self._clients: List[Dict] = []
        self._build()

    def _build(self):
        # Barre de recherche
        search = ctk.CTkFrame(self, fg_color="#1E1E22", corner_radius=8, height=38)
        search.pack(fill="x", padx=8, pady=(8, 6))
        search.pack_propagate(False)

        ctk.CTkLabel(search, text="🔍", font=ctk.CTkFont(size=13),
                     text_color="#555566").pack(side="left", padx=10)

        self._search_var = ctk.StringVar()
        ctk.CTkEntry(search, textvariable=self._search_var,
                     placeholder_text="Rechercher un client…",
                     border_width=0, fg_color="transparent",
                     font=ctk.CTkFont(size=13)).pack(side="left", fill="x",
                                                      expand=True, pady=4)
        self._search_var.trace_add("write", lambda *_: self._rebuild(self._filter()))

        # Liste scrollable
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    # ── API publique ──────────────────────────────────────────────────────────

    def load(self, clients: List[Dict]):
        self._clients = clients
        self._rebuild(clients)

    # ── Logique interne ───────────────────────────────────────────────────────

    def _filter(self) -> List[Dict]:
        q = self._search_var.get().strip().lower()
        if len(q) < 2:
            return self._clients
        return [
            c for c in self._clients
            if q in c["first_name"].lower()
            or q in c["last_name"].lower()
            or q in c["email"].lower()
        ]

    def _rebuild(self, clients: List[Dict]):
        for w in self._scroll.winfo_children():
            w.destroy()

        if not clients:
            ctk.CTkLabel(self._scroll, text="Aucun client",
                         text_color="#3D3D4A",
                         font=ctk.CTkFont(size=13)).pack(pady=48)
            return

        for c in clients:
            self._make_row(c)

    def _make_row(self, c: Dict):
        NORMAL = "#1E1E25"
        HOVER  = "#272733"

        outer = ctk.CTkFrame(self._scroll, fg_color="transparent")
        outer.pack(fill="x", pady=1)

        inner = ctk.CTkFrame(outer, fg_color=NORMAL, corner_radius=4)
        inner.pack(fill="x")

        inner.columnconfigure(1, weight=1)

        # Initiales dans un cercle
        initials = f"{c['first_name'][0]}{c['last_name'][0]}".upper()
        badge = ctk.CTkLabel(
            inner, text=initials, width=34, height=34,
            fg_color="#2D2D3A", corner_radius=17,
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        badge.grid(row=0, column=0, rowspan=2, padx=(10, 8), pady=8)

        # Nom
        lbl_name = ctk.CTkLabel(
            inner,
            text=f"{c['first_name']} {c['last_name'].upper()}",
            font=ctk.CTkFont(size=12, weight="bold"), anchor="w",
        )
        lbl_name.grid(row=0, column=1, sticky="sw", pady=(7, 0))

        # Email
        lbl_email = ctk.CTkLabel(
            inner, text=c["email"],
            text_color="#8888AA", font=ctk.CTkFont(size=10), anchor="w",
        )
        lbl_email.grid(row=1, column=1, sticky="nw", pady=(0, 7))

        # Compteur de réservations
        n = c.get("reservation_count", 0)
        lbl_count = ctk.CTkLabel(
            inner, text=f"{n} résa",
            text_color="#C9963A", font=ctk.CTkFont(size=11, weight="bold"),
            width=55,
        )
        lbl_count.grid(row=0, column=2, rowspan=2, padx=12, sticky="e")

        # Hover + clic
        def on_enter(_): inner.configure(fg_color=HOVER)
        def on_leave(_): inner.configure(fg_color=NORMAL)
        def on_click(_, client=c): self._on_select(client)

        for w in (outer, inner, badge, lbl_name, lbl_email, lbl_count):
            try:
                w.bind("<Button-1>", on_click)
                w.bind("<Enter>", on_enter)
                w.bind("<Leave>", on_leave)
                w.configure(cursor="hand2")
            except Exception:
                pass
