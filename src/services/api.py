from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, validator
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from ..database.database import get_db, engine, SessionLocal
from ..database.models import Base, Analysis, Project, JobOffer, LLMSettings, LLMJob, LLMJobItem, WtjCandidate
from ..database.project_manager import ProjectManager
from ..database.job_offer_manager import JobOfferManager
from .cv_analyzer import CVAnalyzer
from .job_offer_parser import JobOfferParser
from . import llm_jobs, report_export, wtj_import
from .report_export import (
    extract_short_opinion,
    get_recommendation_emoji,
    get_recommendation_label,
    parse_llm_response,
)
from ..utils.error_handling import (
    handle_application_error,
    validate_keywords,
    validate_folder_path,
    ValidationError,
    DatabaseError,
    FileSystemError
)
import asyncio
import os
import re

app = FastAPI()


def _ensure_columns() -> None:
    """Ajoute les colonnes apparues apres la creation de la base (create_all ne le fait pas)."""
    from sqlalchemy import inspect, text
    if "custom_prompt" not in {c["name"] for c in inspect(engine).get_columns("llm_jobs")}:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE llm_jobs ADD COLUMN custom_prompt VARCHAR DEFAULT ''"))


@app.on_event("startup")
def init_database_and_jobs():
    """Cree les tables manquantes et marque les lots LLM laisses 'running' comme interrompus."""
    Base.metadata.create_all(bind=engine)
    _ensure_columns()
    db = SessionLocal()
    try:
        llm_jobs.mark_interrupted_jobs(db)
    finally:
        db.close()

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
    provider: str = "ollama"  # 'ollama', 'openai', 'anthropic', 'azure_openai' (ollama_url = endpoint Azure)
    api_key: str = ""
    model: str = "llama3.2"
    ollama_url: str = "http://localhost:11434"


API_KEY_MASK = "****"


def mask_api_key(api_key: str) -> str:
    """Return the key masked for the UI: only the last 4 characters stay visible.

    Args:
        api_key: The stored API key.

    Returns:
        An empty string if no key, otherwise ``****`` followed by the last 4 characters.
    """
    if not api_key:
        return ""
    return API_KEY_MASK + api_key[-4:] if len(api_key) > 8 else API_KEY_MASK


def settings_response(settings: LLMSettings) -> "LLMSettingsResponse":
    """Build the API response of the LLM settings with a masked API key."""
    return LLMSettingsResponse(
        id=settings.id,
        provider=settings.provider,
        api_key=mask_api_key(settings.api_key or ""),
        model=settings.model,
        ollama_url=settings.ollama_url,
        updated_at=settings.updated_at,
    )


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
        return settings_response(settings)
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
        # La cle masquee renvoyee par le GET (ou vide) ne remplace pas la cle stockee
        if not request.api_key.startswith(API_KEY_MASK):
            settings.api_key = request.api_key
        settings.model = request.model
        settings.ollama_url = request.ollama_url

        db.commit()
        db.refresh(settings)
        return settings_response(settings)
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
            # Test reel avec l'API OpenAI
            import httpx
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(
                        "https://api.openai.com/v1/models",
                        headers={"Authorization": f"Bearer {settings.api_key}"}
                    )
                    if response.status_code == 200:
                        return {"status": "ok", "provider": "openai", "message": "Connexion reussie"}
                    elif response.status_code == 401:
                        return {"status": "error", "message": "Cle API invalide ou expiree"}
                    else:
                        return {"status": "error", "message": f"Erreur API: {response.status_code}"}
            except Exception as e:
                return {"status": "error", "message": f"Erreur de connexion: {str(e)}"}

        elif settings.provider == "anthropic":
            if not settings.api_key:
                return {"status": "error", "message": "Cle API Anthropic manquante"}
            # Test reel avec l'API Anthropic
            import httpx
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={
                            "x-api-key": settings.api_key,
                            "anthropic-version": "2023-06-01",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": settings.model,
                            "max_tokens": 10,
                            "messages": [{"role": "user", "content": "test"}]
                        }
                    )
                    if response.status_code == 200:
                        return {"status": "ok", "provider": "anthropic", "message": "Connexion reussie"}
                    elif response.status_code == 401:
                        return {"status": "error", "message": "Cle API invalide ou expiree"}
                    else:
                        error_data = response.json()
                        error_msg = error_data.get("error", {}).get("message", f"Erreur {response.status_code}")
                        return {"status": "error", "message": error_msg}
            except Exception as e:
                return {"status": "error", "message": f"Erreur de connexion: {str(e)}"}

        elif settings.provider == "azure_openai":
            from .llm_adapters import AzureOpenAIAdapter
            adapter = AzureOpenAIAdapter(
                api_key=settings.api_key,
                model=settings.model,
                endpoint=settings.ollama_url
            )
            return await adapter.test_connection()

        else:
            return {"status": "error", "message": f"Provider inconnu: {settings.provider}"}

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"ERROR in test_llm_connection: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ===== LLM ANALYSIS ENDPOINT =====

class LLMAnalysisRequest(BaseModel):
    folder_path: str
    job_offer_id: str
    cv_files: Optional[List[str]] = None  # Liste optionnelle de fichiers specifiques
    source_analysis_id: Optional[int] = None  # ID de l'analyse source (pour traçabilité)
    min_years: Optional[float] = None  # fourchette d'experience (donnees WTJ), bornes incluses
    max_years: Optional[float] = None
    custom_prompt: str = ""  # instructions du recruteur, propres a ce lancement


@app.post("/api/projects/{project_id}/analyze-llm")
async def analyze_with_llm(project_id: str, request: LLMAnalysisRequest, db: Session = Depends(get_db)):
    """
    Analyse les CVs avec un LLM par rapport a une offre d'emploi.
    Retourne une analyse detaillee pour chaque CV.
    """
    try:
        # 1. Verifier que le projet existe
        project = ProjectManager.get_project(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Projet non trouve")

        # 2. Verifier que l'offre existe
        job_offer = JobOfferManager.get_job_offer(db, request.job_offer_id)
        if not job_offer:
            raise HTTPException(status_code=404, detail="Offre d'emploi non trouvee")

        # 3. Verifier le dossier CVs
        folder_path = request.folder_path
        if not os.path.exists(folder_path):
            raise HTTPException(status_code=400, detail=f"Dossier non trouve: {folder_path}")

        # 4. Charger les settings LLM
        settings = db.query(LLMSettings).first()
        if not settings:
            raise HTTPException(status_code=400, detail="LLM non configure. Allez dans les parametres.")

        # 5. Lister les CVs (la lecture des PDF se fait dans le job, hors boucle asyncio)
        filenames = llm_jobs.list_pdf_files(folder_path, request.cv_files)
        if not filenames:
            raise HTTPException(status_code=400, detail="Aucun CV valide trouve dans le dossier")

        # 5b. Fourchette d'experience (CVs sans donnees WTJ conserves)
        split = wtj_import.filter_by_experience(
            db, project_id, filenames, request.min_years, request.max_years
        )
        filenames = split["kept"]
        if not filenames:
            raise HTTPException(
                status_code=400,
                detail="Aucun CV dans la fourchette d'experience demandee",
            )

        # 6. Creer le lot et le lancer en arriere-plan
        job = llm_jobs.create_job(
            db, project_id, request.job_offer_id, folder_path, filenames,
            settings.provider, settings.model, request.custom_prompt
        )
        llm_jobs.start_job(job.id, generate_llm_report)
        return {
            **llm_jobs.job_to_dict(db, job),
            "excluded_by_experience": len(split["excluded"]),
            "unknown_experience": len(split["unknown"]),
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"ERROR in analyze_with_llm: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ===== LLM JOBS (suivi, reprise, annulation) =====

def _get_job_or_404(db: Session, job_id: str) -> LLMJob:
    job = db.get(LLMJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Lot d'analyse non trouve")
    return job


_EXPORT_TYPES = {
    "html": "text/html; charset=utf-8",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pdf": "application/pdf",
}


@app.get("/api/analyses/{analysis_id}/export/{fmt}")
def export_analysis(analysis_id: int, fmt: str, db: Session = Depends(get_db)):
    """Exporte une analyse LLM : html (autonome), xlsx (classement) ou pdf (resume)."""
    if fmt not in _EXPORT_TYPES:
        raise HTTPException(status_code=400, detail="Format inconnu (html, xlsx, pdf)")
    analysis = db.get(Analysis, analysis_id)
    if not analysis or not analysis.results:
        raise HTTPException(status_code=404, detail="Analyse LLM non trouvee")
    offer = db.get(JobOffer, analysis.job_offer_id) if analysis.job_offer_id else None
    settings = analysis.keywords or {}
    info = report_export.report_info(
        offer.filename if offer else "", settings.get("provider", ""),
        settings.get("model", ""), analysis.date,
    )
    if fmt == "html":
        content = report_export.build_html(analysis.results, info).encode("utf-8")
    elif fmt == "xlsx":
        content = report_export.build_xlsx(analysis.results, info)
    else:
        content = report_export.build_pdf(analysis.results, info)
    filename = f"rapport_analyse_{analysis.id}_{analysis.date:%Y%m%d_%H%M}.{fmt}"
    return Response(
        content=content,
        media_type=_EXPORT_TYPES[fmt],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/llm-jobs/{job_id}")
async def get_llm_job(job_id: str, db: Session = Depends(get_db)):
    """Progression d'un lot ; inclut report et results une fois termine."""
    job = _get_job_or_404(db, job_id)
    data = llm_jobs.job_to_dict(db, job)
    if data["status"] == "completed" and job.analysis_id:
        analysis = db.get(Analysis, job.analysis_id)
        if analysis:
            data["report"] = analysis.report
            data["results"] = analysis.results
    return data


@app.get("/api/projects/{project_id}/llm-jobs")
async def list_unfinished_llm_jobs(project_id: str, db: Session = Depends(get_db)):
    """Lots a traiter : en cours, interrompus, annules, en erreur, ou termines avec des CVs en erreur."""
    jobs = (
        db.query(LLMJob)
        .filter(LLMJob.project_id == project_id)
        .order_by(LLMJob.created_at.desc())
        .all()
    )
    result = []
    for j in jobs:
        data = llm_jobs.job_to_dict(db, j)
        if j.status in llm_jobs.ACTIVE_STATUSES or (j.status == "completed" and data["error"] > 0):
            result.append(data)
    return result


@app.post("/api/llm-jobs/{job_id}/resume")
async def resume_llm_job(job_id: str, db: Session = Depends(get_db)):
    """Reprend un lot : relance les CVs non traites et ceux en erreur."""
    job = _get_job_or_404(db, job_id)
    if llm_jobs.is_running(job_id):
        raise HTTPException(status_code=409, detail="Ce lot est deja en cours")
    db.query(LLMJobItem).filter(
        LLMJobItem.job_id == job_id, LLMJobItem.status == "error"
    ).update({"status": "pending", "result": None})
    job.status = "running"
    job.error = ""
    db.commit()
    llm_jobs.start_job(job_id, generate_llm_report)
    return llm_jobs.job_to_dict(db, job)


@app.post("/api/llm-jobs/{job_id}/cancel")
async def cancel_llm_job(job_id: str, db: Session = Depends(get_db)):
    """Annule un lot en cours ; les resultats deja obtenus sont conserves."""
    job = _get_job_or_404(db, job_id)
    await llm_jobs.cancel_job(job_id)
    db.refresh(job)
    return llm_jobs.job_to_dict(db, job)


@app.delete("/api/llm-jobs/{job_id}")
async def delete_llm_job(job_id: str, db: Session = Depends(get_db)):
    """Abandonne un lot non termine (supprime le lot et ses items)."""
    job = _get_job_or_404(db, job_id)
    if llm_jobs.is_running(job_id):
        raise HTTPException(status_code=409, detail="Annulez le lot avant de le supprimer")
    db.query(LLMJobItem).filter(LLMJobItem.job_id == job_id).delete()
    db.delete(job)
    db.commit()
    return {"message": "Lot supprime"}


def generate_llm_report(results: list, job_offer_name: str, provider: str, model: str) -> str:
    """Genere un rapport Markdown avec classement a partir des resultats LLM."""

    # Separer les succes et echecs
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]

    # Parser les scores pour les resultats reussis
    parsed_results = []
    for r in successful:
        parsed = parse_llm_response(r.get("analysis", ""))
        parsed_results.append({
            'filename': r['filename'],
            'score': parsed['score'],
            'recommendation': parsed['recommendation'],
            'analysis': parsed['analysis']
        })

    # Trier par score decroissant (None a la fin)
    parsed_results.sort(key=lambda x: (x['score'] is not None, x['score'] or 0), reverse=True)

    has_wtj = any(r.get("wtj") for r in successful)
    wtj_by_file = {r["filename"]: r.get("wtj") or {} for r in successful}

    report = f"""# Rapport d'Analyse IA

## Informations
| | |
|---|---|
| **Offre d'emploi** | {job_offer_name} |
| **Provider** | {provider} |
| **Modèle** | {model} |
| **CVs analysés** | {len(results)} |
| **Date** | {datetime.now().strftime('%d/%m/%Y à %H:%M')} |

---

## Synthèse et Classement

"""

    if parsed_results:
        header = "| Rang | Candidat | Score | Recommandation |"
        sep = "|:----:|----------|:-----:|----------------|"
        if has_wtj:
            header += " Exp. (ans) | WTJ |"
            sep += ":-------:|:---:|"
        report += header + "\n" + sep + "\n"

        for i, r in enumerate(parsed_results, 1):
            score_str = f"{r['score']}/100" if r['score'] is not None else "N/A"
            row = f"| {i} | {r['filename']} | **{score_str}** | {get_recommendation_label(r['recommendation'])} |"
            if has_wtj:
                w = wtj_by_file.get(r['filename'], {})
                years = f"{w['years_exp']:g}" if w.get('years_exp') is not None else "-"
                link = f"[WTJ]({w['wtj_url']})" if w.get('wtj_url') else "-"
                row += f" {years} | {link} |"
            report += row + "\n"

        report += "\n"

        # Top 10 : avis court de l'IA
        top = [r for r in parsed_results if r['score'] is not None][:10]
        if top:
            report += f"### Top {len(top)} des profils\n\n"
            for i, r in enumerate(top, 1):
                opinion = extract_short_opinion(r['analysis'])
                report += f"{i}. **{r['filename']}** ({r['score']}/100) : {opinion}\n"
            report += "\n"

        report += "\n---\n\n"

        # Analyses detaillees (sans rang : le classement est dans le tableau)
        report += "## Analyses Détaillées\n\n"

        for r in parsed_results:
            score_str = f"{r['score']}/100" if r['score'] is not None else "N/A"
            report += f"### {r['filename']}\n\n"
            report += f"**Score : {score_str}** | **Recommandation : {get_recommendation_label(r['recommendation'])}**\n\n"

            clean_analysis = re.sub(r'^SCORE:.*$', '', r['analysis'], flags=re.MULTILINE | re.IGNORECASE)
            clean_analysis = re.sub(r'^RECOMMANDATION:.*$', '', clean_analysis, flags=re.MULTILINE | re.IGNORECASE)
            clean_analysis = clean_analysis.strip()

            report += clean_analysis
            report += "\n\n---\n\n"

    # Erreurs
    if failed:
        report += f"## Erreurs ({len(failed)} CVs)\n\n"
        for result in failed:
            report += f"- **{result['filename']}**: {result.get('error', 'Erreur inconnue')}\n"
        report += "\n"

    return report


# ===== WTJ CANDIDATES (import CSV) =====

class WtjImportRequest(BaseModel):
    csv_path: str


@app.post("/api/projects/{project_id}/wtj-import")
async def import_wtj_csv(project_id: str, request: WtjImportRequest, db: Session = Depends(get_db)):
    """Importe un export CSV Welcome to the Jungle (rapprochement par cv_fichier)."""
    if not ProjectManager.get_project(db, project_id):
        raise HTTPException(status_code=404, detail="Projet non trouve")
    if not os.path.isfile(request.csv_path):
        raise HTTPException(status_code=400, detail=f"Fichier non trouve: {request.csv_path}")
    try:
        return wtj_import.import_csv(db, project_id, request.csv_path)
    except (ValueError, UnicodeDecodeError) as e:
        raise HTTPException(status_code=400, detail=f"CSV invalide: {e}")


@app.get("/api/projects/{project_id}/wtj-candidates")
async def list_wtj_candidates(project_id: str, db: Session = Depends(get_db)):
    """Liste les candidats WTJ importes pour le projet."""
    rows = db.query(WtjCandidate).filter(WtjCandidate.project_id == project_id).all()
    return [wtj_import.candidate_to_dict(c) for c in rows]


@app.delete("/api/projects/{project_id}/wtj-candidates")
async def clear_wtj_candidates(project_id: str, db: Session = Depends(get_db)):
    """Supprime les candidats WTJ importes du projet."""
    n = db.query(WtjCandidate).filter(WtjCandidate.project_id == project_id).delete()
    db.commit()
    return {"deleted": n}
