from typing import Dict, Any, Optional
from fastapi import HTTPException, status

class CVAnalyzerError(Exception):
    """Classe de base pour les erreurs personnalisées de l'application"""
    def __init__(self, message: str, error_code: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class FileSystemError(CVAnalyzerError):
    """Erreurs liées aux opérations sur les fichiers"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "FILE_SYSTEM_ERROR", details)

class PDFProcessingError(CVAnalyzerError):
    """Erreurs liées au traitement des fichiers PDF"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "PDF_PROCESSING_ERROR", details)

class ValidationError(CVAnalyzerError):
    """Erreurs de validation des données"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", details)

class DatabaseError(CVAnalyzerError):
    """Erreurs liées à la base de données"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DATABASE_ERROR", details)

def handle_application_error(error: Exception) -> Dict[str, Any]:
    """
    Convertit les exceptions en réponses HTTP appropriées
    """
    if isinstance(error, CVAnalyzerError):
        status_code = status.HTTP_400_BAD_REQUEST
        if isinstance(error, FileSystemError):
            status_code = status.HTTP_404_NOT_FOUND
        elif isinstance(error, DatabaseError):
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        
        raise HTTPException(
            status_code=status_code,
            detail={
                "message": error.message,
                "error_code": error.error_code,
                "details": error.details
            }
        )
    
    # Pour les erreurs non gérées
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "message": "Une erreur inattendue s'est produite",
            "error_code": "INTERNAL_SERVER_ERROR",
            "details": {"error": str(error)}
        }
    )

def validate_keywords(keywords: Dict[str, float]) -> None:
    """Valide les mots-clés et leurs pondérations"""
    if not keywords:
        raise ValidationError(
            "La liste des mots-clés ne peut pas être vide",
            {"keywords": keywords}
        )
    
    for keyword, weight in keywords.items():
        if not isinstance(keyword, str) or not keyword.strip():
            raise ValidationError(
                "Les mots-clés doivent être des chaînes de caractères non vides",
                {"invalid_keyword": keyword}
            )
        
        if not isinstance(weight, (int, float)) or weight < 0 or weight > 100:
            raise ValidationError(
                "Les pondérations doivent être des nombres entre 0 et 100",
                {"keyword": keyword, "invalid_weight": weight}
            )

def validate_folder_path(folder_path: str) -> None:
    """Valide le chemin du dossier"""
    import os
    
    if not folder_path:
        raise ValidationError("Le chemin du dossier ne peut pas être vide")
    
    if not os.path.exists(folder_path):
        raise FileSystemError(
            "Le dossier spécifié n'existe pas",
            {"folder_path": folder_path}
        )
    
    if not os.path.isdir(folder_path):
        raise FileSystemError(
            "Le chemin spécifié n'est pas un dossier",
            {"folder_path": folder_path}
        )
    
    # Vérifier les permissions
    try:
        os.access(folder_path, os.R_OK)
    except Exception as e:
        raise FileSystemError(
            "Impossible d'accéder au dossier spécifié",
            {"folder_path": folder_path, "error": str(e)}
        )
