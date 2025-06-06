# check_models.py
import google.generativeai as genai

# Mettez votre clé API Gemini ici
VOTRE_CLE_GEMINI_API = "xxx" # <-- METTEZ VOTRE CLÉ API

if "AIzaSy" not in VOTRE_CLE_GEMINI_API:
    print("❌ Veuillez insérer votre clé API Gemini dans le script.")
    exit()

try:
    genai.configure(api_key=VOTRE_CLE_GEMINI_API)

    print("🔎 Recherche des modèles disponibles pour votre clé API...")
    print("-----------------------------------------------------")
    
    # On boucle sur tous les modèles et on affiche ceux qui supportent "generateContent"
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ Modèle trouvé : {m.name}")

    print("-----------------------------------------------------")
    print("=> Copiez l'un des noms de modèle ci-dessus (ex: 'models/gemini-1.0-pro') et utilisez-le dans 3_app.py.")

except Exception as e:
    print(f"Une erreur est survenue: {e}")
