::: cover
# Guide utilisateur

## Application de gestion — **Savora**
### Client lourd (poste du personnel)

---

**BTS SIO – option SLAM – Session 2026**
Épreuve E6 — Conception et développement d'applications

**Candidat :** Balla Gueye — **N° :** 02149092520
**Période :** Janvier – Mars 2026 · **Lieu :** Paris
:::

---

## 1. À qui s'adresse ce guide ?

Ce guide est destiné au **personnel du restaurant** (Staff) qui utilise
l'application de bureau **Savora** pour gérer les réservations, les clients et la
capacité du restaurant. Aucune compétence technique n'est requise.

---

## 2. Démarrer l'application

Au préalable, l'**API** doit être démarrée (par le responsable technique). Ensuite :

1. Ouvrir le dossier `savora_desktop`.
2. Lancer l'application :

```
python main.py
```

La fenêtre principale s'ouvre sur le **planning du jour**.

> Si un message d'erreur de connexion apparaît, c'est que l'API n'est pas démarrée.
> Prévenir le responsable technique.

---

## 3. Vue d'ensemble de l'interface

L'écran se compose de quatre zones :

| Zone | Emplacement | Rôle |
|------|-------------|------|
| **Barre d'en-tête** | En haut | Logo, navigation par date, filtres, changement de vue, bouton de création. |
| **Barre de statuts** | Sous l'en-tête | Compteurs par statut (tous, en attente, confirmées, refusées, annulées). |
| **Planning** | À gauche | Liste des réservations groupées par créneau horaire. |
| **Panneau de détail** | À droite | Détail de la réservation sélectionnée et actions. |
| **Barre de quota** | En bas | Réglage de la capacité de couverts par service. |

---

## 4. Consulter le planning

### 4.1 Changer de date

- Utiliser les flèches **‹** et **›** pour reculer/avancer d'un jour.
- La date courante s'affiche au centre (ex. *MAR. 27 JUIN*).
- Cliquer sur **TOUT** pour afficher **toutes les réservations**, toutes dates
  confondues.

### 4.2 Filtrer par service

Boutons **TOUS** / **DÉJEUNER** / **DÎNER** : n'afficher qu'un service.

### 4.3 Filtrer par statut

Dans la barre de statuts, cliquer un compteur pour ne garder que les réservations
de ce statut. Les chiffres indiquent le nombre de réservations dans chaque état.

### 4.4 Rechercher un client

Le champ **🔍 Rechercher** filtre la liste par nom ou prénom (saisir au moins
2 caractères).

### 4.5 Lire le planning

Chaque créneau affiche un en-tête : **heure**, nombre de réservations (📋) et total
de couverts (🍴 X / 15). Chaque ligne montre l'icône de statut, le nom, le téléphone
et le nombre de couverts. La **barre colorée** à gauche indique le statut :

| Couleur | Statut |
|---------|--------|
| 🟢 Vert | Confirmée |
| 🟠 Ambre | En attente |
| 🔴 Rouge | Refusée |
| ⚪ Gris | Annulée |

---

## 5. Traiter une réservation

Cliquer sur une ligne du planning : son détail s'affiche à droite.

### 5.1 Valider ou refuser

- **✓ Confirmer** : valide la réservation (passe en *confirmée*).
- **✕ Refuser** : refuse la réservation (passe en *refusée*).

> À la validation, l'application **revérifie automatiquement la capacité**. Si le
> service est complet, la confirmation est refusée avec un message d'alerte.

### 5.2 Modifier le nombre de couverts

Dans **Modifier couverts**, saisir la nouvelle valeur puis **Enregistrer**.

### 5.3 Ajouter une note interne

Saisir un texte dans **Note interne** (visible uniquement par le personnel), puis
effectuer une action (la note est enregistrée avec le changement de statut).

### 5.4 Annuler ou supprimer

- **Annuler la résa** : passe la réservation en *annulée* (conservée dans
  l'historique).
- **Supprimer** : efface définitivement la réservation (confirmation demandée).

---

## 6. Créer une réservation manuelle

Pour une réservation reçue **par téléphone** :

1. Cliquer sur **＋ Nouvelle réservation** (en haut à droite).
2. Renseigner la date, le créneau, le nombre de couverts et les coordonnées du
   client.
3. Valider : la réservation est créée et le **client est automatiquement ajouté**
   au fichier clients s'il n'existe pas encore.

> Si la capacité du service est atteinte, la création est bloquée.

---

## 7. Gérer les clients

Cliquer sur **👥 Clients** dans l'en-tête pour basculer en vue clients.

### 7.1 Consulter

La liste affiche chaque client avec ses initiales, son e-mail et son nombre de
réservations. Cliquer un client affiche sa fiche détaillée et son **historique de
réservations** à droite.

### 7.2 Créer un client

1. Cliquer **＋ Nouveau client**.
2. Renseigner civilité, prénom, nom, téléphone, e-mail (et éventuellement des
   notes).
3. Valider. *(L'e-mail doit être unique : un message d'erreur apparaît s'il existe
   déjà.)*

### 7.3 Modifier ou supprimer

Sur la fiche d'un client : **✎ Modifier** pour éditer les informations,
**Supprimer** pour retirer la fiche.

### 7.4 Importer les clients existants

Le bouton **⬇ Importer réservations** crée automatiquement une fiche client pour
chaque e-mail présent dans les réservations mais sans fiche. Utile pour initialiser
le fichier clients.

---

## 8. Régler la capacité (quotas)

La **barre de quota** en bas permet de définir le nombre maximal de couverts pour
le service affiché :

1. Saisir la valeur dans **Max couverts** (15 par défaut).
2. Cliquer **Enregistrer**.

Dès qu'un service atteint sa capacité, les nouvelles réservations en ligne sont
**automatiquement bloquées** et le créneau apparaît *complet* sur le site web.

---

## 9. Astuces & dépannage

| Situation | Solution |
|-----------|----------|
| La liste ne se met pas à jour | Cliquer le bouton **↻** (rafraîchir). L'app se rafraîchit aussi toutes les 30 s. |
| « Erreur de connexion » | L'API n'est pas démarrée → prévenir le responsable technique. |
| Impossible de confirmer | Le service est complet : augmenter le quota ou refuser une autre réservation. |
| Un client n'apparaît pas | Utiliser **⬇ Importer réservations** ou le créer manuellement. |

---

*Guide utilisateur — BTS SIO SLAM, session 2026.*
