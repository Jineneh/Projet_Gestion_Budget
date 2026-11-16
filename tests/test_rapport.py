"""Tests du rapport mensuel : calcul, mise en forme, et équivalence avec la V1."""
import csv
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from budget.alertes import NiveauAlerte
from budget.journal import Journal
from budget.modeles import Budget, Transaction, TypeTransaction, lire_date
from budget.rapport import FormateurRapportTexte, RapportMensuel
from budget.suivi import SuiviBudget

MOIS = "2026-10"
FICHIER_EXEMPLE = Path(__file__).resolve().parents[1] / "data" / "exemple_transactions.csv"


def transaction(montant, categorie, type_transaction=TypeTransaction.DEPENSE):
    return Transaction(montant, date(2026, 10, 10), categorie, type_transaction)


def rapport_de(*transactions, budgets=()):
    journal = Journal(transactions)
    return RapportMensuel.calculer(journal, SuiviBudget(journal, budgets), MOIS)


def journal_exemple():
    """Lit le CSV d'exemple (lecture simple : le vrai import CSV est dans depots.py)."""
    with open(FICHIER_EXEMPLE, encoding="utf-8") as fichier:
        return Journal(
            Transaction(
                ligne["montant"],
                lire_date(ligne["date"]),
                ligne["categorie"],
                TypeTransaction.depuis_texte(ligne["type"]),
                ligne["description"],
            )
            for ligne in csv.DictReader(fichier)
        )


# ---------- Calcul ----------

def test_mois_vide():
    rapport = rapport_de()
    assert rapport.total_revenus == rapport.total_depenses == rapport.solde == 0
    assert rapport.depenses_par_categorie == {}


def test_solde_negatif():
    rapport = rapport_de(transaction("100", "Salaire", TypeTransaction.REVENU),
                         transaction("150", "Logement"))
    assert rapport.solde == Decimal("-50.00")


def test_regroupement_par_categorie():
    rapport = rapport_de(transaction("10", "Alimentation"), transaction("5.50", "Alimentation"),
                         transaction("20", "Transport"))
    assert rapport.depenses_par_categorie == {
        "Alimentation": Decimal("15.50"),
        "Transport": Decimal("20.00"),
    }


def test_le_rapport_est_immuable():
    with pytest.raises(AttributeError):
        rapport_de().mois = "2027-01"


# ---------- Mise en forme ----------

def test_formateur_renvoie_du_texte_sans_rien_afficher(capsys):
    rapport = rapport_de(transaction("120", "Loisirs"), budgets=[Budget("Loisirs", 100)])
    texte = FormateurRapportTexte().formater(rapport)
    assert capsys.readouterr().out == ""
    assert "Solde    : -120.00 EUR" in texte
    assert "  - Loisirs : 120.00 EUR" in texte
    assert "!!! Loisirs : plafond dépassé" in texte


def test_formateur_n_affiche_pas_les_categories_sans_alerte():
    rapport = rapport_de(transaction("10", "Loisirs"), budgets=[Budget("Loisirs", 100)])
    assert "!" not in FormateurRapportTexte().formater(rapport)


# ---------- Équivalence avec la V1 legacy ----------

def test_memes_resultats_que_la_v1_sur_les_donnees_d_exemple():
    """Mêmes données, mêmes plafonds que legacy/ : le refactoring n'a rien cassé."""
    journal = journal_exemple()
    budgets = [Budget("Alimentation", 350), Budget("Loisirs", 100), Budget("Transport", 150)]
    rapport = RapportMensuel.calculer(journal, SuiviBudget(journal, budgets), MOIS)

    assert rapport.total_revenus == Decimal("2320.00")
    assert rapport.total_depenses == Decimal("1199.99")
    assert rapport.solde == Decimal("1120.01")
    assert rapport.depenses_par_categorie["Alimentation"] == Decimal("315.60")
    assert rapport.alertes == {
        "Alimentation": NiveauAlerte.ATTENTION,
        "Loisirs": NiveauAlerte.DEPASSEMENT,
        "Transport": NiveauAlerte.OK,
    }
