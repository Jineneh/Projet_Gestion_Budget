"""RapportMensuel (calcul) et FormateurRapportTexte (mise en forme).

Principe SRP : le calcul et l'affichage sont deux responsabilités différentes,
donc deux classes différentes. Changer la présentation ne touche pas aux calculs.
"""
from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal

from budget.alertes import NiveauAlerte
from budget.constantes import DEVISE
from budget.journal import Journal
from budget.modeles import somme_montants
from budget.suivi import SuiviBudget


@dataclass(frozen=True)
class RapportMensuel:
    """Statistiques calculées d'un mois (aucun affichage ici)."""

    mois: str
    total_revenus: Decimal
    total_depenses: Decimal
    depenses_par_categorie: dict[str, Decimal] = field(default_factory=dict)
    alertes: dict[str, NiveauAlerte] = field(default_factory=dict)

    @property
    def solde(self) -> Decimal:
        return self.total_revenus - self.total_depenses

    @classmethod
    def calculer(cls, journal: Journal, suivi: SuiviBudget, mois: str) -> "RapportMensuel":
        depenses = journal.depenses_du_mois(mois)
        par_categorie: dict[str, Decimal] = defaultdict(Decimal)
        for depense in depenses:
            par_categorie[depense.categorie] += depense.montant
        return cls(
            mois=mois,
            total_revenus=somme_montants(journal.revenus_du_mois(mois)),
            total_depenses=somme_montants(depenses),
            depenses_par_categorie=dict(par_categorie),
            alertes=suivi.alertes(mois),
        )


class FormateurRapportTexte:
    """Met un RapportMensuel en forme pour la console. Renvoie du texte, n'affiche rien."""

    MESSAGES_ALERTE = {
        NiveauAlerte.ATTENTION: "! {categorie} : plafond bientôt atteint",
        NiveauAlerte.DEPASSEMENT: "!!! {categorie} : plafond dépassé",
    }

    def formater(self, rapport: RapportMensuel) -> str:
        lignes = [
            f"===== Rapport {rapport.mois} =====",
            f"Revenus  : {self._montant(rapport.total_revenus)}",
            f"Dépenses : {self._montant(rapport.total_depenses)}",
            f"Solde    : {self._montant(rapport.solde)}",
        ]
        lignes += self._lignes_categories(rapport)
        lignes += self._lignes_alertes(rapport)
        return "\n".join(lignes)

    def _lignes_categories(self, rapport: RapportMensuel) -> list[str]:
        return [
            f"  - {categorie} : {self._montant(montant)}"
            for categorie, montant in rapport.depenses_par_categorie.items()
        ]

    def _lignes_alertes(self, rapport: RapportMensuel) -> list[str]:
        return [
            self.MESSAGES_ALERTE[niveau].format(categorie=categorie)
            for categorie, niveau in rapport.alertes.items()
            if niveau in self.MESSAGES_ALERTE
        ]

    @staticmethod
    def _montant(valeur: Decimal) -> str:
        return f"{valeur:.2f} {DEVISE}"
