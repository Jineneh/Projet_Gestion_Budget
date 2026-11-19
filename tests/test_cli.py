"""Tests de la CLI : sessions scriptées, sans clavier ni écran."""
import runpy
import shutil
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from budget.application import Application
from budget.cli import CLI, main
from budget.depots import Depot, DepotJson, ResultatChargement
from budget.erreurs import FichierDonneesError

DOSSIER_DATA = Path(__file__).resolve().parents[1] / "data"
TRANSACTIONS = str(DOSSIER_DATA / "exemple_transactions.csv")
PLAFONDS = str(DOSSIER_DATA / "exemple_plafonds.csv")
INVALIDES = str(DOSSIER_DATA / "exemple_transactions_invalides.csv")
AUJOURDHUI = date(2026, 10, 15)


class DepotMemoire(Depot):
    def __init__(self, echec_sauvegarde=False):
        self.echec_sauvegarde = echec_sauvegarde
        self.nombre_sauvegardes = 0

    def charger(self):
        return ResultatChargement()

    def sauvegarder(self, transactions, budgets):
        if self.echec_sauvegarde:
            raise FichierDonneesError("disque plein")
        self.nombre_sauvegardes += 1


def session(reponses, application=None):
    """Joue une session : renvoie (texte affiché, application). Fin des réponses = Ctrl+D."""
    application = application or Application(DepotMemoire())
    restantes = iter(reponses)
    affichage = []

    def entree(question):
        affichage.append(question)
        try:
            return next(restantes)
        except StopIteration:
            raise EOFError from None

    CLI(application, entree, affichage.append, lambda: AUJOURDHUI).executer()
    return "\n".join(affichage), application


# ---------- Navigation ----------

def test_quitter_directement():
    sortie, _ = session(["0"])
    assert "Gestion de budget personnel" in sortie
    assert "Au revoir." in sortie


def test_choix_inconnu_puis_poursuite():
    sortie, _ = session(["9", "0"])
    assert "Choix inconnu : '9'" in sortie
    assert "Au revoir." in sortie


@pytest.mark.parametrize("reponses", [[], ["1"]])
def test_fin_de_saisie_quitte_proprement(reponses):
    sortie, _ = session(reponses)
    assert "Au revoir." in sortie


def test_ctrl_c_quitte_proprement():
    def entree(_question):
        raise KeyboardInterrupt

    sorties = []
    CLI(Application(DepotMemoire()), entree, sorties.append).executer()
    assert sorties[-1] == "Au revoir."


# ---------- Saisie de transactions ----------

def test_ajouter_une_depense_avec_virgule_decimale():
    sortie, app = session(["1", "depense", "12,50", "2026-10-05", "Transport", "Ticket", "0", "n"])
    (transaction,) = app.lister_transactions()
    assert transaction.montant == Decimal("12.50")
    assert "Ajoutée : 2026-10-05" in sortie
    assert "-12.50 EUR" in sortie


def test_date_vide_utilise_la_date_du_jour():
    _, app = session(["1", "revenu", "100", "", "Salaire", "", "0", "n"])
    assert app.lister_transactions()[0].jour == AUJOURDHUI


@pytest.mark.parametrize(
    ("saisie", "message"),
    [
        (["virement", "10", "2026-10-05", "Transport", ""], "Type inconnu"),
        (["depense", "abc", "2026-10-05", "Transport", ""], "Montant non numérique"),
        (["depense", "-5", "2026-10-05", "Transport", ""], "strictement positif"),
        (["depense", "10", "2026-13-05", "Transport", ""], "Date invalide"),
        (["depense", "10", "2026-10-05", "  ", ""], "catégorie"),
    ],
)
def test_saisie_invalide_affiche_une_erreur_et_continue(saisie, message):
    sortie, app = session(["1", *saisie, "0"])
    assert "Erreur : " in sortie
    assert message in sortie
    assert app.lister_transactions() == ()
    assert "Au revoir." in sortie


# ---------- Consultation ----------

def test_lister_sans_transaction():
    sortie, _ = session(["2", "", "0"])
    assert "Aucune transaction." in sortie


def test_lister_filtre_par_mois():
    sortie, _ = session(["5", TRANSACTIONS, "", "2", "2026-11", "2", "2026-10", "0", "n"])
    assert sortie.count("Aucune transaction.") == 1
    assert "+2200.00 EUR  Salaire (Salaire octobre)" in sortie


def test_definir_un_plafond():
    sortie, app = session(["3", "Loisirs", "100,5", "0", "n"])
    assert "Plafond de 100.50 EUR défini pour Loisirs." in sortie
    assert app.plafonds[0].plafond == Decimal("100.50")


def test_plafond_invalide():
    sortie, app = session(["3", "Loisirs", "0", "0"])
    assert "Erreur :" in sortie
    assert app.plafonds == ()


def test_rapport_et_alertes_sur_les_donnees_d_exemple():
    sortie, _ = session(["5", TRANSACTIONS, PLAFONDS, "4", "2026-10", "0", "n"])
    assert "===== Rapport 2026-10 =====" in sortie
    assert "Solde    : 1120.01 EUR" in sortie
    assert "! Alimentation : plafond bientôt atteint" in sortie
    assert "!!! Loisirs : plafond dépassé" in sortie
    assert "Transport : plafond" not in sortie


def test_rapport_utilise_le_mois_courant_par_defaut():
    sortie, _ = session(["4", "", "0"])
    assert "Rapport 2026-10" in sortie


def test_rapport_mois_invalide():
    sortie, _ = session(["4", "octobre", "0"])
    assert "Erreur : Mois invalide" in sortie


# ---------- Import ----------

def test_import_csv_signale_les_lignes_rejetees():
    sortie, app = session(["5", INVALIDES, "", "0", "n"])
    assert "2 transaction(s) et 0 plafond(s) importés, 5 ligne(s) rejetée(s)." in sortie
    assert "  - Ligne 3 :" in sortie
    assert len(app.lister_transactions()) == 2


def test_import_d_un_fichier_absent():
    sortie, _ = session(["5", "inexistant.csv", "", "0"])
    assert "Erreur : Fichier introuvable" in sortie


# ---------- Sauvegarde et sortie ----------

def test_sauvegarder_puis_charger_avec_un_vrai_depot(tmp_path):
    fichier = tmp_path / "budget.json"
    session(["5", TRANSACTIONS, PLAFONDS, "6", "0"], Application(DepotJson(fichier)))

    sortie, app = session(["7", "0"], Application(DepotJson(fichier)))

    assert "Données chargées : 15 transaction(s), 3 plafond(s), 0 rejet(s)." in sortie
    assert len(app.lister_transactions()) == 15


def test_charger_un_fichier_absent_affiche_une_erreur(tmp_path):
    sortie, _ = session(["7", "0"], Application(DepotJson(tmp_path / "absent.json")))
    assert "Erreur : Fichier introuvable" in sortie


def test_quitter_avec_modifications_propose_de_sauvegarder():
    depot = DepotMemoire()
    session(["3", "Loisirs", "100", "0", "o"], Application(depot))
    assert depot.nombre_sauvegardes == 1


def test_quitter_en_refusant_la_sauvegarde():
    depot = DepotMemoire()
    sortie, _ = session(["3", "Loisirs", "100", "0", "n"], Application(depot))
    assert depot.nombre_sauvegardes == 0
    assert "Au revoir." in sortie


def test_quitter_apres_sauvegarde_ne_redemande_rien():
    depot = DepotMemoire()
    sortie, _ = session(["3", "Loisirs", "100", "6", "0"], Application(depot))
    assert "Sauvegarder avant de quitter" not in sortie


def test_echec_de_sauvegarde_a_la_sortie_ne_ferme_pas_le_programme():
    depot = DepotMemoire(echec_sauvegarde=True)
    sortie, _ = session(["3", "Loisirs", "100", "0", "o", "0", "n"], Application(depot))
    assert "Erreur : disque plein" in sortie
    assert sortie.count("Votre choix") == 3


# ---------- Point d'entrée ----------

def entrees(monkeypatch, *reponses):
    suite = iter(reponses)
    monkeypatch.setattr("builtins.input", lambda _question="": next(suite))


def test_main_demarre_sans_fichier(monkeypatch, tmp_path, capsys):
    entrees(monkeypatch, "0")
    assert main(["--fichier", str(tmp_path / "neuf.json")]) == 0
    assert "Au revoir." in capsys.readouterr().out


def test_main_charge_un_fichier_existant(monkeypatch, tmp_path, capsys):
    fichier = tmp_path / "budget.json"
    shutil.copy(DOSSIER_DATA / "exemple_budget.json", fichier)
    entrees(monkeypatch, "0")
    assert main(["--fichier", str(fichier)]) == 0
    assert "Données chargées : 15 transaction(s)" in capsys.readouterr().out


def test_main_refuse_d_ecraser_un_fichier_corrompu(monkeypatch, tmp_path, capsys):
    fichier = tmp_path / "budget.json"
    fichier.write_text("{ corrompu", encoding="utf-8")
    entrees(monkeypatch, "0")
    assert main(["--fichier", str(fichier)]) == 1
    capture = capsys.readouterr()
    assert "Erreur : JSON corrompu" in capture.out
    assert "Corrigez ou déplacez" in capture.err
    assert fichier.read_text(encoding="utf-8") == "{ corrompu"


def test_python_m_budget_lance_le_programme(monkeypatch, tmp_path):
    monkeypatch.setattr("sys.argv", ["budget", "--fichier", str(tmp_path / "neuf.json")])
    entrees(monkeypatch, "0")
    with pytest.raises(SystemExit) as sortie:
        runpy.run_module("budget", run_name="__main__")
    assert sortie.value.code == 0
