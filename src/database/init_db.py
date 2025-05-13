"""
Script pour initialiser la base de données
"""
from src.database.database import engine
from src.database.models import Base

def init_database():
    """Initialise la base de données en créant toutes les tables"""
    # Création des tables
    Base.metadata.create_all(bind=engine)
    print("Base de données initialisée avec succès !")

if __name__ == "__main__":
    init_database()
