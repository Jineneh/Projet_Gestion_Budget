"""Exceptions métier : BudgetError et ses dérivées.

La CLI intercepte uniquement BudgetError : une erreur imprévue n'est jamais masquée.
"""


class BudgetError(Exception):
    """Racine de toutes les erreurs métier de l'application."""


class MontantInvalideError(BudgetError):
    """Le montant n'est pas un nombre strictement positif."""


class CategorieInvalideError(BudgetError):
    """La catégorie est vide."""


class DateInvalideError(BudgetError):
    """La date n'existe pas ou n'est pas au format attendu."""


class TypeTransactionInvalideError(BudgetError):
    """Le type n'est ni « revenu » ni « depense »."""


class PlafondInvalideError(BudgetError):
    """Le plafond d'une catégorie n'est pas strictement positif."""


class FichierDonneesError(BudgetError):
    """Le fichier de données est absent, illisible ou corrompu."""
