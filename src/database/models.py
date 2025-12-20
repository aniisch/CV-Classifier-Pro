from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class Project(Base):
    """Modèle pour stocker les projets d'analyse"""
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(String, default="")
    mode = Column(String, default="simple")  # 'simple' ou 'llm'
    keywords = Column(JSON, default={})  # {"keyword": weight, ...}
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class Analysis(Base):
    """Modèle pour stocker l'historique des analyses"""
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True)
    project_id = Column(String, ForeignKey('projects.id'), nullable=True)
    date = Column(DateTime, default=datetime.now)
    folder_path = Column(String)
    keywords = Column(JSON)  # Stocke les mots-clés et leurs pondérations
    results = Column(JSON)   # Stocke les résultats de l'analyse
    report = Column(String)  # Stocke le rapport Markdown
