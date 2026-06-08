# Documentation technique — Système de réservation **Savora**

> **BTS SIO – option SLAM – Session 2026**
> Épreuve E6 : Conception et développement d'applications
> Candidat : **Balla Gueye** — N° candidat : **02149092520**
> Période : Janvier / Mars 2026 — Lieu : Paris — Modalité : Seul

---

## Table des matières

1. [Présentation générale](#1-présentation-générale)
2. [Contexte et acteurs](#2-contexte-et-acteurs)
3. [Architecture globale](#3-architecture-globale)
4. [Stack technique](#4-stack-technique)
5. [Modèle de données](#5-modèle-de-données)
6. [API REST (FastAPI)](#6-api-rest-fastapi)
7. [Client léger (SvelteKit)](#7-client-léger-sveltekit)
8. [Client lourd (CustomTkinter)](#8-client-lourd-customtkinter)
9. [Règles de gestion métier](#9-règles-de-gestion-métier)
10. [Sécurité](#10-sécurité)
11. [Scénarios / flux de données](#11-scénarios--flux-de-données)
12. [Déploiement](#12-déploiement)
13. [Installation & exécution en développement](#13-installation--exécution-en-développement)
14. [Annexes](#14-annexes)

---

## 1. Présentation générale

Le projet **Savora** est un système complet de gestion des réservations pour un
restaurant gastronomique. Il se compose de **trois applications** qui partagent
une **base de données PostgreSQL** unique via une **API REST centrale** :

| Composant | Rôle | Technologie | Acteur |
|-----------|------|-------------|--------|
| **Client léger** (`SavoraWeb`) | Site vitrine + réservation en ligne | SvelteKit + Drizzle ORM | Client final |
| **API REST** (`savora_api`) | Logique métier, accès aux données | FastAPI + SQLAlchemy | — (cœur du système) |
| **Client lourd** (`savora_desktop`) | Outil interne de gestion | Python + CustomTkinter | Personnel (Staff) |

Le principe directeur : **toute donnée transite par l'API REST**. Ni le client
léger ni le client lourd n'écrivent « en dur » dans la base — ils passent par les
endpoints HTTP, ce qui garantit la **cohérence des données** entre les deux
interfaces.

---

## 2. Contexte et acteurs

### 2.1 Contexte métier

Le restaurant gastronomique Savora fait face à une forte augmentation de sa
fréquentation. Les réservations par téléphone saturent. L'objectif est de :

- **Présenter** le restaurant (concept, menus, horaires, localisation) via une
  vitrine élégante.
- **Permettre** aux clients de vérifier les disponibilités et de réserver une
  table en ligne, 24 h/24.
- **Doter** le personnel d'un outil interne pour valider, refuser, modifier les
  réservations et gérer les clients, avec un **blocage automatique** quand la
  capacité maximale est atteinte.

### 2.2 Diagramme des cas d'utilisation (DCU)

Deux acteurs interagissent avec le système :

```
                          ┌─────────────────────────────────────────┐
                          │        Système de réservation Savora     │
                          │                                          │
   ┌────────┐             │   ┌────────────────────────┐             │
   │ Client │────────────▶│   │ Effectuer une réservation│            │
   └────────┘             │   └────────────────────────┘             │
                          │                                          │
                          │   ┌────────────────────────┐             │
                          │   │ Valider / refuser résa  │◀──────┐     │
                          │   └────────────────────────┘       │     │
                          │   ┌────────────────────────┐       │     │
                          │   │ Modifier une réservation│◀──────┤     │
                          │   └────────────────────────┘       │   ┌──────┐
                          │   ┌────────────────────────┐       ├───│ Staff│
                          │   │ Consulter le planning   │◀──────┤   └──────┘
                          │   └────────────────────────┘       │     │
                          │   ┌────────────────────────┐       │     │
                          │   │ Gérer les clients (CRUD)│◀──────┤     │
                          │   └────────────────────────┘       │     │
                          │   ┌────────────────────────┐       │     │
                          │   │ Gérer les places dispo. │◀──────┘     │
                          │   └────────────────────────┘             │
                          └─────────────────────────────────────────┘

         Communication via API REST (FastAPI) — base PostgreSQL partagée
```

| Acteur | Description | Interface utilisée |
|--------|-------------|--------------------|
| **Client** | Visiteur du site web qui consulte le restaurant et réserve une table. | Client léger (SvelteKit) |
| **Staff** | Personnel du restaurant qui gère réservations, clients et quotas. | Client lourd (CustomTkinter) |

---

## 3. Architecture globale

### 3.1 Schéma d'architecture (3-tiers)

```
┌──────────────────────────┐        ┌──────────────────────────┐
│   CLIENT LÉGER (Web)      │        │   CLIENT LOURD (Desktop)  │
│   SvelteKit               │        │   Python + CustomTkinter  │
│   (navigateur)            │        │   (poste du personnel)    │
└──────────┬───────────────┘        └──────────┬───────────────┘
           │ HTTP (proxy serveur)              │ HTTP (requests)
           │ /api/reservations                 │ http://serveur:8000
           │ /api/availability                 │
           ▼                                   ▼
        ┌──────────────────────────────────────────────┐
        │              API REST — FastAPI               │
        │   Validation (Pydantic) · Logique métier      │
        │   Routers : reservations / quota / clients    │
        └───────────────────────┬──────────────────────┘
                                │ SQLAlchemy ORM
                                ▼
                   ┌────────────────────────┐
                   │      PostgreSQL         │
                   │  reservations · clients │
                   │      daily_quotas       │
                   └────────────────────────┘
```

### 3.2 Principes d'architecture

- **3-tiers** : présentation (clients) / logique (API) / données (PostgreSQL).
- **Source de vérité unique** : la base PostgreSQL, jamais accédée directement
  par les clients.
- **API comme contrat** : les deux clients consomment les mêmes endpoints, ce qui
  garantit que les règles métier (quotas, validation) sont appliquées de façon
  identique.
- **Modèle MVC** côté client lourd : séparation Vue (`components/`) / accès
  données (`api_client.py`) / contrôleur (`main.py`).

---

## 4. Stack technique

### 4.1 API REST — `savora_api`

| Outil | Version | Rôle |
|-------|---------|------|
| **FastAPI** | 0.115.0 | Framework web / API REST |
| **Uvicorn** | 0.30.6 | Serveur ASGI |
| **SQLAlchemy** | 2.0.35 | ORM (mapping objet-relationnel) |
| **psycopg2-binary** | 2.9.12 | Driver PostgreSQL |
| **Pydantic** | 2.9.2 | Validation des données (+ `email-validator`) |
| **python-dotenv** | 1.0.1 | Chargement des variables d'environnement |

### 4.2 Client léger — `SavoraWeb`

| Outil | Version | Rôle |
|-------|---------|------|
| **SvelteKit** | 2.50.2 | Framework full-stack (SSR + client) |
| **Svelte** | 5.54 | Bibliothèque UI (runes : `$state`, `$derived`, `$effect`) |
| **Drizzle ORM** | 0.45.1 | ORM TypeScript (typage strict du schéma) |
| **drizzle-kit** | 0.31.8 | Outils CLI (push, studio, migrations) |
| **postgres** | 3.4.8 | Driver PostgreSQL (Node) |
| **bits-ui** | 2.16.4 | Composants accessibles (calendrier) |
| **phosphor-svelte** | 3.1.0 | Icônes |
| **TypeScript** | 5.9.3 | Typage statique |
| **Vite** | 7.3.1 | Bundler / serveur de dev |

### 4.3 Client lourd — `savora_desktop`

| Outil | Version | Rôle |
|-------|---------|------|
| **Python** | 3.13 | Langage |
| **CustomTkinter** | — | Bibliothèque UI moderne basée sur Tkinter |
| **requests** | — | Client HTTP vers l'API |
| **threading** | (stdlib) | Appels API non bloquants |

### 4.4 Outils transverses

- **SGBD** : PostgreSQL
- **Versionning** : Git / GitHub (`SavoraApp`, `SavoraWeb`)
- **IDE** : Visual Studio Code
- **Conception** : Figma, Excalidraw
- **Déploiement cible** : VM Debian + Apache (reverse proxy)

---

## 5. Modèle de données

### 5.1 Modèle Conceptuel de Données (MCD)

```
CLIENT (1,n) ─────< effectue >───── (1,1) RÉSERVATION
   id                                    id
   civility                              party_size
   first_name                            date
   last_name                             time_slot
   phone                                 meal_period
   email  ◀──── lien logique par email ──── email
   notes                                 civility, first_name, last_name, phone
   created_at                            special_requests
                                         status
                                         staff_note
                                         created_at, updated_at

DAILY_QUOTA
   id
   date            ┐ contrainte d'unicité
   meal_period     ┘ (date + meal_period)
   max_covers
```

> **Note de conception** : le lien Client ⇆ Réservation est un **lien logique par
> adresse e-mail** (et non une clé étrangère stricte). Ce choix permet à une
> réservation d'exister même si aucune fiche client n'a encore été créée (cas du
> formulaire web), la fiche client étant créée/rapprochée ensuite.

### 5.2 Modèle Logique de Données (MLD)

```
clients (id PK, created_at, updated_at, civility, first_name, last_name,
         phone, email UNIQUE, notes)

reservations (id PK, created_at, updated_at, party_size, date, time_slot,
              meal_period, civility, first_name, last_name, phone, email,
              special_requests, save_data_consent, terms_accepted,
              status, staff_note)

daily_quotas (id PK, date, meal_period, max_covers,
              UNIQUE(date, meal_period))
```

### 5.3 Types énumérés (PostgreSQL `ENUM`)

| Enum | Valeurs |
|------|---------|
| `mealperiod` | `lunch`, `dinner` |
| `reservationstatus` | `pending`, `confirmed`, `refused`, `cancelled` |
| `civility` | `Madame`, `Monsieur`, `Mx.` |

### 5.4 Description détaillée des tables

#### Table `reservations`

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| `id` | INTEGER | PK, auto-incrément | Identifiant |
| `created_at` | TIMESTAMP TZ | défaut = now() | Date de création |
| `updated_at` | TIMESTAMP TZ | maj auto | Dernière modification |
| `party_size` | INTEGER | 1 à 6 | Nombre de couverts |
| `date` | DATE | ≥ aujourd'hui | Date de la réservation |
| `time_slot` | VARCHAR(5) | créneau valide | Heure (ex : `19:30`) |
| `meal_period` | ENUM | lunch / dinner | Service |
| `civility` | ENUM | — | Civilité du client |
| `first_name` | VARCHAR(100) | NOT NULL | Prénom |
| `last_name` | VARCHAR(100) | NOT NULL | Nom |
| `phone` | VARCHAR(20) | NOT NULL | Téléphone |
| `email` | VARCHAR(200) | NOT NULL | E-mail (lien client) |
| `special_requests` | TEXT | nullable | Demandes spéciales |
| `save_data_consent` | BOOLEAN | défaut false | Consentement RGPD |
| `terms_accepted` | BOOLEAN | défaut false | CGU acceptées |
| `status` | ENUM | défaut `pending` | État de la réservation |
| `staff_note` | TEXT | nullable | Note interne du personnel |

#### Table `clients`

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| `id` | INTEGER | PK | Identifiant client |
| `created_at` | TIMESTAMP TZ | défaut now() | Création |
| `updated_at` | TIMESTAMP TZ | maj auto | Modification |
| `civility` | ENUM | NOT NULL | Civilité |
| `first_name` | VARCHAR(100) | NOT NULL | Prénom |
| `last_name` | VARCHAR(100) | NOT NULL | Nom |
| `phone` | VARCHAR(20) | NOT NULL | Téléphone |
| `email` | VARCHAR(200) | **UNIQUE**, indexé | E-mail (clé de rapprochement) |
| `notes` | TEXT | nullable | Notes internes |

#### Table `daily_quotas`

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| `id` | INTEGER | PK | Identifiant |
| `date` | DATE | — | Jour concerné |
| `meal_period` | ENUM | — | Service concerné |
| `max_covers` | INTEGER | défaut 15 | Capacité max de couverts |
| | | UNIQUE(date, meal_period) | Un quota par service et par jour |

> **Capacité par défaut** : si aucun quota n'est défini pour un service donné,
> la valeur par défaut est **15 couverts** (constante `DEFAULT_MAX_COVERS`).

---

## 6. API REST (FastAPI)

L'API est exposée sur le port **8000**. Documentation interactive Swagger
disponible sur **`/docs`** et ReDoc sur **`/redoc`**.

### 6.1 Organisation du code

```
savora_api/
├── main.py            # Point d'entrée, montage des routers, CORS
├── database.py        # Connexion SQLAlchemy, session, get_db()
├── models.py          # Modèles ORM (tables) + enums
├── schemas.py         # Schémas Pydantic (validation entrée/sortie)
├── requirements.txt   # Dépendances
├── .env               # DATABASE_URL
└── routers/
    ├── reservations.py # CRUD réservations + changement de statut
    ├── quota.py        # Quotas & disponibilités
    └── clients.py      # CRUD clients + import
```

### 6.2 Endpoints — Réservations

| Méthode | Route | Description |
|---------|-------|-------------|
| `POST` | `/reservations/` | Créer une réservation (vérifie le quota, auto-crée le client) |
| `GET` | `/reservations` | Lister (filtres : `date`, `meal_period`, `status`) |
| `GET` | `/reservations/{id}` | Détail d'une réservation |
| `PATCH` | `/reservations/{id}` | Modifier (revérifie le quota si couverts/date/service change) |
| `PATCH` | `/reservations/{id}/status` | Valider / refuser / annuler |
| `DELETE` | `/reservations/{id}` | Supprimer |

### 6.3 Endpoints — Quota & Disponibilité

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/quota/{date}/{meal_period}` | Quota d'un service (max, réservé, dispo, complet ?) |
| `PUT` | `/quota/{date}/{meal_period}` | Définir/modifier le quota d'un service |
| `GET` | `/availability/{date}` | Disponibilité midi/soir (utilisé par le site web) |

### 6.4 Endpoints — Clients

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/clients/` | Lister (avec nombre de réservations par client) |
| `GET` | `/clients/{id}` | Détail d'un client |
| `GET` | `/clients/{id}/reservations` | Historique des réservations (lien par e-mail) |
| `POST` | `/clients/` | Créer (409 si e-mail déjà existant) |
| `PATCH` | `/clients/{id}` | Modifier |
| `DELETE` | `/clients/{id}` | Supprimer |
| `POST` | `/clients/import-from-reservations` | Importer auto les clients depuis les réservations |

### 6.5 Endpoint — Santé

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/` | Vérification de l'état du service (`{"status": "ok"}`) |

### 6.6 Validation des données (Pydantic)

Le schéma `ReservationCreate` applique automatiquement les règles suivantes
avant tout enregistrement :

- `party_size` : entre **1 et 6** couverts.
- `time_slot` : doit appartenir aux créneaux valides :
  - **Midi** : `12:00, 12:30, 13:00, 13:30`
  - **Soir** : `19:00, 19:30, 20:00, 20:30, 21:00, 21:30`
- `date` : ne peut **pas** être dans le passé.
- `email` : format e-mail valide (type `EmailStr`).
- `terms_accepted` : doit être `true` (acceptation des CGU obligatoire).

---

## 7. Client léger (SvelteKit)

### 7.1 Rôle

Site web public à **deux fonctions** :
1. **Vitrine** : présentation du restaurant (concept, philosophie, horaires).
2. **Réservation en ligne** : formulaire avec vérification des disponibilités en
   temps réel.

### 7.2 Structure

```
src/
├── app.html, app.d.ts
├── routes/
│   ├── +layout.svelte
│   ├── +page.svelte            # Assemble tous les composants de la page
│   └── api/                    # Routes serveur (proxy vers FastAPI)
│       ├── reservations/+server.ts        # POST -> FastAPI /reservations/
│       └── availability/[date]/+server.ts # GET  -> FastAPI /availability/{date}
├── lib/
│   ├── components/
│   │   ├── Navbar.svelte
│   │   ├── Presentation.svelte
│   │   ├── Philosophy.svelte
│   │   ├── Manifeste.svelte
│   │   ├── DiningHours.svelte
│   │   ├── Reservation.svelte   # Formulaire + logique de réservation
│   │   └── Footer.svelte
│   └── server/db/
│       ├── index.ts             # Connexion Drizzle (postgres-js)
│       └── schema.ts            # Schéma Drizzle (miroir typé des tables)
```

### 7.3 Rôle de Drizzle ORM

Drizzle fournit un **schéma TypeScript fortement typé** (`schema.ts`) qui reflète
les tables PostgreSQL. Il garantit :
- un **typage strict** des données côté serveur SvelteKit (`Reservation`,
  `NewReservation` inférés du schéma) ;
- des outils CLI (`db:studio`, `db:push`) pour inspecter/synchroniser la base.

> Les **migrations** restent gérées côté FastAPI (SQLAlchemy
> `Base.metadata.create_all`). Drizzle agit ici comme couche de **typage et
> d'inspection**, conformément à une architecture où l'API REST reste le point
> d'écriture unique.

### 7.4 Architecture proxy (pas de CORS)

Le navigateur n'appelle **jamais** FastAPI directement. Il appelle des routes
serveur SvelteKit (`/api/...`) qui relaient la requête vers FastAPI. Avantages :
- **Pas de problème CORS** (même origine pour le navigateur).
- L'URL de l'API (`API_URL`) reste **côté serveur**, configurable par
  variable d'environnement.

### 7.5 Réservation dynamique

Le composant `Reservation.svelte` :
1. À chaque changement de date, appelle `/api/availability/{date}`.
2. **Grise et désactive** les créneaux d'un service complet (réactivité Svelte 5).
3. À la soumission, envoie un `POST /api/reservations` qui applique côté serveur
   toutes les validations métier.

---

## 8. Client lourd (CustomTkinter)

### 8.1 Rôle

Application de bureau destinée au **personnel**. Interface inspirée des outils
professionnels (type Zenchef) : navigation par date, planning groupé par créneau,
onglets de statut, gestion des clients.

### 8.2 Structure (modèle MVC)

```
savora_desktop/
├── main.py             # CONTRÔLEUR : orchestration, navigation, threads
├── api_client.py       # MODÈLE : accès aux données via l'API REST
├── config.py           # Constantes (capacité, couleurs, libellés FR)
├── requirements.txt
└── components/         # VUES
    ├── reservation_list.py      # Liste groupée par créneau horaire
    ├── reservation_detail.py    # Détail + actions (valider/refuser/modifier)
    ├── quota_panel.py           # Réglage du quota de couverts
    ├── clients_list.py          # Liste des clients (recherche)
    ├── client_detail.py         # Fiche client + historique
    ├── new_reservation_dialog.py# Création d'une réservation
    └── new_client_dialog.py     # Création d'un client
```

| Couche MVC | Fichiers | Responsabilité |
|------------|----------|----------------|
| **Modèle** | `api_client.py` | Communication HTTP avec l'API (aucune logique UI) |
| **Vue** | `components/*.py` | Affichage et interactions utilisateur |
| **Contrôleur** | `main.py` | Coordonne vues ↔ modèle, gère l'état applicatif |

### 8.3 Fonctionnalités (couverture du DCU)

| Cas d'utilisation | Implémentation |
|-------------------|----------------|
| **Consulter le planning** | Vue liste groupée par créneau, navigation par date (‹ ›), filtre service (midi/soir), onglets de statut avec compteurs |
| **Valider / refuser / annuler** | Boutons dans le panneau détail → `PATCH /reservations/{id}/status` |
| **Modifier une réservation** | Édition des couverts, note interne → `PATCH /reservations/{id}` |
| **Gérer les clients (CRUD)** | Liste, création, modification, suppression, historique, import |
| **Gérer les places disponibles** | Panneau quota → `PUT /quota/{date}/{meal_period}` |

### 8.4 Fluidité (appels non bloquants)

Tous les appels réseau s'exécutent dans des **threads séparés** (`threading.Thread`),
les mises à jour de l'interface étant renvoyées sur le thread principal via
`self.after(0, ...)`. Optimisations mises en place :

- **Session HTTP persistante** (`requests.Session`) : réutilise la connexion TCP
  (keep-alive) → gain ~50–150 ms par appel.
- **Debounce** sur le rechargement : les clics rapides (navigation date, filtres)
  sont fusionnés en un seul appel réseau.
- **Boutons désactivés** pendant un appel : évite les doubles soumissions et
  signale visuellement le traitement.
- **Rafraîchissement automatique** toutes les 30 s.

---

## 9. Règles de gestion métier

| # | Règle | Où elle est appliquée |
|---|-------|----------------------|
| RG1 | Une réservation comporte de **1 à 6 couverts**. | API (Pydantic) |
| RG2 | Créneaux **midi** (12:00–13:30) et **soir** (19:00–21:30) uniquement. | API (Pydantic) |
| RG3 | Une réservation ne peut pas être dans le **passé**. | API (Pydantic) |
| RG4 | La capacité par service est de **15 couverts** par défaut (modifiable). | API (`DEFAULT_MAX_COVERS`) |
| RG5 | Si l'ajout d'une réservation **dépasse le quota**, elle est **refusée** (HTTP 409). | API (`_check_quota`) |
| RG6 | Seules les réservations **`pending`** et **`confirmed`** comptent dans le total de couverts réservés. | API (quota) |
| RG7 | À la création d'une réservation, le **client est auto-créé** s'il n'existe pas (lien par e-mail). | API (`create_reservation`) |
| RG8 | Un e-mail client est **unique**. | BDD + API (409) |
| RG9 | L'acceptation des **CGU** est obligatoire pour réserver. | API (Pydantic) |
| RG10 | À la **confirmation**, le quota est revérifié. | API (`update_status`) |

### Cycle de vie d'une réservation

```
   [Client web]            [Staff]                 [Staff]
        │                     │                       │
   POST réservation     valider / refuser        modifier / annuler
        │                     │                       │
        ▼                     ▼                       ▼
   ┌─────────┐  confirm  ┌──────────┐           ┌──────────┐
   │ pending │──────────▶│confirmed │──────────▶│cancelled │
   └────┬────┘           └──────────┘           └──────────┘
        │ refuse
        ▼
   ┌─────────┐
   │ refused │
   └─────────┘
```

---

## 10. Sécurité

| Mesure | Description |
|--------|-------------|
| **Validation systématique** | Toute entrée passe par Pydantic (types, bornes, formats). |
| **ORM paramétré** | SQLAlchemy et Drizzle évitent les injections SQL (requêtes paramétrées). |
| **Pas d'accès direct à la BDD** | Les clients passent uniquement par l'API REST. |
| **Proxy serveur (SvelteKit)** | L'URL et les accès API restent côté serveur, jamais exposés au navigateur. |
| **CORS restreint** | Seules les origines déclarées sont autorisées (dev local). |
| **Utilisateur BDD dédié** | En production, PostgreSQL est accédé par un utilisateur **non-root** disposant des privilèges sur la seule base `savora`. |
| **Variables d'environnement** | Les secrets (URL BDD, mot de passe) sont dans `.env`, hors du dépôt Git. |
| **Consentement RGPD** | Champ `save_data_consent` recueilli au moment de la réservation. |

---

## 11. Scénarios / flux de données

### 11.1 Réservation depuis le site web

```
Client (navigateur)
   │  1. Choisit date → GET /api/availability/{date}
   ▼
SvelteKit (serveur)  ──proxy──▶  FastAPI  ──▶  PostgreSQL
   │  2. Créneaux complets grisés
   │  3. Remplit le formulaire → POST /api/reservations
   ▼
SvelteKit (serveur)  ──proxy──▶  FastAPI
                                   │ vérifie quota (RG5)
                                   │ crée la réservation (status=pending)
                                   │ auto-crée le client (RG7)
                                   ▼
                                PostgreSQL
```

### 11.2 Validation par le personnel

```
Staff (client lourd)
   │  1. Sélectionne une date → GET /reservations?date=...
   │  2. Clique une réservation → panneau détail
   │  3. Clique « Confirmer » → PATCH /reservations/{id}/status
   ▼
FastAPI  → revérifie le quota (RG10) → met à jour le statut → PostgreSQL
   │
   ▼
Rafraîchissement automatique de la liste (client lourd)
```

### 11.3 Cohérence inter-clients

Une réservation créée sur le **site web** apparaît immédiatement dans le **client
lourd** (au prochain rafraîchissement), car les deux interrogent la **même base**
via la **même API**. Inversement, une modification de quota par le personnel
impacte aussitôt les disponibilités affichées sur le site.

---

## 12. Déploiement

### 12.1 Cible

Machine virtuelle **Debian** hébergeant :
- **PostgreSQL** (port 5432) — utilisateur applicatif non-root.
- **API FastAPI** (port 8000) via Uvicorn.
- **Client léger SvelteKit** (port 3000) via Node.
- **Apache** en **reverse proxy** (port 80) routant `/` → SvelteKit et `/api/` → FastAPI.

Le **client lourd** s'exécute sur les postes du personnel (Windows) et pointe vers
l'IP de la VM.

### 12.2 Pré-requis serveur

```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib python3 python3-venv python3-pip \
                    nodejs npm apache2
```

### 12.3 PostgreSQL — utilisateur non-root

```bash
sudo -u postgres psql <<'EOF'
CREATE USER savora WITH PASSWORD 'CHANGER_CE_MOT_DE_PASSE';
CREATE DATABASE savora OWNER savora;
GRANT ALL PRIVILEGES ON DATABASE savora TO savora;
EOF
```

### 12.4 API FastAPI

```bash
cd /opt/savora/savora_api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# .env :
#   DATABASE_URL=postgresql://savora:MOT_DE_PASSE@localhost:5432/savora
nohup venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 &
```

### 12.5 Client léger SvelteKit

> **⚠️ Action requise** : remplacer `@sveltejs/adapter-auto` par
> **`@sveltejs/adapter-node`** pour générer un serveur Node autonome.

```bash
cd /opt/savora/savora_web
npm install @sveltejs/adapter-node
# svelte.config.js : import adapter from '@sveltejs/adapter-node';
npm install
npm run build
# .env :
#   API_URL=http://localhost:8000
#   DATABASE_URL=postgresql://savora:MOT_DE_PASSE@localhost:5432/savora
node build &   # écoute sur le port 3000
```

### 12.6 Apache — reverse proxy

```apache
# /etc/apache2/sites-available/savora.conf
<VirtualHost *:80>
    ServerName  savora.local

    ProxyPreserveHost On

    # API REST
    ProxyPass        /api/  http://localhost:8000/
    ProxyPassReverse /api/  http://localhost:8000/

    # Site web (SvelteKit)
    ProxyPass        /      http://localhost:3000/
    ProxyPassReverse /      http://localhost:3000/

    ErrorLog  ${APACHE_LOG_DIR}/savora-error.log
    CustomLog ${APACHE_LOG_DIR}/savora-access.log combined
</VirtualHost>
```

```bash
sudo a2enmod proxy proxy_http
sudo a2ensite savora.conf
sudo a2dissite 000-default.conf
sudo systemctl restart apache2
```

### 12.7 Services persistants (recommandé)

Pour que l'API et le site survivent aux redémarrages, créer des **services
systemd** (`savora-api.service`, `savora-web.service`) plutôt que `nohup`.

---

## 13. Installation & exécution en développement

### 13.1 API

```bash
cd savora_api
python -m venv venv && venv\Scripts\activate     # Windows
pip install -r requirements.txt
uvicorn main:app --reload
# → http://localhost:8000/docs
```

> Sans Docker/PostgreSQL, l'API bascule sur **SQLite** (`sqlite:///./savora.db`)
> automatiquement (fallback de développement).

### 13.2 Client léger

```bash
cd "Client Leger"
npm install
npm run dev
# → http://localhost:5173
```

### 13.3 Client lourd

```bash
cd savora_desktop
pip install -r requirements.txt
python main.py
```

---

## 14. Annexes

### 14.1 Dépôts Git

| Dépôt | URL |
|-------|-----|
| API + client lourd | https://github.com/ballagye/SavoraApp |
| Client léger | https://github.com/ballagye/SavoraWeb |

### 14.2 Variables d'environnement

| Variable | Composant | Exemple |
|----------|-----------|---------|
| `DATABASE_URL` | API / SvelteKit | `postgresql://savora:***@localhost:5432/savora` |
| `API_URL` | SvelteKit | `http://localhost:8000` |
| `BASE_URL` | Client lourd (`api_client.py`) | `http://localhost:8000` |

### 14.3 Glossaire

| Terme | Définition |
|-------|------------|
| **Client léger** | Application web exécutée dans un navigateur (SvelteKit). |
| **Client lourd** | Application de bureau installée (CustomTkinter). |
| **ORM** | Object-Relational Mapping : couche traduisant objets ↔ tables. |
| **Quota** | Nombre maximal de couverts autorisés pour un service donné. |
| **Service** | Période de repas : midi (lunch) ou soir (dinner). |
| **Reverse proxy** | Serveur (Apache) qui redistribue les requêtes vers les bons services internes. |

---

*Document rédigé dans le cadre de l'épreuve E6 — BTS SIO SLAM, session 2026.*
