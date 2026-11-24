"""
LLM Jobs - Execution en arriere-plan des analyses LLM (gros lots de CVs).

Chaque CV est un LLMJobItem sauvegarde des que son resultat arrive : un lot
interrompu (arret de l'app, annulation, erreurs) peut etre repris sans refaire
les CVs deja traites.
"""

import asyncio
import os
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database.database import SessionLocal
from .wtj_import import build_candidate_context, candidate_to_dict
from ..database.models import Analysis, JobOffer, LLMJob, LLMJobItem, WtjCandidate

ACTIVE_STATUSES = ("running", "cancelled", "interrupted", "failed")

# Taches asyncio en cours, par job_id
_running: Dict[str, "asyncio.Task[None]"] = {}


def extract_pdf_text(filepath: str) -> str:
    """Extrait le texte d'un PDF (bloquant : a appeler via asyncio.to_thread)."""
    from PyPDF2 import PdfReader

    reader = PdfReader(filepath)
    return "".join((page.extract_text() or "") for page in reader.pages)


def get_concurrency(provider: str) -> int:
    """Concurrence : LLM_CONCURRENCY, sinon 1 pour Ollama et 8 pour le cloud."""
    default = 1 if provider == "ollama" else 8
    try:
        return max(1, int(os.environ.get("LLM_CONCURRENCY", default)))
    except ValueError:
        return default


def is_running(job_id: str) -> bool:
    task = _running.get(job_id)
    return task is not None and not task.done()


def list_pdf_files(folder_path: str, cv_files: Optional[List[str]] = None) -> List[str]:
    """Liste les PDF a analyser (selection explicite ou tout le dossier)."""
    if cv_files:
        names = [f for f in cv_files if f.lower().endswith(".pdf")]
    else:
        names = sorted(f for f in os.listdir(folder_path) if f.lower().endswith(".pdf"))
    return list(dict.fromkeys(names))  # sans doublons, ordre conserve


def create_job(
    db: Session,
    project_id: str,
    job_offer_id: str,
    folder_path: str,
    filenames: List[str],
    provider: str,
    model: str,
    custom_prompt: str = "",
) -> LLMJob:
    """Cree le lot et ses items (tous 'pending')."""
    job = LLMJob(
        project_id=project_id,
        job_offer_id=job_offer_id,
        folder_path=folder_path,
        provider=provider,
        model=model,
        custom_prompt=(custom_prompt or "").strip(),
        status="running",
    )
    db.add(job)
    db.flush()
    db.add_all(
        LLMJobItem(job_id=job.id, position=i, filename=name, status="pending")
        for i, name in enumerate(filenames)
    )
    db.commit()
    db.refresh(job)
    return job


def build_context(custom_prompt: str, candidate: Optional[WtjCandidate]) -> Optional[str]:
    """Combine the per-run custom prompt and the WTJ data of a candidate.

    Args:
        custom_prompt: Recruiter instructions for this run (may be empty).
        candidate: WTJ data matching the CV, if any.

    Returns:
        The extra prompt context, or None when there is nothing to add.
    """
    parts = []
    if custom_prompt:
        parts.append(f"INSTRUCTIONS DU RECRUTEUR (prioritaires) :\n{custom_prompt}")
    if candidate is not None:
        parts.append(build_candidate_context(candidate))
        if not custom_prompt:
            parts.append(
                "Compare ces donnees et les reponses du candidat avec son CV et l'offre ; "
                "signale toute incoherence."
            )
    return "\n\n".join(parts) or None


def get_progress(db: Session, job_id: str) -> Dict[str, int]:
    """Compteurs de progression calcules depuis les items."""
    rows = (
        db.query(LLMJobItem.status, func.count(LLMJobItem.id))
        .filter(LLMJobItem.job_id == job_id)
        .group_by(LLMJobItem.status)
        .all()
    )
    counts = {status: n for status, n in rows}
    ok = counts.get("ok", 0)
    error = counts.get("error", 0)
    pending = counts.get("pending", 0)
    return {"total": ok + error + pending, "done": ok + error, "ok": ok, "error": error, "pending": pending}


def job_to_dict(db: Session, job: LLMJob) -> Dict[str, Any]:
    return {
        "id": job.id,
        "project_id": job.project_id,
        "job_offer_id": job.job_offer_id,
        "status": job.status if job.status != "running" or is_running(job.id) else "interrupted",
        "job_error": job.error or "",
        "provider": job.provider,
        "model": job.model,
        "analysis_id": job.analysis_id,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        **get_progress(db, job.id),
    }


def mark_interrupted_jobs(db: Session) -> int:
    """Au demarrage : les lots restes 'running' (app fermee) deviennent 'interrupted'."""
    jobs = db.query(LLMJob).filter(LLMJob.status == "running").all()
    for job in jobs:
        job.status = "interrupted"
    db.commit()
    return len(jobs)


def collect_results(db: Session, job_id: str) -> List[Dict[str, Any]]:
    """Resultats des items traites, dans l'ordre d'origine."""
    items = (
        db.query(LLMJobItem)
        .filter(LLMJobItem.job_id == job_id, LLMJobItem.status != "pending")
        .order_by(LLMJobItem.position)
        .all()
    )
    return [item.result for item in items if item.result]


def _finalize(
    session_factory: Callable[[], Session],
    job_id: str,
    report_fn: Callable[[list, str, str, str], str],
) -> None:
    """Genere le rapport et cree (ou met a jour) l'Analysis du lot."""
    db = session_factory()
    try:
        job = db.get(LLMJob, job_id)
        offer = db.get(JobOffer, job.job_offer_id)
        results = collect_results(db, job_id)
        report = report_fn(results, offer.filename if offer else "", job.provider, job.model)

        analysis = db.get(Analysis, job.analysis_id) if job.analysis_id else None
        if analysis is None:
            analysis = Analysis(
                project_id=job.project_id,
                job_offer_id=job.job_offer_id,
                date=datetime.now(),
                folder_path=job.folder_path,
                keywords={"mode": "llm", "provider": job.provider, "model": job.model},
            )
            db.add(analysis)
        analysis.report = report
        analysis.results = results
        db.flush()
        job.analysis_id = analysis.id
        job.status = "completed"
        db.commit()
    finally:
        db.close()


async def run_job(
    job_id: str,
    report_fn: Callable[[list, str, str, str], str],
    session_factory: Callable[[], Session] = SessionLocal,
    manager_factory: Optional[Callable[[Session], Any]] = None,
    extract_fn: Callable[[str], str] = extract_pdf_text,
) -> None:
    """
    Traite les items 'pending' d'un lot. Chaque resultat est sauvegarde
    immediatement ; la lecture des PDF se fait dans un thread.
    """
    if manager_factory is None:
        from .llm_manager import LLMManager

        manager_factory = LLMManager

    db = session_factory()
    try:
        job = db.get(LLMJob, job_id)
        offer = db.get(JobOffer, job.job_offer_id)
        if offer is None:
            raise RuntimeError("Offre d'emploi introuvable")
        offer_content = offer.raw_content or ""
        folder_path = job.folder_path
        provider = job.provider
        custom_prompt = job.custom_prompt or ""
        candidates = {
            c.cv_fichier: c
            for c in db.query(WtjCandidate).filter(WtjCandidate.project_id == job.project_id)
        }
        contexts = {name: build_context(custom_prompt, c) for name, c in candidates.items()}
        default_context = build_context(custom_prompt, None)
        wtj_data = {name: candidate_to_dict(c) for name, c in candidates.items()}
        job.status = "running"
        job.error = ""
        db.commit()

        manager = manager_factory(db)
        manager._get_adapter()  # charge les settings une fois, la session peut etre fermee ensuite
        pending = [
            (item.id, item.filename)
            for item in db.query(LLMJobItem)
            .filter(LLMJobItem.job_id == job_id, LLMJobItem.status == "pending")
            .order_by(LLMJobItem.position)
            .all()
        ]
    except Exception as e:
        db.rollback()
        job = db.get(LLMJob, job_id)
        if job is not None:
            job.status = "failed"
            job.error = str(e)
            db.commit()
        print(f"[LLM] Lot {job_id} echoue: {e}")
        db.close()
        return
    db.close()

    semaphore = asyncio.Semaphore(get_concurrency(provider))

    def save(item_id: int, status: str, result: Dict[str, Any]) -> None:
        session = session_factory()
        try:
            item = session.get(LLMJobItem, item_id)
            item.status = status
            item.result = result
            session.commit()
        finally:
            session.close()

    async def process(item_id: int, filename: str) -> None:
        async with semaphore:
            try:
                filepath = os.path.join(folder_path, filename)
                if not os.path.exists(filepath):
                    raise FileNotFoundError("Fichier introuvable")
                text = await asyncio.to_thread(extract_fn, filepath)
                if not text.strip():
                    raise ValueError("Aucun texte extractible (PDF scanne ou vide)")
                response = await manager.analyze_cv(cv_content=text, job_offer_content=offer_content,
                    additional_context=contexts.get(filename, default_context),
                )
                print(f"[LLM] OK {filename}")
                save(item_id, "ok", {
                    "filename": filename,
                    "success": True,
                    "analysis": response.content,
                    "model": response.model,
                    "provider": response.provider,
                    "tokens": response.usage,
                    **({"wtj": wtj_data[filename]} if filename in wtj_data else {}),
                })
            except asyncio.CancelledError:
                raise
            except Exception as e:
                print(f"[LLM] ERREUR {filename}: {e}")
                save(item_id, "error", {"filename": filename, "success": False, "error": str(e)})

    try:
        await asyncio.gather(*(process(item_id, name) for item_id, name in pending))
        _finalize(session_factory, job_id, report_fn)
    except asyncio.CancelledError:
        session = session_factory()
        try:
            job = session.get(LLMJob, job_id)
            if job is not None and job.status == "running":
                job.status = "cancelled"
                session.commit()
        finally:
            session.close()
        raise
    except Exception as e:
        print(f"[LLM] Lot {job_id} echoue: {e}")
        session = session_factory()
        try:
            job = session.get(LLMJob, job_id)
            if job is not None:
                job.status = "failed"
                job.error = str(e)
                session.commit()
        finally:
            session.close()


def start_job(job_id: str, report_fn: Callable[[list, str, str, str], str], **kwargs: Any) -> None:
    """Lance run_job en tache de fond (a appeler depuis la boucle asyncio)."""
    if is_running(job_id):
        return
    task = asyncio.get_running_loop().create_task(run_job(job_id, report_fn, **kwargs))
    _running[job_id] = task

    def _done(t: "asyncio.Task[None]") -> None:
        if _running.get(job_id) is t:
            del _running[job_id]
        if not t.cancelled() and t.exception() is not None:
            print(f"[LLM] Lot {job_id} en erreur: {t.exception()}")

    task.add_done_callback(_done)


async def cancel_job(job_id: str) -> bool:
    """Annule la tache d'un lot et attend sa fin ; les CVs deja traites sont conserves."""
    task = _running.get(job_id)
    if task is None or task.done():
        return False
    task.cancel()
    await asyncio.wait([task])
    return True
