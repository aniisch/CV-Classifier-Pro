from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from ..database.database import get_db
from ..database.models import Analysis, Project
from ..database.project_manager import ProjectManager
from .cv_analyzer import CVAnalyzer
from ..utils.error_handling import (
    handle_application_error,
    validate_keywords,
    validate_folder_path,
    ValidationError,
    DatabaseError,
    FileSystemError
)
import os

app = FastAPI()

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProjectRequest(BaseModel):
    name: str
    description: str = ""
    keywords: Dict[str, float] = {}

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str
    mode: str
    keywords: Dict[str, float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AnalysisResponse(BaseModel):
    id: int
    date: datetime
    report: str
    keywords: Dict[str, float]

    class Config:
        from_attributes = True

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return handle_application_error(exc)

# ===== PROJECT ENDPOINTS =====

@app.get("/api/projects", response_model=List[ProjectResponse])
async def get_projects(db: Session = Depends(get_db)):
    """Liste tous les projets"""
    try:
        projects = ProjectManager.get_all_projects(db)
        return [ProjectManager.project_to_dict(p) for p in projects]
    except Exception as e:
        import traceback
        print(f"ERROR in get_projects: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects", response_model=ProjectResponse)
async def create_project(request: ProjectRequest, db: Session = Depends(get_db)):
    """Crée un nouveau projet"""
    try:
        project = ProjectManager.create_project(
            db,
            name=request.name,
            description=request.description,
            keywords=request.keywords
        )
        return ProjectManager.project_to_dict(project)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    """Récupère un projet spécifique"""
    try:
        project = ProjectManager.get_project(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
        return ProjectManager.project_to_dict(project)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/projects/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, request: ProjectRequest, db: Session = Depends(get_db)):
    """Met à jour un projet"""
    try:
        project = ProjectManager.update_project(
            db,
            project_id,
            name=request.name,
            description=request.description,
            keywords=request.keywords
        )
        if not project:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
        return ProjectManager.project_to_dict(project)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str, db: Session = Depends(get_db)):
    """Supprime un projet"""
    try:
        success = ProjectManager.delete_project(db, project_id)
        if not success:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
        return {"message": "Projet supprimé avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}/analyses")
async def get_project_analyses(project_id: str, db: Session = Depends(get_db)):
    """Récupère l'historique des analyses pour un projet spécifique"""
    try:
        # Vérifier que le projet existe
        project = ProjectManager.get_project(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Projet non trouvé")

        # Récupérer les analyses du projet
        analyses = db.query(Analysis).filter(
            Analysis.project_id == project_id
        ).order_by(Analysis.date.desc()).all()

        return [
            {
                "id": a.id,
                "date": a.date,
                "report": a.report,
                "keywords": a.keywords,
                "folder_path": a.folder_path
            }
            for a in analyses
        ]
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"ERROR in get_project_analyses: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/analyze")
async def analyze_project(project_id: str, request: dict, db: Session = Depends(get_db)):
    """Analyse les CVs pour un projet spécifique"""
    try:
        # Récupérer le projet
        project = ProjectManager.get_project(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Projet non trouvé")

        # Extraire folder_path et keywords du projet
        folder_path = request.get('folder_path')
        keywords = project.keywords

        if not folder_path:
            raise HTTPException(status_code=400, detail="folder_path requis")

        if not keywords:
            raise HTTPException(status_code=400, detail="Mots-clés du projet manquants")

        # Convertir les keywords en floats (au cas où ils seraient des strings/ints depuis la DB)
        keywords = {k: float(v) for k, v in keywords.items()}

        # Lancer l'analyse avec CVAnalyzer
        analyzer = CVAnalyzer(folder_path, keywords)
        results = analyzer.analyze_cvs()
        report = analyzer.generate_markdown_report(results)

        # Sauvegarder l'analyse en DB
        analysis = Analysis(
            project_id=project_id,
            date=datetime.now(),
            report=report,
            keywords=keywords,
            folder_path=folder_path
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)

        return {"report": report}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"ERROR in analyze_project: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Vérification de la connexion"""
    return {"status": "ok"}

# ===== ANALYSIS ENDPOINTS =====

@app.delete("/api/analyses/{analysis_id}")
async def delete_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """Supprime une analyse spécifique"""
    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            raise HTTPException(status_code=404, detail="Analyse non trouvée")

        db.delete(analysis)
        db.commit()

        return {"message": "Analyse supprimée avec succès"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Erreur lors de la suppression de l'analyse")
