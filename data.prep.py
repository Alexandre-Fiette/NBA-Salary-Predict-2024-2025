import pandas as pd

# 1. Chargement des données
# On utilise 'sep' et 'encoding' car parfois les CSV venant du web sont capricieux
try:
    df_stats = pd.read_csv("stats.csv") # Vérifie si ton séparateur est , ou ;
    df_salary = pd.read_csv('salaries.csv')
except:
    # Si ça plante, essaie avec un autre encodage courant sur Excel
    df_stats = pd.read_csv('stats.csv', sep=',', encoding='latin-1')
    df_salary = pd.read_csv('salaries.csv', sep=',', encoding='latin-1')

print("--- Aperçu Brut ---")
print(f"Stats : {df_stats.shape} lignes")
print(f"Salaires : {df_salary.shape} lignes")

# 2. Identification des colonnes de Noms
# AFFICHE CECI POUR ME RÉPONDRE
print("\nCOLONNES STATS :", df_stats.columns.tolist())
print("COLONNES SALAIRES :", df_salary.columns.tolist())

# 3. Nettoyage préliminaire (Exemple classique)
# Souvent, dans les stats, il y a des lignes répétées pour les joueurs transférés (TOT, LAL, CLE...)
# On ne garde que la ligne 'TOT' (Total) si elle existe, ou la dernière équipe.

