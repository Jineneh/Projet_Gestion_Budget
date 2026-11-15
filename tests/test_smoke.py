"""Test de fumée : le paquet s'importe (garde la CI verte avant l'arrivée du code)."""
import budget


def test_le_paquet_s_importe():
    assert budget.__doc__
