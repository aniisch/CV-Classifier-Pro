from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from ..database.database import get_db
from ..database.models import Analysis
from .cv_analyzer import CVAnalyzer
from .pdf_service import PDFService
from ..utils.error_handling import (
    handle_application_error,
    validate_keywords,
    validate_folder_path,
    ValidationError,
    DatabaseError,
    FileSystemError
)
import os
import base64

app = FastAPI()
pdf_service = PDFService()

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PDFRequest(BaseModel):
    report: str

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
        except FileSystemError as e:
            raise ValueError(e.message)

class AnalysisResponse(BaseModel):
    id: int
    date: datetime
    report: str
    keywords: Dict[str, float]

    class Config:
        from_attributes = True

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return handle_application_error(exc)

@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_cvs(request: AnalysisRequest, db: Session = Depends(get_db)):
    try:
        # Analyse des CVs
        analyzer = CVAnalyzer(request.folderPath, request.keywords)
        results = analyzer.analyze_cvs()
        
        # Génération du rapport
        report_content = analyzer.generate_markdown_report(results)
        
        # Sauvegarde dans la base de données
        try:
            analysis = Analysis(
                folder_path=request.folderPath,
                keywords=request.keywords,
                results=[{
                    "filename": cv.filename,
                    "score": float(cv.score),
                    "found_keywords": cv.found_keywords
                } for cv in results],
                report=report_content
            )
            
            db.add(analysis)
            db.commit()
            db.refresh(analysis)
            
        except SQLAlchemyError as e:
            db.rollback()
            raise DatabaseError(
                "Erreur lors de la sauvegarde de l'analyse",
                {"error": str(e)}
            )
        
        return {
            "id": analysis.id,
            "date": analysis.date,
            "report": report_content,
            "keywords": request.keywords
        }
        
    except Exception as e:
        raise handle_application_error(e)

@app.get("/api/analyses", response_model=List[AnalysisResponse])
async def get_analyses(db: Session = Depends(get_db)):
    """Récupère l'historique des analyses"""
    try:
        analyses = db.query(Analysis).order_by(Analysis.date.desc()).all()
        return [{
            "id": analysis.id,
            "date": analysis.date,
            "report": analysis.report,
            "keywords": {k: float(v) for k, v in analysis.keywords.items()}
        } for analysis in analyses]
    except SQLAlchemyError as e:
        raise DatabaseError(
            "Erreur lors de la récupération de l'historique",
            {"error": str(e)}
        )

@app.get("/api/analyses/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """Récupère une analyse spécifique"""
    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            raise ValidationError(
                "Analyse non trouvée",
                {"analysis_id": analysis_id}
            )
        return {
            "id": analysis.id,
            "date": analysis.date,
            "report": analysis.report,
            "keywords": {k: float(v) for k, v in analysis.keywords.items()}
        }
    except SQLAlchemyError as e:
        raise DatabaseError(
            "Erreur lors de la récupération de l'analyse",
            {"analysis_id": analysis_id, "error": str(e)}
        )

@app.delete("/api/analyses/{analysis_id}")
async def delete_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """Supprime une analyse spécifique"""
    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            raise ValidationError(
                "Analyse non trouvée",
                {"analysis_id": analysis_id}
            )
        
        db.delete(analysis)
        db.commit()
        return {"message": "Analyse supprimée avec succès"}
    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseError(
            "Erreur lors de la suppression de l'analyse",
            {"analysis_id": analysis_id, "error": str(e)}
        )

@app.post("/api/export/pdf/{analysis_id}")
async def export_analysis_to_pdf(analysis_id: int, request: PDFRequest, db: Session = Depends(get_db)):
    """Exporte une analyse au format PDF"""
    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            raise ValidationError(
                "Analyse non trouvée",
                {"analysis_id": analysis_id}
            )
            
        # Le PDF est maintenant généré côté client
        # On reçoit juste le contenu à sauvegarder
        if request.report.startswith('data:application/pdf;base64,'):
            pdf_data = base64.b64decode(request.report.split(',')[1])
        else:
            raise ValidationError("Format de données PDF invalide")
            
        # Sauvegarder le PDF
        filepath = pdf_service.save_pdf(pdf_data, analysis_id)
        
        return {"message": "PDF sauvegardé avec succès", "filepath": filepath}
        
    except Exception as e:
        raise handle_application_error(e)
