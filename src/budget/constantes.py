"""Constantes du projet : seuils d'alerte, formats de date, noms de fichiers.

Toute valeur « magique » du programme est définie ici, une seule fois.
"""
from decimal import Decimal

# Formats de date
FORMAT_DATE = "%Y-%m-%d"
FORMAT_MOIS = "%Y-%m"

# Montants
DEVISE = "EUR"
PRECISION_MONTANT = Decimal("0.01")

# Seuils d'alerte budgétaire, en pourcentage du plafond
SEUIL_ALERTE_POURCENT = Decimal("80")
SEUIL_DEPASSEMENT_POURCENT = Decimal("100")

# Fichiers de données
FICHIER_DONNEES_PAR_DEFAUT = "budget.json"
ENCODAGE_FICHIERS = "utf-8"
