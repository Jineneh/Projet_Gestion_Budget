"""Modèles du domaine : TypeTransaction, Transaction, Budget.

Chaque objet est valide dès sa construction : il est impossible de créer une
transaction avec un montant négatif ou une catégorie vide.
"""
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum

from budget.constantes import FORMAT_DATE, FORMAT_MOIS, PRECISION_MONTANT
from budget.erreurs import (
    CategorieInvalideError,
    DateInvalideError,
    MontantInvalideError,
    PlafondInvalideError,
    TypeTransactionInvalideError,
)

# ---------- Validation : écrite UNE seule fois (DRY) ----------


def valider_montant(montant: object) -> Decimal:
    """Convertit le montant en Decimal arrondi au centime, strictement positif."""
    if isinstance(montant, bool):
        raise MontantInvalideError(f"Montant invalide : {montant!r}")
    try:
        valeur = Decimal(str(montant).strip())
    except InvalidOperation as erreur:
        raise MontantInvalideError(f"Montant non numérique : {montant!r}") from erreur
    if not valeur.is_finite():
        raise MontantInvalideError(f"Montant non numérique : {montant!r}")
    try:
        arrondi = valeur.quantize(PRECISION_MONTANT)
    except InvalidOperation as erreur:  # nombre trop grand pour être arrondi au centime
        raise MontantInvalideError(f"Montant hors limites : {montant!r}") from erreur
    if arrondi <= 0:
        raise MontantInvalideError(f"Le montant doit être strictement positif : {montant!r}")
    return arrondi


def valider_categorie(categorie: object) -> str:
    """Renvoie la catégorie sans espaces superflus ; refuse une catégorie vide."""
    if not isinstance(categorie, str) or not categorie.strip():
        raise CategorieInvalideError("La catégorie ne peut pas être vide")
    return categorie.strip()


def lire_date(texte: str) -> date:
    """Convertit un texte AAAA-MM-JJ en date ; refuse une date impossible."""
    try:
        return datetime.strptime(texte.strip(), FORMAT_DATE).date()
    except (ValueError, AttributeError) as erreur:
        message = f"Date invalide : {texte!r} (format attendu AAAA-MM-JJ)"
        raise DateInvalideError(message) from erreur


def mois_de(jour: date) -> str:
    """Renvoie le mois d'une date au format AAAA-MM."""
    return jour.strftime(FORMAT_MOIS)


# ---------- Modèles ----------


class TypeTransaction(Enum):
    """Nature d'une transaction : remplace les chaînes magiques « revenu » / « depense »."""

    REVENU = "revenu"
    DEPENSE = "depense"

    @classmethod
    def depuis_texte(cls, texte: str) -> "TypeTransaction":
        try:
            return cls(texte.strip().lower())
        except (ValueError, AttributeError) as erreur:
            raise TypeTransactionInvalideError(f"Type inconnu : {texte!r}") from erreur


@dataclass(frozen=True)
class Transaction:
    """Opération immuable et toujours valide."""

    montant: Decimal
    jour: date
    categorie: str
    type: TypeTransaction
    description: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.jour, date):
            raise DateInvalideError(f"Date invalide : {self.jour!r}")
        if not isinstance(self.type, TypeTransaction):
            raise TypeTransactionInvalideError(f"Type inconnu : {self.type!r}")
        # dataclass gelée : on passe par object.__setattr__ pour normaliser les valeurs
        object.__setattr__(self, "montant", valider_montant(self.montant))
        object.__setattr__(self, "categorie", valider_categorie(self.categorie))
        object.__setattr__(self, "description", str(self.description).strip())

    @property
    def est_depense(self) -> bool:
        return self.type is TypeTransaction.DEPENSE

    @property
    def mois(self) -> str:
        return mois_de(self.jour)

    @property
    def montant_signe(self) -> Decimal:
        """Montant positif pour un revenu, négatif pour une dépense."""
        return -self.montant if self.est_depense else self.montant


def somme_montants(transactions: Iterable[Transaction]) -> Decimal:
    """Additionne les montants (non signés) des transactions données."""
    return sum((transaction.montant for transaction in transactions), Decimal("0"))


class Budget:
    """Plafond mensuel de dépenses d'une catégorie."""

    def __init__(self, categorie: str, plafond: object) -> None:
        self._categorie = valider_categorie(categorie)
        try:
            self._plafond = valider_montant(plafond)
        except MontantInvalideError as erreur:
            raise PlafondInvalideError(
                f"Le plafond de « {self._categorie} » doit être strictement positif"
            ) from erreur

    @property
    def categorie(self) -> str:
        return self._categorie

    @property
    def plafond(self) -> Decimal:
        return self._plafond

    def pourcentage_consomme(self, depenses: Decimal) -> Decimal:
        """Part du plafond déjà consommée, en pourcentage."""
        return depenses * 100 / self._plafond

    def __repr__(self) -> str:
        return f"Budget({self._categorie!r}, {self._plafond})"
