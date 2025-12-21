"""
Script complet pour créer une release de CV Classifier Pro
Usage: python build_release.py

Ce script:
1. Build le backend Python avec PyInstaller
2. Build le frontend React avec Vite
3. Package l'application Electron
"""
import os
import subprocess
import shutil
import sys
from pathlib import Path

def run_command(cmd, cwd=None, shell=True):
    """Execute une commande et affiche la sortie"""
    print(f"\n> {cmd if isinstance(cmd, str) else ' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, shell=shell)
    if result.returncode != 0:
        print(f"ERREUR: Commande échouée avec code {result.returncode}")
        return False
    return True

def build():
    print("=" * 60)
    print("BUILD RELEASE - CV Classifier Pro v2.0.0")
    print("=" * 60)

    root = Path(__file__).parent

    # Vérifier qu'on est dans le bon dossier
    if not (root / "package.json").exists():
        print("ERREUR: package.json non trouvé. Exécutez ce script depuis la racine du projet.")
        return False

    # Étape 1: Build du backend Python
    print("\n" + "=" * 60)
    print("ÉTAPE 1: Build du backend Python avec PyInstaller")
    print("=" * 60)

    # Créer le fichier d'entrée pour PyInstaller
    entry_file = root / "backend_entry.py"
    entry_content = '''# -*- coding: utf-8 -*-
"""Point d'entree pour le backend package"""
import uvicorn
import sys
import os

# Ajouter le dossier parent au path pour les imports
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
    os.chdir(os.path.dirname(sys.executable))
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, base_path)

# Initialiser la base de donnees au demarrage
from src.database.database import engine
from src.database.models import Base

print("Initialisation de la base de donnees...")
Base.metadata.create_all(bind=engine)
print("Base de donnees prete!")

from src.services.api import app

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
'''

    print(f"1.1 Creation du fichier d'entree: {entry_file}")
    with open(entry_file, 'w', encoding='utf-8') as f:
        f.write(entry_content)

    # Commande PyInstaller
    print("1.2 Lancement de PyInstaller...")

    # Déterminer le séparateur pour --add-data selon l'OS
    sep = ";" if sys.platform == "win32" else ":"

    cmd = [
        "pyinstaller",
        "--onefile",
        "--name", "backend",
        "--clean",
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
        "--hidden-import", "starlette",
        "--hidden-import", "anyio",
        "--hidden-import", "h11",
        f"--add-data", f"src{sep}src",
        str(entry_file)
    ]

    if not run_command(cmd, cwd=root, shell=False):
        print("ERREUR: PyInstaller a échoué!")
        return False

    # Copier le backend dans electron/backend
    print("1.3 Copie du backend dans electron/backend/...")
    electron_backend = root / "electron" / "backend"
    electron_backend.mkdir(parents=True, exist_ok=True)

    if sys.platform == "win32":
        backend_exe = root / "dist" / "backend.exe"
        target = electron_backend / "backend.exe"
    else:
        backend_exe = root / "dist" / "backend"
        target = electron_backend / "backend"

    if backend_exe.exists():
        shutil.copy(backend_exe, target)
        print(f"   Copié: {target}")
    else:
        print(f"ERREUR: Backend non trouvé: {backend_exe}")
        return False

    # Nettoyer le fichier d'entrée
    if entry_file.exists():
        entry_file.unlink()

    # Étape 2: Build du frontend
    print("\n" + "=" * 60)
    print("ÉTAPE 2: Build du frontend React avec Vite")
    print("=" * 60)

    if not run_command("npm run build", cwd=root):
        print("ERREUR: Build frontend échoué!")
        return False

    # Étape 3: Package Electron
    print("\n" + "=" * 60)
    print("ÉTAPE 3: Package Electron")
    print("=" * 60)

    if sys.platform == "win32":
        make_cmd = "npm run make:win"
    elif sys.platform == "darwin":
        make_cmd = "npm run make:mac"
    else:
        make_cmd = "npm run make:linux"

    if not run_command(make_cmd, cwd=root):
        print("ERREUR: Electron Forge make a échoué!")
        return False

    # Résumé
    print("\n" + "=" * 60)
    print("BUILD TERMINÉ AVEC SUCCÈS!")
    print("=" * 60)

    out_dir = root / "out" / "make"
    print(f"\nFichiers de distribution dans: {out_dir}")

    if out_dir.exists():
        for item in out_dir.rglob("*"):
            if item.is_file():
                print(f"  - {item.relative_to(root)}")

    return True

if __name__ == "__main__":
    success = build()
    sys.exit(0 if success else 1)
