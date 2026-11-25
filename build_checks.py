"""Controles communs aux scripts de build : aucune base de donnees ne doit etre embarquee."""
from pathlib import Path

DB_PATTERNS = ("*.db", "*.db-journal", "*.sqlite", "*.sqlite3")


def find_database_files(root: Path) -> list:
    """Liste les bases SQLite presentes dans src/ (embarque par PyInstaller)."""
    found = []
    src = root / "src"
    if src.exists():
        for pattern in DB_PATTERNS:
            found.extend(src.rglob(pattern))
    return sorted(found)


def remove_stale_backend_databases(electron_backend: Path) -> None:
    """Supprime les bases copiees par d'anciens builds dans electron/backend."""
    if not electron_backend.exists():
        return
    for pattern in DB_PATTERNS:
        for path in electron_backend.glob(pattern):
            path.unlink()
            print(f"   Ancienne base supprimee: {path}")


def check_no_database(root: Path) -> bool:
    """Retourne False (et explique pourquoi) si une base est trouvee dans src/."""
    found = find_database_files(root)
    if not found:
        return True
    print("ERREUR: base de donnees detectee, elle serait embarquee dans l'exe:")
    for path in found:
        print(f"   - {path}")
    print("Supprimez ces fichiers (la base de l'application vit dans le dossier utilisateur).")
    return False
