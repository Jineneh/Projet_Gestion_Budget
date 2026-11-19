# Gestion de budget personnel

Application en ligne de commande (Python 3.11+) pour suivre ses revenus et ses dépenses, fixer un
plafond mensuel par catégorie, être alerté avant le dépassement et obtenir un rapport mensuel.
Projet du cours *Programmation épurée* (Master 2) : programmation orientée objet et Clean Code.

## Fonctionnalités

- Ajouter un revenu ou une dépense (montant, date, catégorie, description)
- Définir un plafond mensuel par catégorie, avec alertes « Attention » à 80 % et « Dépassement » au-delà de 100 %
- Rapport mensuel : revenus, dépenses, solde, détail par catégorie, alertes
- Sauvegarde et chargement (JSON) ; import de CSV qui rejette les lignes invalides avec un message clair

## Prérequis

Python 3.11 ou plus récent. L'application n'utilise que la bibliothèque standard ; `requirements.txt`
ne contient que les outils de développement (pytest, pytest-cov, ruff).

## Installation

```bash
git clone https://github.com/Jineneh/Projet_Gestion_Budget.git
cd Projet_Gestion_Budget
python -m venv .venv
source .venv/bin/activate          # Windows (PowerShell) : .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

Sous PowerShell, si l'activation est refusée : `Set-ExecutionPolicy -Scope Process Bypass`.

## Exécution

```bash
python -m budget                                   # données dans budget.json
python -m budget --fichier data/mon_budget.json    # autre fichier de données
```

Le menu propose : ajouter, lister, définir un plafond, rapport et alertes, importer un CSV,
sauvegarder, charger. Un fichier de données illisible n'est jamais écrasé.

### Scénario de démonstration

1. Choisir `5` (importer), puis `data/exemple_transactions.csv` et `data/exemple_plafonds.csv` :
   15 transactions et 3 plafonds importés.
2. Choisir `4` (rapport), mois `2026-10` : solde de 1 120,01 EUR, alerte « Attention » sur
   Alimentation (90 %), « Dépassement » sur Loisirs (105 %).
3. Choisir `5`, puis `data/exemple_transactions_invalides.csv` : 2 lignes importées, 5 rejetées
   avec leur motif (montant négatif, montant non numérique, date impossible, type inconnu,
   catégorie vide).
4. Choisir `1` avec un montant `abc` : un message d'erreur s'affiche et le programme continue.

## Tests et qualité

```bash
python -m pytest --cov=budget        # 187 tests, couverture 100 %
python -m ruff check src tests       # style et complexité (maximum 8 par fonction)
```

Une intégration continue (`.github/workflows/tests.yml`) lance ces deux commandes à chaque push.

## Architecture

```
src/budget/
├── modeles.py       TypeTransaction, Transaction, Budget
├── journal.py       Journal (transactions et filtres)
├── alertes.py       politiques d'alerte interchangeables
├── suivi.py         SuiviBudget (dépenses contre plafonds)
├── rapport.py       RapportMensuel (calcul) et FormateurRapportTexte (mise en forme)
├── depots.py        Depot, DepotJson, DepotCsv
├── application.py   Application (cas d'usage)
├── cli.py           interface en ligne de commande
├── constantes.py    seuils, formats, colonnes
└── erreurs.py       exceptions métier
```

La CLI appelle `Application`, qui orchestre le métier et ne connaît que l'abstraction `Depot`.
Diagramme de classes : [docs/diagrammes/diagramme_classes.png](docs/diagrammes/diagramme_classes.png).

## Choix techniques essentiels

- **Montants en `Decimal`** : aucune erreur d'arrondi sur les centimes.
- **Objets toujours valides** : `Transaction` et `Budget` valident leurs données à la construction.
- **Une responsabilité par classe** : calcul, mise en forme, stockage et dialogue sont séparés.
- **Héritage limité à deux hiérarchies** (`PolitiqueAlerte`, `Depot`), le reste est de la composition.
- **Entrée et sortie injectées** dans la CLI : l'interface se teste sans clavier ni écran.
- **Version 1 conservée** dans `legacy/` (tag Git `avant-refactoring`) pour les exemples « avant / après ».

## Documentation

- [Conception réalisée](docs/conception.md) : classes, relations, principes, écarts, limites
- [Trois exemples avant / après](docs/avant_apres.md) : SRP, Open/Closed, DRY et constantes
- [Cadrage initial](docs/Cadrage_et_conception.pdf)
- [Organisation Git](docs/workflow_git.md)

## Équipe

Jinene Hamrouni et Myriam Aoun. La répartition des tâches est détaillée dans
[docs/conception.md](docs/conception.md#8-répartition-du-travail).
