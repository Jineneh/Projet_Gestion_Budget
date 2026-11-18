"""Application : orchestration des cas d'usage.

Cette classe relie le journal, le suivi des budgets et le dépôt. Elle ne contient
ni affichage (print) ni saisie (input) : c'est le travail de la CLI. Elle ne connaît
que l'abstraction Depot, jamais un format de fichier (inversion de dépendance).
"""
from collections.abc import Iterable

from budget.alertes import NiveauAlerte, PolitiqueAlerte
from budget.depots import Depot, ResultatChargement
from budget.journal import Journal
from budget.modeles import Budget, Transaction, TypeTransaction, lire_date, lire_mois
from budget.rapport import RapportMensuel
from budget.suivi import SuiviBudget


class Application:
    """Point d'entrée unique de la logique métier, utilisé par la CLI."""

    def __init__(
        self, depot: Depot, politiques: Iterable[PolitiqueAlerte] | None = None
    ) -> None:
        self._depot = depot
        self._politiques = list(politiques) if politiques is not None else None
        self._journal = Journal()
        self._suivi = SuiviBudget(self._journal, politiques=self._politiques)

    # ---------- Saisie ----------

    def ajouter_transaction(
        self, type_texte: str, montant: object, date_texte: str, categorie: str,
        description: str = "",
    ) -> Transaction:
        """Ajoute un revenu ou une dépense à partir de données brutes (une seule méthode,
        pas une par type : pas de duplication)."""
        transaction = Transaction(
            montant=montant,
            jour=lire_date(date_texte),
            categorie=categorie,
            type=TypeTransaction.depuis_texte(type_texte),
            description=description,
        )
        self._journal.ajouter(transaction)
        return transaction

    def definir_plafond(self, categorie: str, plafond: object) -> Budget:
        """Fixe le plafond mensuel d'une catégorie (un nouveau plafond remplace l'ancien)."""
        budget = Budget(categorie, plafond)
        self._suivi.definir_budget(budget)
        return budget

    # ---------- Consultation ----------

    def lister_transactions(
        self, mois: str | None = None, categorie: str | None = None
    ) -> tuple[Transaction, ...]:
        mois_valide = lire_mois(mois) if mois is not None else None
        return self._journal.filtrer(mois=mois_valide, categorie=categorie)

    @property
    def plafonds(self) -> tuple[Budget, ...]:
        return self._suivi.budgets

    def generer_rapport(self, mois: str) -> RapportMensuel:
        return RapportMensuel.calculer(self._journal, self._suivi, lire_mois(mois))

    def alertes(self, mois: str) -> dict[str, NiveauAlerte]:
        return self._suivi.alertes(lire_mois(mois))

    # ---------- Persistance ----------

    def sauvegarder(self) -> None:
        self._depot.sauvegarder(self._journal.transactions, self._suivi.budgets)

    def charger(self) -> ResultatChargement:
        """Remplace les données en mémoire par celles du dépôt.

        Si le dépôt échoue, l'exception est propagée et les données actuelles restent intactes.
        """
        resultat = self._depot.charger()
        self._journal = Journal(resultat.transactions)
        self._suivi = SuiviBudget(self._journal, resultat.budgets, self._politiques)
        return resultat

    def importer(self, source: Depot) -> ResultatChargement:
        """Ajoute aux données actuelles celles d'une autre source (ex. un CSV).

        Les lignes invalides sont rejetées et signalées dans le résultat. Importer deux fois
        la même source ajoute deux fois les transactions : deux achats identiques le même jour
        sont légitimes, on ne peut donc pas dédoublonner automatiquement.
        """
        resultat = source.charger()
        for transaction in resultat.transactions:
            self._journal.ajouter(transaction)
        for budget in resultat.budgets:
            self._suivi.definir_budget(budget)
        return resultat
