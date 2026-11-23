"""Tableau de bord : période, reste à dépenser, plafonds contre dépenses, répartition."""

import etat
import streamlit as st
from composants import (
    COULEUR_FOND_DONUT,
    PALETTE,
    bandeau,
    barres_comparees,
    donut,
    echapper,
    jauge,
    legende,
    panneau,
    tableau,
)

from budget.alertes import NiveauAlerte
from budget.application import Application
from budget.modeles import TypeTransaction
from budget.rapport import RapportMensuel
from vues.affichage import (
    COULEURS_NIVEAU,
    afficher_html,
    formater_montant,
    formater_pourcentage,
    nom_du_mois,
    pastille,
    periode_du_mois,
)

DERNIERES_TRANSACTIONS = 6
HAUTEUR_HAUT = 26.5
HAUTEUR_BAS = 15


def afficher(application: Application) -> None:
    if not application.lister_transactions():
        _accueil_vide()
        return
    mois = st.session_state["mois"]
    rapport = application.generer_rapport(mois)
    _bandeau_alertes(rapport)
    colonnes = st.columns([1.05, 1.15, 1.45, 1.2])
    contenus = (
        panneau("Période", _periode(application, mois), hauteur=HAUTEUR_HAUT),
        panneau("Reste à dépenser", _reste_a_depenser(rapport), hauteur=HAUTEUR_HAUT),
        panneau("Plafonds et dépenses", _plafonds_et_depenses(application, rapport), hauteur=HAUTEUR_HAUT),
        panneau("Répartition des dépenses", _repartition(rapport), "mauve", HAUTEUR_HAUT),
    )
    for colonne, contenu in zip(colonnes, contenus, strict=True):
        colonne.markdown(contenu, unsafe_allow_html=True)
    bas = st.columns([1.0, 2.5, 1.15])
    bas[0].markdown(panneau("Résumé du mois", _resume(rapport), "peche", HAUTEUR_BAS), unsafe_allow_html=True)
    bas[1].markdown(
        panneau("Suivi des plafonds", tableau_plafonds(application, rapport), "mauve", HAUTEUR_BAS),
        unsafe_allow_html=True,
    )
    bas[2].markdown(panneau("Dernières transactions", _dernieres(application, mois), "rose", HAUTEUR_BAS), unsafe_allow_html=True)


def _accueil_vide() -> None:
    afficher_html(
        panneau(
            "Bienvenue",
            '<div class="centre"><p style="font-family:var(--serif);font-size:1.7rem;margin:.2rem 0">'
            "Votre budget commence ici.</p>"
            "<p>Chargez les données d'exemple pour tout découvrir en un clic, "
            "ou ajoutez votre première transaction dans l'onglet Transactions.</p></div>",
        )
    )
    _, milieu, _ = st.columns([1, 1, 1])
    if milieu.button(
        "Charger les données d'exemple",
        type="primary",
        key="accueil_charger",
        use_container_width=True,
    ):
        st.session_state["dernier_import"] = etat.charger_exemple()
        st.rerun()


def _bandeau_alertes(rapport: RapportMensuel) -> None:
    depassements = [c for c, n in rapport.alertes.items() if n is NiveauAlerte.DEPASSEMENT]
    attentions = [c for c, n in rapport.alertes.items() if n is NiveauAlerte.ATTENTION]
    if depassements:
        noms = ", ".join(echapper(c) for c in depassements)
        afficher_html(
            bandeau(
                f"<b>Plafond dépassé</b> : {noms}. Réduisez les dépenses ou ajustez le plafond.",
                True,
            )
        )
    if attentions:
        noms = ", ".join(echapper(c) for c in attentions)
        afficher_html(bandeau(f"<b>Attention</b> : {noms} approche du plafond (au moins 80 %)."))


def _periode(application: Application, mois: str) -> str:
    nombre = len(application.lister_transactions(mois=mois))
    return (
        f'<div class="mois-nom">{nom_du_mois(mois)}</div>'
        f'<div class="mois-periode">{periode_du_mois(mois)}</div>'
        f'<div class="mini-stats"><div><b>{nombre}</b><span>transactions</span></div>'
        f"<div><b>{len(application.plafonds)}</b><span>plafonds</span></div></div>"
    )


def _reste_a_depenser(rapport: RapportMensuel) -> str:
    depense = float(rapport.total_depenses)
    revenus = float(rapport.total_revenus)
    reste = max(revenus - depense, 0.0)
    depense_affichee = min(depense, revenus) if revenus else depense
    part = 100 * depense / revenus if revenus else 100.0
    anneau = donut(
        [(depense_affichee, PALETTE[0]), (reste, COULEUR_FOND_DONUT)],
        formater_montant(rapport.solde),
        "solde",
    )
    return anneau + legende(
        [
            (PALETTE[0], "Dépensé", formater_pourcentage(min(part, 100.0))),
            (COULEUR_FOND_DONUT, "Revenus", formater_montant(rapport.total_revenus)),
        ]
    )


def _plafonds_et_depenses(application: Application, rapport: RapportMensuel) -> str:
    plafonds = {b.categorie: float(b.plafond) for b in application.plafonds}
    lignes = [
        (
            categorie,
            float(montant),
            plafonds.get(categorie),
            COULEURS_NIVEAU[rapport.alertes[categorie]] if categorie in rapport.alertes else PALETTE[0],
        )
        for categorie, montant in sorted(rapport.depenses_par_categorie.items(), key=lambda p: -p[1])
    ]
    return barres_comparees(lignes) if lignes else "<p>Aucune dépense ce mois-ci.</p>"


def _repartition(rapport: RapportMensuel) -> str:
    categories = sorted(rapport.depenses_par_categorie.items(), key=lambda p: -p[1])
    total = float(rapport.total_depenses)
    segments = [(float(m), PALETTE[i % len(PALETTE)]) for i, (_, m) in enumerate(categories)]
    items = [
        (PALETTE[i % len(PALETTE)], c, formater_pourcentage(100 * float(m) / total if total else 0))
        for i, (c, m) in enumerate(categories)
    ]
    return donut(segments, formater_montant(rapport.total_depenses), "dépensé", 170) + legende(items)


def _resume(rapport: RapportMensuel) -> str:
    lignes = [
        ["+ Revenus", formater_montant(rapport.total_revenus)],
        ["&minus; Dépenses", formater_montant(rapport.total_depenses)],
    ]
    total = ["Solde", formater_montant(rapport.solde)]
    return tableau(["Catégorie", "Réel"], lignes, [1], total)


def tableau_plafonds(application: Application, rapport: RapportMensuel) -> str:
    """Tableau plafond / dépensé / reste / statut, partagé avec la page Plafonds."""
    if not application.plafonds:
        return "<p>Aucun plafond défini : ajoutez-en dans l'onglet Plafonds.</p>"
    lignes = []
    for budget in application.plafonds:
        depense = rapport.depenses_par_categorie.get(budget.categorie, 0)
        pourcentage = float(budget.pourcentage_consomme(depense))
        niveau = rapport.alertes[budget.categorie]
        lignes.append(
            [
                echapper(budget.categorie),
                formater_montant(budget.plafond),
                formater_montant(depense),
                formater_montant(budget.plafond - depense),
                jauge(pourcentage, COULEURS_NIVEAU[niveau]) + f"<small>{formater_pourcentage(pourcentage)}</small>",
                pastille(niveau),
            ]
        )
    return tableau(["Catégorie", "Plafond", "Dépensé", "Reste", "Consommé", "Statut"], lignes, [1, 2, 3])


def _dernieres(application: Application, mois: str) -> str:
    transactions = sorted(application.lister_transactions(mois=mois), key=lambda t: t.jour, reverse=True)
    lignes = [
        [
            t.jour.strftime("%d/%m"),
            echapper(t.categorie),
            ("+" if t.type is TypeTransaction.REVENU else "&minus;") + " " + formater_montant(t.montant),
        ]
        for t in transactions[:DERNIERES_TRANSACTIONS]
    ]
    return tableau(["Date", "Catégorie", "Montant"], lignes, [2])
