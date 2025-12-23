# -*- coding: utf-8 -*-
"""
Parser d'offres d'emploi - Extraction de texte et parsing des requirements
"""
import re
from pathlib import Path
from typing import Dict, Optional

# Essayer d'importer PyPDF2
try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None


# Liste des mots-cles techniques a detecter
TECH_KEYWORDS = {
    # Langages de programmation
    "python", "javascript", "java", "c++", "c#", "csharp", "go", "golang",
    "rust", "php", "ruby", "swift", "kotlin", "scala", "typescript",
    "perl", "matlab", "bash", "shell", "powershell",

    # Frontend
    "react", "reactjs", "vue", "vuejs", "angular", "angularjs",
    "html", "html5", "css", "css3", "sass", "scss", "less",
    "webpack", "vite", "nextjs", "next.js", "nuxt", "gatsby",
    "tailwind", "bootstrap", "material-ui", "mui",

    # Backend
    "node", "nodejs", "node.js", "express", "expressjs",
    "django", "flask", "fastapi", "spring", "springboot",
    "laravel", "symfony", "rails", "ruby on rails",
    "asp.net", "dotnet", ".net",

    # Base de donnees
    "sql", "mysql", "postgresql", "postgres", "mongodb", "mongo",
    "redis", "elasticsearch", "oracle", "sqlite", "mariadb",
    "dynamodb", "cassandra", "neo4j", "graphql",

    # Cloud & DevOps
    "aws", "amazon web services", "azure", "gcp", "google cloud",
    "docker", "kubernetes", "k8s", "jenkins", "gitlab", "github",
    "terraform", "ansible", "puppet", "chef",
    "ci/cd", "cicd", "devops", "sre",

    # Data & ML
    "machine learning", "deep learning",
    "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn",
    "pandas", "numpy", "spark", "hadoop", "airflow",
    "data science", "data engineering", "etl",
    "tableau", "power bi", "looker",

    # Methodologies & pratiques
    "agile", "scrum", "kanban", "jira",
    "rest api", "restful", "soap", "microservices",
    "git", "svn",
    "tdd", "bdd", "unit testing",

    # Securite
    "cybersecurity", "owasp", "penetration testing",
    "oauth", "jwt",

    # Mobile
    "android", "ios", "react native", "flutter", "xamarin",

    # Autres
    "linux", "unix", "windows server",
    "nginx", "apache"
}


class JobOfferParser:
    """Classe pour parser les offres d'emploi et extraire les requirements"""

    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        """Extrait le texte d'un fichier PDF"""
        if PdfReader is None:
            raise ImportError("PyPDF2 n'est pas installe. Installez-le avec: pip install PyPDF2")

        try:
            reader = PdfReader(file_path)
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            return "\n".join(text_parts)
        except Exception as e:
            raise ValueError(f"Erreur lors de la lecture du PDF: {str(e)}")

    @staticmethod
    def extract_text_from_txt(file_path: str) -> str:
        """Extrait le texte d'un fichier TXT"""
        try:
            # Essayer plusieurs encodages
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            raise ValueError("Impossible de decoder le fichier avec les encodages connus")
        except Exception as e:
            raise ValueError(f"Erreur lors de la lecture du fichier TXT: {str(e)}")

    @staticmethod
    def extract_text(file_path: str) -> str:
        """Extrait le texte d'un fichier PDF ou TXT"""
        path = Path(file_path)
        extension = path.suffix.lower()

        if extension == '.pdf':
            return JobOfferParser.extract_text_from_pdf(file_path)
        elif extension == '.txt':
            return JobOfferParser.extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Format de fichier non supporte: {extension}. Utilisez PDF ou TXT.")

    @staticmethod
    def parse_requirements(text: str) -> Dict[str, float]:
        """
        Parse le texte et extrait les mots-cles techniques.
        Ponderation intelligente basee sur:
        - Frequence d'apparition du mot-cle
        - Position (bonus si dans le premier tiers du document)
        Retourne un dictionnaire avec les ponderations (total = 100%).
        """
        if not text:
            return {}

        # Normaliser le texte
        text_lower = text.lower()
        text_length = len(text_lower)
        first_third = text_length // 3  # Premier tiers du document

        # Dictionnaire pour stocker les scores bruts
        keyword_scores = {}

        for keyword in TECH_KEYWORDS:
            # Pattern pour matcher le mot-cle comme mot complet
            pattern = r'\b' + re.escape(keyword) + r'\b'
            matches = list(re.finditer(pattern, text_lower))

            if matches:
                normalized = JobOfferParser._normalize_keyword(keyword)

                # Score de base = nombre d'occurrences
                count = len(matches)

                # Bonus si apparait dans le premier tiers (titre, intro, requirements principaux)
                early_matches = sum(1 for m in matches if m.start() < first_third)
                position_bonus = early_matches * 0.5  # +0.5 par occurrence dans le premier tiers

                # Score total pour ce keyword
                score = count + position_bonus

                # Ajouter ou cumuler si synonyme deja present
                if normalized in keyword_scores:
                    keyword_scores[normalized] += score
                else:
                    keyword_scores[normalized] = score

        if not keyword_scores:
            return {}

        # Convertir les scores en pourcentages (total = 100%)
        total_score = sum(keyword_scores.values())
        requirements = {}

        for keyword, score in keyword_scores.items():
            # Calculer le pourcentage proportionnel
            percentage = (score / total_score) * 100
            requirements[keyword] = round(percentage, 1)

        # Ajuster pour que le total soit exactement 100%
        total = sum(requirements.values())
        if total != 100 and requirements:
            # Ajuster le plus gros pour compenser
            max_keyword = max(requirements, key=requirements.get)
            requirements[max_keyword] = round(requirements[max_keyword] + (100 - total), 1)

        # Trier par poids decroissant
        requirements = dict(sorted(requirements.items(), key=lambda x: x[1], reverse=True))

        return requirements

    @staticmethod
    def _normalize_keyword(keyword: str) -> str:
        """Normalise les synonymes de mots-cles"""
        normalizations = {
            "reactjs": "React",
            "vuejs": "Vue",
            "angularjs": "Angular",
            "nodejs": "Node.js",
            "node.js": "Node.js",
            "node": "Node.js",
            "expressjs": "Express",
            "golang": "Go",
            "csharp": "C#",
            "c#": "C#",
            "postgres": "PostgreSQL",
            "postgresql": "PostgreSQL",
            "mongo": "MongoDB",
            "mongodb": "MongoDB",
            "k8s": "Kubernetes",
            "kubernetes": "Kubernetes",
            "amazon web services": "AWS",
            "aws": "AWS",
            "google cloud": "GCP",
            "gcp": "GCP",
            "cicd": "CI/CD",
            "ci/cd": "CI/CD",
            "ml": "Machine Learning",
            "machine learning": "Machine Learning",
            "dl": "Deep Learning",
            "deep learning": "Deep Learning",
            "sklearn": "Scikit-learn",
            "scikit-learn": "Scikit-learn",
            "next.js": "Next.js",
            "nextjs": "Next.js",
            "ruby on rails": "Rails",
            "dotnet": ".NET",
            ".net": ".NET",
            "asp.net": ".NET",
        }

        lower = keyword.lower()
        if lower in normalizations:
            return normalizations[lower]

        # Capitaliser la premiere lettre
        return keyword.capitalize()

    @staticmethod
    def process_file(file_path: str) -> Dict:
        """
        Traite un fichier complet: extraction + parsing.
        Retourne un dict avec le contenu brut et les requirements.
        """
        raw_content = JobOfferParser.extract_text(file_path)
        requirements = JobOfferParser.parse_requirements(raw_content)

        return {
            "raw_content": raw_content,
            "requirements": requirements
        }
