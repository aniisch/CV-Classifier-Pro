from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from ..database.database import get_db
from ..database.models import Analysis
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

class AnalysisRequest(BaseModel):
    folderPath: str
    keywords: Dict[str, float]

    @validator('keywords')
    def validate_keywords_data(cls, v):
        try:
            validate_keywords(v)
            return {k: float(v) for k, v in v.items()}
        except ValidationError as e:
            raise ValueError(e.message)

    @validator('folderPath')
    def validate_folder_path_data(cls, v):
        try:
            validate_folder_path(v)
            return v
        except ValidationError as e:
            raise ValueError(e.message)

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

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_cvs(request: AnalysisRequest, db: Session = Depends(get_db)):
    """
    Analyse les CVs dans le dossier spécifié selon les mots-clés fournis
    """
    try:
        # Créer une nouvelle instance de l'analyseur
        analyzer = CVAnalyzer()
        
        # Analyser les CVs
        report = analyzer.analyze_folder(
            request.folderPath,
            request.keywords
        )
        
        # Créer une nouvelle analyse en base de données
        analysis = Analysis(
            date=datetime.now(),
            report=report,
            keywords=request.keywords
        )
        
        # Sauvegarder l'analyse
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        
        return analysis
        
    except (ValidationError, FileSystemError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde en base de données")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analyses", response_model=List[AnalysisResponse])
async def get_analyses(db: Session = Depends(get_db)):
    """
    Récupère l'historique des analyses
    """
    try:
        analyses = db.query(Analysis).order_by(Analysis.date.desc()).all()
        return analyses
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des analyses")

@app.get("/analyses/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """
    Récupère une analyse spécifique
    """
    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            raise HTTPException(status_code=404, detail="Analyse non trouvée")
        return analysis
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération de l'analyse")

@app.delete("/analyses/{analysis_id}")
async def delete_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """
    Supprime une analyse spécifique
    """
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
