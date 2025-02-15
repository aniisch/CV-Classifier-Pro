from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict
from .cv_analyzer import CVAnalyzer
import os

app = FastAPI()

class AnalysisRequest(BaseModel):
    folderPath: str
    keywords: Dict[str, float]

@app.post("/api/analyze")
async def analyze_cvs(request: AnalysisRequest):
    if not os.path.exists(request.folderPath):
        raise HTTPException(status_code=400, detail="Le dossier spécifié n'existe pas")
        
    try:
        analyzer = CVAnalyzer(request.folderPath, request.keywords)
        results = analyzer.analyze_cvs()
        
        # Générer le rapport
        report_path = 'rapport_analyse_cv.md'
        analyzer.generate_markdown_report(results, report_path)
        
        # Lire le contenu du rapport
        with open(report_path, 'r', encoding='utf-8') as f:
            report_content = f.read()
        
        return {"report": report_content}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
