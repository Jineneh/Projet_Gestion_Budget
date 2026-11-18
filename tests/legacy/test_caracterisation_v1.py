"""Tests de caractérisation de la V1 legacy.

Ils figent le comportement ACTUEL de la V1, avant tout refactoring.
La version propre (src/budget/) devra produire les mêmes résultats.
"""
from pathlib import Path

import pytest
from legacy.gestionnaire_budget import GestionnaireBudget

DOSSIER_DATA = Path(__file__).resolve().parents[2] / "data"
MOIS = "2026-10"


@pytest.fixture
def gestionnaire():
    return GestionnaireBudget()


@pytest.fixture
def gestionnaire_exemple():
    gestionnaire = GestionnaireBudget()
    gestionnaire.importer_csv(DOSSIER_DATA / "exemple_transactions.csv")
    return gestionnaire


# ---------- Validation ----------

@pytest.mark.parametrize("montant", [0, -10, "abc"])
def test_depense_refusee_si_montant_invalide(gestionnaire, montant):
    with pytest.raises(ValueError):
        gestionnaire.ajouter_depense(montant, "2026-10-01", "Alimentation")


def test_revenu_refuse_si_categorie_vide(gestionnaire):
    with pytest.raises(ValueError):
        gestionnaire.ajouter_revenu(100, "2026-10-01", "   ")


def test_depense_refusee_si_date_impossible(gestionnaire):
    with pytest.raises(ValueError):
        gestionnaire.ajouter_depense(10, "2026-13-05", "Loisirs")


def test_plafond_refuse_si_negatif(gestionnaire):
    with pytest.raises(ValueError):
        gestionnaire.definir_plafond("Loisirs", -100)


# ---------- Calculs sur les données d'exemple ----------

def test_solde_du_mois_exemple(gestionnaire_exemple):
    assert gestionnaire_exemple.solde(MOIS) == pytest.approx(1120.01)


def test_total_alimentation_du_mois_exemple(gestionnaire_exemple):
    total = gestionnaire_exemple.total_depenses_categorie("Alimentation", MOIS)
    assert total == pytest.approx(315.60)


def test_solde_d_un_mois_vide(gestionnaire_exemple):
    assert gestionnaire_exemple.solde("2026-11") == 0


# ---------- Alertes : valeurs limites 79 / 80 / 100 / 101 % ----------

@pytest.mark.parametrize(
    ("depense", "niveau_attendu"),
    [(79, "OK"), (80, "ATTENTION"), (100, "ATTENTION"), (101, "DEPASSEMENT")],
)
def test_niveau_alerte_aux_valeurs_limites(gestionnaire, depense, niveau_attendu):
    gestionnaire.definir_plafond("Loisirs", 100)
    gestionnaire.ajouter_depense(depense, "2026-10-10", "Loisirs")
    assert gestionnaire.calculer_alertes(MOIS)["Loisirs"] == niveau_attendu


def test_aucune_depense_sous_plafond(gestionnaire):
    gestionnaire.definir_plafond("Loisirs", 100)
    assert gestionnaire.calculer_alertes(MOIS)["Loisirs"] == "AUCUNE_DEPENSE"


def test_les_revenus_ne_declenchent_pas_d_alerte(gestionnaire):
    gestionnaire.definir_plafond("Freelance", 100)
    gestionnaire.ajouter_revenu(500, "2026-10-10", "Freelance")
    assert gestionnaire.calculer_alertes(MOIS)["Freelance"] == "AUCUNE_DEPENSE"


# ---------- Fichiers ----------

def test_import_csv_rejette_les_lignes_invalides(gestionnaire):
    erreurs = gestionnaire.importer_csv(DOSSIER_DATA / "exemple_transactions_invalides.csv")
    assert len(gestionnaire.transactions) == 2
    assert len(erreurs) == 5


def test_sauvegarde_puis_chargement_identiques(gestionnaire_exemple, tmp_path):
    gestionnaire_exemple.definir_plafond("Loisirs", 100)
    fichier = tmp_path / "budget.json"
    gestionnaire_exemple.sauvegarder(fichier)

    recharge = GestionnaireBudget()
    recharge.charger(fichier)

    assert recharge.transactions == gestionnaire_exemple.transactions
    assert recharge.plafonds == gestionnaire_exemple.plafonds


def test_rapport_affiche_solde_et_alertes(gestionnaire_exemple, capsys):
    gestionnaire_exemple.definir_plafond("Loisirs", 100)
    gestionnaire_exemple.afficher_rapport(MOIS)
    sortie = capsys.readouterr().out
    assert "Solde    : 1120.01 EUR" in sortie
    assert "Loisirs : plafond dépassé" in sortie
