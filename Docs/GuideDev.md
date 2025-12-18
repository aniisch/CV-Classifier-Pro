# Guide Développeur - CV Classifier Pro

## Table des Matières
1. [Vue d'ensemble](#vue-densemble)
2. [Architecture Phase 1](#architecture-phase-1)
3. [Roadmap détaillée avec tâches](#roadmap-détaillée-avec-tâches)
4. [Modèles de données](#modèles-de-données)
5. [Guide Backend (Python)](#guide-backend-python)
6. [Guide Frontend (React)](#guide-frontend-react)
7. [Démarrage du projet](#démarrage-du-projet)
8. [Phases futures](#phases-futures)

## Vue d'ensemble

CV Classifier Pro évolue vers une application desktop multi-projets avec deux modes d'analyse:

**Mode Simple** (Phase 1 - Actuel): Analyse par mots-clés pondérés
**Mode LLM** (Phase 3 - Futur): Comparaison intelligente CV-Offre avec LLM

L'application utilise:
- Backend: Python (FastAPI + SQLAlchemy)
- Frontend: React (Material-UI + Vite)
- Desktop: Electron (multi-plateforme)
- Database: SQLite (local)

### Architecture globale Phase 1

```
┌─────────────────────────────────────────────────────┐
│         ELECTRON APP (Desktop)                      │
├─────────────────────────────────────────────────────┤
│  FRONTEND (React)                                   │
│  ├─ HomeScreen (liste des projets)                 │
│  ├─ ProjectEditor (édition d'un projet)            │
│  ├─ CVAnalyzerForm (analyse simple)                │
│  ├─ AnalysisReport (affichage rapport)             │
│  └─ AnalysisHistory (historique par projet)        │
├─────────────────────────────────────────────────────┤
│  BACKEND (Python FastAPI)                          │
│  ├─ ProjectManager (CRUD + persistence)            │
│  ├─ CVAnalyzer (analyse par mots-clés)             │
│  ├─ FileManager (chargement des CVs)               │
│  └─ API endpoints                                   │
├─────────────────────────────────────────────────────┤
│  DATABASE (SQLite)                                  │
│  ├─ projects (projets créés)                       │
│  ├─ analyses (résultats des analyses)              │
│  └─ settings (configuration utilisateur)           │
└─────────────────────────────────────────────────────┘
```

## Architecture Phase 1

### Flux de données

```
User → HomeScreen
       ↓
   Select/Create Project
       ↓
   ProjectEditor → Save to DB
       ↓
   CVAnalyzerForm (keywords + folder path)
       ↓
   POST /api/analyze
       ↓
   Backend: CVAnalyzer process
       ↓
   Save to DB (analyses table)
       ↓
   AnalysisReport (display)
       ↓
   AnalysisHistory (persistence)
```

## Roadmap détaillée avec tâches

### Phase 1 - Mode Simple et Multi-Projet

#### 1.1 - Home Screen et Gestion Projets
**Objectif**: Écran d'accueil permettant de créer/lister/éditer/supprimer des projets

**Fichiers à créer/modifier:**
- [ ] `src/components/HomeScreen.jsx` - Nouvel écran d'accueil (À CRÉER)
- [ ] `src/components/ProjectEditor.jsx` - Édition d'un projet (À CRÉER)
- [ ] `src/components/App.jsx` - Mettre à jour pour routing HomeScreen → ProjectEditor (À MODIFIER)
- [ ] `src/database/project_manager.py` - Service gestion projets (À CRÉER)
- [ ] `src/database/models.py` - Ajouter modèle Project (À MODIFIER)

**Features:**
- Afficher liste de tous les projets
- Bouton créer nouveau projet
- Bouton éditer/supprimer projet
- Sauvegarder les projets en BD

**Tests manuels:**
- Créer 3 projets et vérifier persistence après restart
- Éditer un projet et vérifier changements
- Supprimer un projet (avec confirmation)

---

#### 1.2 - Refactoriser CVAnalyzerForm
**Objectif**: Utiliser le projet sélectionné comme contexte

**Fichiers à modifier:**
- [ ] `src/components/CVAnalyzerForm.jsx` - Utiliser project context (À MODIFIER)
- [ ] `src/hooks/useProject.js` - Créer hook pour gérer le projet courant (À CRÉER)
- [ ] `src/database/models.py` - Ajouter champ project_id aux analyses (À MODIFIER)

**Changes:**
- Les analyses sont liées à un projet spécifique
- Les mots-clés sont stockés dans le projet, pas dans le formulaire
- Afficher le nom du projet en haut du formulaire

---

#### 1.3 - Historique des Analyses par Projet
**Objectif**: Afficher et gérer l'historique des analyses pour le projet courant

**Fichiers à modifier:**
- [ ] `src/components/AnalysisHistory.jsx` - Filtrer par projet (À MODIFIER)
- [ ] `src/services/api.py` - Endpoint GET /api/projects/{id}/analyses (À CRÉER)

**Changes:**
- Lister uniquement les analyses du projet sélectionné
- Garder fonctionnalités: delete, export, etc.

---

#### 1.4 - Setup Electron
**Objectif**: Configuration pour build desktop

**Fichiers à créer/modifier:**
- [ ] `electron/main.js` - Point d'entrée Electron (À CRÉER)
- [ ] `electron/preload.js` - Bridge Electron (À CRÉER si nécessaire)
- [ ] `package.json` - Ajouter dépendances Electron et scripts (À MODIFIER)
- [ ] `vite.config.js` - Configuration Electron (À MODIFIER)
- [ ] `forge.config.js` - Configuration Electron Forge (À CRÉER)

**Scripts npm à ajouter:**
- `npm run electron-dev` - Lancer en dev
- `npm run electron-build` - Build cross-plateforme
- `npm run make:win` - Build Windows .exe
- `npm run make:mac` - Build macOS .dmg
- `npm run make:linux` - Build Linux .AppImage

**Tests:**
- Build et exécuter sur Windows/Mac/Linux

---

### Phase 2 - Offres d'Emploi

#### 2.1 - Upload et Parser Offre
**Objectif**: Permettre l'upload d'une offre d'emploi et extraire les requirements

**Fichiers à créer:**
- [ ] `src/components/JobOfferUpload.jsx` - Interface upload (À CRÉER)
- [ ] `src/services/job_offer_parser.py` - Parser PDF/TXT (À CRÉER)
- [ ] `src/database/models.py` - Ajouter modèle JobOffer (À MODIFIER)

**Features:**
- Upload PDF ou TXT
- Extraire et afficher les requirements
- Sauvegarder l'offre en BD

---

### Phase 3 - Mode LLM

#### 3.1 - Configuration LLM
**Objectif**: Permettre la configuration des LLM

**Fichiers à créer:**
- [ ] `src/components/LLMSettings.jsx` - Interface configuration (À CRÉER)
- [ ] `src/services/llm_manager.py` - Gestion LLM (À CRÉER)
- [ ] `src/utils/llm_adapters/openai_adapter.py` - Adapter OpenAI (À CRÉER)
- [ ] `src/utils/llm_adapters/anthropic_adapter.py` - Adapter Anthropic (À CRÉER)
- [ ] `src/utils/llm_adapters/ollama_adapter.py` - Adapter OLLAMA (À CRÉER)
- [ ] `src/database/models.py` - Ajouter modèle LLMConfig (À MODIFIER)

**Features:**
- Configuration multi-provider (OpenAI, Anthropic, OLLAMA)
- Sauvegarde sécurisée des API keys
- Guide setup OLLAMA dans l'app

---

## Modèles de données

### Schéma SQLite Phase 1

```sql
-- Projets utilisateur
CREATE TABLE projects (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  mode TEXT DEFAULT 'simple',  -- 'simple' ou 'llm'
  keywords JSON,  -- {"keyword": weight, ...}
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Analyses
CREATE TABLE analyses (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  timestamp TIMESTAMP,
  mode TEXT,  -- 'simple' ou 'llm'
  results JSON,  -- [{filename, score, found_keywords, ...}, ...]
  report TEXT,  -- Markdown content
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

-- Offres (Phase 2)
CREATE TABLE job_offers (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  content TEXT,
  parsed_requirements JSON,
  created_at TIMESTAMP,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

-- Configuration LLM (Phase 3)
CREATE TABLE llm_configs (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  provider TEXT,  -- 'openai', 'anthropic', 'ollama'
  model TEXT,
  api_key TEXT,  -- Chiffré
  ollama_url TEXT,
  created_at TIMESTAMP,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);
```

### Structures Pydantic (API)

```python
# Phase 1
class Project(BaseModel):
    id: str
    name: str
    description: str
    mode: str = "simple"
    keywords: dict
    created_at: datetime
    updated_at: datetime

class Analysis(BaseModel):
    id: str
    project_id: str
    timestamp: datetime
    mode: str
    results: list
    report: str

# Phase 2
class JobOffer(BaseModel):
    id: str
    project_id: str
    content: str
    parsed_requirements: list

# Phase 3
class LLMConfig(BaseModel):
    id: str
    project_id: str
    provider: str
    model: str
    ollama_url: str = None
```

## Guide Backend (Python)

### Structure Backend

```
src/services/
├── api.py                    # FastAPI app + endpoints
├── cv_analyzer.py            # Analyse CVs (à garder)
├── job_offer_parser.py       # Parser offres (Phase 2)
└── llm_manager.py            # Gestion LLM (Phase 3)

src/database/
├── database.py               # Config SQLAlchemy + connexion
├── models.py                 # Modèles ORM
├── project_manager.py        # CRUD projets
└── analyses.db               # Fichier SQLite

src/utils/
├── error_handling.py         # À garder
└── llm_adapters/             # Adaptateurs LLM (Phase 3)
    ├── base_adapter.py
    ├── openai_adapter.py
    ├── anthropic_adapter.py
    └── ollama_adapter.py
```

### API Endpoints Phase 1

```python
# Projets
GET    /api/projects              # Lister tous les projets
POST   /api/projects              # Créer un projet
GET    /api/projects/{id}         # Récupérer un projet
PUT    /api/projects/{id}         # Mettre à jour un projet
DELETE /api/projects/{id}         # Supprimer un projet

# Analyses (pour un projet)
GET    /api/projects/{id}/analyses     # Lister les analyses
POST   /api/projects/{id}/analyze      # Lancer une analyse
DELETE /api/analyses/{analysis_id}     # Supprimer une analyse

# Health
GET    /api/health                # Vérifier la connexion
```

### Exemple endpoint analyse Phase 1

```python
@app.post("/api/projects/{project_id}/analyze")
async def analyze_cvs_for_project(project_id: str, request: AnalyzeRequest):
    """
    Request body:
    {
        "folder_path": "chemin/vers/cvs"
    }

    Récupère les keywords du projet en BD
    Lance l'analyse
    Sauvegarde le résultat
    """
```

## Guide Frontend (React)

### Structure Components Phase 1

```
src/components/
├── App.jsx                      # Router principal
├── HomeScreen.jsx               # Accueil + liste projets
├── ProjectEditor.jsx            # Édition d'un projet
├── CVAnalyzerForm.jsx           # Formulaire analyse (à adapter)
├── AnalysisReport.jsx           # Affichage rapport
├── AnalysisHistory.jsx          # Historique (à adapter)
├── ErrorAlert.jsx               # À garder
└── ErrorBoundary.jsx            # À garder
```

### Hooks Phase 1

```
src/hooks/
├── useError.js                  # À garder
└── useProject.js                # Nouveau - gestion projet courant
```

### State Management

Utiliser React Context pour:
- Projet sélectionné courant
- Liste des projets (pour HomeScreen)
- Erreurs

```javascript
// useProject.js example
function useProject() {
  const [currentProject, setCurrentProject] = useState(null);
  const [projects, setProjects] = useState([]);

  const fetchProjects = async () => { /* ... */ };
  const selectProject = async (id) => { /* ... */ };
  const createProject = async (data) => { /* ... */ };
  // etc.
}
```

## Démarrage du projet

### 1. Installation initiale

```bash
# Backend
pip install -r requirements.txt

# Frontend
npm install
```

### 2. Lancement en développement (Phase 1)

```bash
# Terminal 1 - Backend
uvicorn src.services.api:app --reload --port 8000

# Terminal 2 - Frontend
npm run start

# Frontend sera accessible sur http://localhost:5173
# Backend sur http://localhost:8000
```

### 3. Vérification connexion

- Frontend: http://localhost:5173
- Backend: http://localhost:8000/docs (Swagger)
- DB: `src/database/analyses.db` (SQLite)

## Phases futures

### Phase 2 - Offres d'Emploi
1. Créer composant JobOfferUpload
2. Implémenter parser PDF/TXT
3. Modifier CVAnalyzerForm pour utiliser l'offre
4. Ajouter endpoint /api/projects/{id}/analyze-with-offer

### Phase 3 - Mode LLM
1. Implémenter adaptateurs LLM
2. Ajouter configuration sécurisée des API keys
3. Créer UI pour mode LLM
4. Guide setup OLLAMA intégré dans l'app
5. Endpoint /api/projects/{id}/analyze-with-llm

### Optimisations
1. Queue/Worker pour gros batches
2. Caching et indexing
3. Tests unitaires
4. Logging structuré
5. CI/CD pipeline
