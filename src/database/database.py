"""
Configuration de la base de données
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import os

# Obtenir le chemin absolu du répertoire racine du projet
project_root = Path(__file__).parent.parent.parent

# Création du dossier data s'il n'existe pas
data_dir = project_root / "data"
data_dir.mkdir(exist_ok=True)

# Création de la base de données SQLite
SQLALCHEMY_DATABASE_URL = f"sqlite:///{data_dir}/cv_analyzer.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Session pour interagir avec la base de données
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour les modèles
Base = declarative_base()

def get_db():
    """Fonction utilitaire pour obtenir une session de base de données"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
