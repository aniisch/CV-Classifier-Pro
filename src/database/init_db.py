# -*- coding: utf-8 -*-
"""
Script d'initialisation de la base de donnees
Cree toutes les tables necessaires

Usage: python init_db.py (depuis le dossier src/database)
"""
import os
import sys

# Obtenir le chemin absolu du dossier actuel
current_dir = os.path.dirname(os.path.abspath(__file__))

# Ajouter le dossier src au path
src_dir = os.path.dirname(current_dir)
sys.path.insert(0, src_dir)

# Maintenant on peut importer avec des imports absolus depuis src
from database import engine
from models import Base, Project, Analysis, JobOffer

def init_database():
    """Initialise la base de donnees en creant toutes les tables"""
    print("Creation des tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables creees:")
    for table in Base.metadata.tables:
        print(f"  - {table}")

if __name__ == "__main__":
    init_database()
    print("\nBase de donnees initialisee avec succes!")
