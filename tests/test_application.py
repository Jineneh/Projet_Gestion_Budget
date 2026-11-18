"""Tests de l'Application : cas d'usage, persistance injectée, équivalence avec la V1."""
from decimal import Decimal
from pathlib import Path

import pytest
from legacy.gestionnaire_budget import GestionnaireBudget

from budget.alertes import NiveauAlerte, PolitiqueAlerte
from budget.application import Application
from budget.depots import Depot, DepotCsv, DepotJson, ResultatChargement
from budget.erreurs import (
    CategorieInvalideError,
    DateInvalideError,
    FichierDonneesError,
    MontantInvalideError,
    PlafondInvalideError,
    TypeTransactionInvalideError,
)

DOSSIER_DATA = Path(__file__).resolve().parents[1] / "data"
MOIS = "2026-10"


class DepotMemoire(Depot):
    """Faux dépôt : prouve que l'Application ne dépend d'aucun format de fichier."""

    def __init__(self, resultat=None):
        self.resultat = resultat or ResultatChargement()
        self.sauvegardes = []

    def charger(self):
        return self.resultat

    def sauvegarder(self, transactions, budgets):
        self.sauvegardes.append((tuple(transactions), tuple(budgets)))


@pytest.fixture
def application():
    return Application(DepotMemoire())


@pytest.fixture
def application_exemple():
    """Application chargée avec les données d'exemple et les plafonds de démonstration."""
    app = Application(DepotMemoire())
    app.importer(DepotCsv(DOSSIER_DATA / "exemple_transactions.csv",
                          DOSSIER_DATA / "exemple_plafonds.csv"))
    return app


# ---------- Saisie ----------

def test_ajouter_une_depense(application):
    transaction = application.ajouter_transaction("depense", "12.5", "2026-10-05", "Transport")
    assert transaction.montant == Decimal("12.50")
    assert application.lister_transactions() == (transaction,)


def test_ajouter_un_revenu(application):
    transaction = application.ajouter_transaction("revenu", 2200, "2026-10-01", "Salaire", "Paie")
    assert transaction.montant_signe == Decimal("2200.00")
    assert transaction.description == "Paie"


@pytest.mark.parametrize(
    ("arguments", "erreur"),
    [
        (("depense", "abc", "2026-10-05", "Transport"), MontantInvalideError),
        (("depense", "-5", "2026-10-05", "Transport"), MontantInvalideError),
        (("depense", "5", "2026-13-05", "Transport"), DateInvalideError),
        (("depense", "5", "2026-10-05", "  "), CategorieInvalideError),
        (("virement", "5", "2026-10-05", "Transport"), TypeTransactionInvalideError),
    ],
)
def test_saisie_invalide_refusee_sans_modifier_les_donnees(application, arguments, erreur):
    with pytest.raises(erreur):
        application.ajouter_transaction(*arguments)
    assert application.lister_transactions() == ()


def test_definir_un_plafond(application):
    budget = application.definir_plafond("Loisirs", "100")
    assert application.plafonds == (budget,)


def test_un_nouveau_plafond_remplace_l_ancien(application):
    application.definir_plafond("Loisirs", "100")
    application.definir_plafond("Loisirs", "250")
    assert [b.plafond for b in application.plafonds] == [Decimal("250.00")]


@pytest.mark.parametrize("plafond", [0, -10, "abc"])
def test_plafond_invalide_refuse(application, plafond):
    with pytest.raises(PlafondInvalideError):
        application.definir_plafond("Loisirs", plafond)
    assert application.plafonds == ()


# ---------- Consultation ----------

def test_lister_filtre_par_mois_et_categorie(application):
    application.ajouter_transaction("depense", "10", "2026-10-05", "Transport")
    application.ajouter_transaction("depense", "20", "2026-11-05", "Transport")
    application.ajouter_transaction("depense", "30", "2026-10-06", "Loisirs")
    assert len(application.lister_transactions()) == 3
    assert len(application.lister_transactions(mois="2026-10")) == 2
    assert len(application.lister_transactions(mois="2026-10", categorie="Loisirs")) == 1


@pytest.mark.parametrize("mois", ["2026-13", "octobre", ""])
def test_mois_invalide_refuse(application, mois):
    with pytest.raises(DateInvalideError):
        application.generer_rapport(mois)
    with pytest.raises(DateInvalideError):
        application.lister_transactions(mois=mois)
    with pytest.raises(DateInvalideError):
        application.alertes(mois)


def test_rapport_d_un_mois_vide(application):
    rapport = application.generer_rapport(MOIS)
    assert (rapport.total_revenus, rapport.total_depenses, rapport.solde) == (0, 0, 0)


def test_rapport_des_donnees_d_exemple(application_exemple):
    rapport = application_exemple.generer_rapport(MOIS)
    assert rapport.total_revenus == Decimal("2320.00")
    assert rapport.total_depenses == Decimal("1199.99")
    assert rapport.solde == Decimal("1120.01")
    assert rapport.depenses_par_categorie["Alimentation"] == Decimal("315.60")


def test_alertes_des_donnees_d_exemple(application_exemple):
    assert application_exemple.alertes(MOIS) == {
        "Alimentation": NiveauAlerte.ATTENTION,
        "Loisirs": NiveauAlerte.DEPASSEMENT,
        "Transport": NiveauAlerte.OK,
    }


def test_alertes_identiques_a_celles_de_la_v1(application_exemple):
    legacy = GestionnaireBudget()
    legacy.importer_csv(DOSSIER_DATA / "exemple_transactions.csv")
    for categorie, plafond in (("Alimentation", 350), ("Loisirs", 100), ("Transport", 150)):
        legacy.definir_plafond(categorie, plafond)
    alertes = {c: niveau.name for c, niveau in application_exemple.alertes(MOIS).items()}
    assert alertes == legacy.calculer_alertes(MOIS)


def test_aucun_affichage_dans_la_logique_metier(application_exemple, capsys):
    application_exemple.generer_rapport(MOIS)
    application_exemple.sauvegarder()
    assert capsys.readouterr().out == ""


# ---------- Persistance ----------

def test_sauvegarder_transmet_les_donnees_au_depot():
    depot = DepotMemoire()
    app = Application(depot)
    transaction = app.ajouter_transaction("depense", "10", "2026-10-05", "Transport")
    budget = app.definir_plafond("Transport", "150")
    app.sauvegarder()
    assert depot.sauvegardes == [((transaction,), (budget,))]


def test_charger_remplace_les_donnees_en_memoire():
    depot = DepotMemoire(DepotCsv(DOSSIER_DATA / "exemple_transactions_invalides.csv").charger())
    app = Application(depot)
    ancienne = app.ajouter_transaction("depense", "999", "2026-10-01", "Autre")

    resultat = app.charger()

    assert len(app.lister_transactions()) == 2
    assert ancienne not in app.lister_transactions()
    assert len(resultat.erreurs) == 5


def test_charger_en_echec_conserve_les_donnees_actuelles(tmp_path):
    app = Application(DepotJson(tmp_path / "absent.json"))
    app.ajouter_transaction("depense", "10", "2026-10-05", "Transport")
    with pytest.raises(FichierDonneesError):
        app.charger()
    assert len(app.lister_transactions()) == 1


def test_importer_ajoute_sans_remplacer():
    app = Application(DepotMemoire())
    app.ajouter_transaction("depense", "10", "2026-10-05", "Transport")
    resultat = app.importer(DepotCsv(DOSSIER_DATA / "exemple_transactions_invalides.csv"))
    assert len(app.lister_transactions()) == 3
    assert len(resultat.erreurs) == 5


def test_aller_retour_complet_avec_un_vrai_depot(application_exemple, tmp_path):
    fichier = tmp_path / "budget.json"
    ecrivain = Application(DepotJson(fichier))
    ecrivain.importer(DepotCsv(DOSSIER_DATA / "exemple_transactions.csv",
                               DOSSIER_DATA / "exemple_plafonds.csv"))
    ecrivain.sauvegarder()

    lecteur = Application(DepotJson(fichier))
    lecteur.charger()

    assert lecteur.generer_rapport(MOIS) == application_exemple.generer_rapport(MOIS)


# ---------- Open/Closed : une politique personnalisée survit au rechargement ----------

class PolitiqueToujoursCritique(PolitiqueAlerte):
    def evaluer(self, pourcentage):
        return NiveauAlerte.DEPASSEMENT


def test_la_politique_injectee_est_conservee_apres_charger():
    depot = DepotMemoire()
    app = Application(depot, politiques=[PolitiqueToujoursCritique()])
    app.definir_plafond("Loisirs", "100")
    app.ajouter_transaction("depense", "1", "2026-10-05", "Loisirs")
    assert app.alertes(MOIS)["Loisirs"] is NiveauAlerte.DEPASSEMENT

    app.sauvegarder()
    depot.resultat = ResultatChargement(*depot.sauvegardes[-1])
    app.charger()

    assert app.alertes(MOIS)["Loisirs"] is NiveauAlerte.DEPASSEMENT
