from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pathlib import Path
import sys
import os

# Déterminer le dossier racine de l'application
# En mode PyInstaller, sys._MEIPASS existe et __file__ est dans un temp folder
# En mode dev, on utilise le chemin relatif normal
if getattr(sys, 'frozen', False):
    # Mode PyInstaller - utiliser le dossier de l'exe
    app_dir = Path(os.path.dirname(sys.executable))
else:
    # Mode développement
    app_dir = Path(__file__).parent.parent.parent

# Création du dossier data s'il n'existe pas
data_dir = app_dir / "data"
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
