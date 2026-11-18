"""Tests des dépôts : aller-retour, rejet des lignes invalides, erreurs de fichier."""
import json
from decimal import Decimal
from pathlib import Path

import pytest
from legacy.gestionnaire_budget import GestionnaireBudget

from budget.depots import Depot, DepotCsv, DepotJson
from budget.erreurs import FichierDonneesError
from budget.journal import Journal
from budget.modeles import Budget, Transaction, TypeTransaction, lire_date

DOSSIER_DATA = Path(__file__).resolve().parents[1] / "data"
TRANSACTIONS_EXEMPLE = DOSSIER_DATA / "exemple_transactions.csv"
TRANSACTIONS_INVALIDES = DOSSIER_DATA / "exemple_transactions_invalides.csv"
PLAFONDS_EXEMPLE = DOSSIER_DATA / "exemple_plafonds.csv"


def resume_budgets(budgets):
    return [(budget.categorie, budget.plafond) for budget in budgets]


def une_transaction(description="Courses"):
    return Transaction(
        montant="12.50", jour=lire_date("2026-10-05"), categorie="Alimentation",
        type=TypeTransaction.DEPENSE, description=description,
    )


@pytest.fixture(params=["json", "csv"])
def depot_vide(request, tmp_path):
    """Les deux dépôts doivent se comporter pareil : mêmes tests (substitution de Liskov)."""
    if request.param == "json":
        return DepotJson(tmp_path / "budget.json")
    return DepotCsv(tmp_path / "transactions.csv", tmp_path / "plafonds.csv")


# ---------- Contrat commun ----------

def test_depot_abstrait_non_instanciable():
    with pytest.raises(TypeError):
        Depot()


def test_aller_retour_identique(depot_vide):
    transactions = (une_transaction(), une_transaction("Marché, légumes « bio »"))
    budgets = (Budget("Alimentation", "350"), Budget("Loisirs", "100.50"))
    depot_vide.sauvegarder(transactions, budgets)

    resultat = depot_vide.charger()

    assert resultat.transactions == transactions
    assert resume_budgets(resultat.budgets) == resume_budgets(budgets)
    assert resultat.erreurs == ()


def test_sauvegarde_sans_donnees_puis_chargement(depot_vide):
    depot_vide.sauvegarder((), ())
    resultat = depot_vide.charger()
    assert (resultat.transactions, resultat.budgets, resultat.erreurs) == ((), (), ())


def test_sauvegarde_ne_laisse_aucun_fichier_temporaire(depot_vide, tmp_path):
    depot_vide.sauvegarder((une_transaction(),), ())
    assert list(tmp_path.glob("*.tmp")) == []


def test_fichier_absent_leve_une_erreur_claire(depot_vide):
    with pytest.raises(FichierDonneesError, match="introuvable"):
        depot_vide.charger()


# ---------- CSV : données d'exemple et rejet des lignes invalides ----------

def test_csv_exemple_donne_les_memes_resultats_que_la_v1():
    resultat = DepotCsv(TRANSACTIONS_EXEMPLE, PLAFONDS_EXEMPLE).charger()
    journal = Journal(resultat.transactions)
    solde = sum(t.montant_signe for t in journal.filtrer(mois="2026-10"))

    assert len(resultat.transactions) == 15
    assert solde == Decimal("1120.01")
    assert resultat.erreurs == ()
    assert resume_budgets(resultat.budgets) == [
        ("Alimentation", Decimal("350.00")), ("Loisirs", Decimal("100.00")),
        ("Transport", Decimal("150.00")),
    ]


def test_csv_invalide_garde_2_lignes_et_rejette_5_comme_la_v1():
    resultat = DepotCsv(TRANSACTIONS_INVALIDES).charger()
    assert len(resultat.transactions) == 2
    assert len(resultat.erreurs) == 5
    numeros_de_ligne = [erreur.split(" :")[0] for erreur in resultat.erreurs]
    assert numeros_de_ligne == [f"Ligne {numero}" for numero in range(3, 8)]


def test_csv_invalide_correspond_a_la_v1():
    legacy = GestionnaireBudget()
    erreurs_v1 = legacy.importer_csv(TRANSACTIONS_INVALIDES)
    resultat = DepotCsv(TRANSACTIONS_INVALIDES).charger()
    assert len(resultat.transactions) == len(legacy.transactions)
    assert len(resultat.erreurs) == len(erreurs_v1)


def test_csv_plafond_invalide_est_rejete_sans_arreter_le_chargement(tmp_path):
    plafonds = tmp_path / "plafonds.csv"
    plafonds.write_text("categorie,plafond\nLoisirs,100\nSport,-5\nVoyage,abc\n", encoding="utf-8")
    resultat = DepotCsv(TRANSACTIONS_EXEMPLE, plafonds).charger()
    assert resume_budgets(resultat.budgets) == [("Loisirs", Decimal("100.00"))]
    assert len(resultat.erreurs) == 2


def test_csv_colonne_manquante(tmp_path):
    fichier = tmp_path / "t.csv"
    fichier.write_text("date,type,montant\n2026-10-01,depense,10\n", encoding="utf-8")
    with pytest.raises(FichierDonneesError, match="categorie"):
        DepotCsv(fichier).charger()


def test_csv_vide(tmp_path):
    fichier = tmp_path / "t.csv"
    fichier.write_text("", encoding="utf-8")
    with pytest.raises(FichierDonneesError, match="Colonnes manquantes"):
        DepotCsv(fichier).charger()


def test_csv_ligne_incomplete_est_rejetee(tmp_path):
    fichier = tmp_path / "t.csv"
    fichier.write_text(
        "date,type,montant,categorie,description\n2026-10-01,depense\n", encoding="utf-8"
    )
    resultat = DepotCsv(fichier).charger()
    assert resultat.transactions == ()
    assert len(resultat.erreurs) == 1


def test_csv_montant_gigantesque_est_rejete_sans_planter(tmp_path):
    fichier = tmp_path / "t.csv"
    fichier.write_text(
        "date,type,montant,categorie,description\n2026-10-01,depense,1e30,Loisirs,\n",
        encoding="utf-8",
    )
    assert len(DepotCsv(fichier).charger().erreurs) == 1


def test_csv_corrompu_leve_une_erreur_claire(tmp_path):
    fichier = tmp_path / "t.csv"
    champ_demesure = "x" * 200_000  # dépasse la limite de taille de champ du module csv
    fichier.write_text(f"date,type,montant,categorie,description\n{champ_demesure},a,b,c,d\n",
                       encoding="utf-8")
    with pytest.raises(FichierDonneesError, match="corrompu"):
        DepotCsv(fichier).charger()


def test_fichier_non_utf8_leve_une_erreur_claire(tmp_path):
    fichier = tmp_path / "t.csv"
    fichier.write_bytes(b"date,type\n\xff\xfe\x00")
    with pytest.raises(FichierDonneesError, match="illisible"):
        DepotCsv(fichier).charger()


# ---------- JSON : fichiers corrompus et compatibilité V1 ----------

def test_json_corrompu(tmp_path):
    fichier = tmp_path / "budget.json"
    fichier.write_text("{ ceci n'est pas du json", encoding="utf-8")
    with pytest.raises(FichierDonneesError, match="corrompu"):
        DepotJson(fichier).charger()


CONTENUS_JSON_INATTENDUS = ["[]", '{"transactions": 5}', '{"transactions": [], "plafonds": []}']


@pytest.mark.parametrize("contenu", CONTENUS_JSON_INATTENDUS)
def test_json_de_structure_inattendue(tmp_path, contenu):
    fichier = tmp_path / "budget.json"
    fichier.write_text(contenu, encoding="utf-8")
    with pytest.raises(FichierDonneesError, match="Structure"):
        DepotJson(fichier).charger()


def test_json_enregistrement_invalide_est_rejete_sans_arreter_le_chargement(tmp_path):
    fichier = tmp_path / "budget.json"
    contenu = {
        "transactions": [
            {"date": "2026-10-01", "type": "depense", "montant": "10", "categorie": "Loisirs"},
            {"date": "2026-10-02", "type": "depense", "montant": "-3", "categorie": "Loisirs"},
            42,
        ],
        "plafonds": {"Loisirs": "0"},
    }
    fichier.write_text(json.dumps(contenu), encoding="utf-8")
    resultat = DepotJson(fichier).charger()
    assert len(resultat.transactions) == 1
    assert len(resultat.erreurs) == 3


def test_json_ecrit_par_la_v1_est_relu_par_la_version_propre(tmp_path):
    legacy = GestionnaireBudget()
    legacy.importer_csv(TRANSACTIONS_EXEMPLE)
    legacy.definir_plafond("Loisirs", 100)
    fichier = tmp_path / "v1.json"
    legacy.sauvegarder(fichier)

    resultat = DepotJson(fichier).charger()

    assert len(resultat.transactions) == 15
    assert resume_budgets(resultat.budgets) == [("Loisirs", Decimal("100.00"))]
    assert resultat.erreurs == ()


def test_json_cree_le_dossier_manquant(tmp_path):
    cible = tmp_path / "sous" / "dossier" / "budget.json"
    DepotJson(cible).sauvegarder((une_transaction(),), ())
    assert cible.exists()


def test_ecriture_impossible_leve_une_erreur_claire(tmp_path):
    bloqueur = tmp_path / "fichier_gene"
    bloqueur.write_text("je suis un fichier, pas un dossier", encoding="utf-8")
    with pytest.raises(FichierDonneesError, match="Écriture impossible"):
        DepotJson(bloqueur / "budget.json").sauvegarder((), ())
