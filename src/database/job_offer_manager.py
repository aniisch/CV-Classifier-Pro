"""
Gestionnaire d'offres d'emploi - CRUD operations pour les offres
"""
from sqlalchemy.orm import Session
from .models import JobOffer
from datetime import datetime


class JobOfferManager:
    """Classe statique pour gerer les operations CRUD sur les offres d'emploi"""

    @staticmethod
    def create_job_offer(db: Session, project_id: str, filename: str,
                         raw_content: str, requirements: dict = None) -> JobOffer:
        """Cree une nouvelle offre d'emploi"""
        job_offer = JobOffer(
            project_id=project_id,
            filename=filename,
            raw_content=raw_content,
            requirements=requirements or {}
        )
        db.add(job_offer)
        db.commit()
        db.refresh(job_offer)
        return job_offer

    @staticmethod
    def get_job_offers_by_project(db: Session, project_id: str) -> list:
        """Recupere toutes les offres d'un projet"""
        return db.query(JobOffer).filter(
            JobOffer.project_id == project_id
        ).order_by(JobOffer.created_at.desc()).all()

    @staticmethod
    def get_job_offer(db: Session, offer_id: str) -> JobOffer:
        """Recupere une offre par son ID"""
        return db.query(JobOffer).filter(JobOffer.id == offer_id).first()

    @staticmethod
    def update_job_offer(db: Session, offer_id: str,
                         requirements: dict = None) -> JobOffer:
        """Met a jour les requirements d'une offre"""
        job_offer = db.query(JobOffer).filter(JobOffer.id == offer_id).first()
        if not job_offer:
            return None

        if requirements is not None:
            job_offer.requirements = requirements

        db.commit()
        db.refresh(job_offer)
        return job_offer

    @staticmethod
    def delete_job_offer(db: Session, offer_id: str) -> bool:
        """Supprime une offre d'emploi"""
        job_offer = db.query(JobOffer).filter(JobOffer.id == offer_id).first()
        if not job_offer:
            return False

        db.delete(job_offer)
        db.commit()
        return True

    @staticmethod
    def job_offer_to_dict(job_offer: JobOffer) -> dict:
        """Convertit une offre en dictionnaire"""
        return {
            "id": job_offer.id,
            "project_id": job_offer.project_id,
            "filename": job_offer.filename,
            "raw_content": job_offer.raw_content,
            "requirements": job_offer.requirements or {},
            "created_at": job_offer.created_at.isoformat() if job_offer.created_at else None
        }
