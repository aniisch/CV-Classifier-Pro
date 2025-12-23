from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from ..database.database import get_db
from ..database.models import Analysis, Project, JobOffer, LLMSettings
from ..database.project_manager import ProjectManager
from ..database.job_offer_manager import JobOfferManager
from .cv_analyzer import CVAnalyzer
from .job_offer_parser import JobOfferParser
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


class JobOfferRequest(BaseModel):
    file_path: str


class JobOfferUpdateRequest(BaseModel):
    requirements: Dict[str, float]


class JobOfferResponse(BaseModel):
    id: str
    project_id: str
    filename: str
    raw_content: Optional[str] = None
    requirements: Dict[str, float]
    created_at: datetime

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


# ===== JOB OFFER ENDPOINTS =====

@app.post("/api/projects/{project_id}/job-offers")
async def create_job_offer(project_id: str, request: JobOfferRequest, db: Session = Depends(get_db)):
    """Upload et parse une offre d'emploi"""
    try:
        # Verifier que le projet existe
        project = ProjectManager.get_project(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Projet non trouve")

        file_path = request.file_path

        # Verifier que le fichier existe
        if not os.path.exists(file_path):
            raise HTTPException(status_code=400, detail=f"Fichier non trouve: {file_path}")

        # Parser le fichier
        try:
            parsed = JobOfferParser.process_file(file_path)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Extraire le nom du fichier
        filename = os.path.basename(file_path)

        # Creer l'offre en base
        job_offer = JobOfferManager.create_job_offer(
            db,
            project_id=project_id,
            filename=filename,
            raw_content=parsed["raw_content"],
            requirements=parsed["requirements"]
        )

        return JobOfferManager.job_offer_to_dict(job_offer)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"ERROR in create_job_offer: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_id}/job-offers")
async def get_project_job_offers(project_id: str, db: Session = Depends(get_db)):
    """Liste toutes les offres d'emploi d'un projet"""
    try:
        # Verifier que le projet existe
        project = ProjectManager.get_project(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Projet non trouve")

        job_offers = JobOfferManager.get_job_offers_by_project(db, project_id)
        return [JobOfferManager.job_offer_to_dict(jo) for jo in job_offers]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/job-offers/{offer_id}")
async def get_job_offer(offer_id: str, db: Session = Depends(get_db)):
    """Recupere une offre d'emploi specifique"""
    try:
        job_offer = JobOfferManager.get_job_offer(db, offer_id)
        if not job_offer:
            raise HTTPException(status_code=404, detail="Offre non trouvee")
        return JobOfferManager.job_offer_to_dict(job_offer)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/job-offers/{offer_id}")
async def update_job_offer(offer_id: str, request: JobOfferUpdateRequest, db: Session = Depends(get_db)):
    """Met a jour les requirements d'une offre"""
    try:
        job_offer = JobOfferManager.update_job_offer(
            db,
            offer_id,
            requirements=request.requirements
        )
        if not job_offer:
            raise HTTPException(status_code=404, detail="Offre non trouvee")
        return JobOfferManager.job_offer_to_dict(job_offer)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/job-offers/{offer_id}")
async def delete_job_offer(offer_id: str, db: Session = Depends(get_db)):
    """Supprime une offre d'emploi"""
    try:
        success = JobOfferManager.delete_job_offer(db, offer_id)
        if not success:
            raise HTTPException(status_code=404, detail="Offre non trouvee")
        return {"message": "Offre supprimee avec succes"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/projects/{project_id}/analyze-offer/{offer_id}")
async def analyze_with_job_offer(project_id: str, offer_id: str, request: dict, db: Session = Depends(get_db)):
    """Analyse les CVs en utilisant les requirements d'une offre d'emploi"""
    try:
        # Verifier que le projet existe
        project = ProjectManager.get_project(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Projet non trouve")

        # Verifier que l'offre existe et appartient au projet
        job_offer = JobOfferManager.get_job_offer(db, offer_id)
        if not job_offer:
            raise HTTPException(status_code=404, detail="Offre non trouvee")
        if job_offer.project_id != project_id:
            raise HTTPException(status_code=400, detail="L'offre n'appartient pas a ce projet")

        # Extraire folder_path et keywords de l'offre
        folder_path = request.get('folder_path')
        keywords = job_offer.requirements

        if not folder_path:
            raise HTTPException(status_code=400, detail="folder_path requis")

        if not keywords:
            raise HTTPException(status_code=400, detail="Aucun requirement dans l'offre")

        # Convertir les keywords en floats
        keywords = {k: float(v) for k, v in keywords.items()}

        # Lancer l'analyse avec CVAnalyzer
        analyzer = CVAnalyzer(folder_path, keywords)
        results = analyzer.analyze_cvs()
        report = analyzer.generate_markdown_report(results)

        # Sauvegarder l'analyse en DB avec reference a l'offre
        analysis = Analysis(
            project_id=project_id,
            job_offer_id=offer_id,
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
        print(f"ERROR in analyze_with_job_offer: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ===== LLM SETTINGS ENDPOINTS =====

class LLMSettingsRequest(BaseModel):
    provider: str = "ollama"  # 'ollama', 'openai', 'anthropic'
    api_key: str = ""
    model: str = "llama3.2"
    ollama_url: str = "http://localhost:11434"


class LLMSettingsResponse(BaseModel):
    id: int
    provider: str
    api_key: str
    model: str
    ollama_url: str
    updated_at: datetime

    class Config:
        from_attributes = True


@app.get("/api/llm-settings", response_model=LLMSettingsResponse)
async def get_llm_settings(db: Session = Depends(get_db)):
    """Recupere les parametres LLM"""
    try:
        settings = db.query(LLMSettings).first()
        if not settings:
            # Creer les settings par defaut si inexistants
            settings = LLMSettings(
                id=1,
                provider="ollama",
                api_key="",
                model="llama3.2",
                ollama_url="http://localhost:11434"
            )
            db.add(settings)
            db.commit()
            db.refresh(settings)
        return settings
    except Exception as e:
        import traceback
        print(f"ERROR in get_llm_settings: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/llm-settings", response_model=LLMSettingsResponse)
async def update_llm_settings(request: LLMSettingsRequest, db: Session = Depends(get_db)):
    """Met a jour les parametres LLM"""
    try:
        settings = db.query(LLMSettings).first()
        if not settings:
            # Creer si inexistant
            settings = LLMSettings(id=1)
            db.add(settings)

        settings.provider = request.provider
        settings.api_key = request.api_key
        settings.model = request.model
        settings.ollama_url = request.ollama_url

        db.commit()
        db.refresh(settings)
        return settings
    except Exception as e:
        import traceback
        print(f"ERROR in update_llm_settings: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/llm-settings/test")
async def test_llm_connection(db: Session = Depends(get_db)):
    """Teste la connexion au LLM configure"""
    try:
        settings = db.query(LLMSettings).first()
        if not settings:
            raise HTTPException(status_code=400, detail="LLM non configure")

        # Test selon le provider
        if settings.provider == "ollama":
            import httpx
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{settings.ollama_url}/api/tags")
                    if response.status_code == 200:
                        models = response.json().get("models", [])
                        model_names = [m.get("name", "") for m in models]
                        return {
                            "status": "ok",
                            "provider": "ollama",
                            "available_models": model_names
                        }
                    else:
                        return {"status": "error", "message": "Ollama ne repond pas correctement"}
            except Exception as e:
                return {"status": "error", "message": f"Impossible de se connecter a Ollama: {str(e)}"}

        elif settings.provider == "openai":
            if not settings.api_key:
                return {"status": "error", "message": "Cle API OpenAI manquante"}
            # Test simple - on verifie juste que la cle a le bon format
            if settings.api_key.startswith("sk-"):
                return {"status": "ok", "provider": "openai", "message": "Cle API configuree"}
            else:
                return {"status": "error", "message": "Format de cle API invalide"}

        elif settings.provider == "anthropic":
            if not settings.api_key:
                return {"status": "error", "message": "Cle API Anthropic manquante"}
            if settings.api_key.startswith("sk-ant-"):
                return {"status": "ok", "provider": "anthropic", "message": "Cle API configuree"}
            else:
                return {"status": "error", "message": "Format de cle API invalide"}

        else:
            return {"status": "error", "message": f"Provider inconnu: {settings.provider}"}

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"ERROR in test_llm_connection: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
