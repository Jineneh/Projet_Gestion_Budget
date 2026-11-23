"""Plafonds par catégorie et simulateur d'alertes."""

from datetime import date

import streamlit as st
from composants import bandeau, donut, echapper, entete, panneau

from budget.alertes import NiveauAlerte
from budget.application import Application
from budget.constantes import FORMAT_MOIS
from budget.erreurs import BudgetError
from budget.journal import Journal
from budget.modeles import Budget, Transaction, TypeTransaction
from budget.suivi import SuiviBudget
from vues.affichage import (
    COULEURS_NIVEAU,
    afficher_html,
    formater_montant,
    pastille,
)
from vues.tableau_de_bord import tableau_plafonds

PLAFOND_SIMULE = 100
CATEGORIE_SIMULEE = "Simulation"
JOUR_SIMULE = date(2026, 1, 15)
COULEUR_RESTE = "#F3DDE2"


def afficher(application: Application) -> None:
    gauche, droite = st.columns([1, 1.9])
    with gauche:
        _formulaire(application)
    with droite:
        _suivi(application)
    _simulateur()


def _formulaire(application: Application) -> None:
    with st.container(key="panneau_plafond"):
        afficher_html(entete("Définir un plafond"))
        with st.form("formulaire_plafond", border=False):
            categorie = st.text_input("Catégorie", key="categorie_plafond", placeholder="Loisirs")
            plafond = st.text_input("Plafond mensuel en euros", key="montant_plafond", placeholder="100")
            envoye = st.form_submit_button("Enregistrer le plafond", type="primary", key="envoyer_plafond")
        st.caption("Un nouveau plafond remplace l'ancien pour la même catégorie.")
        if envoye:
            _definir(application, categorie, plafond)


def _definir(application: Application, categorie: str, plafond: str) -> None:
    try:
        budget = application.definir_plafond(categorie, plafond.replace(",", "."))
    except BudgetError as erreur:
        afficher_html(bandeau(f"<b>Saisie refusée</b> : {echapper(erreur)}", rouge=True))
        return
    afficher_html(
        bandeau(
            f"<b>Plafond enregistré</b> : {formater_montant(budget.plafond)} par mois pour {echapper(budget.categorie)}.",
            vert=True,
        )
    )


def _suivi(application: Application) -> None:
    rapport = application.generer_rapport(st.session_state["mois"])
    afficher_html(panneau("Suivi des plafonds du mois", tableau_plafonds(application, rapport), "mauve"))


def _simulateur() -> None:
    with st.container(key="panneau_simulateur"):
        afficher_html(entete("Simulateur d'alertes"))
        gauche, droite = st.columns([1.5, 1])
        with gauche:
            st.write(
                "Faites glisser le curseur : le simulateur interroge le vrai suivi de budget et ses "
                "politiques d'alerte. Essayez 79, 80, 100 puis 101 sur un plafond de 100 euros."
            )
            depense = st.slider("Dépense du mois, en euros (plafond : 100)", 0, 150, 79, key="depense_simulee")
        niveau = _niveau_simule(depense)
        with droite:
            afficher_html(
                donut(
                    [
                        (min(depense, PLAFOND_SIMULE), COULEURS_NIVEAU[niveau]),
                        (max(PLAFOND_SIMULE - depense, 0), COULEUR_RESTE),
                    ],
                    f"{depense} %",
                    "du plafond",
                    170,
                )
                + f'<div class="centre">{pastille(niveau)}</div>'
            )


def _niveau_simule(depense: int) -> NiveauAlerte:
    """Construit un mini-journal d'une dépense et interroge le suivi réel."""
    journal = Journal()
    if depense > 0:
        journal.ajouter(
            Transaction(
                montant=depense,
                jour=JOUR_SIMULE,
                categorie=CATEGORIE_SIMULEE,
                type=TypeTransaction.DEPENSE,
            )
        )
    suivi = SuiviBudget(journal, [Budget(CATEGORIE_SIMULEE, PLAFOND_SIMULE)])
    return suivi.niveau(JOUR_SIMULE.strftime(FORMAT_MOIS), CATEGORIE_SIMULEE)
