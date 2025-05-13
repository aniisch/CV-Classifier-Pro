"""
Modèles de base de données pour l'application
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from datetime import datetime
from src.database.database import Base

class Analysis(Base):
    """Modèle pour stocker l'historique des analyses"""
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=datetime.now)
    folder_path = Column(String)
    keywords = Column(JSON)  # Stocke les mots-clés et leurs pondérations
    results = Column(JSON)   # Stocke les résultats de l'analyse
    report = Column(String)  # Stocke le rapport Markdown
