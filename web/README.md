# Interface web

Interface Streamlit au-dessus de la même `Application` que la ligne de commande : visite guidée,
tableau de bord, saisie avec validation, simulateur d'alertes, import de CSV, architecture.

```bash
pip install -r web/requirements.txt
pip install -e .
streamlit run web/app.py
```

Tests de l'interface (sans navigateur) : `python -m pytest web`.

Chaque visiteur a ses propres données, en mémoire : rien n'est partagé et rien n'est conservé
après la fermeture. Le bouton « Sauvegarde JSON » permet de les emporter.
