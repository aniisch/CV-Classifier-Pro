# cv_analyzer.py
import os
from pathlib import Path
import PyPDF2
import re
from typing import Dict, List, Tuple
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class ScoredCV:
    """Classe pour stocker les résultats d'analyse d'un CV"""
    filename: str
    score: float
    found_keywords: Dict[str, int]
    
class CVAnalyzer:
    def __init__(self, pdf_folder: str, keywords: Dict[str, float]):
        """
        Initialise l'analyseur de CV
        
        Args:
            pdf_folder: Chemin vers le dossier contenant les PDFs
            keywords: Dictionnaire avec les mots-clés et leurs pourcentages
        """
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
        """
        Nettoie le texte extrait du PDF
        """
        # Affiche le texte avant nettoyage
        # print("\nTexte avant nettoyage (premiers 200 caractères):")
        # print(text[:200])
        
        # Nettoyage étape par étape
        # 1. Remplace les retours à la ligne par des espaces
        text = text.replace('\n', ' ')
        
        # 2. Sépare les mots collés avec des majuscules
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        
        # 3. Remplace les multiples espaces par un seul
        text = re.sub(r'\s+', ' ', text)
        
        # 4. Normalise les espaces autour de la ponctuation
        text = re.sub(r'\s*([,.])\s*', r'\1 ', text)
        
        # print("\nTexte après nettoyage (premiers 200 caractères):")
        # print(text[:200])
        
        return text
    
    def _create_case_insensitive_pattern(self, keyword: str) -> str:
        """
        Crée un pattern simple qui match le mot-clé
        """
        return re.escape(keyword)
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """
        Extraire le texte d'un PDF et sauvegarder les versions avant/après nettoyage
        """
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            
            # Sauvegarde du texte brut
            raw_text_file = pdf_path.with_suffix('.raw.txt')
            with open(raw_text_file, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"Texte brut sauvegardé dans: {raw_text_file}")
            
            # Nettoie le texte
            cleaned_text = self.clean_text(text)
            
            # Sauvegarde du texte nettoyé
            cleaned_text_file = pdf_path.with_suffix('.cleaned.txt')
            with open(cleaned_text_file, 'w', encoding='utf-8') as f:
                f.write(cleaned_text)
            print(f"Texte nettoyé sauvegardé dans: {cleaned_text_file}")
            
            return cleaned_text
                
        except Exception as e:
            self.failed_conversions.append((pdf_path.name, str(e)))
            return ""
    
    def count_keywords(self, text: str) -> Dict[str, int]:
        """
        Compte les occurrences de chaque mot-clé dans le texte
        """
        keyword_counts = {}
        # print("\nDébut analyse des mots-clés:")
        # print(f"Longueur du texte: {len(text)} caractères")
        # print("\nTexte nettoyé (premiers 200 caractères):")
        # print(text[:200])  # Pour voir à quoi ressemble le texte après nettoyage
        
        # Pour chaque pattern de mot-clé
        for pattern in self.keywords_patterns:
            # Recherche simple avec re.findall pour voir toutes les correspondances
            matches = re.findall(pattern, text, re.IGNORECASE)
            count = len(matches)
            
            # Récupère le mot-clé original
            original_keyword = next(k for k in self.keywords_original.keys() 
                                if self._create_case_insensitive_pattern(k) == pattern)
            
            # print(f"\nRecherche de '{original_keyword}'")
            # print(f"Pattern utilisé: {pattern}")
            # print(f"Nombre de correspondances: {count}")
            
            if count > 0:
                print("Correspondances trouvées:")
                print(matches)
                
            keyword_counts[original_keyword] = count
        
        return keyword_counts
    def calculate_score(self, keyword_counts: Dict[str, int]) -> float:
        """
        Calcule le score final basé sur les occurrences et les pourcentages
        """
        score = 0
        for keyword, count in keyword_counts.items():
            if count > 0:
                score += self.keywords_original[keyword]
        return score
    
    def analyze_cvs(self) -> List[ScoredCV]:
        """
        Analyse tous les CVs dans le dossier et retourne les résultats triés
        """
        results = []
        
        # Parcours des fichiers PDF
        for pdf_file in self.pdf_folder.glob('*.pdf'):
            print(f"\nAnalyse de {pdf_file.name}...")
            
            # Extraction du texte
            text = self.extract_text_from_pdf(pdf_file)
            if not text:
                print(f"Échec de l'extraction pour {pdf_file.name}")
                continue
                
            print(f"Extraction réussie pour {pdf_file.name}")
            
            # Analyse des mots-clés
            keyword_counts = self.count_keywords(text)
            score = self.calculate_score(keyword_counts)
            
            results.append(ScoredCV(
                filename=pdf_file.name,
                score=score,
                found_keywords=keyword_counts
            ))
        
        # Tri des résultats par score décroissant
        return sorted(results, key=lambda x: x.score, reverse=True)

def main():
    """Point d'entrée principal du script"""
    
    # Configuration du chemin et des mots-clés
    pdf_folder = "C:/Users/anisc/OneDrive/Bureau/CV Classifier Pro/CV-Classifier-Pro/cvs"
    
    # Vérification du dossier
    if not os.path.exists(pdf_folder):
        print(f"⚠️ Le dossier {pdf_folder} n'existe pas!")
        return
        
    keywords = {
        "AZUREML": 30,
        "Python": 20,
        "LLM": 15,
        "DevOps": 10,
        "Azure": 10,
        "TensorFlow": 5,
        "PyTorch": 5,
        "Docker": 5
    }
    
    try:
        # Liste les fichiers PDF
        pdf_files = list(Path(pdf_folder).glob('*.pdf'))
        print(f"\nFichiers PDF trouvés ({len(pdf_files)}):")
        for pdf_file in pdf_files:
            print(f"- {pdf_file}")
            
        if not pdf_files:
            print("⚠️ Aucun fichier PDF trouvé dans le dossier!")
            return
            
        print("\nMots-clés recherchés:")
        for keyword, weight in keywords.items():
            print(f"- {keyword}: {weight}%")
            
        # Création et exécution de l'analyseur
        print("\nInitialisation de l'analyseur...")
        analyzer = CVAnalyzer(pdf_folder, keywords)
        results = analyzer.analyze_cvs()
        
        if not results:
            print("\n⚠️ Aucun CV n'a pu être analysé!")
            return
            
        # Affichage des résultats
        print("\n=== Résultats de l'analyse ===")
        for i, cv in enumerate(results, 1):
            print(f"\n{i}. {cv.filename} - Score: {cv.score}%")
            print("Mots-clés trouvés:")
            for keyword, count in cv.found_keywords.items():
                if count > 0:
                    print(f"  - {keyword}: {count} fois ({keywords[keyword]}%)")
        
        # Affichage des erreurs de conversion
        if analyzer.failed_conversions:
            print("\n=== Erreurs de conversion ===")
            for filename, error in analyzer.failed_conversions:
                print(f"❌ {filename}: {error}")
                
    except Exception as e:
        print(f"Erreur: {str(e)}")
        import traceback
        print("\nDétails de l'erreur:")
        print(traceback.format_exc())

if __name__ == "__main__":
    main()