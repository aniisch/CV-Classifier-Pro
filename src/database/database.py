from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pathlib import Path
import sys
import os
import shutil

DB_FILENAME = "cv_analyzer.db"


def _user_data_dir() -> Path:
    """Dossier de donnees stable de l'utilisateur (survit aux mises a jour de l'application)."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return base / "CV Classifier Pro" / "data"


def _resolve_data_dir() -> Path:
    """Choisit le dossier de la base SQLite.

    - CV_CLASSIFIER_DATA_DIR : surcharge explicite.
    - Application packagee : dossier utilisateur (et non le dossier de l'exe, qui change
      a chaque version ou copie). Une ancienne base placee a cote de l'exe est copiee
      une seule fois si aucune base n'existe encore.
    - Mode developpement : dossier data/ du depot.
    """
    override = os.environ.get("CV_CLASSIFIER_DATA_DIR")
    if override:
        directory = Path(override)
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    if getattr(sys, 'frozen', False):
        directory = _user_data_dir()
        directory.mkdir(parents=True, exist_ok=True)
        legacy = Path(os.path.dirname(sys.executable)) / "data" / DB_FILENAME
        target = directory / DB_FILENAME
        if legacy.exists() and not target.exists():
            shutil.copy2(legacy, target)
        return directory

    directory = Path(__file__).parent.parent.parent / "data"
    directory.mkdir(exist_ok=True)
    return directory


data_dir = _resolve_data_dir()

# Création de la base de données SQLite
SQLALCHEMY_DATABASE_URL = f"sqlite:///{data_dir / DB_FILENAME}"
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
