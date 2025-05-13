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

    def analyze_folder(self, folder_path: str, keywords: Dict[str, float]) -> str:
        """
        Analyse un dossier de CVs et génère un rapport
        
        Args:
            folder_path: Chemin vers le dossier contenant les CVs
            keywords: Dictionnaire des mots-clés et leurs poids
            
        Returns:
            str: Le rapport d'analyse au format Markdown
        """
        # Mettre à jour les attributs de l'instance avec les nouveaux paramètres
        self.pdf_folder = Path(folder_path)
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
        
        # Analyser les CVs
        results = self.analyze_cvs()
        
        if not results:
            return "# Aucun CV analysé\n\nAucun CV n'a pu être analysé dans le dossier spécifié."
        
        # Générer le rapport
        report = self.generate_markdown_report(results)
        
        return report
    
    def generate_markdown_report(self, results: List[ScoredCV], output_file: str = "rapport_analyse_cv.md") -> str:
        """
        Génère un rapport détaillé au format Markdown avec les résultats de l'analyse
        
        Args:
            results: Liste des CVs analysés et leurs scores
            output_file: Nom du fichier de sortie (par défaut: rapport_analyse_cv.md)
            
        Returns:
            str: Le contenu du rapport au format Markdown
        """
        current_date = datetime.now().strftime("%d %B %Y")
        
        # Création du contenu du rapport
        report = [
            "# Rapport d'Analyse des CV\n",
            f"*Généré le {current_date}*\n",
            "\n## Résumé\n",
            f"- Nombre total de CV analysés: **{len(results)}**",
            f"- Score moyen: **{sum(cv.score for cv in results) / len(results):.1f}%**",
            f"- Meilleur score: **{max(cv.score for cv in results):.1f}%**\n",
            "\n## Critères d'évaluation\n",
            "| Compétence | Pondération |",
            "|------------|-------------|"            
        ]
        
        # Ajouter les critères d'évaluation
        for keyword, weight in self.keywords_original.items():
            report.append(f"| {keyword} | {weight}% |")
            
        # Ajouter le top 3 des candidats
        report.extend([
            "\n## Top 3 des Candidats\n",
        ])
        
        for i, cv in enumerate(results[:3], 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
            report.extend([
                f"### {emoji} {cv.filename} ({cv.score:.1f}%)\n",
                "| Compétence | Occurrences | Points |",
                "|------------|-------------|---------|"                
            ])
            for keyword, count in cv.found_keywords.items():
                if count > 0:
                    points = self.keywords_original[keyword]
                    report.append(f"| {keyword} | {count} | {points}% |")
            report.append("\n")
            
        # Ajouter les résultats détaillés
        report.extend([
            "## Résultats Détaillés\n",
            "| Position | Candidat | Score | Compétences Clés |",
            "|----------|----------|--------|------------------|"            
        ])
        
        for i, cv in enumerate(results, 1):
            key_skills = ", ".join(f"{k} ({c})" for k, c in cv.found_keywords.items() if c > 0)
            report.append(f"| {i} | {cv.filename} | {cv.score:.1f}% | {key_skills} |")
            
        # Ajouter les erreurs de conversion si présentes
        if self.failed_conversions:
            report.extend([
                "\n## Erreurs de Conversion\n",
                "Les fichiers suivants n'ont pas pu être analysés:\n"
            ])
            for filename, error in self.failed_conversions:
                report.append(f"- {filename}: {error}\n")
        
        # Écriture du rapport dans un fichier
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
            
        print(f"\nRapport généré avec succès: {output_file}")
        
        # Retourner le contenu du rapport pour l'API
        return '\n'.join(report)
