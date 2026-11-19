"""Interface en ligne de commande.

La CLI ne fait que dialoguer : elle lit des saisies, appelle l'Application et affiche
le résultat. Aucune règle métier ici. Les fonctions de lecture et d'écriture sont
injectées, ce qui permet de tester toute l'interface sans clavier ni écran.
"""
import argparse
import sys
from collections.abc import Callable
from datetime import date
from pathlib import Path

from budget.application import Application
from budget.constantes import DEVISE, FICHIER_DONNEES_PAR_DEFAUT, FORMAT_DATE, FORMAT_MOIS
from budget.depots import DepotCsv, DepotJson
from budget.erreurs import BudgetError
from budget.modeles import Transaction
from budget.rapport import FormateurRapportTexte

TITRE = "===== Gestion de budget personnel ====="
CHOIX_QUITTER = "0"
INVITE_CHOIX = "Votre choix"


class CLI:
    """Menu interactif au-dessus d'une Application."""

    def __init__(
        self,
        application: Application,
        entree: Callable[[str], str] | None = None,
        sortie: Callable[[str], None] | None = None,
        aujourdhui: Callable[[], date] = date.today,
        formateur: FormateurRapportTexte | None = None,
    ) -> None:
        self._application = application
        self._entree = entree if entree is not None else input
        self._sortie = sortie if sortie is not None else print
        self._aujourdhui = aujourdhui
        self._formateur = formateur or FormateurRapportTexte()
        self._modifications_non_sauvegardees = False
        # Table de dispatch : ajouter une fonctionnalité = ajouter une ligne (Open/Closed)
        self._actions = {
            "1": ("Ajouter une transaction", self._ajouter_transaction),
            "2": ("Lister les transactions", self._lister_transactions),
            "3": ("Définir un plafond mensuel", self._definir_plafond),
            "4": ("Rapport mensuel et alertes", self._afficher_rapport),
            "5": ("Importer un fichier CSV", self._importer_csv),
            "6": ("Sauvegarder", self._sauvegarder),
            "7": ("Charger", self._charger),
            CHOIX_QUITTER: ("Quitter", None),
        }

    # ---------- Boucle principale ----------

    def executer(self) -> None:
        self._sortie(TITRE)
        try:
            self._boucle()
        except (EOFError, KeyboardInterrupt):
            self._sortie("")
        self._sortie("Au revoir.")

    def charger_au_demarrage(self) -> bool:
        """Charge le fichier de données existant. Faux si le chargement échoue."""
        return self._executer_action(self._charger)

    def _boucle(self) -> None:
        while True:
            self._afficher_menu()
            choix = self._demander(INVITE_CHOIX).strip()
            if choix == CHOIX_QUITTER:
                if self._peut_quitter():
                    return
            else:
                self._lancer(choix)

    def _afficher_menu(self) -> None:
        self._sortie("")
        for numero, (libelle, _) in self._actions.items():
            self._sortie(f"  {numero}. {libelle}")

    def _lancer(self, choix: str) -> None:
        if choix not in self._actions:
            self._sortie(f"Choix inconnu : {choix!r}")
            return
        self._executer_action(self._actions[choix][1])

    def _executer_action(self, action: Callable[[], None]) -> bool:
        """Lance une action ; une erreur métier est affichée, jamais propagée."""
        try:
            action()
        except BudgetError as erreur:
            self._sortie(f"Erreur : {erreur}")
            return False
        return True

    def _peut_quitter(self) -> bool:
        if not self._modifications_non_sauvegardees:
            return True
        reponse = self._demander("Sauvegarder avant de quitter ? (o/n)", defaut="o")
        if reponse.lower().startswith("o"):
            return self._executer_action(self._sauvegarder)
        return True

    # ---------- Actions du menu ----------

    def _ajouter_transaction(self) -> None:
        type_texte = self._demander("Type (revenu/depense)")
        montant = self._demander("Montant").replace(",", ".")  # « 12,50 » est accepté
        date_texte = self._demander("Date AAAA-MM-JJ", defaut=self._date_du_jour())
        categorie = self._demander("Catégorie")
        description = self._demander("Description (facultatif)", defaut="")
        transaction = self._application.ajouter_transaction(
            type_texte, montant, date_texte, categorie, description
        )
        self._modifications_non_sauvegardees = True
        self._sortie(f"Ajoutée : {self._formater_transaction(transaction)}")

    def _lister_transactions(self) -> None:
        mois = self._demander("Mois AAAA-MM (Entrée pour tout afficher)", defaut="")
        transactions = self._application.lister_transactions(mois=mois or None)
        if not transactions:
            self._sortie("Aucune transaction.")
        for transaction in transactions:
            self._sortie(self._formater_transaction(transaction))

    def _definir_plafond(self) -> None:
        categorie = self._demander("Catégorie")
        plafond = self._demander("Plafond mensuel").replace(",", ".")
        budget = self._application.definir_plafond(categorie, plafond)
        self._modifications_non_sauvegardees = True
        self._sortie(f"Plafond de {budget.plafond:.2f} {DEVISE} défini pour {budget.categorie}.")

    def _afficher_rapport(self) -> None:
        mois = self._demander("Mois AAAA-MM", defaut=self._aujourdhui().strftime(FORMAT_MOIS))
        rapport = self._application.generer_rapport(mois)
        self._sortie(self._formateur.formater(rapport))

    def _importer_csv(self) -> None:
        chemin = self._demander("Fichier CSV de transactions")
        chemin_plafonds = self._demander("Fichier CSV de plafonds (Entrée pour aucun)", defaut="")
        source = DepotCsv(chemin, chemin_plafonds or None)
        resultat = self._application.importer(source)
        self._modifications_non_sauvegardees = True
        self._sortie(
            f"{len(resultat.transactions)} transaction(s) et {len(resultat.budgets)} plafond(s) "
            f"importés, {len(resultat.erreurs)} ligne(s) rejetée(s)."
        )
        self._afficher_rejets(resultat.erreurs)

    def _sauvegarder(self) -> None:
        self._application.sauvegarder()
        self._modifications_non_sauvegardees = False
        self._sortie("Données sauvegardées.")

    def _charger(self) -> None:
        resultat = self._application.charger()
        self._modifications_non_sauvegardees = False
        self._sortie(
            f"Données chargées : {len(resultat.transactions)} transaction(s), "
            f"{len(resultat.budgets)} plafond(s), {len(resultat.erreurs)} rejet(s)."
        )
        self._afficher_rejets(resultat.erreurs)

    # ---------- Entrées et affichage ----------

    def _demander(self, question: str, defaut: str | None = None) -> str:
        indication = f" [{defaut}]" if defaut else ""
        reponse = self._entree(f"{question}{indication} : ").strip()
        return reponse if reponse or defaut is None else defaut

    def _date_du_jour(self) -> str:
        return self._aujourdhui().strftime(FORMAT_DATE)

    def _afficher_rejets(self, erreurs: tuple[str, ...]) -> None:
        for erreur in erreurs:
            self._sortie(f"  - {erreur}")

    @staticmethod
    def _formater_transaction(transaction: Transaction) -> str:
        jour = transaction.jour.strftime(FORMAT_DATE)
        montant = f"{transaction.montant_signe:+.2f} {DEVISE}"
        description = f" ({transaction.description})" if transaction.description else ""
        return f"{jour}  {montant:>14}  {transaction.categorie}{description}"


def main(arguments: list[str] | None = None) -> int:
    """Assemble l'application (racine de composition) et lance la CLI. Renvoie le code de sortie."""
    analyseur = argparse.ArgumentParser(prog="budget", description="Gestion de budget personnel")
    analyseur.add_argument(
        "--fichier", default=FICHIER_DONNEES_PAR_DEFAUT,
        help=f"fichier JSON des données (défaut : {FICHIER_DONNEES_PAR_DEFAUT})",
    )
    options = analyseur.parse_args(arguments)

    cli = CLI(Application(DepotJson(options.fichier)))
    # Un fichier existant mais illisible n'est jamais écrasé : on s'arrête plutôt que de le perdre.
    if Path(options.fichier).exists() and not cli.charger_au_demarrage():
        print(f"Corrigez ou déplacez le fichier {options.fichier} puis relancez.", file=sys.stderr)
        return 1
    cli.executer()
    return 0
