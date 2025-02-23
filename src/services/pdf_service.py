from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
import os
from datetime import datetime
from ..utils.text_cleaner import clean_markdown

class PDFService:
    def __init__(self, export_dir="exports"):
        self.export_dir = export_dir
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)

    def export_to_pdf(self, analysis_data, analysis_id):
        # Créer le nom du fichier
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"rapport_analyse_{analysis_id}_{timestamp}.pdf"
        filepath = os.path.join(self.export_dir, filename)

        # Créer le document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12
        )
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=8
        )

        # Contenu
        story = []

        # Titre
        title = f"Rapport d'analyse CV - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 20))

        # Mots-clés recherchés
        story.append(Paragraph("Mots-clés recherchés", heading_style))
        for keyword, weight in analysis_data.get('keywords', {}).items():
            text = f"{keyword}: {weight:.1f}%"
            story.append(Paragraph(text, normal_style))
        story.append(Spacer(1, 20))

        # Résumé
        story.append(Paragraph("Résumé", heading_style))
        
        # Statistiques de base
        stats = [
            f"Nombre de CV analysés: {analysis_data.get('total_cvs', 0)}",
            f"Score moyen: {analysis_data.get('average_score', 0):.1f}%",
            f"Meilleur score: {analysis_data.get('best_score', 0):.1f}%"
        ]
        for stat in stats:
            story.append(Paragraph(stat, normal_style))
        story.append(Spacer(1, 20))

        # Critères d'évaluation
        story.append(Paragraph("Critères d'évaluation", heading_style))
        for keyword, weight in analysis_data.get('keywords', {}).items():
            text = f"{keyword}: {weight:.1f}%"
            story.append(Paragraph(text, normal_style))
        story.append(Spacer(1, 20))

        # Top 3 des Candidats
        if analysis_data.get('top_candidates'):
            story.append(Paragraph("Top 3 des Candidats", heading_style))
            for candidate in analysis_data.get('top_candidates', []):
                filename = candidate.get('filename', '')
                score = candidate.get('score', 0)
                skills = candidate.get('skills', {})
                
                story.append(Paragraph(f"• {filename} ({score:.1f}%)", normal_style))
                for skill, count in skills.items():
                    story.append(Paragraph(f"  - {skill}: {count} occurrences", normal_style))
            story.append(Spacer(1, 20))

        # Rapport détaillé
        if analysis_data.get('report'):
            story.append(Paragraph("Rapport détaillé", heading_style))
            cleaned_report = clean_markdown(analysis_data.get('report', ''))
            for line in cleaned_report.split('\n'):
                if line.strip():
                    story.append(Paragraph(line, normal_style))

        # Générer le PDF
        doc.build(story)
        return filepath
