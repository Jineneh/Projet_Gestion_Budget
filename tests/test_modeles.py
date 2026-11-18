"""Tests des modèles : validation à la construction, immuabilité, plafonds."""
from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal

import pytest

from budget.erreurs import (
    BudgetError,
    CategorieInvalideError,
    DateInvalideError,
    MontantInvalideError,
    PlafondInvalideError,
    TypeTransactionInvalideError,
)
from budget.modeles import (
    Budget,
    Transaction,
    TypeTransaction,
    lire_date,
    somme_montants,
    valider_montant,
)

JOUR = date(2026, 10, 10)


def depense(montant="10", categorie="Loisirs"):
    return Transaction(montant, JOUR, categorie, TypeTransaction.DEPENSE)


# ---------- valider_montant ----------

@pytest.mark.parametrize(
    ("brut", "attendu"),
    [(10, Decimal("10.00")), (12.5, Decimal("12.50")), ("48.30", Decimal("48.30"))],
)
def test_valider_montant_arrondit_au_centime(brut, attendu):
    assert valider_montant(brut) == attendu


@pytest.mark.parametrize("brut", [0, -10, "-50.00", "0.004", "abc", "", None, True, "nan", "inf"])
def test_valider_montant_refuse_les_valeurs_invalides(brut):
    with pytest.raises(MontantInvalideError):
        valider_montant(brut)


# ---------- Transaction ----------

def test_transaction_valide_est_normalisee():
    transaction = Transaction("48.3", JOUR, "  Alimentation ", TypeTransaction.DEPENSE, " Courses ")
    assert transaction.montant == Decimal("48.30")
    assert transaction.categorie == "Alimentation"
    assert transaction.description == "Courses"
    assert transaction.mois == "2026-10"


def test_transaction_refuse_un_montant_negatif():
    with pytest.raises(MontantInvalideError):
        depense("-5")


def test_transaction_refuse_une_categorie_vide():
    with pytest.raises(CategorieInvalideError):
        depense(categorie="   ")


def test_transaction_refuse_une_date_qui_n_est_pas_une_date():
    with pytest.raises(DateInvalideError):
        Transaction("10", "2026-10-10", "Loisirs", TypeTransaction.DEPENSE)


def test_transaction_refuse_un_type_texte():
    with pytest.raises(TypeTransactionInvalideError):
        Transaction("10", JOUR, "Loisirs", "depense")


def test_transaction_est_immuable():
    transaction = depense()
    with pytest.raises(FrozenInstanceError):
        transaction.montant = Decimal("999")


def test_montant_signe_selon_le_type():
    revenu = Transaction("100", JOUR, "Salaire", TypeTransaction.REVENU)
    assert revenu.montant_signe == Decimal("100.00")
    assert depense("30").montant_signe == Decimal("-30.00")


def test_toutes_les_erreurs_derivent_de_budget_error():
    with pytest.raises(BudgetError):
        depense("abc")


# ---------- TypeTransaction et dates ----------

@pytest.mark.parametrize(
    ("texte", "attendu"),
    [("revenu", TypeTransaction.REVENU), (" DEPENSE ", TypeTransaction.DEPENSE)],
)
def test_type_depuis_texte(texte, attendu):
    assert TypeTransaction.depuis_texte(texte) is attendu


def test_type_inconnu_refuse():
    with pytest.raises(TypeTransactionInvalideError):
        TypeTransaction.depuis_texte("virement")


def test_lire_date_valide():
    assert lire_date("2026-10-01") == date(2026, 10, 1)


@pytest.mark.parametrize("texte", ["2026-13-05", "01/10/2026", "", "abc"])
def test_lire_date_refuse_une_date_impossible(texte):
    with pytest.raises(DateInvalideError):
        lire_date(texte)


def test_somme_montants():
    assert somme_montants([depense("10.10"), depense("5.05")]) == Decimal("15.15")
    assert somme_montants([]) == Decimal("0")


# ---------- Budget ----------

def test_budget_valide():
    budget = Budget(" Loisirs ", 100)
    assert budget.categorie == "Loisirs"
    assert budget.plafond == Decimal("100.00")


@pytest.mark.parametrize("plafond", [0, -100, "abc"])
def test_budget_refuse_un_plafond_invalide(plafond):
    with pytest.raises(PlafondInvalideError):
        Budget("Loisirs", plafond)


def test_budget_refuse_une_categorie_vide():
    with pytest.raises(CategorieInvalideError):
        Budget("", 100)


def test_pourcentage_consomme():
    assert Budget("Loisirs", 100).pourcentage_consomme(Decimal("80")) == Decimal("80")


def test_representation_lisible_du_budget():
    assert repr(Budget("Loisirs", 100)) == "Budget('Loisirs', 100.00)"


def test_montant_trop_grand_pour_etre_arrondi_est_refuse():
    with pytest.raises(MontantInvalideError):
        valider_montant("1e30")
