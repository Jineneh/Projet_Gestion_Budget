"""Tests de l'interface web avec le simulateur de Streamlit (aucun navigateur nécessaire).

Lancer :  python -m pytest web
"""

from pathlib import Path

from streamlit.testing.v1 import AppTest

APPLICATION = str(Path(__file__).resolve().parent / "app.py")


def demarrer() -> AppTest:
    test = AppTest.from_file(APPLICATION, default_timeout=30)
    test.run()
    return test


def aller_a(test: AppTest, page: str) -> AppTest:
    test.radio(key="page").set_value(page).run()
    return test


def charger_exemple() -> AppTest:
    test = aller_a(demarrer(), "Données")
    test.button(key="bouton_exemple").click().run()
    return test


def textes(test: AppTest) -> str:
    return "\n".join(element.value for element in test.markdown)


def test_l_application_demarre_sans_erreur():
    test = demarrer()
    assert not test.exception
    assert "Gestion de budget personnel" in textes(test)
    assert "Votre budget commence ici" in textes(test)


def test_aucun_emoji_dans_l_interface():
    test = charger_exemple()
    for page in ("Tableau de bord", "Transactions", "Plafonds", "Rapport", "Données", "Guide"):
        contenu = textes(aller_a(test, page))
        assert not any(ord(caractere) > 0x2FFF for caractere in contenu), page


def test_donnees_d_exemple_donnent_les_memes_chiffres_que_la_cli():
    test = charger_exemple()
    assert not test.exception
    assert test.selectbox(key="mois").value == "2026-10"
    contenu = textes(aller_a(test, "Tableau de bord"))
    assert "Octobre 2026" in contenu
    assert "2 320,00 €" in contenu
    assert "1 199,99 €" in contenu
    assert "1 120,01 €" in contenu


def test_alertes_du_tableau_de_bord():
    contenu = textes(aller_a(charger_exemple(), "Tableau de bord"))
    assert "Plafond dépassé</b> : Loisirs" in contenu
    assert "Attention</b> : Alimentation" in contenu
    assert "p-attention" in contenu
    assert "p-depassement" in contenu
    assert "p-ok" in contenu


def test_rapport_identique_a_celui_de_la_cli():
    contenu = textes(aller_a(charger_exemple(), "Rapport"))
    assert "Solde    : 1120.01 EUR" in contenu
    assert "!!! Loisirs : plafond dépassé" in contenu


def saisir_transaction(test: AppTest, montant: str, categorie: str) -> AppTest:
    test.text_input(key="montant_saisie").set_value(montant)
    test.text_input(key="categorie_saisie").set_value(categorie)
    test.button(key="envoyer_transaction").click().run()
    return test


def test_saisie_invalide_est_refusee_avec_un_message():
    contenu = textes(saisir_transaction(aller_a(demarrer(), "Transactions"), "abc", "Transport"))
    assert "Saisie refusée" in contenu
    assert "Montant non numérique" in contenu


def test_categorie_vide_est_refusee():
    contenu = textes(saisir_transaction(aller_a(demarrer(), "Transactions"), "10", "  "))
    assert "Saisie refusée" in contenu
    assert "catégorie" in contenu


def test_saisie_valide_avec_virgule_decimale():
    test = saisir_transaction(aller_a(demarrer(), "Transactions"), "12,5", "Transport")
    assert "Transaction ajoutée</b> : Transport, 12,50 €" in textes(test)


def test_une_saisie_html_est_neutralisee():
    test = saisir_transaction(aller_a(demarrer(), "Transactions"), "5", "<script>alert(1)</script>")
    contenu = textes(aller_a(test, "Transactions"))
    assert "<script>" not in contenu
    assert "&lt;script&gt;" in contenu


def test_definir_un_plafond():
    test = aller_a(demarrer(), "Plafonds")
    test.text_input(key="categorie_plafond").set_value("Loisirs")
    test.text_input(key="montant_plafond").set_value("100")
    test.button(key="envoyer_plafond").click().run()
    assert "Plafond enregistré</b> : 100,00 € par mois pour Loisirs" in textes(test)


def test_simulateur_aux_valeurs_limites():
    test = aller_a(demarrer(), "Plafonds")
    attendu = {
        0: "Aucune dépense",
        79: "Dans le budget",
        80: "Attention",
        100: "Attention",
        101: "Dépassement",
    }
    for depense, libelle in attendu.items():
        test.slider(key="depense_simulee").set_value(depense).run()
        assert libelle in textes(test), depense


def test_import_d_un_fichier_invalide_signale_les_lignes_rejetees():
    test = aller_a(demarrer(), "Données")
    test.button(key="bouton_invalide").click().run()
    contenu = textes(test)
    assert "2 transaction(s)" in contenu
    assert "5 ligne(s) rejetée(s)" in contenu
    assert "Lignes rejetées" in contenu


def test_reinitialiser_efface_les_donnees():
    test = charger_exemple()
    test.button(key="bouton_reinitialiser").click().run()
    assert not test.exception
    assert "Votre budget commence ici" in textes(aller_a(test, "Tableau de bord"))


def test_guide_ouvre_la_page_de_l_etape():
    test = aller_a(demarrer(), "Guide")
    test.button(key="guide_2").click().run()
    assert test.radio(key="page").value == "Tableau de bord"


def test_page_architecture_s_affiche():
    assert not aller_a(demarrer(), "Architecture").exception
