import pandas as pd

# 1. Chargement
# On utilise engine='python' pour éviter les erreurs de format bizarres
df_stats = pd.read_csv('stats.csv', encoding='latin-1', sep=None, engine='python')
df_salary = pd.read_csv('salaries.csv', encoding='latin-1', sep=None, engine='python')

print(f"Charge : Stats ({len(df_stats)}) | Salaires ({len(df_salary)})")

# ---------------------------------------------------------
# ETAPE 2 : NETTOYAGE DES DOUBLONS (TRÈS IMPORTANT)
# ---------------------------------------------------------
# Comme tu as 735 lignes de stats, tu as des doublons (joueurs transférés).
# On ne garde que la première occurrence (souvent c'est la ligne 'TOT' ou la dernière équipe)
# Cela évite d'avoir 3 fois le même joueur dans la base finale.
df_stats = df_stats.drop_duplicates(subset=['Player'], keep='first')
print(f"Stats après dédoublonnage : {len(df_stats)} joueurs uniques.")

# ---------------------------------------------------------
# ETAPE 3 : NETTOYAGE DES SALAIRES
# ---------------------------------------------------------
# On enlève les '$' et ',' pour en faire des nombres
if df_salary['Salary'].dtype == 'object':
    df_salary['Salary'] = df_salary['Salary'].astype(str).str.replace('$', '', regex=False)
    df_salary['Salary'] = df_salary['Salary'].str.replace(',', '', regex=False)
    df_salary['Salary'] = pd.to_numeric(df_salary['Salary'], errors='coerce')

# ---------------------------------------------------------
# ETAPE 4 : LA FUSION (INNER JOIN)
# ---------------------------------------------------------
# On merge sur 'Player'. 
# Si on a 'Team' dans les deux, Pandas va créer Team_x et Team_y.
# On garde juste les colonnes utiles de stats + le salaire.

# Liste des colonnes qu'on veut garder des stats
cols_to_keep = ['Player', 'Age', 'Pos', 'G', 'MP', 'PTS', 'TRB', 'AST', 'STL', 'BLK', 'FG%', '3P%']

# Petite sécurité si tes colonnes s'appellent différemment (ex: TRB vs REB)
# On prend l'intersection des colonnes existantes
existing_cols = [c for c in cols_to_keep if c in df_stats.columns]
df_stats_clean = df_stats[existing_cols]

# MERGE
df_final = pd.merge(df_stats_clean, df_salary[['Player', 'Salary']], on='Player', how='inner')

# ---------------------------------------------------------
# ETAPE 5 : SAUVEGARDE
# ---------------------------------------------------------
# On supprime les lignes où le salaire serait vide (par sécurité)
df_final = df_final.dropna(subset=['Salary'])

print("-" * 30)
print(f"✅ DATASET PRÊT : {len(df_final)} joueurs fusionnés.")
print("-" * 30)
print(df_final.head())

df_final.to_csv('nba_final.csv', index=False)