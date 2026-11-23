"""État de la session web : une Application par visiteur, et les échanges de fichiers.

Chaque visiteur a sa propre Application et son propre dossier temporaire : les données de
l'un ne sont jamais visibles par l'autre. Aucune règle métier ici : tout passe par Application.
"""

import tempfile
from datetime import date
from pathlib import Path

import streamlit as st

from budget.application import Application
from budget.constantes import FORMAT_MOIS
from budget.depots import DepotCsv, DepotJson, ResultatChargement

RACINE = Path(__file__).resolve().parents[1]
DOSSIER_DATA = RACINE / "data"


def obtenir_application() -> Application:
    if "application" not in st.session_state:
        dossier = Path(tempfile.mkdtemp(prefix="budget_"))
        st.session_state["dossier_session"] = dossier
        st.session_state["application"] = Application(DepotJson(dossier / "budget.json"))
    return st.session_state["application"]


def reinitialiser() -> None:
    st.session_state.pop("application", None)


def mois_disponibles(application: Application) -> list[str]:
    mois = sorted({transaction.mois for transaction in application.lister_transactions()})
    return mois or [date.today().strftime(FORMAT_MOIS)]


def charger_exemple() -> ResultatChargement:
    """Repart d'une application vide puis importe les fichiers d'exemple du dépôt."""
    reinitialiser()
    source = DepotCsv(DOSSIER_DATA / "exemple_transactions.csv", DOSSIER_DATA / "exemple_plafonds.csv")
    return obtenir_application().importer(source)


def importer_exemple_invalide() -> ResultatChargement:
    source = DepotCsv(DOSSIER_DATA / "exemple_transactions_invalides.csv")
    return obtenir_application().importer(source)


def importer_csv(transactions: bytes, plafonds: bytes | None) -> ResultatChargement:
    dossier = st.session_state["dossier_session"]
    (dossier / "transactions.csv").write_bytes(transactions)
    chemin_plafonds = None
    if plafonds is not None:
        chemin_plafonds = dossier / "plafonds.csv"
        chemin_plafonds.write_bytes(plafonds)
    return obtenir_application().importer(DepotCsv(dossier / "transactions.csv", chemin_plafonds))


def exporter_json() -> bytes:
    obtenir_application().sauvegarder()
    return (st.session_state["dossier_session"] / "budget.json").read_bytes()


def importer_json(contenu: bytes) -> ResultatChargement:
    (st.session_state["dossier_session"] / "budget.json").write_bytes(contenu)
    return obtenir_application().charger()
