"""
Script pour démarrer le backend FastAPI
"""
import uvicorn
import os
import sys

# Ajouter le répertoire racine au chemin Python pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Initialiser la base de données
from src.database.init_db import init_database

if __name__ == "__main__":
    # S'assurer que la base de données est initialisée
    init_database()
    
    # Démarrer le serveur FastAPI
    print("Démarrage du serveur API sur http://127.0.0.1:8000...")
    uvicorn.run("src.services.api:app", host="127.0.0.1", port=8000, reload=True)
