"""Chargement, import, export et réinitialisation des données."""

import etat
import streamlit as st
from composants import bandeau, echapper, entete

from budget.application import Application
from budget.erreurs import BudgetError
from vues.affichage import afficher_dernier_import, afficher_html, memoriser_import


def afficher(_application: Application) -> None:
    afficher_dernier_import()
    exemple, importer, sauvegarde = st.columns(3)
    with exemple:
        _exemple()
    with importer:
        _import_csv()
    with sauvegarde:
        _sauvegarde()


def _exemple() -> None:
    with st.container(key="panneau_exemple"):
        afficher_html(entete("Données d'exemple"))
        st.write("Charge 15 transactions d'octobre 2026 et 3 plafonds : Alimentation, Loisirs, Transport.")
        if st.button("Charger l'exemple", type="primary", key="bouton_exemple", use_container_width=True):
            memoriser_import(etat.charger_exemple())
        st.write("Gestion des erreurs : ce fichier contient 2 lignes valides et 5 lignes invalides.")
        if st.button("Tester un fichier invalide", key="bouton_invalide", use_container_width=True):
            memoriser_import(etat.importer_exemple_invalide())


def _import_csv() -> None:
    with st.container(key="panneau_import"):
        afficher_html(entete("Importer un fichier CSV"))
        st.caption("Colonnes : date, type, montant, categorie, description (UTF-8).")
        transactions = st.file_uploader("Transactions", type="csv", key="csv_transactions")
        plafonds = st.file_uploader("Plafonds (facultatif)", type="csv", key="csv_plafonds")
        if transactions is not None and st.button("Importer", type="primary", key="bouton_import"):
            _importer(transactions, plafonds)


def _importer(transactions, plafonds) -> None:
    try:
        contenu = plafonds.getvalue() if plafonds is not None else None
        memoriser_import(etat.importer_csv(transactions.getvalue(), contenu))
    except BudgetError as erreur:
        afficher_html(bandeau(f"<b>Import impossible</b> : {echapper(erreur)}", rouge=True))


def _sauvegarde() -> None:
    with st.container(key="panneau_sauvegarde"):
        afficher_html(entete("Sauvegarde et remise à zéro"))
        st.download_button(
            "Télécharger ma sauvegarde (.json)",
            etat.exporter_json(),
            file_name="budget.json",
            mime="application/json",
            key="telechargement_json",
            use_container_width=True,
        )
        fichier = st.file_uploader("Restaurer une sauvegarde", type="json", key="json_restauration")
        if fichier is not None and st.button("Restaurer", key="bouton_restauration"):
            _restaurer(fichier)
        if st.button("Tout réinitialiser", key="bouton_reinitialiser", use_container_width=True):
            etat.reinitialiser()
            st.rerun()


def _restaurer(fichier) -> None:
    try:
        memoriser_import(etat.importer_json(fichier.getvalue()))
    except BudgetError as erreur:
        afficher_html(bandeau(f"<b>Restauration impossible</b> : {echapper(erreur)}", rouge=True))
