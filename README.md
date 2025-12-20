# CV Classifier Pro

Application desktop multi-projets pour l'analyse et la classification de CV. Deux modes disponibles : mode simple avec analyse par mots-clés pondérés, et mode LLM pour comparaison intelligente avec les offres d'emploi.

## Fonctionnalités

### Phase 1 - Mode Simple (Terminé)
- Gestion multi-projets : créez et gérez plusieurs projets d'analyse indépendants
- Analyse par mots-clés avec système de pondération (total = 100%)
- Scoring pondéré basé sur les mots-clés trouvés dans les CVs
- Rapports détaillés en Markdown avec statistiques
- Export PDF des rapports
- Base de données locale SQLite pour l'historique persistant
- Interface intuitive avec Material-UI
- Mode hors-ligne complet
- Application desktop Electron avec sélection native de dossiers

### Phase 2 - Gestion des Offres d'Emploi (Prochain)
- Upload d'offres d'emploi (PDF/TXT)
- Parsing automatique pour extraire les requirements
- Analyse basée sur l'offre avec matching de mots-clés

### Phase 3 - Mode LLM (Futur)
- Support multi-provider LLM : OpenAI, Anthropic, OLLAMA
- Exécution locale avec OLLAMA pour la sécurité
- Analyse intelligente de compatibilité CV-Offre
- Reasoning et suggestions contextuelles

## Prérequis

- Node.js >= 18 (recommandé: 20.x ou 22.x)
- Python 3.8+
- pip (gestionnaire de paquets Python)

## Installation

```bash
# Clone du repository
git clone https://github.com/aniisch/CV-Classifier-Pro.git
cd CV-Classifier-Pro

# Installation des dépendances Node.js
npm install

# Installation des dépendances Python
pip install -r requirements.txt

# Initialisation de la base de données (première fois uniquement)
cd src/database
python init_db.py
cd ../..
```

## Développement

### Mode Web (navigateur)

```bash
# Terminal 1 - Backend Python
uvicorn src.services.api:app --reload --port 8000

# Terminal 2 - Frontend Vite
npm run start
```

Ouvrir http://localhost:5173 dans le navigateur.

### Mode Desktop (Electron)

```bash
# Lance tout automatiquement (backend + frontend + Electron)
npm run electron-dev
```

## Build Production

### Option 1 : Script automatique (recommandé)

```bash
# Installer PyInstaller si pas déjà fait
pip install pyinstaller

# Lancer le build complet
python build_release.py
```

Ce script effectue automatiquement :
1. Build du backend Python avec PyInstaller
2. Build du frontend React avec Vite
3. Package de l'application Electron

### Option 2 : Build manuel

#### Étape 1 : Créer l'exécutable backend

```bash
pip install pyinstaller
python build_backend.py
```

#### Étape 2 : Build l'application Electron

```bash
# Build pour Windows (.exe)
npm run make:win

# Build pour macOS (.dmg)
npm run make:mac

# Build pour Linux (.deb, .rpm)
npm run make:linux
```

Les fichiers de distribution seront dans `out/make/`.



## Structure du Projet

```
cv-classifier-pro/
├── src/
│   ├── components/         # Composants React
│   │   ├── HomeScreen.jsx       # Accueil et gestion projets
│   │   ├── ProjectEditor.jsx    # Édition d'un projet
│   │   ├── CVAnalyzerForm.jsx   # Formulaire d'analyse
│   │   ├── AnalysisReport.jsx   # Affichage rapport
│   │   └── AnalysisHistory.jsx  # Historique analyses
│   ├── services/
│   │   ├── api.py              # Backend FastAPI
│   │   └── cv_analyzer.py      # Logique d'analyse
│   ├── database/
│   │   ├── models.py           # Modèles SQLAlchemy
│   │   ├── database.py         # Configuration DB
│   │   ├── project_manager.py  # CRUD projets
│   │   └── init_db.py          # Initialisation DB
│   ├── hooks/
│   │   └── useProject.js       # Hook gestion projet
│   └── main.jsx
├── electron/
│   ├── main.js                 # Point d'entrée Electron
│   └── preload.js              # APIs exposées au frontend
├── package.json
├── vite.config.js
├── forge.config.js             # Config build Electron
└── requirements.txt
```

## API Endpoints

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | /api/projects | Liste tous les projets |
| POST | /api/projects | Crée un projet |
| GET | /api/projects/{id} | Récupère un projet |
| PUT | /api/projects/{id} | Met à jour un projet |
| DELETE | /api/projects/{id} | Supprime un projet |
| GET | /api/projects/{id}/analyses | Historique des analyses |
| POST | /api/projects/{id}/analyze | Lance une analyse |
| DELETE | /api/analyses/{id} | Supprime une analyse |
| GET | /api/health | Health check |

Swagger UI disponible sur http://localhost:8000/docs

## Roadmap

### Phase 1 - Mode Simple (Terminé)
- [x] Home screen avec liste des projets
- [x] CRUD des projets
- [x] Persistance SQLite
- [x] CVAnalyzerForm avec projet sélectionné
- [x] Historique des analyses par projet
- [x] Setup Electron (mode dev)
- [x] Dialog sélection de dossier natif
- [x] Build production avec PyInstaller
- [x] Scripts de build automatisés

### Phase 2 - Offres d'Emploi
- [ ] Composant upload d'offre
- [ ] Parser offre (extraction requirements)
- [ ] Modèle database pour job_offers
- [ ] Analyse basée sur offre

### Phase 3 - Mode LLM
- [ ] Adaptateurs LLM (OpenAI, Anthropic, OLLAMA)
- [ ] Configuration API keys
- [ ] Guide setup OLLAMA
- [ ] LLMAnalyzer service

## Licence

MIT
