# Gestion de budget personnel

Application (Python 3.11+) pour suivre ses revenus et ses dépenses, fixer un plafond mensuel par
catégorie, être alerté avant le dépassement et obtenir un rapport mensuel. Elle s'utilise en ligne
de commande ou depuis une interface web.
Projet du cours *Programmation épurée* (Master 2) : programmation orientée objet et Clean Code.

**Interface web en ligne : https://gestion-budget-project.streamlit.app/**

## Fonctionnalités

- Ajouter un revenu ou une dépense (montant, date, catégorie, description)
- Définir un plafond mensuel par catégorie, avec alertes « Attention » à 80 % et « Dépassement » au-delà de 100 %
- Rapport mensuel : revenus, dépenses, solde, détail par catégorie, alertes
- Sauvegarde et chargement (JSON) ; import de CSV qui rejette les lignes invalides avec un message clair
- Deux interfaces au-dessus de la même logique métier : ligne de commande et interface web

## Prérequis

Python 3.11 ou plus récent. L'application en ligne de commande n'utilise que la bibliothèque standard ;
`requirements.txt` ne contient que les outils de développement (pytest, pytest-cov, ruff).
L'interface web ajoute une dépendance, Streamlit (`web/requirements.txt`).

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

## Exécution en ligne de commande

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

## Interface web

Disponible en ligne sur https://gestion-budget-project.streamlit.app/ (Streamlit). Aucune installation
n'est nécessaire : ouvrir le lien, puis cliquer sur « Charger les données d'exemple ».

Pages : tableau de bord (reste à dépenser, plafonds contre dépenses, répartition), transactions
(saisie validée et suivi filtrable), plafonds (suivi et simulateur d'alertes), rapport mensuel,
données (import CSV, sauvegarde JSON), architecture (diagramme UML, avant / après) et guide en six étapes.

Pour la lancer en local :

```bash
pip install -r web/requirements.txt
python -m streamlit run web/app.py          # ouvre http://localhost:8501
```

Points à connaître :

- L'interface réutilise l'`Application` du dossier `src/` sans la modifier : la ligne de commande et
  le web partagent exactement la même logique métier.
- Les données de chaque visiteur sont gardées en mémoire, séparées de celles des autres, et
  disparaissent à la fermeture. Le bouton « Télécharger ma sauvegarde (.json) » permet de les conserver.
- Une application gratuite s'endort après quelques jours sans visite : un clic sur « Wake up » la réveille.
- Le thème est défini dans `.streamlit/config.toml`. Les médias de la page Guide (vidéo, captures)
  se déposent dans `web/assets/`.

## Tests et qualité

```bash
python -m pytest --cov=budget        # 187 tests, couverture 100 %
python -m pytest web                 # 15 tests de l'interface web (simulateur Streamlit)
python -m ruff check src tests       # style et complexité (maximum 8 par fonction)
```

Une intégration continue (`.github/workflows/tests.yml`) lance les tests du projet et ruff à chaque push.

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
web/
├── app.py           point d'entrée Streamlit et navigation
├── vues/            une page par module (tableau de bord, transactions, plafonds, ...)
├── composants.py    panneaux, donuts, barres et tableaux (HTML et SVG)
├── etat.py          une Application par visiteur
└── style.py         thème rose et mauve
```

La CLI et l'interface web appellent `Application`, qui orchestre le métier et ne connaît que
l'abstraction `Depot`. Diagramme de classes : [docs/diagrammes/diagramme_classes.png](docs/diagrammes/diagramme_classes.png).

## Choix techniques essentiels

- **Montants en `Decimal`** : aucune erreur d'arrondi sur les centimes.
- **Objets toujours valides** : `Transaction` et `Budget` valident leurs données à la construction.
- **Une responsabilité par classe** : calcul, mise en forme, stockage et dialogue sont séparés.
- **Héritage limité à deux hiérarchies** (`PolitiqueAlerte`, `Depot`), le reste est de la composition.
- **Une logique, deux interfaces** : la CLI et le web ne contiennent aucune règle métier.
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

Jinene Hamrouni et Myriam Aoun. La répartition des tâches est détaillée dans
[docs/conception.md](docs/conception.md#8-répartition-du-travail).
