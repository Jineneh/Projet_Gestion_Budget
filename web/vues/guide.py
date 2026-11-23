"""Guide pas à pas, vidéo de démonstration et captures d'écran."""

from dataclasses import dataclass
from pathlib import Path

import streamlit as st
from composants import bandeau, panneau

from budget.application import Application
from vues.affichage import afficher_html

ASSETS = Path(__file__).resolve().parents[1] / "assets"
VIDEO = ASSETS / "demo.mp4"
LIEN_VIDEO = ASSETS / "video_url.txt"  # lien YouTube (non répertorié) à la place du fichier
FORMATS_IMAGE = ("*.png", "*.jpg", "*.jpeg")


@dataclass(frozen=True)
class Etape:
    titre: str
    explication: str
    page: str


ETAPES = (
    Etape(
        "Charger des données",
        "Onglet Données : un clic charge 15 transactions et 3 plafonds d'octobre 2026.",
        "Données",
    ),
    Etape(
        "Lire le tableau de bord",
        "Alimentation est à 90 % (attention), Loisirs à 105 % (dépassement), solde de 1 120,01 euros.",
        "Tableau de bord",
    ),
    Etape(
        "Tester la validation",
        "Ajoutez une dépense avec le montant abc ou -5 : la saisie est refusée et expliquée.",
        "Transactions",
    ),
    Etape(
        "Jouer avec les alertes",
        "Le simulateur utilise le vrai suivi de budget : essayez 79, 80, 100 puis 101 euros.",
        "Plafonds",
    ),
    Etape(
        "Importer un fichier invalide",
        "2 lignes valides, 5 rejetées avec leur motif : l'import ne plante jamais.",
        "Données",
    ),
    Etape(
        "Découvrir l'architecture",
        "Diagramme UML, trois exemples avant et après, indicateurs de qualité.",
        "Architecture",
    ),
)


def aller_a(page: str) -> None:
    st.session_state["page"] = page


def afficher(_application: Application) -> None:
    afficher_html(
        panneau(
            "Visite guidée en six étapes",
            "<p>Chaque étape ouvre la page concernée. Le même code métier fait fonctionner cette "
            "interface et la ligne de commande.</p>",
        )
    )
    for position, etape in enumerate(ETAPES, start=1):
        numero, texte, action = st.columns([0.5, 5, 1.5], vertical_alignment="center")
        numero.markdown(
            f'<div class="etape"><span class="numero">{position}</span></div>',
            unsafe_allow_html=True,
        )
        texte.markdown(
            f'<div class="etape"><div><h4>{etape.titre}</h4><p>{etape.explication}</p></div></div>',
            unsafe_allow_html=True,
        )
        action.button(
            "Ouvrir",
            key=f"guide_{position}",
            on_click=aller_a,
            args=(etape.page,),
            use_container_width=True,
        )
    _demonstration()


def _demonstration() -> None:
    st.markdown("### Démonstration")
    source = _source_video()
    if source:
        st.video(source)
    else:
        afficher_html(bandeau("Déposez votre vidéo dans web/assets/demo.mp4, ou un lien YouTube dans web/assets/video_url.txt."))
    images = sorted(chemin for motif in FORMATS_IMAGE for chemin in ASSETS.glob(motif))
    if not images:
        afficher_html(bandeau("Déposez des captures d'écran (.png ou .jpg) dans web/assets/ : elles s'afficheront ici."))
        return
    colonnes = st.columns(2)
    for position, image in enumerate(images):
        colonnes[position % 2].image(str(image), caption=image.stem.replace("_", " "))


def _source_video() -> str | None:
    if VIDEO.exists():
        return str(VIDEO)
    if LIEN_VIDEO.exists():
        return LIEN_VIDEO.read_text(encoding="utf-8").strip() or None
    return None
