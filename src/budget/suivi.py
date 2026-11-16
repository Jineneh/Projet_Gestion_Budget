"""SuiviBudget : comparaison des dépenses d'un mois aux plafonds."""
from collections.abc import Iterable
from decimal import Decimal

from budget.alertes import NiveauAlerte, PolitiqueAlerte, politiques_par_defaut
from budget.journal import Journal
from budget.modeles import Budget, TypeTransaction, somme_montants


class SuiviBudget:
    """Applique les politiques d'alerte aux dépenses de chaque catégorie budgétée.

    Le suivi UTILISE le journal sans le posséder (association), et DÉTIENT
    ses politiques d'alerte (composition).
    """

    def __init__(
        self,
        journal: Journal,
        budgets: Iterable[Budget] = (),
        politiques: Iterable[PolitiqueAlerte] | None = None,
    ) -> None:
        self._journal = journal
        self._budgets: dict[str, Budget] = {}
        self._politiques = list(politiques) if politiques is not None else politiques_par_defaut()
        for budget in budgets:
            self.definir_budget(budget)

    def definir_budget(self, budget: Budget) -> None:
        """Un seul plafond par catégorie : un nouveau budget remplace l'ancien."""
        self._budgets[budget.categorie] = budget

    @property
    def budgets(self) -> tuple[Budget, ...]:
        return tuple(self._budgets.values())

    def depenses_categorie(self, mois: str, categorie: str) -> Decimal:
        depenses = self._journal.filtrer(
            mois=mois, categorie=categorie, type_transaction=TypeTransaction.DEPENSE
        )
        return somme_montants(depenses)

    def niveau(self, mois: str, categorie: str) -> NiveauAlerte:
        """Niveau d'alerte d'une catégorie budgétée pour le mois donné."""
        budget = self._budgets[categorie]
        depenses = self.depenses_categorie(mois, categorie)
        if depenses == 0:
            return NiveauAlerte.AUCUNE_DEPENSE
        pourcentage = budget.pourcentage_consomme(depenses)
        for politique in self._politiques:
            niveau = politique.evaluer(pourcentage)
            if niveau is not None:
                return niveau
        return NiveauAlerte.OK

    def alertes(self, mois: str) -> dict[str, NiveauAlerte]:
        """Niveau d'alerte de chaque catégorie qui a un plafond."""
        return {categorie: self.niveau(mois, categorie) for categorie in self._budgets}
