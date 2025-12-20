"""
Service d'analyse des CV
"""
import os
from pathlib import Path
import PyPDF2
import re
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ScoredCV:
    """Classe pour stocker les résultats d'analyse d'un CV"""
    filename: str
    score: float
    found_keywords: Dict[str, int]

class CVAnalyzer:
    def __init__(self, pdf_folder: str, keywords: Dict[str, float]):
        self.pdf_folder = Path(pdf_folder)
        self.keywords_original = keywords
        self.keywords_patterns = {
            self._create_case_insensitive_pattern(k): v
            for k, v in keywords.items()
        }
        self.failed_conversions = []

        # Validation que les pourcentages totalisent 100%
        total = sum(keywords.values())
        if not(99.5 <= total <= 100.5):
            raise ValueError(f"La somme des pourcentages doit être 100%. Actuellement: {total}%")

    def _create_case_insensitive_pattern(self, keyword: str) -> str:
        """Crée un pattern regex case-insensitive pour un mot-clé"""
        return f"\\b{re.escape(keyword)}\\b"

    def clean_text(self, text: str) -> str:
        """Nettoie le texte extrait"""
        text = text.replace('\n', ' ')
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s*([,.])\s*', r'\1 ', text)
        return text

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extrait le texte d'un PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ''
                for page in reader.pages:
                    text += page.extract_text() or ''
                return self.clean_text(text)
        except Exception as e:
            self.failed_conversions.append({
                'file': pdf_path.name,
                'error': str(e)
            })
            return ''

    def count_keywords(self, text: str) -> Dict[str, int]:
        """Compte les occurrences de chaque mot-clé"""
        keyword_counts = {}
        for pattern in self.keywords_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            count = len(matches)
            original_keyword = next(k for k in self.keywords_original.keys()
                                if self._create_case_insensitive_pattern(k) == pattern)
            keyword_counts[original_keyword] = count
        return keyword_counts

    def calculate_score(self, keyword_counts: Dict[str, int]) -> float:
        """Calcule le score: somme des poids des keywords trouvés"""
        score = 0
        for keyword, count in keyword_counts.items():
            if count > 0:  # Si le keyword est trouvé au moins une fois
                score += self.keywords_original[keyword]  # Ajouter son poids une seule fois
        return score

    def analyze_cvs(self) -> List[ScoredCV]:
        """Analyse tous les CVs du dossier"""
        results = []
        for pdf_file in self.pdf_folder.glob('*.pdf'):
            text = self.extract_text_from_pdf(pdf_file)
            if not text:
                continue
            keyword_counts = self.count_keywords(text)
            score = self.calculate_score(keyword_counts)

            results.append(ScoredCV(
                filename=pdf_file.name,
                score=score,
                found_keywords=keyword_counts
            ))

        return sorted(results, key=lambda x: x.score, reverse=True)

    def calculate_average_score(self, results: List[ScoredCV]) -> float:
        """Calcule le score moyen"""
        if not results:
            return 0
        return sum(cv.score for cv in results) / len(results)

    def calculate_best_score(self, results: List[ScoredCV]) -> float:
        """Calcule le meilleur score"""
        if not results:
            return 0
        return max(cv.score for cv in results)

    def generate_markdown_report(self, results: List[ScoredCV]) -> str:
        """Génère un rapport détaillé au format Markdown"""
        now = datetime.now()

        # En-tête du rapport
        report = [
            "# 📊 Rapport d'Analyse des CV",
            "",
            f"Généré le {now.strftime('%d %B %Y à %H:%M')}",
            "",
            "## 📋 Résumé",
            f"- 📁 Nombre total de CV analysés: **{len(results)}**",
            f"- ⭐ Score moyen: **{self.calculate_average_score(results):.1f}%**",
            f"- 🏆 Meilleur score: **{self.calculate_best_score(results):.1f}%**",
            "",
            "## 🎯 Critères d'évaluation",
            "| Compétence | Pondération |",
            "|------------|-------------|",
        ]

        # Ajouter les critères d'évaluation (sans multiplier par 100)
        for keyword, weight in self.keywords_original.items():
            # weight est déjà en pourcentage (100 = 100%), donc affiche tel quel
            report.append(f"| {keyword} | {weight}% |")

        report.append("")
        report.append("## 🏅 Top 3 des Candidats")

        # Top 3
        top_3 = results[:3] if len(results) >= 3 else results

        for cv in top_3:
            report.append(f"\n### 🏆 {cv.filename} ({cv.score:.1f}%)")
            report.append("| Compétence | Occurrences | Points |")
            report.append("|------------|-------------|---------|")

            for keyword, count in cv.found_keywords.items():
                weight = self.keywords_original.get(keyword, 0)
                # Points = le poids du keyword s'il est trouvé (déjà en %)
                points = weight if count > 0 else 0
                report.append(f"| {keyword} | {count} | {points}% |")

        # Résultats détaillés
        report.append("")
        report.append("## 📋 Résultats Détaillés")
        report.append("| Position | Candidat | Score | Compétences Clés |")
        report.append("|----------|----------|-------|------------------|")

        for idx, cv in enumerate(results, 1):
            # Construire la liste des compétences avec occurrences
            competences = []
            for keyword, count in cv.found_keywords.items():
                if count > 0:
                    competences.append(f"{keyword} ({count})")

            competences_str = ", ".join(competences) if competences else "Aucune"
            report.append(f"| {idx} | {cv.filename} | {cv.score:.1f}% | {competences_str} |")

        return "\n".join(report)
