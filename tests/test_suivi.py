"""Tests de SuiviBudget : valeurs limites, revenus ignorés, extension Open/Closed."""
from datetime import date
from decimal import Decimal

import pytest

from budget.alertes import NiveauAlerte, PolitiqueAlerte
from budget.journal import Journal
from budget.modeles import Budget, Transaction, TypeTransaction
from budget.suivi import SuiviBudget

MOIS = "2026-10"
JOUR = date(2026, 10, 10)


def depense(montant, categorie="Loisirs", jour=JOUR):
    return Transaction(montant, jour, categorie, TypeTransaction.DEPENSE)


def suivi_loisirs(*transactions):
    return SuiviBudget(Journal(transactions), [Budget("Loisirs", 100)])


@pytest.mark.parametrize(
    ("montant", "attendu"),
    [(79, NiveauAlerte.OK), (80, NiveauAlerte.ATTENTION), (100, NiveauAlerte.ATTENTION),
     (101, NiveauAlerte.DEPASSEMENT)],
)
def test_niveau_aux_valeurs_limites(montant, attendu):
    assert suivi_loisirs(depense(montant)).niveau(MOIS, "Loisirs") is attendu


def test_aucune_depense():
    assert suivi_loisirs().niveau(MOIS, "Loisirs") is NiveauAlerte.AUCUNE_DEPENSE


def test_les_revenus_sont_ignores():
    revenu = Transaction("500", JOUR, "Loisirs", TypeTransaction.REVENU)
    assert suivi_loisirs(revenu).niveau(MOIS, "Loisirs") is NiveauAlerte.AUCUNE_DEPENSE


def test_les_depenses_d_un_autre_mois_sont_ignorees():
    suivi = suivi_loisirs(depense(500, jour=date(2026, 11, 1)))
    assert suivi.niveau(MOIS, "Loisirs") is NiveauAlerte.AUCUNE_DEPENSE


def test_plusieurs_depenses_s_additionnent():
    suivi = suivi_loisirs(depense(50), depense(35))
    assert suivi.depenses_categorie(MOIS, "Loisirs") == Decimal("85.00")
    assert suivi.niveau(MOIS, "Loisirs") is NiveauAlerte.ATTENTION


def test_un_nouveau_plafond_remplace_l_ancien():
    suivi = suivi_loisirs(depense(90))
    suivi.definir_budget(Budget("Loisirs", 200))
    assert len(suivi.budgets) == 1
    assert suivi.niveau(MOIS, "Loisirs") is NiveauAlerte.OK


def test_alertes_seulement_pour_les_categories_budgetees():
    suivi = suivi_loisirs(depense(120), depense(500, categorie="Logement"))
    assert suivi.alertes(MOIS) == {"Loisirs": NiveauAlerte.DEPASSEMENT}


def test_categorie_sans_budget_refusee():
    with pytest.raises(KeyError):
        suivi_loisirs().niveau(MOIS, "Logement")


def test_open_closed_nouvelle_politique_sans_modifier_le_code():
    """On ajoute une règle en écrivant une classe, sans toucher à SuiviBudget."""

    class PolitiqueToujoursAttention(PolitiqueAlerte):
        def evaluer(self, pourcentage):
            return NiveauAlerte.ATTENTION

    suivi = SuiviBudget(
        Journal([depense(1)]), [Budget("Loisirs", 100)], [PolitiqueToujoursAttention()]
    )
    assert suivi.niveau(MOIS, "Loisirs") is NiveauAlerte.ATTENTION
