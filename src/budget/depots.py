"""Dépôts de données : Depot (abstrait), DepotJson, DepotCsv.

Principe d'inversion de dépendance : le reste de l'application ne connaît que
l'abstraction Depot. Changer de format de fichier ne modifie aucune autre classe.

Les montants sont écrits en texte ("650.00") pour ne jamais passer par un float.
"""
import csv
import io
import json
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

from budget.constantes import (
    COLONNES_PLAFONDS,
    COLONNES_TRANSACTIONS,
    ENCODAGE_FICHIERS,
    FORMAT_DATE,
)
from budget.erreurs import BudgetError, FichierDonneesError
from budget.modeles import Budget, Transaction, TypeTransaction, lire_date


@dataclass(frozen=True)
class ResultatChargement:
    """Données lues, plus un message par enregistrement rejeté (jamais d'arrêt brutal)."""

    transactions: tuple[Transaction, ...] = ()
    budgets: tuple[Budget, ...] = ()
    erreurs: tuple[str, ...] = ()


class Depot(ABC):
    """Contrat commun à tous les formats de stockage."""

    @abstractmethod
    def charger(self) -> ResultatChargement:
        """Lit les données. Lève FichierDonneesError si le fichier est inutilisable."""

    @abstractmethod
    def sauvegarder(self, transactions: Iterable[Transaction], budgets: Iterable[Budget]) -> None:
        """Écrit les données. Lève FichierDonneesError si l'écriture échoue."""


# ---------- Conversion enregistrement <-> objet (partagée par JSON et CSV : DRY) ----------


def _transaction_depuis_enregistrement(enregistrement: Mapping) -> Transaction:
    return Transaction(
        montant=enregistrement.get("montant"),
        jour=lire_date(enregistrement.get("date")),
        categorie=enregistrement.get("categorie"),
        type=TypeTransaction.depuis_texte(enregistrement.get("type")),
        description=enregistrement.get("description") or "",
    )


def _budget_depuis_enregistrement(enregistrement: Mapping) -> Budget:
    return Budget(enregistrement.get("categorie"), enregistrement.get("plafond"))


def _enregistrement_transaction(transaction: Transaction) -> dict[str, str]:
    return {
        "date": transaction.jour.strftime(FORMAT_DATE),
        "type": transaction.type.value,
        "montant": str(transaction.montant),
        "categorie": transaction.categorie,
        "description": transaction.description,
    }


def _enregistrement_budget(budget: Budget) -> dict[str, str]:
    return {"categorie": budget.categorie, "plafond": str(budget.plafond)}


def _construire_objets(
    enregistrements: Iterable,
    construire: Callable[[Mapping], object],
    etiquette: str,
    premier_numero: int = 1,
) -> tuple[tuple, tuple[str, ...]]:
    """Construit un objet par enregistrement ; un enregistrement invalide donne un message."""
    objets, erreurs = [], []
    for numero, enregistrement in enumerate(enregistrements, start=premier_numero):
        try:
            if not isinstance(enregistrement, Mapping):
                raise FichierDonneesError("enregistrement mal formé")
            objets.append(construire(enregistrement))
        except BudgetError as erreur:
            erreurs.append(f"{etiquette} {numero} : {erreur}")
    return tuple(objets), tuple(erreurs)


# ---------- Accès aux fichiers (seul endroit qui touche au disque) ----------


def _lire_texte(chemin: Path) -> str:
    try:
        return chemin.read_text(encoding=ENCODAGE_FICHIERS)
    except FileNotFoundError as erreur:
        raise FichierDonneesError(f"Fichier introuvable : {chemin}") from erreur
    except (OSError, UnicodeDecodeError) as erreur:
        raise FichierDonneesError(f"Fichier illisible : {chemin}") from erreur


def _ecrire_texte(chemin: Path, texte: str) -> None:
    """Écrit via un fichier temporaire : une panne ne laisse jamais un fichier tronqué."""
    temporaire = chemin.with_name(chemin.name + ".tmp")
    try:
        chemin.parent.mkdir(parents=True, exist_ok=True)
        temporaire.write_text(texte, encoding=ENCODAGE_FICHIERS)
        temporaire.replace(chemin)
    except OSError as erreur:
        raise FichierDonneesError(f"Écriture impossible : {chemin}") from erreur


def _lire_csv(chemin: Path, colonnes: tuple[str, ...]) -> list[dict[str, str]]:
    try:
        lecteur = csv.DictReader(io.StringIO(_lire_texte(chemin)))
        manquantes = set(colonnes) - set(lecteur.fieldnames or ())
        if manquantes:
            noms = ", ".join(sorted(manquantes))
            raise FichierDonneesError(f"Colonnes manquantes dans {chemin.name} : {noms}")
        return list(lecteur)
    except csv.Error as erreur:
        raise FichierDonneesError(f"CSV corrompu : {chemin}") from erreur


def _ecrire_csv(chemin: Path, colonnes: tuple[str, ...], enregistrements: Iterable) -> None:
    sortie = io.StringIO()
    ecrivain = csv.DictWriter(sortie, fieldnames=colonnes, lineterminator="\n")
    ecrivain.writeheader()
    ecrivain.writerows(enregistrements)
    _ecrire_texte(chemin, sortie.getvalue())


# ---------- Dépôts concrets ----------


class DepotJson(Depot):
    """Un seul fichier JSON : {"transactions": [...], "plafonds": {catégorie: plafond}}.

    Le format est compatible avec celui de la V1 legacy.
    """

    def __init__(self, chemin: str | Path) -> None:
        self._chemin = Path(chemin)

    def charger(self) -> ResultatChargement:
        enregistrements, plafonds = self._lire_structure()
        transactions, erreurs = _construire_objets(
            enregistrements, _transaction_depuis_enregistrement, "Enregistrement"
        )
        lignes_plafonds = [{"categorie": c, "plafond": p} for c, p in plafonds.items()]
        budgets, erreurs_budgets = _construire_objets(
            lignes_plafonds, _budget_depuis_enregistrement, "Plafond"
        )
        return ResultatChargement(transactions, budgets, erreurs + erreurs_budgets)

    def sauvegarder(self, transactions: Iterable[Transaction], budgets: Iterable[Budget]) -> None:
        contenu = {
            "transactions": [_enregistrement_transaction(t) for t in transactions],
            "plafonds": {b.categorie: str(b.plafond) for b in budgets},
        }
        _ecrire_texte(self._chemin, json.dumps(contenu, ensure_ascii=False, indent=2))

    def _lire_structure(self) -> tuple[list, dict]:
        try:
            contenu = json.loads(_lire_texte(self._chemin))
        except json.JSONDecodeError as erreur:
            raise FichierDonneesError(f"JSON corrompu : {self._chemin}") from erreur
        enregistrements = contenu.get("transactions") if isinstance(contenu, dict) else None
        plafonds = contenu.get("plafonds", {}) if isinstance(contenu, dict) else None
        if not isinstance(enregistrements, list) or not isinstance(plafonds, dict):
            raise FichierDonneesError(f"Structure JSON inattendue : {self._chemin}")
        return enregistrements, plafonds


class DepotCsv(Depot):
    """Un CSV de transactions, et facultativement un CSV de plafonds (categorie,plafond).

    Les lignes invalides sont rejetées avec un message ; les autres sont conservées.
    """

    def __init__(
        self, chemin_transactions: str | Path, chemin_plafonds: str | Path | None = None
    ) -> None:
        self._chemin_transactions = Path(chemin_transactions)
        self._chemin_plafonds = Path(chemin_plafonds) if chemin_plafonds else None

    def charger(self) -> ResultatChargement:
        lignes = _lire_csv(self._chemin_transactions, COLONNES_TRANSACTIONS)
        # la ligne 1 du fichier est l'en-tête : les données commencent à la ligne 2
        transactions, erreurs = _construire_objets(
            lignes, _transaction_depuis_enregistrement, "Ligne", premier_numero=2
        )
        budgets, erreurs_budgets = self._charger_budgets()
        return ResultatChargement(transactions, budgets, erreurs + erreurs_budgets)

    def sauvegarder(self, transactions: Iterable[Transaction], budgets: Iterable[Budget]) -> None:
        enregistrements = (_enregistrement_transaction(t) for t in transactions)
        _ecrire_csv(self._chemin_transactions, COLONNES_TRANSACTIONS, enregistrements)
        if self._chemin_plafonds:
            plafonds = (_enregistrement_budget(b) for b in budgets)
            _ecrire_csv(self._chemin_plafonds, COLONNES_PLAFONDS, plafonds)

    def _charger_budgets(self) -> tuple[tuple[Budget, ...], tuple[str, ...]]:
        if self._chemin_plafonds is None:
            return (), ()
        lignes = _lire_csv(self._chemin_plafonds, COLONNES_PLAFONDS)
        return _construire_objets(
            lignes, _budget_depuis_enregistrement, "Plafond", premier_numero=2
        )
