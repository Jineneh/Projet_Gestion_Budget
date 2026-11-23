"""Rapport mensuel : le même texte que la ligne de commande, et téléchargement."""

import streamlit as st
from composants import echapper, indicateur, panneau

from budget.application import Application
from budget.rapport import FormateurRapportTexte
from vues.affichage import afficher_html, formater_montant, nom_du_mois


def afficher(application: Application) -> None:
    if not application.lister_transactions():
        afficher_html(
            panneau(
                "Rapport mensuel",
                "<p>Aucune donnée : chargez l'exemple depuis l'onglet Données.</p>",
            )
        )
        return
    mois = st.session_state["mois"]
    rapport = application.generer_rapport(mois)
    texte = FormateurRapportTexte().formater(rapport)
    gauche, droite = st.columns([1.5, 1])
    with gauche:
        afficher_html(
            panneau(
                f"Rapport de {nom_du_mois(mois)}",
                f'<pre class="rapport">{echapper(texte)}</pre>',
                "mauve",
            )
        )
    with droite:
        corps = (
            indicateur("Revenus", formater_montant(rapport.total_revenus))
            + indicateur("Dépenses", formater_montant(rapport.total_depenses))
            + indicateur("Solde", formater_montant(rapport.solde))
        )
        afficher_html(panneau("En un coup d'oeil", corps))
        st.caption(
            "Même RapportMensuel et même FormateurRapportTexte que la ligne de commande : "
            "deux interfaces, une seule logique métier."
        )
        st.download_button(
            "Télécharger le rapport (.txt)",
            texte,
            file_name=f"rapport_{mois}.txt",
            key="telechargement_rapport",
        )
