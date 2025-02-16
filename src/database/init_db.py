from database import engine
from models import Base

def init_database():
    """Initialise la base de données en créant toutes les tables"""
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_database()
    print("Base de données initialisée avec succès !")
