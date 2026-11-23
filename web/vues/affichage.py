"""Fonctions d'affichage partagées par les pages (formats français, pastilles, import)."""

import calendar
from decimal import Decimal

import streamlit as st
from composants import bandeau, echapper, panneau, tableau

from budget.alertes import NiveauAlerte
from budget.application import Application
from budget.constantes import DEVISE
from budget.depots import ResultatChargement

SYMBOLES = {"EUR": "€"}
MOIS = (
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
)
LIBELLES = {
    NiveauAlerte.AUCUNE_DEPENSE: "Aucune dépense",
    NiveauAlerte.OK: "Dans le budget",
    NiveauAlerte.ATTENTION: "Attention",
    NiveauAlerte.DEPASSEMENT: "Dépassement",
}
CLASSES_PASTILLE = {
    NiveauAlerte.AUCUNE_DEPENSE: "aucune",
    NiveauAlerte.OK: "ok",
    NiveauAlerte.ATTENTION: "attention",
    NiveauAlerte.DEPASSEMENT: "depassement",
}
COULEURS_NIVEAU = {
    NiveauAlerte.AUCUNE_DEPENSE: "#BDB5BA",
    NiveauAlerte.OK: "#8CC7A1",
    NiveauAlerte.ATTENTION: "#E8A94B",
    NiveauAlerte.DEPASSEMENT: "#D9657B",
}


def afficher_html(contenu: str) -> None:
    st.markdown(contenu, unsafe_allow_html=True)


def formater_montant(montant: Decimal) -> str:
    """1120.01 devient « 1 120,01 € »."""
    texte = f"{montant:,.2f}".replace(",", " ").replace(".", ",")
    return f"{texte} {SYMBOLES.get(DEVISE, DEVISE)}"


def formater_pourcentage(valeur: float) -> str:
    return f"{valeur:.1f}".replace(".", ",") + " %"


def nom_du_mois(mois: str) -> str:
    """« 2026-10 » devient « Octobre 2026 »."""
    annee, numero = mois.split("-")
    return f"{MOIS[int(numero) - 1].capitalize()} {annee}"


def periode_du_mois(mois: str) -> str:
    annee, numero = (int(partie) for partie in mois.split("-"))
    dernier_jour = calendar.monthrange(annee, numero)[1]
    return f"Du 1er au {dernier_jour} {MOIS[numero - 1]} {annee}"


def pastille(niveau: NiveauAlerte) -> str:
    return f'<span class="pastille p-{CLASSES_PASTILLE[niveau]}">{LIBELLES[niveau]}</span>'


def a_des_donnees(application: Application) -> bool:
    return bool(application.lister_transactions())


def memoriser_import(resultat: ResultatChargement) -> None:
    """Garde le résultat pour l'afficher après le rechargement de la page."""
    st.session_state["dernier_import"] = resultat
    st.rerun()


def afficher_dernier_import() -> None:
    resultat = st.session_state.pop("dernier_import", None)
    if resultat is None:
        return
    afficher_html(
        bandeau(
            f"<b>Import terminé</b> : {len(resultat.transactions)} transaction(s) et "
            f"{len(resultat.budgets)} plafond(s) ajoutés, {len(resultat.erreurs)} ligne(s) rejetée(s).",
            vert=not resultat.erreurs,
        )
    )
    if resultat.erreurs:
        lignes = [_decouper_erreur(erreur) for erreur in resultat.erreurs]
        corps = tableau(["Ligne", "Motif du rejet"], lignes)
        afficher_html(panneau("Lignes rejetées, sans arrêter l'import", corps, "mauve"))


def _decouper_erreur(erreur: str) -> list[str]:
    ligne, _, motif = erreur.partition(" : ")
    return [echapper(ligne), echapper(motif)]
