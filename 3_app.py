# 3_app.py
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import joblib
import google.generativeai as genai
from google.api_core import exceptions # Important: Assurez-vous que cet import est présent

# --- CONFIGURATION DE LA CLÉ API GEMINI ---
VOTRE_CLE_GEMINI_API = "AIzaSyAe1RlVGEe5fvHbJrfHpNKUsfhBfMtu_uM" # <-- METTEZ VOTRE CLÉ API ICI

if not VOTRE_CLE_GEMINI_API or "AIzaSy" not in VOTRE_CLE_GEMINI_API:
    print("❌ ERREUR: Votre clé API Gemini semble incorrecte ou manquante.")
    exit()

genai.configure(api_key=VOTRE_CLE_GEMINI_API)
# On utilise gemini-1.0-pro, qui a souvent un quota séparé et est très stable.
gemini_model = genai.GenerativeModel('gemini-1.0-pro')

print("\nÉtape 3: Démarrage du serveur Flask (API)...")
app = Flask(__name__)
CORS(app) 

# --- PARTIE 1 : CHARGEMENT DES DONNÉES ET MODÈLE ---
try:
    model = joblib.load('models/thonia_model.joblib')
    daily_df = pd.read_csv('data/daily_data.csv')
    print("✅ Données du jour (daily_data.csv) chargées.")
except FileNotFoundError:
    print("❌ ERREUR: Fichiers de données ou de modèle non trouvés. Lancez 'data_pipeline.py'.")
    exit()

# --- PARTIE 2 : PRÉDICTIONS POUR LA CARTE ---
@app.route('/api/predictions', methods=['GET'])
def get_predictions():
    # ... (cette partie est inchangée et correcte)
    features_for_prediction = daily_df[['latitude', 'longitude', 'temp_surface_c', 'chlorophylle_mg_m3', 'vent_noeuds']]
    predictions_proba = model.predict_proba(features_for_prediction)[:, 1]
    results = []
    for index, row in daily_df.iterrows():
        results.append({
            'lat': row['latitude'], 'lon': row['longitude'],
            'prediction_score': round(float(predictions_proba[index]), 2),
            'details': { 'Température': f"{row['temp_surface_c']:.1f}°C", 'Vent': f"{row['vent_noeuds']:.0f} noeuds" }
        })
    return jsonify(results)

# --- PARTIE 3 : CHATBOT PROPULSÉ PAR GEMINI ---
@app.route('/api/chat', methods=['POST'])
def chat_with_ia():
    user_message = request.json.get('message')
    if not user_message: 
        return jsonify({"error": "Message manquant"}), 400

    # Le prompt est créé AVANT le bloc try
    avg_temp = daily_df['temp_surface_c'].mean()
    avg_wind = daily_df['vent_noeuds'].mean()
    
    full_prompt = (
        "Contexte : Tu es ThonIA, un expert de la pêche au thon dans le Golfe de Gascogne. "
        "Tu es amical, concis et précis. Tes réponses doivent aider les pêcheurs. "
        "Utilise des emojis liés à la mer 🎣🐟🌊☀️. "
        f"Les conditions réelles aujourd'hui sont : température moyenne de l'eau de {avg_temp:.1f}°C et vent moyen de {avg_wind:.0f} noeuds. "
        "Les zones les plus prometteuses sont visibles en rouge/orange sur la carte de l'utilisateur. "
        f"Question de l'utilisateur : \"{user_message}\"\n\n"
        "Ta réponse :"
    )

    try:
        response = gemini_model.generate_content(full_prompt)
        bot_response = response.text
        return jsonify({"reply": bot_response})
        
    except exceptions.ResourceExhausted as e:
        print(f"Quota Gemini dépassé: {e}")
        return jsonify({"reply": "Désolé, ThonIA est très demandé en ce moment ! 😅 Veuillez réessayer dans une minute."}), 429

    except Exception as e:
        print(f"Erreur lors de l'appel à l'API Gemini: {e}")
        return jsonify({"reply": "Désolé, une erreur est survenue avec l'assistant IA."}), 500

if __name__ == '__main__':
    print("✅ Serveur démarré avec le modèle Gemini.")
    app.run(debug=True, port=5000)