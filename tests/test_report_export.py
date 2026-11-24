import io

import pytest
from openpyxl import load_workbook
from PyPDF2 import PdfReader

from src.services import report_export


def make_results(n):
    results = [
        {
            "filename": f"cv_{i}.pdf",
            "success": True,
            "analysis": (
                f"SCORE: {i % 100}/100\nRECOMMANDATION: A_REVOIR\n## Avis court\nProfil <{i}> & co\n"
                "## Points Forts\n- **Python** solide\n## Avis sur les réponses\nReponses coherentes\n"
            ),
            "wtj": {"years_exp": 2.0, "wtj_url": "http://w/x", "city": "Paris", "title": "DS"},
        }
        for i in range(n)
    ]
    results.append({"filename": "bad.pdf", "success": False, "error": "PDF vide"})
    return results


INFO = {"offer": "Offre.pdf", "provider": "azure_openai", "model": "m", "date": "01/01/2026"}


def test_xlsx_ranking_and_answers():
    wb = load_workbook(io.BytesIO(report_export.build_xlsx(make_results(5), INFO)))
    ws = wb["Classement"]
    assert ws.cell(4, 2).value == "cv_4.pdf"  # best score first
    assert "coherentes" in ws.cell(4, 10).value
    assert wb["Erreurs"].cell(2, 1).value == "bad.pdf"


def test_html_is_standalone_and_escaped():
    doc = report_export.build_html(make_results(3), INFO)
    assert doc.count("<details") == 3 and "<script>" in doc
    assert "&lt;2&gt;" in doc and "<strong>Python</strong>" in doc


@pytest.mark.parametrize("n", [3, 311])
def test_pdf_is_valid_and_paginated(n):
    reader = PdfReader(io.BytesIO(report_export.build_pdf(make_results(n), INFO)))
    text = "\n".join(p.extract_text() for p in reader.pages)
    assert "Classement" in text and "des profils" in text
    assert (len(reader.pages) > 5) == (n > 100)


def test_markdown_table_rendered_even_with_blank_lines():
    md = "| A | B |\n\n|---|---:|\n\n| **x** | 1 |\n\nTexte"
    out = report_export.markdown_to_html(md)
    assert "<th>A</th>" in out and "<td><strong>x</strong></td>" in out and "|" not in out
    assert out.count("<table>") == 1 and "<p>Texte</p>" in out
