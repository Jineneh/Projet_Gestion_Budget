# Trois exemples « avant / après »

Chaque exemple compare la version 1 (`legacy/gestionnaire_budget.py`, tag Git `avant-refactoring`)
à la version propre (`src/budget/`). La version 1 fonctionne : le comportement est figé par
19 tests de caractérisation (`tests/legacy/`), et des tests de parité vérifient que la version
propre donne les mêmes résultats (`test_rapport.py`, `test_application.py`, `test_depots.py`).

| Mesure | Version 1 | Version propre |
|---|---|---|
| Organisation | 1 fichier, 1 classe, 12 méthodes | 10 modules métier, une responsabilité chacun |
| Complexité cyclomatique moyenne (radon) | 4,0 | 2,0 |
| Fonction la plus complexe | `afficher_rapport` : 9 | `Journal.filtrer` : 8 (plafond imposé par ruff) |
| Tests automatisés | 19 | 187 |
| Couverture du code | non mesurée | 100 % |

## 1. SRP : une classe qui fait trop de choses

**Problème.** `GestionnaireBudget` calcule, affiche avec `print()` et lit/écrit les fichiers :
trois raisons de changer pour une seule classe. On ne peut pas tester le calcul du rapport sans
capturer l'affichage, ni changer le format de fichier sans toucher au métier.

**Avant** (`legacy/gestionnaire_budget.py`)

```python
def afficher_rapport(self, mois):
    revenus = 0
    depenses = 0
    par_categorie = {}
    for t in self.transactions:                      # calcul...
        if t["date"][:7] == mois:
            ...
    print("===== Rapport " + mois + " =====")       # ...mélangé à l'affichage
    print("Revenus  : " + str(round(revenus, 2)) + " EUR")
    ...

def sauvegarder(self, chemin):                       # ...et aux fichiers
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump({"transactions": self.transactions, "plafonds": self.plafonds}, f)
```

**Après** (`rapport.py`, `depots.py`) : trois classes, trois responsabilités.

```python
class RapportMensuel:                                # calcule, n'affiche rien
    @classmethod
    def calculer(cls, journal, suivi, mois) -> "RapportMensuel": ...

class FormateurRapportTexte:                         # met en forme, renvoie du texte
    def formater(self, rapport: RapportMensuel) -> str: ...

class DepotJson(Depot):                              # seul à connaître le disque
    def sauvegarder(self, transactions, budgets) -> None: ...
```

**Bénéfices.** Le calcul est une valeur testable sans affichage. Changer la présentation ne touche
que `FormateurRapportTexte`. `Application` ne connaît que l'abstraction `Depot` : on peut tester
toute la logique avec un faux dépôt en mémoire (`tests/test_application.py`).

## 2. Open/Closed : un `if/elif` géant à modifier à chaque nouveau cas

**Problème.** Pour ajouter un niveau d'alerte, il faut rouvrir `calculer_alertes()` et la modifier :
le risque de régression touche tout le calcul.

**Avant**

```python
ratio = depense / plafond
if ratio > 1.0:
    alertes[categorie] = "DEPASSEMENT"
elif ratio >= 0.8:
    alertes[categorie] = "ATTENTION"
elif ratio > 0:
    alertes[categorie] = "OK"
else:
    alertes[categorie] = "AUCUNE_DEPENSE"
```

**Après** (`alertes.py`, `suivi.py`) : chaque règle est une classe, `SuiviBudget` les parcourt.

```python
class PolitiqueAlerte(ABC):
    @abstractmethod
    def evaluer(self, pourcentage: Decimal) -> NiveauAlerte | None: ...

class PolitiqueSeuil(PolitiqueAlerte):
    def evaluer(self, pourcentage):
        return NiveauAlerte.ATTENTION if pourcentage >= SEUIL_ALERTE_POURCENT else None

# SuiviBudget.niveau : aucune règle écrite en dur, il applique la première qui répond
for politique in self._politiques:
    niveau = politique.evaluer(pourcentage)
    if niveau is not None:
        return niveau
```

**Bénéfices.** Ajouter une règle = ajouter une classe et l'enregistrer dans la liste ; `SuiviBudget`
n'est pas modifié. `tests/test_application.py::test_la_politique_injectee_est_conservee_apres_charger`
le démontre avec une politique définie uniquement dans le test. Chaque règle se teste isolément
(`tests/test_alertes.py`, valeurs limites 79 / 80 / 100 / 101 %).

## 3. DRY et nombres magiques : même code copié, valeurs sans nom

**Problème.** La validation du montant et de la catégorie est copiée dans `ajouter_revenu`,
`ajouter_depense` et `definir_plafond` : corriger une règle oblige à penser aux trois endroits.
`0.8` et `1.0` sont écrits en dur, sans dire ce qu'ils représentent.

**Avant**

```python
def ajouter_revenu(self, montant, date, categorie, description=""):
    if not isinstance(montant, (int, float)) or montant <= 0:
        raise ValueError("Le montant doit être un nombre strictement positif")
    if not categorie or not categorie.strip():
        raise ValueError("La catégorie ne peut pas être vide")
    ...
# ajouter_depense() et definir_plafond() répètent ces mêmes lignes
```

**Après** (`modeles.py`, `constantes.py`) : une définition par règle, des constantes nommées.

```python
def valider_montant(montant: object) -> Decimal: ...     # utilisée par Transaction et Budget
def valider_categorie(categorie: object) -> str: ...

SEUIL_ALERTE_POURCENT = Decimal("80")
SEUIL_DEPASSEMENT_POURCENT = Decimal("100")
BASE_POURCENTAGE = 100
```

**Bénéfices.** Un objet `Transaction` ou `Budget` invalide ne peut pas être créé : la validation vit
dans le constructeur, donc aucune entrée (CLI, CSV, JSON) ne la contourne. Les seuils se changent en
un seul endroit. Les montants passent en `Decimal`, ce qui supprime les erreurs d'arrondi des
`float` sur les centimes. Une seule méthode `Application.ajouter_transaction` remplace
`ajouter_revenu` et `ajouter_depense`.
