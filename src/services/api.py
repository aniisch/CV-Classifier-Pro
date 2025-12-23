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
import re

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

        # 5. Lire les CVs du dossier
        from PyPDF2 import PdfReader
        cvs = []
        for filename in os.listdir(folder_path):
            if filename.lower().endswith('.pdf'):
                filepath = os.path.join(folder_path, filename)
                try:
                    reader = PdfReader(filepath)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() or ""
                    if text.strip():
                        cvs.append({"filename": filename, "content": text})
                except Exception as e:
                    print(f"Erreur lecture {filename}: {e}")

        if not cvs:
            raise HTTPException(status_code=400, detail="Aucun CV valide trouve dans le dossier")

        # 6. Creer le LLM Manager et analyser
        from .llm_manager import LLMManager
        llm_manager = LLMManager(db)

        results = []
        for cv in cvs:
            try:
                response = await llm_manager.analyze_cv(
                    cv_content=cv["content"],
                    job_offer_content=job_offer.raw_content
                )
                results.append({
                    "filename": cv["filename"],
                    "success": True,
                    "analysis": response.content,
                    "model": response.model,
                    "provider": response.provider,
                    "tokens": response.usage
                })
            except Exception as e:
                results.append({
                    "filename": cv["filename"],
                    "success": False,
                    "error": str(e)
                })

        # 7. Generer le rapport Markdown
        report = generate_llm_report(results, job_offer.filename, settings.provider, settings.model)

        # 8. Sauvegarder l'analyse
        analysis = Analysis(
            project_id=project_id,
            job_offer_id=request.job_offer_id,
            date=datetime.now(),
            report=report,
            keywords={"mode": "llm", "provider": settings.provider, "model": settings.model},
            folder_path=folder_path,
            results=results
        )
        db.add(analysis)
        db.commit()

        return {"report": report, "results": results}

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"ERROR in analyze_with_llm: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def parse_llm_response(analysis_text: str) -> dict:
    """
    Parse le score et la recommandation depuis la reponse LLM.

    Returns:
        dict avec 'score' (int ou None), 'recommendation' (str ou None), 'analysis' (str)
    """
    score = None
    recommendation = None

    # Parser le score (format: "SCORE: XX/100" ou "SCORE: XX")
    score_match = re.search(r'SCORE:\s*(\d+)\s*(?:/100)?', analysis_text, re.IGNORECASE)
    if score_match:
        score = int(score_match.group(1))
        # S'assurer que le score est entre 0 et 100
        score = max(0, min(100, score))

    # Parser la recommandation
    rec_match = re.search(r'RECOMMANDATION:\s*(RETENIR|A_REVOIR|A REVOIR|REJETER)', analysis_text, re.IGNORECASE)
    if rec_match:
        recommendation = rec_match.group(1).upper().replace(' ', '_')

    return {
        'score': score,
        'recommendation': recommendation,
        'analysis': analysis_text
    }


def get_recommendation_emoji(recommendation: str) -> str:
    """Retourne l'emoji correspondant a la recommandation."""
    emojis = {
        'RETENIR': '✅',
        'A_REVOIR': '⚠️',
        'REJETER': '❌'
    }
    return emojis.get(recommendation, '❓')


def get_recommendation_label(recommendation: str) -> str:
    """Retourne le label lisible de la recommandation."""
    labels = {
        'RETENIR': 'Fortement recommandé',
        'A_REVOIR': 'À considérer',
        'REJETER': 'Non recommandé'
    }
    return labels.get(recommendation, 'Non évalué')


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

    # Generer le rapport
    report = f"""# 📊 Rapport d'Analyse IA

## Informations
| | |
|---|---|
| **Offre d'emploi** | {job_offer_name} |
| **Provider** | {provider} |
| **Modèle** | {model} |
| **CVs analysés** | {len(results)} |
| **Date** | {datetime.now().strftime('%d/%m/%Y à %H:%M')} |

---

## 🏆 Synthèse et Classement

"""

    if parsed_results:
        # Tableau de classement
        report += "| Rang | Candidat | Score | Recommandation |\n"
        report += "|:----:|----------|:-----:|----------------|\n"

        for i, r in enumerate(parsed_results, 1):
            score_str = f"{r['score']}/100" if r['score'] is not None else "N/A"
            rec_emoji = get_recommendation_emoji(r['recommendation'])
            rec_label = get_recommendation_label(r['recommendation'])
            report += f"| {i} | {r['filename']} | **{score_str}** | {rec_emoji} {rec_label} |\n"

        report += "\n"

        # Top 3 resume
        top_3 = [r for r in parsed_results if r['score'] is not None][:3]
        if top_3:
            report += "### 🎯 Top 3 Profils\n\n"
            for i, r in enumerate(top_3, 1):
                # Extraire le resume du profil depuis l'analyse
                resume_match = re.search(r'## Resume du Profil\s*\n(.*?)(?=\n##|\Z)', r['analysis'], re.DOTALL | re.IGNORECASE)
                resume = resume_match.group(1).strip() if resume_match else "Profil analysé"
                # Limiter a 150 caracteres
                if len(resume) > 150:
                    resume = resume[:147] + "..."
                report += f"{i}. **{r['filename']}** ({r['score']}/100) - {resume}\n\n"

        report += "\n---\n\n"

        # Analyses detaillees
        report += f"## 📄 Analyses Détaillées\n\n"

        for i, r in enumerate(parsed_results, 1):
            score_str = f"{r['score']}/100" if r['score'] is not None else "N/A"
            rec_emoji = get_recommendation_emoji(r['recommendation'])
            report += f"### {i}. {r['filename']}\n\n"
            report += f"**Score: {score_str}** | **Recommandation: {rec_emoji} {get_recommendation_label(r['recommendation'])}**\n\n"

            # Retirer les lignes SCORE et RECOMMANDATION du texte d'analyse
            clean_analysis = re.sub(r'^SCORE:.*$', '', r['analysis'], flags=re.MULTILINE | re.IGNORECASE)
            clean_analysis = re.sub(r'^RECOMMANDATION:.*$', '', clean_analysis, flags=re.MULTILINE | re.IGNORECASE)
            clean_analysis = clean_analysis.strip()

            report += clean_analysis
            report += "\n\n---\n\n"

    # Erreurs
    if failed:
        report += f"## ⚠️ Erreurs ({len(failed)} CVs)\n\n"
        for result in failed:
            report += f"- **{result['filename']}**: {result.get('error', 'Erreur inconnue')}\n"
        report += "\n"

    return report
