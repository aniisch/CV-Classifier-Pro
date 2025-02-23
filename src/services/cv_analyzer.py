"""
Service d'analyse des CV
"""
import os
from pathlib import Path
import PyPDF2
import re
from typing import Dict, List, Tuple
from dataclasses import dataclass
from collections import defaultdict
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
    
    def clean_text(self, text: str) -> str:
        text = text.replace('\n', ' ')
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s*([,.])\s*', r'\1 ', text)
        return text
    
    def _create_case_insensitive_pattern(self, keyword: str) -> str:
        return re.escape(keyword)
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return self.clean_text(text)
        except Exception as e:
            self.failed_conversions.append((pdf_path.name, str(e)))
            return ""
    
    def count_keywords(self, text: str) -> Dict[str, int]:
        keyword_counts = {}
        for pattern in self.keywords_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            count = len(matches)
            original_keyword = next(k for k in self.keywords_original.keys() 
                                if self._create_case_insensitive_pattern(k) == pattern)
            keyword_counts[original_keyword] = count
        return keyword_counts

    def calculate_score(self, keyword_counts: Dict[str, int]) -> float:
        score = 0
        for keyword, count in keyword_counts.items():
            if count > 0:
                score += self.keywords_original[keyword]
        return score
    
    def analyze_cvs(self) -> List[ScoredCV]:
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
        return sum(cv.score for cv in results) / len(results)

    def calculate_best_score(self, results: List[ScoredCV]) -> float:
        return max(cv.score for cv in results)

    def generate_markdown_report(self, results: List[ScoredCV], output_file: str = "rapport_analyse_cv.md") -> str:
        """
        Génère un rapport détaillé au format Markdown avec les résultats de l'analyse
        
        Args:
            results: Liste des CVs analysés et leurs scores
            output_file: Nom du fichier de sortie (par défaut: rapport_analyse_cv.md)
            
        Returns:
            str: Le contenu du rapport au format Markdown
        """
        now = datetime.now()
        
        # En-tête du rapport
        report = [
            f"Rapport d'Analyse des CV",
            f"*Généré le {now.strftime('%d %B %Y à %H:%M')}*\n",
            "# Résumé",
            f"- Nombre total de CV analysés: **{len(results)}**",
            f"- Score moyen: **{self.calculate_average_score(results):.1f}%**",
            f"- Meilleur score: **{self.calculate_best_score(results):.1f}%**\n",
            "# Critères d'évaluation",
            "| Compétence | Pondération |",
            "|------------|-------------|"
        ]
        
        # Ajouter les critères d'évaluation
        for keyword, weight in self.keywords_original.items():
            report.append(f"| {keyword} | {weight * 100:.1f}% |")
        
        report.append("\n# Top 3 des Candidats")
        
        # Trier les résultats par score
        sorted_results = sorted(results, key=lambda x: x.score, reverse=True)
        top_3 = sorted_results[:3]
        
        for cv in top_3:
            report.append(f"\n## {cv.filename} ({cv.score:.1f}%)")
            report.append("| Compétence | Occurrences | Points |")
            report.append("|------------|-------------|---------|")
            
            for keyword, count in cv.found_keywords.items():
                weight = self.keywords_original.get(keyword, 0)
                points = count * weight * 100
                report.append(f"| {keyword} | {count} | {points:.1f}% |")
        
        return "\n".join(report)
