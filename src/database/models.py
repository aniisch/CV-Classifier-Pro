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

class JobOffer(Base):
    """Modèle pour stocker les offres d'emploi"""
    __tablename__ = "job_offers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey('projects.id'), nullable=False)
    filename = Column(String, nullable=False)
    raw_content = Column(String)  # Texte extrait du fichier
    requirements = Column(JSON, default={})  # {"keyword": weight, ...}
    created_at = Column(DateTime, default=datetime.now)


class Analysis(Base):
    """Modèle pour stocker l'historique des analyses"""
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True)
    project_id = Column(String, ForeignKey('projects.id'), nullable=True)
    job_offer_id = Column(String, ForeignKey('job_offers.id'), nullable=True)  # Si analyse basée sur offre
    date = Column(DateTime, default=datetime.now)
    folder_path = Column(String)
    keywords = Column(JSON)  # Stocke les mots-clés et leurs pondérations
    results = Column(JSON)   # Stocke les résultats de l'analyse
    report = Column(String)  # Stocke le rapport Markdown


class LLMSettings(Base):
    """Modèle pour stocker les paramètres LLM (config globale)"""
    __tablename__ = "llm_settings"

    id = Column(Integer, primary_key=True, default=1)  # Une seule entrée
    provider = Column(String, default="ollama")  # 'ollama', 'openai', 'anthropic'
    api_key = Column(String, default="")  # Clé API (vide pour Ollama)
    model = Column(String, default="llama3.2")  # Modèle à utiliser
    ollama_url = Column(String, default="http://localhost:11434")  # URL Ollama
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
