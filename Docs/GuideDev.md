# Guide Développeur - CV Classifier Pro

## Table des Matières
1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Avancement Phase 1](#avancement-phase-1)
4. [API Endpoints](#api-endpoints)
5. [Démarrage du projet](#démarrage-du-projet)
6. [Build Production](#build-production)
7. [Phases futures](#phases-futures)

## Vue d'ensemble

CV Classifier Pro est une application desktop multi-projets avec deux modes d'analyse:

- **Mode Simple** (Phase 1 - Terminé): Analyse par mots-clés pondérés
- **Mode LLM** (Phase 3 - Futur): Comparaison intelligente CV-Offre avec LLM

### Stack Technique

| Couche | Technologie |
|--------|-------------|
| Frontend | React 18 + Material-UI + Vite |
| Backend | Python FastAPI + SQLAlchemy |
| Desktop | Electron |
| Database | SQLite (local) |

## Architecture

```
┌─────────────────────────────────────────────────────┐
│         ELECTRON APP (Desktop)                      │
│  ├─ main.js (lance backend + fenêtre)              │
│  └─ preload.js (APIs: selectFolder, etc.)          │
├─────────────────────────────────────────────────────┤
│  FRONTEND (React - localhost:5173)                  │
│  ├─ HomeScreen (liste des projets)                 │
│  ├─ ProjectEditor (édition d'un projet)            │
│  ├─ CVAnalyzerForm (formulaire analyse)            │
│  ├─ AnalysisReport (affichage rapport)             │
│  └─ AnalysisHistory (historique par projet)        │
├─────────────────────────────────────────────────────┤
│  BACKEND (Python FastAPI - localhost:8000)          │
│  ├─ api.py (endpoints REST)                        │
│  ├─ cv_analyzer.py (logique analyse)               │
│  └─ project_manager.py (CRUD projets)              │
├─────────────────────────────────────────────────────┤
│  DATABASE (SQLite - analyses.db)                    │
│  ├─ projects (projets créés)                       │
│  └─ analyses (résultats des analyses)              │
└─────────────────────────────────────────────────────┘
```

### Flux de données

```
User → HomeScreen (sélectionne un projet)
       ↓
   CVAnalyzerForm (entre chemin dossier CVs)
       ↓
   POST /api/projects/{id}/analyze
       ↓
   Backend: CVAnalyzer traite les PDFs
       ↓
   Sauvegarde en DB (analyses table)
       ↓
   AnalysisReport (affiche le rapport Markdown)
```

## Avancement Phase 1

### 1.1 - Home Screen et Gestion Projets ✅

| Fichier | Status | Description |
|---------|--------|-------------|
| `src/components/HomeScreen.jsx` | ✅ Créé | Écran d'accueil, liste projets |
| `src/components/ProjectEditor.jsx` | ✅ Créé | Édition projet + keywords |
| `src/components/App.jsx` | ✅ Modifié | Navigation entre écrans |
| `src/database/project_manager.py` | ✅ Créé | CRUD projets |
| `src/database/models.py` | ✅ Modifié | Modèle Project ajouté |
| `src/hooks/useProject.js` | ✅ Créé | Hook gestion projets |

### 1.2 - Refactoriser CVAnalyzerForm ✅

| Fichier | Status | Description |
|---------|--------|-------------|
| `src/components/CVAnalyzerForm.jsx` | ✅ Modifié | Utilise project context |
| `src/database/models.py` | ✅ Modifié | project_id dans analyses |

### 1.3 - Historique des Analyses par Projet ✅

| Fichier | Status | Description |
|---------|--------|-------------|
| `src/components/AnalysisHistory.jsx` | ✅ Modifié | Filtré par projet |
| `src/services/api.py` | ✅ Modifié | GET /api/projects/{id}/analyses |

### 1.4 - Setup Electron ✅

| Fichier | Status | Description |
|---------|--------|-------------|
| `electron/main.js` | ✅ Créé | Point d'entrée, lance backend |
| `electron/preload.js` | ✅ Créé | API selectFolder exposée |
| `package.json` | ✅ Modifié | Scripts Electron ajoutés |
| `vite.config.js` | ✅ Modifié | Config pour Electron |
| `forge.config.js` | ✅ Créé | Config build |

### 1.5 - Build Production ✅

| Tâche | Status | Description |
|-------|--------|-------------|
| PyInstaller backend | ✅ Créé | `build_backend.py` crée backend.exe |
| Electron Forge make | ✅ Configuré | `npm run make:win` |
| Script automatisé | ✅ Créé | `build_release.py` fait tout |

## API Endpoints

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/projects` | Liste tous les projets |
| POST | `/api/projects` | Crée un projet |
| GET | `/api/projects/{id}` | Récupère un projet |
| PUT | `/api/projects/{id}` | Met à jour un projet |
| DELETE | `/api/projects/{id}` | Supprime un projet |
| GET | `/api/projects/{id}/analyses` | Historique des analyses |
| POST | `/api/projects/{id}/analyze` | Lance une analyse |
| DELETE | `/api/analyses/{id}` | Supprime une analyse |
| GET | `/api/health` | Health check |

### Exemple requête analyse

```bash
POST /api/projects/abc123/analyze
Content-Type: application/json

{
  "folder_path": "C:\\Users\\user\\CVs"
}
```

## Démarrage du projet

### Installation

```bash
# Dépendances Node.js
npm install

# Dépendances Python
pip install -r requirements.txt

# Initialiser la DB (première fois)
cd src/database && python init_db.py && cd ../..
```

### Mode Développement

#### Option 1 : Web (navigateur)

```bash
# Terminal 1 - Backend
uvicorn src.services.api:app --reload --port 8000

# Terminal 2 - Frontend
npm run start
```

Ouvrir http://localhost:5173

#### Option 2 : Desktop (Electron)

```bash
# Lance tout (frontend + backend + Electron)
npm run electron-dev
```

### Vérification

- Frontend: http://localhost:5173
- Backend Swagger: http://localhost:8000/docs
- Database: `src/database/analyses.db`

## Build Production

### Option 1 : Script automatique (recommandé)

```bash
pip install pyinstaller
python build_release.py
```

### Option 2 : Build manuel

```bash
# Étape 1 : Backend
pip install pyinstaller
python build_backend.py

# Étape 2 : Electron
npm run make:win    # Windows
npm run make:mac    # macOS
npm run make:linux  # Linux
```

Les fichiers seront dans `out/make/`.


## Phases futures

### Phase 2 - Offres d'Emploi

| Tâche | Fichier | Description |
|-------|---------|-------------|
| Upload offre | `src/components/JobOfferUpload.jsx` | Interface upload PDF/TXT |
| Parser | `src/services/job_offer_parser.py` | Extraction requirements |
| Modèle | `src/database/models.py` | Table job_offers |
| Analyse | `src/services/api.py` | Endpoint analyze-with-offer |

### Phase 3 - Mode LLM

| Tâche | Fichier | Description |
|-------|---------|-------------|
| Settings | `src/components/LLMSettings.jsx` | Config LLM |
| Manager | `src/services/llm_manager.py` | Orchestration |
| OpenAI | `src/utils/llm_adapters/openai_adapter.py` | Adapter |
| Anthropic | `src/utils/llm_adapters/anthropic_adapter.py` | Adapter |
| OLLAMA | `src/utils/llm_adapters/ollama_adapter.py` | Adapter local |
| Guide | Intégré dans l'app | Setup OLLAMA |

### Optimisations futures

- [ ] Queue/Worker pour gros batches
- [ ] Tests unitaires
- [ ] CI/CD pipeline
- [ ] Auto-update Electron
