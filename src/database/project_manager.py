from sqlalchemy.orm import Session
from datetime import datetime
import uuid
from .models import Project

class ProjectManager:
    """Gestionnaire des projets CRUD"""

    @staticmethod
    def create_project(db: Session, name: str, description: str = "", keywords: dict = None) -> Project:
        """Créer un nouveau projet"""
        if keywords is None:
            keywords = {}

        project = Project(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            keywords=keywords,
            mode="simple",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def get_all_projects(db: Session) -> list:
        """Récupérer tous les projets"""
        return db.query(Project).order_by(Project.created_at.desc()).all()

    @staticmethod
    def get_project(db: Session, project_id: str) -> Project:
        """Récupérer un projet par ID"""
        return db.query(Project).filter(Project.id == project_id).first()

    @staticmethod
    def update_project(db: Session, project_id: str, name: str = None, description: str = None, keywords: dict = None) -> Project:
        """Mettre à jour un projet"""
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
        """Supprimer un projet"""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False

        db.delete(project)
        db.commit()
        return True

    @staticmethod
    def project_to_dict(project: Project) -> dict:
        """Convertir un projet en dictionnaire"""
        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "mode": project.mode,
            "keywords": project.keywords,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat()
        }
