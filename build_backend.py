"""
Script pour créer l'exécutable du backend avec PyInstaller
Usage: python build_backend.py
"""
import os
import subprocess
import shutil
from pathlib import Path

from build_checks import check_no_database, remove_stale_backend_databases

def build():
    print("=" * 50)
    print("BUILD BACKEND - CV Classifier Pro")
    print("=" * 50)

    # Chemin racine du projet
    root = Path(__file__).parent

    if not check_no_database(root):
        return False

    # Créer le fichier d'entrée pour PyInstaller
    entry_file = root / "backend_entry.py"
    entry_content = '''# -*- coding: utf-8 -*-
"""Point d'entree pour le backend package"""
import uvicorn
import sys
import os

# Ajouter le dossier parent au path pour les imports
if getattr(sys, 'frozen', False):
    # Si on est dans un exe PyInstaller
    base_path = sys._MEIPASS
    os.chdir(os.path.dirname(sys.executable))
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, base_path)

# Importer et creer les tables de la base de donnees
from src.database.database import engine
from src.database.models import Base

print("Initialisation de la base de donnees...")
Base.metadata.create_all(bind=engine)
print("Base de donnees prete!")

from src.services.api import app

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("CV_BACKEND_PORT", "8000")), log_level="info")
'''

    print(f"1. Creation du fichier d'entree: {entry_file}")
    with open(entry_file, 'w', encoding='utf-8') as f:
        f.write(entry_content)

    # Commande PyInstaller
    print("2. Lancement de PyInstaller...")

    cmd = [
        "pyinstaller",
        "--onefile",
        "--name", "backend",
        "--clean",
        # Ajouter les modules nécessaires
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.protocols",
        "--hidden-import", "uvicorn.protocols.http",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.protocols.websockets",
        "--hidden-import", "uvicorn.protocols.websockets.auto",
        "--hidden-import", "uvicorn.lifespan",
        "--hidden-import", "uvicorn.lifespan.on",
        "--hidden-import", "fastapi",
        "--hidden-import", "pydantic",
        "--hidden-import", "sqlalchemy",
        "--hidden-import", "PyPDF2",
        "--hidden-import", "openpyxl",
        "--hidden-import", "reportlab",
        # Ajouter les fichiers source
        "--add-data", f"src;src",
        # Fichier d'entrée
        str(entry_file)
    ]

    result = subprocess.run(cmd, cwd=root)

    if result.returncode != 0:
        print("ERREUR: PyInstaller a échoué!")
        return False

    # Copier le backend dans le dossier electron
    print("3. Copie du backend dans electron/backend/...")
    electron_backend = root / "electron" / "backend"
    electron_backend.mkdir(parents=True, exist_ok=True)

    backend_exe = root / "dist" / "backend.exe"
    if backend_exe.exists():
        shutil.copy(backend_exe, electron_backend / "backend.exe")
        print(f"   Copié: {electron_backend / 'backend.exe'}")
    else:
        # Linux/Mac
        backend_bin = root / "dist" / "backend"
        if backend_bin.exists():
            shutil.copy(backend_bin, electron_backend / "backend")
            print(f"   Copié: {electron_backend / 'backend'}")

    # La base vit dans le dossier utilisateur : ne jamais en embarquer une
    remove_stale_backend_databases(electron_backend)

    # Nettoyer
    print("5. Nettoyage...")
    if entry_file.exists():
        entry_file.unlink()

    print("")
    print("=" * 50)
    print("BUILD TERMINÉ!")
    print("=" * 50)
    print(f"Backend: {electron_backend / 'backend.exe'}")
    print("")
    print("Prochaine étape: npm run make:win")

    return True

if __name__ == "__main__":
    build()
