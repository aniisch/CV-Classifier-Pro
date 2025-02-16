from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from ..database.database import get_db
from ..database.models import Analysis
from .cv_analyzer import CVAnalyzer
import os

app = FastAPI()

class AnalysisRequest(BaseModel):
    folderPath: str
    keywords: Dict[str, float]

class AnalysisResponse(BaseModel):
    id: int
    date: datetime
    report: str
    keywords: Dict[str, float]

@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_cvs(request: AnalysisRequest, db: Session = Depends(get_db)):
    if not os.path.exists(request.folderPath):
        raise HTTPException(status_code=400, detail="Le dossier spécifié n'existe pas")
        
    try:
        # Analyse des CVs
        analyzer = CVAnalyzer(request.folderPath, request.keywords)
        results = analyzer.analyze_cvs()
        
        # Génération du rapport
        report_content = analyzer.generate_markdown_report(results)
        
        # Sauvegarde dans la base de données
        analysis = Analysis(
            folder_path=request.folderPath,
            keywords=request.keywords,
            results=[{
                "filename": cv.filename,
                "score": cv.score,
                "found_keywords": cv.found_keywords
            } for cv in results],
            report=report_content
        )
        
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        
        return {
            "id": analysis.id,
            "date": analysis.date,
            "report": report_content,
            "keywords": request.keywords
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analyses", response_model=List[AnalysisResponse])
async def get_analyses(db: Session = Depends(get_db)):
    """Récupère l'historique des analyses"""
    analyses = db.query(Analysis).order_by(Analysis.date.desc()).all()
    return [{
        "id": analysis.id,
        "date": analysis.date,
        "report": analysis.report,
        "keywords": analysis.keywords
    } for analysis in analyses]

@app.get("/api/analyses/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """Récupère une analyse spécifique"""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    return {
        "id": analysis.id,
        "date": analysis.date,
        "report": analysis.report,
        "keywords": analysis.keywords
    }

@app.delete("/api/analyses/{analysis_id}")
async def delete_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """Supprime une analyse spécifique"""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    
    db.delete(analysis)
    db.commit()
    return {"message": "Analyse supprimée avec succès"}
