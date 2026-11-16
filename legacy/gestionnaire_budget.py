"""Version 1 « legacy » : une seule classe qui fait tout.

ATTENTION : ce code est VOLONTAIREMENT mal organisé. Il fonctionne, mais il contient
les trois défauts corrigés dans src/budget/ et présentés en soutenance :

1. SRP : GestionnaireBudget calcule, affiche ET lit/écrit les fichiers.
2. Open/Closed : un if/elif géant décide du niveau d'alerte.
3. DRY + nombres magiques : la validation du montant est copiée trois fois,
   0.8 et 1.0 sont écrits en dur.

Ne pas corriger ce fichier : il sert de point de départ aux exemples « avant / après ».
"""
import csv
import json
from datetime import datetime


class GestionnaireBudget:
    def __init__(self):
        self.transactions = []
        self.plafonds = {}

    # ---- Ajout des données (validation copiée 3 fois : défaut DRY) ----

    def ajouter_revenu(self, montant, date, categorie, description=""):
        if not isinstance(montant, (int, float)) or montant <= 0:
            raise ValueError("Le montant doit être un nombre strictement positif")
        if not categorie or not categorie.strip():
            raise ValueError("La catégorie ne peut pas être vide")
        datetime.strptime(date, "%Y-%m-%d")
        self.transactions.append(
            {"date": date, "type": "revenu", "montant": float(montant),
             "categorie": categorie.strip(), "description": description}
        )

    def ajouter_depense(self, montant, date, categorie, description=""):
        if not isinstance(montant, (int, float)) or montant <= 0:
            raise ValueError("Le montant doit être un nombre strictement positif")
        if not categorie or not categorie.strip():
            raise ValueError("La catégorie ne peut pas être vide")
        datetime.strptime(date, "%Y-%m-%d")
        self.transactions.append(
            {"date": date, "type": "depense", "montant": float(montant),
             "categorie": categorie.strip(), "description": description}
        )

    def definir_plafond(self, categorie, montant):
        if not isinstance(montant, (int, float)) or montant <= 0:
            raise ValueError("Le montant doit être un nombre strictement positif")
        if not categorie or not categorie.strip():
            raise ValueError("La catégorie ne peut pas être vide")
        self.plafonds[categorie.strip()] = float(montant)

    # ---- Calculs ----

    def total_depenses_categorie(self, categorie, mois):
        total = 0
        for t in self.transactions:
            if t["type"] == "depense" and t["categorie"] == categorie and t["date"][:7] == mois:
                total += t["montant"]
        return total

    def solde(self, mois):
        s = 0
        for t in self.transactions:
            if t["date"][:7] == mois:
                if t["type"] == "revenu":
                    s += t["montant"]
                else:
                    s -= t["montant"]
        return round(s, 2)

    # ---- Alertes : if/elif géant + nombres magiques (défauts Open/Closed et constantes) ----

    def calculer_alertes(self, mois):
        alertes = {}
        for categorie in self.plafonds:
            depense = self.total_depenses_categorie(categorie, mois)
            plafond = self.plafonds[categorie]
            ratio = depense / plafond
            if ratio > 1.0:
                alertes[categorie] = "DEPASSEMENT"
            elif ratio >= 0.8:
                alertes[categorie] = "ATTENTION"
            elif ratio > 0:
                alertes[categorie] = "OK"
            else:
                alertes[categorie] = "AUCUNE_DEPENSE"
        return alertes

    # ---- Affichage mélangé au calcul (défaut SRP) ----

    def afficher_rapport(self, mois):
        revenus = 0
        depenses = 0
        par_categorie = {}
        for t in self.transactions:
            if t["date"][:7] == mois:
                if t["type"] == "revenu":
                    revenus += t["montant"]
                else:
                    depenses += t["montant"]
                    if t["categorie"] not in par_categorie:
                        par_categorie[t["categorie"]] = 0
                    par_categorie[t["categorie"]] += t["montant"]
        print("===== Rapport " + mois + " =====")
        print("Revenus  : " + str(round(revenus, 2)) + " EUR")
        print("Dépenses : " + str(round(depenses, 2)) + " EUR")
        print("Solde    : " + str(round(revenus - depenses, 2)) + " EUR")
        for c in par_categorie:
            print("  - " + c + " : " + str(round(par_categorie[c], 2)) + " EUR")
        alertes = self.calculer_alertes(mois)
        for c in alertes:
            if alertes[c] == "DEPASSEMENT":
                print("!!! " + c + " : plafond dépassé")
            elif alertes[c] == "ATTENTION":
                print("! " + c + " : plus de 80% du plafond")

    # ---- Fichiers mélangés au métier (défaut SRP) ----

    def sauvegarder(self, chemin):
        with open(chemin, "w", encoding="utf-8") as f:
            json.dump({"transactions": self.transactions, "plafonds": self.plafonds}, f)

    def charger(self, chemin):
        with open(chemin, encoding="utf-8") as f:
            data = json.load(f)
        self.transactions = data["transactions"]
        self.plafonds = data["plafonds"]

    def importer_csv(self, chemin):
        erreurs = []
        with open(chemin, encoding="utf-8") as f:
            for numero, ligne in enumerate(csv.DictReader(f), start=2):
                try:
                    montant = float(ligne["montant"])
                    if ligne["type"] == "revenu":
                        self.ajouter_revenu(montant, ligne["date"], ligne["categorie"],
                                            ligne["description"])
                    elif ligne["type"] == "depense":
                        self.ajouter_depense(montant, ligne["date"], ligne["categorie"],
                                             ligne["description"])
                    else:
                        raise ValueError("Type inconnu : " + ligne["type"])
                except ValueError as e:
                    erreurs.append("Ligne " + str(numero) + " : " + str(e))
        return erreurs


def main():
    g = GestionnaireBudget()
    g.importer_csv("data/exemple_transactions.csv")
    g.definir_plafond("Alimentation", 350)
    g.definir_plafond("Loisirs", 100)
    g.definir_plafond("Transport", 150)
    g.afficher_rapport("2026-10")


if __name__ == "__main__":
    main()
