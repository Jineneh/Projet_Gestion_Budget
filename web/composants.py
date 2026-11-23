"""Composants visuels (HTML et SVG générés en Python) : panneaux, donuts, barres, tableaux.

Ce module ne contient que de la présentation. Tout texte venant de l'utilisateur doit passer par
echapper() avant d'être inséré dans du HTML.
"""

import html
import math
from collections.abc import Iterable, Sequence

PALETTE = ("#E39BB2", "#C9A3B8", "#F0B8A4", "#B79AC7", "#E9C0CC", "#D2A0A0", "#C4B0D8", "#EBCDBE")
COULEUR_FOND_DONUT = "#F3DDE2"


def echapper(texte: object) -> str:
    """Neutralise le HTML d'un texte saisi par l'utilisateur."""
    return html.escape(str(texte))


def carte_titre(titre: str, sous_titre: str) -> str:
    return f'<div class="titre-carte"><h1>{echapper(titre)}</h1><p>{echapper(sous_titre)}</p></div>'


def panneau(titre: str, corps: str, teinte: str = "rose", hauteur: float | None = None) -> str:
    style = f' style="min-height:{hauteur}rem"' if hauteur else ""
    return (
        f'<div class="panneau teinte-{teinte}"{style}><div class="panneau-entete">{echapper(titre)}</div>'
        f'<div class="panneau-corps">{corps}</div></div>'
    )


def entete(titre: str) -> str:
    """Bandeau de titre pour un panneau qui contient des widgets Streamlit."""
    return f'<div class="panneau-entete">{echapper(titre)}</div>'


def bandeau(message_html: str, rouge: bool = False, vert: bool = False) -> str:
    classe = "bandeau rouge" if rouge else "bandeau vert" if vert else "bandeau"
    return f'<div class="{classe}">{message_html}</div>'


def indicateur(libelle: str, valeur: str, note: str = "") -> str:
    note_html = f'<div class="note">{echapper(note)}</div>' if note else ""
    return (
        f'<div class="indicateur"><div class="libelle">{echapper(libelle)}</div>'
        f'<div class="valeur">{echapper(valeur)}</div>{note_html}</div>'
    )


def donut(segments: Sequence[tuple[float, str]], centre: str, sous_centre: str = "", taille: int = 200) -> str:
    """Anneau SVG. Chaque segment est (valeur, couleur) ; un total nul donne un anneau vide."""
    epaisseur = taille * 0.13
    rayon = (taille - epaisseur) / 2
    milieu = taille / 2
    circonference = 2 * math.pi * rayon
    total = sum(valeur for valeur, _ in segments)
    arcs = [_cercle(milieu, rayon, epaisseur, COULEUR_FOND_DONUT, circonference, 0)]
    decalage = 0.0
    for valeur, couleur in segments:
        if total > 0 and valeur > 0:
            longueur = circonference * valeur / total
            arcs.append(_cercle(milieu, rayon, epaisseur, couleur, longueur, decalage, circonference))
            decalage += longueur
    texte_centre = (
        f'<text x="{milieu}" y="{milieu - 2}" text-anchor="middle" '
        f'style="font-family:var(--serif);font-size:{taille * 0.125:.0f}px;font-weight:600" '
        f'fill="#2A1F24">{echapper(centre)}</text>'
    )
    texte_sous = (
        f'<text x="{milieu}" y="{milieu + taille * 0.1:.0f}" text-anchor="middle" '
        f'style="font-size:{taille * 0.052:.0f}px;letter-spacing:.12em" fill="#5B4A52">'
        f"{echapper(sous_centre.upper())}</text>"
    )
    return (
        f'<div class="centre"><svg viewBox="0 0 {taille} {taille}" width="{taille}" height="{taille}" '
        f'role="img" aria-label="{echapper(centre)} {echapper(sous_centre)}">'
        f"{''.join(arcs)}{texte_centre}{texte_sous}</svg></div>"
    )


def _cercle(milieu, rayon, epaisseur, couleur, longueur, decalage, circonference=None) -> str:
    reste = (circonference or longueur) - longueur
    return (
        f'<circle cx="{milieu}" cy="{milieu}" r="{rayon:.2f}" fill="none" stroke="{couleur}" '
        f'stroke-width="{epaisseur:.2f}" stroke-dasharray="{longueur:.2f} {reste:.2f}" '
        f'stroke-dashoffset="{-decalage:.2f}" transform="rotate(-90 {milieu} {milieu})"/>'
    )


def legende(lignes: Iterable[tuple[str, str, str]]) -> str:
    """Liste (couleur, libellé, valeur) à placer sous un donut."""
    items = "".join(
        f'<li><span><span class="pt" style="background:{couleur}"></span>{echapper(libelle)}</span>'
        f"<span>{echapper(valeur)}</span></li>"
        for couleur, libelle, valeur in lignes
    )
    return f'<ul class="legende">{items}</ul>'


def barres_comparees(lignes: Sequence[tuple[str, float, float | None, str]]) -> str:
    """Barres plafond / dépensé par catégorie : (catégorie, dépensé, plafond ou None, couleur)."""
    maximum = max((max(depense, plafond or 0) for _, depense, plafond, _ in lignes), default=0) or 1
    cle = '<div class="cle"><span>&#9632; Plafond</span><span style="color:#B5527A">&#9632; Dépensé</span></div>'
    return f'<div class="barres">{cle}{"".join(_ligne_barres(ligne, maximum) for ligne in lignes)}</div>'


def _ligne_barres(ligne, maximum: float) -> str:
    categorie, depense, plafond, couleur = ligne
    piste_plafond = ""
    if plafond is not None:
        largeur = 100 * plafond / maximum
        piste_plafond = f'<div class="piste"><div class="remplie" style="width:{largeur:.1f}%;background:#E4C3CD"></div></div>'
    largeur_depense = 100 * depense / maximum
    return (
        f'<div class="ligne"><div class="nom"><span>{echapper(categorie)}</span></div>{piste_plafond}'
        f'<div class="piste"><div class="remplie" style="width:{largeur_depense:.1f}%;background:{couleur}"></div></div></div>'
    )


def tableau(
    entetes: Sequence[str],
    lignes: Sequence[Sequence[str]],
    colonnes_numeriques: Sequence[int] = (),
    ligne_total: Sequence[str] | None = None,
    defile: bool = False,
) -> str:
    """Tableau de suivi. Les cellules sont du HTML déjà sûr (utiliser echapper pour les saisies)."""
    tete = "".join(f'<th class="{_classe(i, colonnes_numeriques)}">{echapper(e)}</th>' for i, e in enumerate(entetes))
    corps = "".join(_ligne(cellules, colonnes_numeriques) for cellules in lignes)
    total = _ligne(ligne_total, colonnes_numeriques, "total") if ligne_total else ""
    enveloppe = "defile" if defile else ""
    return (
        f'<div class="{enveloppe}"><table class="suivi"><thead><tr>{tete}</tr></thead><tbody>{corps}{total}</tbody></table></div>'
    )


def _classe(position: int, colonnes_numeriques: Sequence[int]) -> str:
    return "num" if position in colonnes_numeriques else ""


def _ligne(cellules: Sequence[str], colonnes_numeriques: Sequence[int], classe: str = "") -> str:
    tds = "".join(f'<td class="{_classe(i, colonnes_numeriques)}">{c}</td>' for i, c in enumerate(cellules))
    return f'<tr class="{classe}">{tds}</tr>'


def jauge(pourcentage: float, couleur: str) -> str:
    largeur = max(0.0, min(pourcentage, 100.0))
    return f'<div class="jauge"><div style="width:{largeur:.0f}%;background:{couleur}"></div></div>'
