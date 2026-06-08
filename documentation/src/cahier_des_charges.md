::: cover
# Cahier des charges

## Système de réservation **Savora**

**Restaurant gastronomique Savora**

---

**BTS SIO – option SLAM – Session 2026**
Épreuve E6 — Conception et développement d'applications

**Candidat :** Balla Gueye — **N° :** 02149092520
**Période :** Janvier – Mars 2026 · **Lieu :** Paris
:::

## 1. Présentation du projet

### 1.1 Le commanditaire

Le restaurant gastronomique **Savora**, situé à Paris, connaît une forte
croissance de sa notoriété et de sa fréquentation. La prise de réservation
s'effectue aujourd'hui exclusivement **par téléphone**, ce qui provoque une
**saturation** aux heures de pointe et une perte de clientèle.

### 1.2 Le besoin exprimé

Le restaurant souhaite se doter d'une **solution numérique complète** permettant :

- de **présenter** l'établissement (concept, menus, horaires, localisation) à
  travers un site web élégant reflétant son prestige ;
- de **recevoir des réservations en ligne** 24 h/24, avec vérification
  automatique des disponibilités ;
- de **gérer ces réservations en interne** grâce à un outil dédié au personnel,
  avec un blocage automatique lorsque la capacité du restaurant est atteinte.

### 1.3 Périmètre de la solution

La solution se décompose en **trois applications** communiquant via une **API
REST** et partageant une **base de données PostgreSQL** unique :

| Application | Nature | Utilisateur |
|-------------|--------|-------------|
| Site web Savora | Client léger (web) | Le client du restaurant |
| API REST Savora | Service central | — |
| Outil de gestion | Client lourd (desktop) | Le personnel (Staff) |

---

## 2. Objectifs

| # | Objectif | Indicateur de réussite |
|---|----------|------------------------|
| O1 | Présenter le restaurant via une vitrine en ligne | Site accessible, pages vitrine complètes |
| O2 | Permettre la réservation en ligne | Une réservation aboutit et est enregistrée en base |
| O3 | Afficher les disponibilités en temps réel | Les créneaux complets sont grisés automatiquement |
| O4 | Outiller le personnel pour la gestion | Valider / refuser / modifier une réservation |
| O5 | Gérer la capacité du restaurant | Blocage automatique au-delà du quota |
| O6 | Gérer la base clientèle (CRUD) | Créer, consulter, modifier, supprimer un client |
| O7 | Garantir la cohérence des données | Une réservation web apparaît côté personnel |

---

## 3. Acteurs du système

| Acteur | Description | Droits |
|--------|-------------|--------|
| **Client** | Visiteur du site web souhaitant réserver une table. | Consulter la vitrine, vérifier les disponibilités, créer une réservation. |
| **Staff** (personnel) | Employé du restaurant gérant l'activité. | Consulter le planning, valider/refuser/modifier une réservation, gérer les clients, définir les quotas. |

---

## 4. Expression fonctionnelle du besoin

### 4.1 Fonctionnalités — Client (site web)

| Réf | Fonctionnalité | Description |
|-----|----------------|-------------|
| F1.1 | Consulter la vitrine | Concept, philosophie, menus, horaires, localisation. |
| F1.2 | Vérifier les disponibilités | Pour une date, voir si midi/soir sont disponibles. |
| F1.3 | Effectuer une réservation | Renseigner date, créneau, couverts, coordonnées. |
| F1.4 | Visualiser un récapitulatif | Confirmation **à l'écran** de l'enregistrement de la demande (statut « en attente »). *Aucun e-mail n'est envoyé : la validation est effectuée par le personnel via l'outil interne.* |

### 4.2 Fonctionnalités — Staff (outil de gestion)

| Réf | Fonctionnalité | Description |
|-----|----------------|-------------|
| F2.1 | Consulter le planning | Réservations groupées par créneau, navigation par date. |
| F2.2 | Filtrer les réservations | Par service (midi/soir) et par statut. |
| F2.3 | Valider une réservation | Passage du statut à « confirmée ». |
| F2.4 | Refuser une réservation | Passage du statut à « refusée ». |
| F2.5 | Modifier une réservation | Couverts, note interne. |
| F2.6 | Annuler / supprimer | Annulation ou suppression d'une réservation. |
| F2.7 | Créer une réservation | Saisie manuelle (réservation par téléphone). |
| F2.8 | Gérer les clients (CRUD) | Créer, consulter, modifier, supprimer une fiche client. |
| F2.9 | Consulter l'historique client | Réservations passées d'un client. |
| F2.10 | Importer les clients | Générer les fiches depuis les réservations existantes. |
| F2.11 | Définir les quotas | Capacité maximale de couverts par service. |

---

## 5. Règles de gestion

| Réf | Règle |
|-----|-------|
| RG1 | Une réservation comporte de **1 à 6 couverts**. |
| RG2 | Les créneaux sont fixés, espacés de 30 minutes : **midi** 12:00–13:30, **soir** 19:00–21:30. |
| RG3 | Une réservation ne peut pas être dans le **passé**. |
| RG4 | La capacité par défaut est de **15 couverts** par service et par jour. |
| RG5 | Toute réservation faisant **dépasser le quota** est refusée automatiquement. |
| RG6 | Seules les réservations **en attente** et **confirmées** consomment des couverts. |
| RG7 | À chaque réservation, la **fiche client est créée** si elle n'existe pas (clé : e-mail). |
| RG8 | L'**e-mail** identifie de façon unique un client. |
| RG9 | L'acceptation des **CGU** est obligatoire pour réserver. |
| RG10 | La **confirmation** d'une réservation revérifie le quota. |

---

## 6. Contraintes techniques

| Domaine | Contrainte |
|---------|-----------|
| **Site web** | SvelteKit, Drizzle ORM, TypeScript |
| **API** | FastAPI (Python), architecture REST |
| **Client lourd** | Python, CustomTkinter, architecture MVC |
| **Base de données** | PostgreSQL |
| **Communication** | Échanges exclusivement via l'API REST (format JSON) |
| **Versionning** | Git / GitHub |
| **Déploiement** | VM Debian, serveur Apache (reverse proxy), utilisateur PostgreSQL non-root |
| **Sécurité** | Validation des entrées, ORM paramétré, secrets hors dépôt |

---

## 7. Contraintes non fonctionnelles

| Domaine | Exigence |
|---------|----------|
| **Ergonomie** | Interfaces claires, prise en main immédiate par le personnel. |
| **Performance** | Réactivité de l'outil de gestion (appels réseau non bloquants). |
| **Fiabilité** | Cohérence garantie entre site web et outil interne. |
| **Maintenabilité** | Code structuré (MVC), typage strict, documentation fournie. |
| **Disponibilité** | Réservation en ligne accessible 24 h/24. |

---

## 8. Livrables attendus

| Livrable | Format |
|----------|--------|
| Base de données PostgreSQL opérationnelle | SGBD |
| API REST fonctionnelle (FastAPI) | Code source |
| Site web (client léger SvelteKit) | Code source déployé |
| Application client lourd (CustomTkinter) | Code source |
| Diagrammes UML (DCU, diagramme de classes) | Documents |
| Maquette de l'application | Document |
| Documentation technique et utilisateur | PDF |
| Code source versionné | Dépôts GitHub |

---

## 9. Planning prévisionnel

| Phase | Période | Contenu |
|-------|---------|---------|
| Analyse | Janvier 2026 | Recueil des besoins, règles de gestion, DCU. |
| Conception | Janvier 2026 | Modèle de données, maquettes, architecture. |
| Développement BDD + API | Février 2026 | Tables, endpoints REST, validation. |
| Développement site web | Février 2026 | Vitrine + module de réservation. |
| Développement client lourd | Février – Mars 2026 | Gestion réservations, clients, quotas. |
| Tests & déploiement | Mars 2026 | Tests, déploiement VM Debian, documentation. |

---

*Cahier des charges — BTS SIO SLAM, session 2026.*
