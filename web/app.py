# ruff: noqa: E402
"""Interface web (Streamlit) de l'application de gestion de budget.

Lancer en local :  streamlit run web/app.py
Cette interface réutilise l'Application du dossier src/ sans la modifier : la logique métier
est la même que celle de la ligne de commande.
"""

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(RACINE / "src"), str(Path(__file__).resolve().parent)]

import etat
import streamlit as st
from composants import carte_titre
from style import CSS
from vues import architecture, donnees, guide, plafonds, rapport, tableau_de_bord, transactions
from vues.affichage import afficher_html, nom_du_mois

# Table de navigation : ajouter une page = ajouter une ligne (Open/Closed)
PAGES = {
    "Tableau de bord": tableau_de_bord.afficher,
    "Transactions": transactions.afficher,
    "Plafonds": plafonds.afficher,
    "Rapport": rapport.afficher,
    "Données": donnees.afficher,
    "Architecture": architecture.afficher,
    "Guide": guide.afficher,
}


def choisir_mois(mois_disponibles: list[str]) -> None:
    if st.session_state.get("mois") not in mois_disponibles:
        st.session_state["mois"] = mois_disponibles[-1]
    st.selectbox("Mois", mois_disponibles, format_func=nom_du_mois, key="mois", label_visibility="collapsed")


def main() -> None:
    st.set_page_config(page_title="Gestion de budget personnel", layout="wide", initial_sidebar_state="collapsed")
    afficher_html(CSS)
    application = etat.obtenir_application()
    afficher_html(carte_titre("Gestion de budget personnel", "Suivre, planifier, anticiper"))
    navigation, selecteur = st.columns([4.6, 1], vertical_alignment="center")
    with navigation:
        page = st.radio("Navigation", list(PAGES), key="page", horizontal=True, label_visibility="collapsed")
    with selecteur:
        choisir_mois(etat.mois_disponibles(application))
    PAGES[page](application)


main()
