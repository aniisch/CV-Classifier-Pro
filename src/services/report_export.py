"""Parsing of LLM results and report exports (standalone HTML, Excel, summary PDF)."""
import html
import io
import re
from datetime import datetime
from typing import Any, Dict, List, Optional


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


def extract_short_opinion(analysis: str, limit: int = 220) -> str:
    """Return the short opinion of an analysis, falling back to the profile summary.

    Args:
        analysis: Raw LLM analysis text.
        limit: Maximum length of the returned text.

    Returns:
        A one-line opinion, truncated to ``limit`` characters.
    """
    for heading in ("Avis court", "Resume du Profil", "Résumé du Profil"):
        m = re.search(rf'##\s*{heading}\s*\n(.*?)(?=\n##|\Z)', analysis, re.DOTALL | re.IGNORECASE)
        if m and m.group(1).strip():
            text = " ".join(m.group(1).split())
            return text if len(text) <= limit else text[:limit - 3] + "..."
    return "Profil analysé"


def extract_section(analysis: str, heading: str) -> str:
    """Return the body of a ``## heading`` section of an analysis, or an empty string.

    Args:
        analysis: Raw LLM analysis text.
        heading: Section title, matched case-insensitively (accents ignored for "reponses").

    Returns:
        The stripped section text.
    """
    pattern = heading.replace("reponses", "r[ée]ponses")
    m = re.search(rf'##\s*{pattern}\s*\n(.*?)(?=\n##|\Z)', analysis, re.DOTALL | re.IGNORECASE)
    return m.group(1).strip() if m else ""


def clean_analysis(analysis: str) -> str:
    """Strip the SCORE / RECOMMANDATION header lines from an analysis."""
    text = re.sub(r'^SCORE:.*$', '', analysis, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'^RECOMMANDATION:.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    return text.strip()


def rank_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Parse stored LLM results into a ranked list.

    Args:
        results: ``Analysis.results`` of an LLM analysis.

    Returns:
        Dict with ``ranked`` (sorted by score, unscored last) and ``failed`` lists.
    """
    ranked = []
    for r in results:
        if not r.get("success"):
            continue
        parsed = parse_llm_response(r.get("analysis", ""))
        wtj = r.get("wtj") or {}
        ranked.append({
            "filename": r["filename"],
            "score": parsed["score"],
            "recommendation": get_recommendation_label(parsed["recommendation"]),
            "opinion": extract_short_opinion(parsed["analysis"]),
            "answers_opinion": extract_section(parsed["analysis"], "Avis sur les reponses"),
            "analysis": clean_analysis(parsed["analysis"]),
            "years_exp": wtj.get("years_exp"),
            "city": wtj.get("city", ""),
            "title": wtj.get("title", ""),
            "wtj_url": wtj.get("wtj_url", ""),
        })
    ranked.sort(key=lambda x: (x["score"] is not None, x["score"] or 0), reverse=True)
    failed = [r for r in results if not r.get("success")]
    return {"ranked": ranked, "failed": failed}


def _score_text(score: Optional[int]) -> str:
    return f"{score}/100" if score is not None else "N/A"


def _inline(text: str) -> str:
    """Escape text and render **bold** for the HTML export."""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html.escape(text))


def _table_cells(line: str) -> List[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _is_table_separator(line: str) -> bool:
    return bool(re.fullmatch(r"\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?", line.strip()))


def markdown_to_html(text: str) -> str:
    """Convert the limited markdown of the analyses (headings, lists, tables, bold) to HTML.

    Args:
        text: Markdown text of an analysis.

    Returns:
        The HTML fragment.
    """
    out: List[str] = []
    in_list = False
    lines = [ln for ln in text.splitlines()]
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        stripped = line.strip()
        if stripped.startswith("|"):
            # Les lignes vides entre les lignes d'un tableau sont ignorees
            block = [stripped]
            while i < len(lines) and (lines[i].strip().startswith("|") or not lines[i].strip()):
                if lines[i].strip():
                    block.append(lines[i].strip())
                elif i + 1 >= len(lines) or not lines[i + 1].strip().startswith("|"):
                    break
                i += 1
            if in_list:
                out.append("</ul>")
                in_list = False
            header = _table_cells(block[0])
            body = [_table_cells(b) for b in block[1:] if not _is_table_separator(b)]
            out.append("<table><thead><tr>" + "".join(f"<th>{_inline(c)}</th>" for c in header) + "</tr></thead><tbody>")
            for cells in body:
                out.append("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in cells) + "</tr>")
            out.append("</tbody></table>")
            continue
        is_item = stripped.startswith(("- ", "* "))
        if in_list and not is_item:
            out.append("</ul>")
            in_list = False
        if not stripped:
            continue
        if stripped.startswith("#"):
            level = min(len(stripped) - len(stripped.lstrip("#")) + 2, 6)
            out.append(f"<h{level}>{_inline(stripped.lstrip('# '))}</h{level}>")
        elif is_item:
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{_inline(stripped[2:])}</li>")
        else:
            out.append(f"<p>{_inline(stripped)}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


_HTML_STYLE = """
body{font-family:Segoe UI,Arial,sans-serif;margin:2rem auto;max-width:1100px;color:#222;padding:0 1rem}
h1{color:#1565c0}table{border-collapse:collapse;width:100%;margin:1rem 0}
th,td{border:1px solid #ddd;padding:6px 10px;text-align:left}th{background:#1565c0;color:#fff;cursor:pointer}
tr:nth-child(even){background:#f7f7f7}input{padding:6px;width:100%;box-sizing:border-box;margin:.5rem 0}
details{border:1px solid #ddd;border-radius:6px;margin:.4rem 0;padding:.4rem .8rem}
summary{cursor:pointer;font-weight:600}.meta{color:#555}.err{color:#b00020}
"""

_HTML_SCRIPT = """
const q=document.getElementById('q');
q.addEventListener('input',()=>{const v=q.value.toLowerCase();
document.querySelectorAll('#rank tbody tr').forEach(r=>r.style.display=r.textContent.toLowerCase().includes(v)?'':'none');
document.querySelectorAll('details').forEach(d=>d.style.display=d.dataset.name.toLowerCase().includes(v)?'':'none');});
document.querySelectorAll('#rank th').forEach((th,i)=>th.addEventListener('click',()=>{
const tb=document.querySelector('#rank tbody');const rows=[...tb.rows];const asc=th.dataset.asc!=='1';th.dataset.asc=asc?'1':'0';
const val=r=>{const t=r.cells[i].textContent.trim();const n=parseFloat(t);return isNaN(n)?t.toLowerCase():n};
rows.sort((a,b)=>{const x=val(a),y=val(b);return (x>y?1:x<y?-1:0)*(asc?1:-1)});rows.forEach(r=>tb.appendChild(r));}));
document.getElementById('open').onclick=()=>document.querySelectorAll('details').forEach(d=>d.open=true);
document.getElementById('close').onclick=()=>document.querySelectorAll('details').forEach(d=>d.open=false);
"""


def build_html(results: List[Dict[str, Any]], info: Dict[str, str]) -> str:
    """Build a standalone HTML report (inline CSS/JS, native ``<details>`` accordions).

    Args:
        results: ``Analysis.results`` of an LLM analysis.
        info: Header values (``offer``, ``provider``, ``model``, ``date``).

    Returns:
        The full HTML document.
    """
    data = rank_results(results)
    ranked = data["ranked"]
    e = html.escape
    rows = []
    for i, r in enumerate(ranked, 1):
        link = f'<a href="{e(r["wtj_url"])}" target="_blank" rel="noopener">WTJ</a>' if r["wtj_url"] else "-"
        years = f'{r["years_exp"]:g}' if r["years_exp"] is not None else "-"
        rows.append(
            f"<tr><td>{i}</td><td>{e(r['filename'])}</td><td>{e(_score_text(r['score']))}</td>"
            f"<td>{e(r['recommendation'])}</td><td>{years}</td><td>{link}</td>"
            f"<td>{e(r['opinion'])}</td></tr>"
        )
    details = []
    for i, r in enumerate(ranked, 1):
        details.append(
            f'<details data-name="{e(r["filename"])}"><summary>{i}. {e(r["filename"])} '
            f'- {e(_score_text(r["score"]))} - {e(r["recommendation"])}</summary>'
            f"{markdown_to_html(r['analysis'])}</details>"
        )
    errors = "".join(
        f'<li class="err"><strong>{e(f["filename"])}</strong> : {e(str(f.get("error", "Erreur inconnue")))}</li>'
        for f in data["failed"]
    )
    return f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><title>Rapport d'analyse IA</title>
<style>{_HTML_STYLE}</style></head><body>
<h1>Rapport d'analyse IA</h1>
<p class="meta">Offre : <strong>{e(info.get('offer', ''))}</strong> | Provider : {e(info.get('provider', ''))}
| Modèle : {e(info.get('model', ''))} | Date : {e(info.get('date', ''))} | CVs analysés : {len(results)}</p>
<h2>Classement</h2>
<input id="q" placeholder="Rechercher un candidat...">
<table id="rank"><thead><tr><th>Rang</th><th>Candidat</th><th>Score</th><th>Recommandation</th>
<th>Exp. (ans)</th><th>WTJ</th><th>Avis court</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<h2>Analyses détaillées</h2>
<p><button id="open">Tout ouvrir</button> <button id="close">Tout fermer</button></p>
{''.join(details)}
{f'<h2>Erreurs ({len(data["failed"])})</h2><ul>{errors}</ul>' if errors else ''}
<script>{_HTML_SCRIPT}</script></body></html>"""


def build_xlsx(results: List[Dict[str, Any]], info: Dict[str, str]) -> bytes:
    """Build an Excel workbook with the ranking and the full analyses.

    Args:
        results: ``Analysis.results`` of an LLM analysis.
        info: Header values (``offer``, ``provider``, ``model``, ``date``).

    Returns:
        The ``.xlsx`` file content.
    """
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    data = rank_results(results)
    wb = Workbook()
    ws = wb.active
    ws.title = "Classement"
    ws.append([f"Offre : {info.get('offer', '')}", f"Date : {info.get('date', '')}",
               f"Modèle : {info.get('model', '')}"])
    ws.append([])
    headers = ["Rang", "Candidat", "Score", "Recommandation", "Exp. (ans)", "Ville", "Titre",
               "Lien WTJ", "Avis court", "Avis sur les réponses"]
    ws.append(headers)
    for cell in ws[3]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1565C0")
    for i, r in enumerate(data["ranked"], 1):
        ws.append([i, r["filename"], r["score"], r["recommendation"], r["years_exp"], r["city"],
                   r["title"], r["wtj_url"], r["opinion"], r["answers_opinion"][:32000]])
    widths = [6, 38, 8, 20, 10, 16, 28, 40, 60, 60]
    for idx, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(idx)].width = w
    for row in ws.iter_rows(min_row=4):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "A4"
    ws.auto_filter.ref = f"A3:{get_column_letter(len(headers))}{max(ws.max_row, 3)}"

    detail = wb.create_sheet("Analyses")
    detail.append(["Candidat", "Analyse complète"])
    for cell in detail[1]:
        cell.font = Font(bold=True)
    for r in data["ranked"]:
        detail.append([r["filename"], r["analysis"][:32000]])
    detail.column_dimensions["A"].width = 38
    detail.column_dimensions["B"].width = 120
    for row in detail.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    if data["failed"]:
        errs = wb.create_sheet("Erreurs")
        errs.append(["Candidat", "Erreur"])
        for f in data["failed"]:
            errs.append([f["filename"], str(f.get("error", ""))])
        errs.column_dimensions["A"].width = 38
        errs.column_dimensions["B"].width = 80

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def build_pdf(results: List[Dict[str, Any]], info: Dict[str, str], top_n: int = 10) -> bytes:
    """Build a summary PDF: ranking table (rows never split) and top N opinions.

    Args:
        results: ``Analysis.results`` of an LLM analysis.
        info: Header values (``offer``, ``provider``, ``model``, ``date``).
        top_n: Number of profiles detailed after the table.

    Returns:
        The PDF file content.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    data = rank_results(results)
    styles = getSampleStyleSheet()
    cell = ParagraphStyle("cell", parent=styles["BodyText"], fontSize=8, leading=10)
    head = ParagraphStyle("head", parent=cell, textColor=colors.white, fontName="Helvetica-Bold")
    esc = html.escape

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=15 * mm, bottomMargin=15 * mm, title="Rapport d'analyse IA")
    story: List[Any] = [
        Paragraph("Rapport d'analyse IA", styles["Title"]),
        Paragraph(
            f"Offre : <b>{esc(info.get('offer', ''))}</b><br/>Provider : {esc(info.get('provider', ''))}"
            f" - Modèle : {esc(info.get('model', ''))}<br/>Date : {esc(info.get('date', ''))}"
            f" - CVs analysés : {len(results)}", styles["BodyText"]),
        Spacer(1, 6 * mm),
        Paragraph("Classement", styles["Heading2"]),
    ]
    has_exp = any(r["years_exp"] is not None for r in data["ranked"])
    cols = ["Rang", "Candidat", "Score", "Recommandation"] + (["Exp. (ans)"] if has_exp else [])
    widths = [12 * mm, 78 * mm, 18 * mm, 40 * mm] + ([22 * mm] if has_exp else [])
    widths[1] += 180 * mm - sum(widths)
    table_data = [[Paragraph(c, head) for c in cols]]
    for i, r in enumerate(data["ranked"], 1):
        row = [Paragraph(str(i), cell), Paragraph(esc(r["filename"]), cell),
               Paragraph(esc(_score_text(r["score"])), cell), Paragraph(esc(r["recommendation"]), cell)]
        if has_exp:
            row.append(Paragraph(f'{r["years_exp"]:g}' if r["years_exp"] is not None else "-", cell))
        table_data.append(row)
    table = Table(table_data, colWidths=widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1565c0")),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6f8")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(table)

    top = [r for r in data["ranked"] if r["score"] is not None][:top_n]
    if top:
        story += [Spacer(1, 8 * mm), Paragraph(f"Top {len(top)} des profils", styles["Heading2"])]
        for i, r in enumerate(top, 1):
            story.append(Paragraph(
                f"<b>{i}. {esc(r['filename'])}</b> ({esc(_score_text(r['score']))}) : {esc(r['opinion'])}",
                styles["BodyText"]))
            story.append(Spacer(1, 2 * mm))
    if data["failed"]:
        story += [Spacer(1, 6 * mm), Paragraph(f"Erreurs ({len(data['failed'])} CVs)", styles["Heading2"])]
        for f in data["failed"]:
            story.append(Paragraph(f"{esc(f['filename'])} : {esc(str(f.get('error', '')))}", cell))
    doc.build(story)
    return buffer.getvalue()


def report_info(offer_name: str, provider: str, model: str, date: Optional[datetime]) -> Dict[str, str]:
    """Build the header values shared by the exports."""
    when = date or datetime.now()
    return {"offer": offer_name, "provider": provider, "model": model,
            "date": when.strftime("%d/%m/%Y à %H:%M")}
