import os
from pathlib import Path

class PDFService:
    def __init__(self):
        """Initialise le service PDF avec le dossier de stockage"""
        self.pdf_dir = Path("pdfs")
        self.pdf_dir.mkdir(exist_ok=True)
        
    def save_pdf(self, pdf_data: bytes, analysis_id: int) -> str:
        """
        Sauvegarde le PDF généré
        
        Args:
            pdf_data: Contenu du PDF en bytes
            analysis_id: ID de l'analyse
            
        Returns:
            str: Chemin du fichier sauvegardé
        """
        filepath = str(self.pdf_dir / f"analyse_{analysis_id}.pdf")
        
        with open(filepath, 'wb') as f:
            f.write(pdf_data)
            
        return filepath
