"""Saisie guidée et suivi des transactions."""

import streamlit as st
from composants import bandeau, echapper, entete, panneau, tableau

from budget.application import Application
from budget.erreurs import BudgetError
from budget.modeles import TypeTransaction
from vues.affichage import afficher_html, formater_montant

TYPES = {"Dépense": "depense", "Revenu": "revenu"}


def afficher(application: Application) -> None:
    gauche, droite = st.columns([1, 1.9])
    with gauche:
        _formulaire(application)
    with droite:
        _suivi(application)


def _formulaire(application: Application) -> None:
    with st.container(key="panneau_saisie"):
        afficher_html(entete("Nouvelle transaction"))
        with st.form("formulaire_transaction", border=False):
            type_libelle = st.radio("Type", list(TYPES), horizontal=True, key="type_saisie")
            montant = st.text_input("Montant en euros", key="montant_saisie", placeholder="12,50")
            jour = st.date_input("Date", key="date_saisie", format="DD/MM/YYYY")
            categorie = st.text_input("Catégorie", key="categorie_saisie", placeholder="Alimentation")
            description = st.text_input("Description (facultatif)", key="description_saisie")
            envoye = st.form_submit_button("Ajouter", type="primary", key="envoyer_transaction")
        categories = sorted({t.categorie for t in application.lister_transactions()})
        if categories:
            st.caption("Catégories déjà utilisées : " + ", ".join(categories))
        st.caption("Essayez un montant invalide (abc, -5) : la saisie est refusée avec une explication.")
        if envoye:
            _enregistrer(application, TYPES[type_libelle], montant, jour, categorie, description)


def _enregistrer(application, type_texte, montant, jour, categorie, description) -> None:
    try:
        transaction = application.ajouter_transaction(
            type_texte, montant.replace(",", "."), jour.isoformat(), categorie, description
        )
    except BudgetError as erreur:
        afficher_html(bandeau(f"<b>Saisie refusée</b> : {echapper(erreur)}", rouge=True))
        return
    afficher_html(
        bandeau(
            f"<b>Transaction ajoutée</b> : {echapper(transaction.categorie)}, {formater_montant(transaction.montant)}.", vert=True
        )
    )


def _suivi(application: Application) -> None:
    toutes = application.lister_transactions()
    colonnes = st.columns(2)
    mois = colonnes[0].selectbox("Mois", ["Tous"] + sorted({t.mois for t in toutes}), key="filtre_mois")
    categorie = colonnes[1].selectbox("Catégorie", ["Toutes"] + sorted({t.categorie for t in toutes}), key="filtre_categorie")
    retenues = application.lister_transactions(
        mois=None if mois == "Tous" else mois,
        categorie=None if categorie == "Toutes" else categorie,
    )
    if not retenues:
        afficher_html(panneau("Suivi des transactions", "<p>Aucune transaction à afficher.</p>", "mauve"))
        return
    lignes = [_ligne(t) for t in sorted(retenues, key=lambda t: t.jour, reverse=True)]
    afficher_html(
        panneau(
            "Suivi des transactions",
            tableau(["Date", "Type", "Catégorie", "Description", "Montant"], lignes, [4], defile=True),
            "mauve",
        )
    )


def _ligne(transaction) -> list[str]:
    est_revenu = transaction.type is TypeTransaction.REVENU
    signe = "+" if est_revenu else "&minus;"
    return [
        transaction.jour.strftime("%d/%m/%Y"),
        "Revenu" if est_revenu else "Dépense",
        echapper(transaction.categorie),
        echapper(transaction.description),
        f"{signe} {formater_montant(transaction.montant)}",
    ]
