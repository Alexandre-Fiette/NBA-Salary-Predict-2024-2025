import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor

# 1. Chargement
try:
    df = pd.read_csv('nba_final.csv')
except:
    print("❌ ERREUR : Lance d'abord data_prep.py pour avoir nba_final.csv")
    exit()

# 2. Features (EXACTEMENT 9 VARIABLES - Pas de 'MP')
features = ['Age', 'G', 'PTS', 'TRB', 'AST', 'STL', 'BLK', 'FG%', '3P%']
target = 'Salary'

X = df[features].fillna(0)
y = df[target]

# 3. Entraînement
print(f"🏀 Entraînement sur {X.shape[1]} variables...")
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)

# 4. Sauvegarde
df['Predicted_Salary'] = model.predict(X)
df['Difference'] = df['Predicted_Salary'] - df['Salary']

df.to_csv('nba_predictions.csv', index=False)
joblib.dump(model, 'nba_model.pkl')

print("✅ SUCCÈS : Modèle à 9 variables sauvegardé sous 'nba_model.pkl'")