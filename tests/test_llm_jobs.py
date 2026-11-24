import asyncio
import threading
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Analysis, Base, JobOffer, LLMJob, LLMJobItem, Project
from src.services import llm_jobs


def report_fn(results, offer_name, provider, model):
    return f"{offer_name}|{provider}|{model}|{len(results)}"


@pytest.fixture
def session_factory(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, autoflush=False)
    db = factory()
    db.add(Project(id="p1", name="P"))
    db.add(JobOffer(id="o1", project_id="p1", filename="offre.pdf", raw_content="offre"))
    db.commit()
    db.close()
    return factory


def make_job(factory, names):
    db = factory()
    job = llm_jobs.create_job(db, "p1", "o1", "/cvs", names, "azure_openai", "m")
    job_id = job.id
    db.close()
    return job_id


class FakeManager:
    """Fait echouer les CVs dont le texte contient 'bad' tant que fail est actif."""

    fail = True
    calls = []
    gate = None
    current = 0
    peak = 0

    def __init__(self, db):
        pass

    def _get_adapter(self):
        return None

    async def analyze_cv(self, cv_content, job_offer_content, additional_context=None):
        FakeManager.calls.append(cv_content)
        FakeManager.current += 1
        FakeManager.peak = max(FakeManager.peak, FakeManager.current)
        try:
            if FakeManager.gate is not None:
                await FakeManager.gate.wait()
            else:
                await asyncio.sleep(0.01)
            if FakeManager.fail and "bad" in cv_content:
                raise Exception("boom")
            return SimpleNamespace(
                content=f"SCORE: 70/100 {cv_content}", model="m", provider="azure_openai", usage={}
            )
        finally:
            FakeManager.current -= 1


@pytest.fixture(autouse=True)
def reset_fake(monkeypatch):
    FakeManager.fail = True
    FakeManager.calls = []
    FakeManager.gate = None
    FakeManager.current = 0
    FakeManager.peak = 0
    llm_jobs._running.clear()
    monkeypatch.setenv("LLM_CONCURRENCY", "2")
    # extract_fn : le nom du fichier sert de contenu
    yield


def run(factory, job_id, extract_fn=lambda path: path.rsplit("/", 1)[-1]):
    return llm_jobs.run_job(
        job_id, report_fn, session_factory=factory, manager_factory=FakeManager, extract_fn=extract_fn
    )


def exists_everywhere(monkeypatch):
    monkeypatch.setattr(llm_jobs.os.path, "exists", lambda p: True)


def test_run_saves_each_result_and_resume_retries_only_errors(session_factory, monkeypatch):
    exists_everywhere(monkeypatch)
    job_id = make_job(session_factory, ["a.pdf", "bad.pdf", "c.pdf"])

    asyncio.run(run(session_factory, job_id))

    db = session_factory()
    progress = llm_jobs.get_progress(db, job_id)
    assert progress == {"total": 3, "done": 3, "ok": 2, "error": 1, "pending": 0}
    job = db.get(LLMJob, job_id)
    assert job.status == "completed"
    first_analysis_id = job.analysis_id
    assert [r["filename"] for r in db.get(Analysis, first_analysis_id).results] == ["a.pdf", "bad.pdf", "c.pdf"]
    db.close()

    # reprise : seul le CV en erreur est relance, l'Analysis est mise a jour (pas dupliquee)
    FakeManager.fail = False
    FakeManager.calls = []
    db = session_factory()
    db.query(LLMJobItem).filter(LLMJobItem.status == "error").update({"status": "pending", "result": None})
    db.commit()
    db.close()
    asyncio.run(run(session_factory, job_id))

    assert FakeManager.calls == ["bad.pdf"]
    db = session_factory()
    assert llm_jobs.get_progress(db, job_id)["ok"] == 3
    assert db.get(LLMJob, job_id).analysis_id == first_analysis_id
    assert db.query(Analysis).count() == 1
    assert all(r["success"] for r in db.get(Analysis, first_analysis_id).results)
    db.close()


def test_pdf_extraction_runs_off_the_event_loop_thread(session_factory, monkeypatch):
    exists_everywhere(monkeypatch)
    job_id = make_job(session_factory, ["a.pdf"])
    threads = []

    def extract(path):
        threads.append(threading.get_ident())
        return "text"

    asyncio.run(run(session_factory, job_id, extract_fn=extract))
    assert threads and threads[0] != threading.get_ident()


def test_concurrency_is_limited(session_factory, monkeypatch):
    exists_everywhere(monkeypatch)
    job_id = make_job(session_factory, [f"{i}.pdf" for i in range(8)])
    asyncio.run(run(session_factory, job_id))
    assert FakeManager.peak == 2


def test_unreadable_pdf_is_an_item_error(session_factory, monkeypatch):
    exists_everywhere(monkeypatch)
    job_id = make_job(session_factory, ["a.pdf"])
    asyncio.run(run(session_factory, job_id, extract_fn=lambda p: "  "))
    db = session_factory()
    item = db.query(LLMJobItem).one()
    assert item.status == "error" and "extractible" in item.result["error"]
    assert db.get(LLMJob, job_id).status == "completed"


def test_cancel_keeps_done_items_and_job_is_resumable(session_factory, monkeypatch):
    exists_everywhere(monkeypatch)
    job_id = make_job(session_factory, ["a.pdf", "b.pdf", "c.pdf", "d.pdf"])

    async def scenario():
        FakeManager.gate = asyncio.Event()
        llm_jobs.start_job(
            job_id, report_fn, session_factory=session_factory,
            manager_factory=FakeManager, extract_fn=lambda p: p.rsplit("/", 1)[-1],
        )
        await asyncio.sleep(0.1)
        assert llm_jobs.is_running(job_id)
        assert await llm_jobs.cancel_job(job_id) is True
        assert not llm_jobs.is_running(job_id)

    asyncio.run(scenario())

    db = session_factory()
    assert db.get(LLMJob, job_id).status == "cancelled"
    assert llm_jobs.get_progress(db, job_id)["pending"] == 4
    assert llm_jobs.job_to_dict(db, db.get(LLMJob, job_id))["status"] == "cancelled"
    db.close()

    FakeManager.gate = None
    FakeManager.fail = False
    asyncio.run(run(session_factory, job_id))
    db = session_factory()
    assert db.get(LLMJob, job_id).status == "completed"
    assert llm_jobs.get_progress(db, job_id)["ok"] == 4


def test_running_jobs_become_interrupted_at_startup(session_factory):
    job_id = make_job(session_factory, ["a.pdf"])
    db = session_factory()
    assert llm_jobs.mark_interrupted_jobs(db) == 1
    assert db.get(LLMJob, job_id).status == "interrupted"
    assert llm_jobs.job_to_dict(db, db.get(LLMJob, job_id))["status"] == "interrupted"


def test_missing_offer_marks_job_failed(session_factory):
    job_id = make_job(session_factory, ["a.pdf"])
    db = session_factory()
    db.delete(db.get(JobOffer, "o1"))
    db.commit()
    db.close()
    asyncio.run(run(session_factory, job_id))
    db = session_factory()
    job = db.get(LLMJob, job_id)
    assert job.status == "failed" and "Offre" in job.error


def test_list_pdf_files_filters_and_dedups(tmp_path):
    (tmp_path / "b.pdf").write_text("x")
    (tmp_path / "a.PDF").write_text("x")
    (tmp_path / "n.txt").write_text("x")
    assert llm_jobs.list_pdf_files(str(tmp_path)) == ["a.PDF", "b.pdf"]
    assert llm_jobs.list_pdf_files(str(tmp_path), ["z.pdf", "z.pdf", "y.txt"]) == ["z.pdf"]


def test_build_context():
    from src.database.models import WtjCandidate

    cand = WtjCandidate(project_id="p1", cv_fichier="a.pdf", years_exp=5.0, exp_ok=False,
                        extra={"rep_projet": "CUBIA"})
    assert llm_jobs.build_context("", None) is None
    assert "INSTRUCTIONS DU RECRUTEUR" in llm_jobs.build_context("Azure", None)
    ctx = llm_jobs.build_context("Azure", cand)
    assert "CUBIA" in ctx and "exp_ok" in ctx and "Compare" not in ctx
    assert "Compare" in llm_jobs.build_context("", cand)


def test_generate_llm_report_top10_and_wtj():
    from src.services.api import extract_short_opinion, generate_llm_report

    def res(i):
        return {"filename": f"c{i}.pdf", "success": True,
                "analysis": f"SCORE: {90 - i}/100\nRECOMMANDATION: RETENIR\n## Avis court\nBon profil {i}\n",
                "wtj": {"years_exp": 2.0, "wtj_url": f"http://w/{i}"}}

    report = generate_llm_report([res(i) for i in range(12)], "offre.pdf", "p", "m")
    assert "### Top 10 des profils" in report and "Bon profil 9" in report
    assert "Bon profil 10" not in report.split("## Analyses")[0]
    assert "| Exp. (ans) | WTJ |" in report and "[WTJ](http://w/0)" in report
    assert "### 1. " not in report and "📊" not in report
    assert extract_short_opinion("## Resume du Profil\nAbc") == "Abc"
