"""Tests du Journal : ajout, filtres, encapsulation de la liste interne."""
from datetime import date

import pytest

from budget.journal import Journal
from budget.modeles import Transaction, TypeTransaction


def transaction(jour, categorie, type_transaction=TypeTransaction.DEPENSE, montant="10"):
    return Transaction(montant, jour, categorie, type_transaction)


@pytest.fixture
def journal():
    return Journal([
        transaction(date(2026, 10, 1), "Salaire", TypeTransaction.REVENU, "2200"),
        transaction(date(2026, 10, 3), "Alimentation"),
        transaction(date(2026, 10, 9), "Loisirs"),
        transaction(date(2026, 11, 2), "Alimentation"),
    ])


def test_ajout(journal):
    journal.ajouter(transaction(date(2026, 11, 5), "Transport"))
    assert len(journal) == 5


def test_ajout_refuse_un_objet_qui_n_est_pas_une_transaction(journal):
    with pytest.raises(TypeError):
        journal.ajouter({"montant": 10})


def test_filtre_par_mois(journal):
    assert len(journal.filtrer(mois="2026-10")) == 3


def test_filtre_par_categorie(journal):
    assert len(journal.filtrer(categorie="Alimentation")) == 2


def test_filtres_combines(journal):
    resultat = journal.filtrer(mois="2026-10", categorie="Alimentation")
    assert [t.jour for t in resultat] == [date(2026, 10, 3)]


def test_depenses_et_revenus_du_mois(journal):
    assert len(journal.depenses_du_mois("2026-10")) == 2
    assert len(journal.revenus_du_mois("2026-10")) == 1


def test_mois_vide(journal):
    assert journal.filtrer(mois="2027-01") == ()


def test_liste_interne_non_modifiable_de_l_exterieur(journal):
    copie = journal.transactions
    assert isinstance(copie, tuple)
    with pytest.raises(AttributeError):
        copie.append(transaction(date(2026, 10, 1), "Piratage"))
    assert len(journal) == 4


def test_iteration(journal):
    assert len(list(journal)) == 4
