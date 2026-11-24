"""Import of a Welcome to the Jungle candidates CSV export."""
import csv
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..database.models import WtjCandidate

CORE_COLUMNS = {
    "reference", "prenom", "nom", "email", "ville", "linkedin", "titre",
    "annees_exp", "exp_confiance", "exp_ok", "lien_wtj", "cv_fichier",
}
_TRUE = {"true", "1", "oui", "yes", "vrai"}
_FALSE = {"false", "0", "non", "no", "faux"}


def _parse_bool(value: str) -> Optional[bool]:
    """Convert a CSV cell to a bool, or None when empty/unknown."""
    v = (value or "").strip().lower()
    if v in _TRUE:
        return True
    if v in _FALSE:
        return False
    return None


def _parse_float(value: str) -> Optional[float]:
    """Convert a CSV cell (comma or dot decimal) to a float, or None."""
    try:
        return float((value or "").strip().replace(",", "."))
    except ValueError:
        return None


def parse_csv(path: str) -> List[Dict[str, Any]]:
    """Read the WTJ CSV (';' separated, UTF-8 with optional BOM).

    Args:
        path: Path of the CSV file.

    Returns:
        One dict per row that has a non-empty ``cv_fichier``.

    Raises:
        ValueError: If the ``cv_fichier`` column is missing.
    """
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        if not reader.fieldnames or "cv_fichier" not in reader.fieldnames:
            raise ValueError("Colonne 'cv_fichier' absente du CSV")
        return [r for r in reader if (r.get("cv_fichier") or "").strip()]


def import_csv(db: Session, project_id: str, path: str) -> Dict[str, int]:
    """Import (upsert) the CSV rows for a project, keyed on ``cv_fichier``.

    Args:
        db: Database session.
        project_id: Target project id.
        path: Path of the CSV file.

    Returns:
        Counters ``created``, ``updated`` and ``total``.

    Raises:
        ValueError: If the CSV has no ``cv_fichier`` column.
    """
    rows = parse_csv(path)
    existing = {
        c.cv_fichier: c
        for c in db.query(WtjCandidate).filter(WtjCandidate.project_id == project_id)
    }
    created = updated = 0
    for row in rows:
        name = row["cv_fichier"].strip()
        cand = existing.get(name)
        if cand is None:
            cand = WtjCandidate(project_id=project_id, cv_fichier=name)
            db.add(cand)
            existing[name] = cand
            created += 1
        else:
            updated += 1
        cand.reference = row.get("reference", "")
        cand.first_name = row.get("prenom", "")
        cand.last_name = row.get("nom", "")
        cand.email = row.get("email", "")
        cand.city = row.get("ville", "")
        cand.linkedin = row.get("linkedin", "")
        cand.title = row.get("titre", "")
        cand.years_exp = _parse_float(row.get("annees_exp", ""))
        cand.exp_confidence = row.get("exp_confiance", "")
        cand.exp_ok = _parse_bool(row.get("exp_ok", ""))
        cand.wtj_url = row.get("lien_wtj", "")
        cand.extra = {k: v for k, v in row.items() if k and k not in CORE_COLUMNS}
    db.commit()
    return {"created": created, "updated": updated, "total": len(rows)}


def candidate_to_dict(c: WtjCandidate) -> Dict[str, Any]:
    """Serialize a candidate for the API (without the bulky ``extra`` answers)."""
    return {
        "cv_fichier": c.cv_fichier,
        "reference": c.reference,
        "first_name": c.first_name,
        "last_name": c.last_name,
        "email": c.email,
        "city": c.city,
        "linkedin": c.linkedin,
        "title": c.title,
        "years_exp": c.years_exp,
        "exp_confidence": c.exp_confidence,
        "exp_ok": c.exp_ok,
        "wtj_url": c.wtj_url,
    }


def build_candidate_context(c: WtjCandidate) -> str:
    """Build the prompt block describing a candidate's WTJ application data.

    Args:
        c: Candidate imported from the WTJ export.

    Returns:
        Text with the structured fields and the candidate's own answers.
    """
    lines = ["Donnees de candidature (export Welcome to the Jungle) :"]
    if c.title:
        lines.append(f"- Titre declare : {c.title}")
    if c.city:
        lines.append(f"- Ville : {c.city}")
    if c.years_exp is not None:
        lines.append(f"- Annees d'experience : {c.years_exp:g} (confiance : {c.exp_confidence or 'n/a'})")
    if c.exp_ok is not None:
        lines.append(f"- Experience suffisante (exp_ok) : {'oui' if c.exp_ok else 'non'}")
    for key, value in (c.extra or {}).items():
        if value not in (None, "") and key.startswith("rep_"):
            lines.append(f"- Reponse '{key[4:]}' : {value}")
    if any(k.startswith("rep_") and v for k, v in (c.extra or {}).items()):
        lines.append(
            "Ajoute dans ton analyse une section '## Avis sur les reponses' : evalue la "
            "qualite et la coherence de ces reponses (par rapport au CV et a l'offre)."
        )
    return "\n".join(lines)


def filter_by_experience(
    db: Session,
    project_id: str,
    filenames: List[str],
    min_years: Optional[float],
    max_years: Optional[float],
) -> Dict[str, List[str]]:
    """Split CV filenames by the candidate's years of experience (WTJ data).

    Bounds are inclusive. A CV without WTJ data or without ``years_exp`` is kept
    and reported as unknown rather than silently excluded.

    Args:
        db: Database session.
        project_id: Project owning the WTJ candidates.
        filenames: CV filenames to filter.
        min_years: Minimum years (inclusive), or None.
        max_years: Maximum years (inclusive), or None.

    Returns:
        Dict with ``kept``, ``excluded`` and ``unknown`` filename lists
        (``unknown`` files are also part of ``kept``).
    """
    if min_years is None and max_years is None:
        return {"kept": list(filenames), "excluded": [], "unknown": []}
    years = {
        c.cv_fichier: c.years_exp
        for c in db.query(WtjCandidate).filter(WtjCandidate.project_id == project_id)
    }
    kept: List[str] = []
    excluded: List[str] = []
    unknown: List[str] = []
    for name in filenames:
        value = years.get(name)
        if value is None:
            kept.append(name)
            unknown.append(name)
        elif (min_years is not None and value < min_years) or (
            max_years is not None and value > max_years
        ):
            excluded.append(name)
        else:
            kept.append(name)
    return {"kept": kept, "excluded": excluded, "unknown": unknown}
