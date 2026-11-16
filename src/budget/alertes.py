"""Niveaux d'alerte et politiques d'alerte interchangeables.

Principe Open/Closed : pour ajouter une nouvelle règle d'alerte, on AJOUTE une
classe qui hérite de PolitiqueAlerte, sans MODIFIER le code existant.
"""
from abc import ABC, abstractmethod
from decimal import Decimal
from enum import Enum

from budget.constantes import SEUIL_ALERTE_POURCENT, SEUIL_DEPASSEMENT_POURCENT


class NiveauAlerte(Enum):
    """Niveaux d'alerte budgétaire, du moins grave au plus grave."""

    AUCUNE_DEPENSE = "aucune dépense"
    OK = "ok"
    ATTENTION = "attention"
    DEPASSEMENT = "dépassement"


class PolitiqueAlerte(ABC):
    """Contrat commun à toutes les règles d'alerte."""

    @abstractmethod
    def evaluer(self, pourcentage: Decimal) -> NiveauAlerte | None:
        """Renvoie le niveau d'alerte si la règle s'applique, sinon None."""


class PolitiqueDepassement(PolitiqueAlerte):
    """Le plafond est dépassé (strictement plus de 100 %)."""

    def evaluer(self, pourcentage: Decimal) -> NiveauAlerte | None:
        if pourcentage > SEUIL_DEPASSEMENT_POURCENT:
            return NiveauAlerte.DEPASSEMENT
        return None


class PolitiqueSeuil(PolitiqueAlerte):
    """Le plafond est presque atteint (80 % ou plus)."""

    def evaluer(self, pourcentage: Decimal) -> NiveauAlerte | None:
        if pourcentage >= SEUIL_ALERTE_POURCENT:
            return NiveauAlerte.ATTENTION
        return None


def politiques_par_defaut() -> list[PolitiqueAlerte]:
    """Politiques standard, de la plus grave à la moins grave (l'ordre compte)."""
    return [PolitiqueDepassement(), PolitiqueSeuil()]
