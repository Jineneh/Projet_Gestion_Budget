# Gestion de budget personnel

Application en ligne de commande (Python 3.11+) pour suivre revenus et dépenses, fixer des
plafonds mensuels par catégorie, être alerté avant dépassement et produire un rapport mensuel.
Projet du cours *Programmation épurée* (Master 2) : POO et Clean Code.

> > **Statut** : version propre en cours. Modèles, journal, alertes, suivi et rapports sont faits et testés ; persistance, CLI et application restent à faire.

## Documentation

- [Cadrage et conception](docs/Cadrage_et_conception.pdf) : besoin, classes, UML
- [Organisation Git](docs/workflow_git.md)

## Prérequis et installation

```bash
git clone https://github.com/Jineneh/Projet_Gestion_Budget.git
cd Projet_Gestion_Budget
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

## Tests

```bash
pytest --cov=budget
ruff check src tests
```

## Exécution (disponible à l'étape CLI)

```bash
python -m budget
```

Données de démonstration : `data/exemple_transactions.csv` (valide) et
`data/exemple_transactions_invalides.csv` (pour montrer le rejet des lignes erronées).

## Structure

```
├── src/budget/      code de l'application (un module = une responsabilité)
├── tests/           tests automatisés (pytest)
├── legacy/          version 1 volontairement perfectible, point de départ des refactorings
├── data/            données d'exemple
├── docs/            conception, UML, workflow Git
└── scala_extension/ extension facultative
```

## Feuille de route

- [x] 1. Cadrage et conception
- [x] 2. Structure du dépôt
- [x] 3. Version 1 legacy et tests de caractérisation
- [x] 4. Refactoring SRP, puis Open/Closed, puis DRY et constantes
- [ ] 5. Persistance, CLI, tests complets
- [ ] 6. Support de présentation, démo, extension Scala

## Équipe

Jinene et Myriam. Répartition détaillée dans le support de présentation.
