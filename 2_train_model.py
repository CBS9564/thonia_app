# 2_train_model.py
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import os

print("\nÉtape 2: Entraînement du modèle IA en cours...")

try:
    df = pd.read_csv('data/dataset.csv')
except FileNotFoundError:
    print("❌ Erreur: Le fichier 'data/dataset.csv' n'a pas été trouvé. Lancez '1_simulate_data.py' d'abord.")
    exit()

features = ['latitude', 'longitude', 'temp_surface_c', 'chlorophylle_mg_m3', 'vent_noeuds']
target = 'thon_present'

X = df[features]
y = df[target]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = xgb.XGBClassifier(objective='binary:logistic', use_label_encoder=False, eval_metric='logloss')
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Performance du modèle (Accuracy) : {accuracy:.2f}")

if not os.path.exists('models'):
    os.makedirs('models')
    
model_path = 'models/thonia_model.joblib'
joblib.dump(model, model_path)

print(f"✅ Modèle IA entraîné et sauvegardé dans '{model_path}'.")