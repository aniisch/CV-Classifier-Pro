"""
Gestionnaire de projets - CRUD operations pour les projets
"""
from sqlalchemy.orm import Session
from .models import Project
from datetime import datetime


class ProjectManager:
    """Classe statique pour gérer les opérations CRUD sur les projets"""

    @staticmethod
    def create_project(db: Session, name: str, description: str = "", keywords: dict = None) -> Project:
        """Crée un nouveau projet"""
        project = Project(
            name=name,
            description=description,
            keywords=keywords or {}
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def get_all_projects(db: Session) -> list:
        """Récupère tous les projets"""
        return db.query(Project).order_by(Project.created_at.desc()).all()

    @staticmethod
    def get_project(db: Session, project_id: str) -> Project:
        """Récupère un projet par son ID"""
        return db.query(Project).filter(Project.id == project_id).first()

    @staticmethod
    def update_project(db: Session, project_id: str, name: str = None,
                       description: str = None, keywords: dict = None) -> Project:
        """Met à jour un projet"""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None

        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        if keywords is not None:
            project.keywords = keywords

        project.updated_at = datetime.now()
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def delete_project(db: Session, project_id: str) -> bool:
        """Supprime un projet"""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False

        db.delete(project)
        db.commit()
        return True

    @staticmethod
    def project_to_dict(project: Project) -> dict:
        """Convertit un projet en dictionnaire"""
        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "mode": project.mode,
            "keywords": project.keywords or {},
            "created_at": project.created_at,
            "updated_at": project.updated_at
        }
