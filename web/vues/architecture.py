"""Architecture : diagramme UML, classes, avant/après et indicateurs de qualité."""

from pathlib import Path

import streamlit as st
from composants import bandeau, indicateur, panneau

from budget.application import Application
from vues.affichage import afficher_html

RACINE = Path(__file__).resolve().parents[2]
DIAGRAMME = RACINE / "docs" / "diagrammes" / "diagramme_classes.png"
CONCEPTION = RACINE / "docs" / "conception.md"
AVANT_APRES = RACINE / "docs" / "avant_apres.md"
SECTIONS = ("2. Classes et responsabilités", "3. Relations entre classes", "4. Principes appliqués")

# Mesures du 19/11/2026 (pytest, coverage, radon)
INDICATEURS = (
    ("Tests automatisés", "187", "19 sur la version 1"),
    ("Couverture du code", "100 %", "de src/budget"),
    ("Complexité moyenne", "2,0", "4,0 sur la version 1"),
    ("Complexité maximale", "8", "imposée par ruff"),
)


def afficher(_application: Application) -> None:
    uml, classes, avant_apres, qualite = st.tabs(["Diagramme UML", "Classes et principes", "Avant et après", "Qualité mesurée"])
    with uml:
        _diagramme()
    with classes:
        _sections()
    with avant_apres:
        _markdown(AVANT_APRES)
    with qualite:
        _indicateurs()


def _diagramme() -> None:
    if DIAGRAMME.exists():
        st.image(str(DIAGRAMME), caption="Diagramme de classes", use_container_width=True)
    else:
        afficher_html(bandeau("Diagramme absent : voir docs/diagrammes/."))


def _sections() -> None:
    texte = CONCEPTION.read_text(encoding="utf-8") if CONCEPTION.exists() else ""
    for titre in SECTIONS:
        section = next((s for s in texte.split("\n## ") if s.startswith(titre)), None)
        if section:
            st.markdown("## " + section)


def _markdown(chemin: Path) -> None:
    if chemin.exists():
        st.markdown(chemin.read_text(encoding="utf-8"))
    else:
        afficher_html(bandeau(f"Document absent : {chemin.name}"))


def _indicateurs() -> None:
    colonnes = st.columns(len(INDICATEURS))
    for colonne, (libelle, valeur, note) in zip(colonnes, INDICATEURS, strict=True):
        colonne.markdown(panneau(libelle, indicateur("", valeur, note)), unsafe_allow_html=True)
    afficher_html(
        panneau(
            "Preuve de non-régression",
            "<p>Les tests incluent les tests de caractérisation de la version 1 et des tests de parité : "
            "la version propre donne les mêmes résultats que la version 1.</p>",
            "mauve",
        )
    )
