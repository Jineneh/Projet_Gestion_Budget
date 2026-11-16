"""Tests des politiques d'alerte, chacune isolément."""
from decimal import Decimal

import pytest

from budget.alertes import (
    NiveauAlerte,
    PolitiqueAlerte,
    PolitiqueDepassement,
    PolitiqueSeuil,
    politiques_par_defaut,
)


@pytest.mark.parametrize(
    ("pourcentage", "attendu"),
    [("79", None), ("80", NiveauAlerte.ATTENTION), ("100", NiveauAlerte.ATTENTION),
     ("150", NiveauAlerte.ATTENTION)],
)
def test_politique_seuil(pourcentage, attendu):
    assert PolitiqueSeuil().evaluer(Decimal(pourcentage)) == attendu


@pytest.mark.parametrize(
    ("pourcentage", "attendu"),
    [("80", None), ("100", None), ("100.01", NiveauAlerte.DEPASSEMENT),
     ("101", NiveauAlerte.DEPASSEMENT)],
)
def test_politique_depassement(pourcentage, attendu):
    assert PolitiqueDepassement().evaluer(Decimal(pourcentage)) == attendu


def test_politique_alerte_est_abstraite():
    with pytest.raises(TypeError):
        PolitiqueAlerte()


def test_politiques_par_defaut_de_la_plus_grave_a_la_moins_grave():
    types = [type(politique) for politique in politiques_par_defaut()]
    assert types == [PolitiqueDepassement, PolitiqueSeuil]
