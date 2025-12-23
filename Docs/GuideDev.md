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

CV Classifier Pro est une application desktop multi-projets avec trois modes d'analyse:

- **Mode Mots-cles** (Phase 1): Analyse par mots-cles ponderes
- **Mode Offre d'emploi** (Phase 2): Extraction auto des requirements + analyse
- **Mode IA/LLM** (Phase 3): Analyse intelligente avec IA (Ollama/OpenAI/Anthropic)

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

### Projets
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/projects` | Liste tous les projets |
| POST | `/api/projects` | Crée un projet |
| GET | `/api/projects/{id}` | Récupère un projet |
| PUT | `/api/projects/{id}` | Met à jour un projet |
| DELETE | `/api/projects/{id}` | Supprime un projet |

### Analyses
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/projects/{id}/analyses` | Historique des analyses |
| POST | `/api/projects/{id}/analyze` | Analyse par mots-cles |
| POST | `/api/projects/{id}/analyze-offer/{offer_id}` | Analyse par offre d'emploi |
| POST | `/api/projects/{id}/analyze-llm` | Analyse IA (LLM) |
| DELETE | `/api/analyses/{id}` | Supprime une analyse |

### Offres d'emploi
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/projects/{id}/job-offers` | Liste les offres d'un projet |
| POST | `/api/projects/{id}/job-offers` | Upload une offre |
| GET | `/api/job-offers/{id}` | Récupère une offre |
| PUT | `/api/job-offers/{id}` | Met à jour une offre |
| DELETE | `/api/job-offers/{id}` | Supprime une offre |

### LLM Settings
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/llm-settings` | Récupère la config LLM |
| PUT | `/api/llm-settings` | Met à jour la config LLM |
| GET | `/api/llm-settings/test` | Teste la connexion LLM |

### Utilitaires
| Méthode | Endpoint | Description |
|---------|----------|-------------|
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


## Historique des versions

### v1.0.0 - Phase 1 Complete
- Gestion multi-projets
- Analyse par mots-cles ponderes
- Build Electron Windows

### v2.0.0 - Phase 2 Complete
- Upload offres d'emploi (PDF/TXT)
- Extraction automatique des requirements techniques
- Analyse CVs vs offre d'emploi
- Deux modes: mots-cles manuels OU offre d'emploi

---

## Phase 2.1 - Optimisations ✅

### 2.1.1 - Manuel d'utilisation ✅
| Fichier | Status | Description |
|---------|--------|-------------|
| `src/components/UserManual.jsx` | ✅ Créé | Modal avec guide utilisateur |
| `src/components/HomeScreen.jsx` | ✅ Modifié | Bouton "?" en haut à droite |
| `src/assets/manual.md` | ✅ Créé | Contenu du manuel |

### 2.1.2 - Icone personnalisee ✅
| Fichier | Status | Description |
|---------|--------|-------------|
| `assets/icon.ico` | ✅ Créé | Icone Windows |
| `assets/icon.png` | ✅ Créé | Icone PNG |
| `forge.config.js` | ✅ Modifié | Reference icone |

### 2.1.3 - Ponderation intelligente des offres ✅
| Fichier | Status | Description |
|---------|--------|-------------|
| `src/services/job_offer_parser.py` | ✅ Modifié | Frequence + position |
| `src/components/JobOfferUpload.jsx` | ✅ Modifié | Edition des ponderations |
| `src/components/JobOfferEdit.jsx` | ✅ Créé | Edition offres existantes |

### 2.1.4 - Splash screen personnalise ✅
| Fichier | Status | Description |
|---------|--------|-------------|
| `electron/splash.html` | ✅ Créé | HTML du splash animé |
| `electron/main.js` | ✅ Modifié | Splash → Backend → Main window |

---

## Phase 3 - Mode LLM ✅

### Objectif
Analyse intelligente CV vs Offre d'emploi avec un LLM (IA).

### Architecture
```
┌─────────────────────────────────────────────────────┐
│  FRONTEND                                           │
│  ├─ LLMSettings.jsx (config provider/API key)      │
│  └─ CVAnalyzerForm.jsx (3 modes: keywords/offre/IA)│
├─────────────────────────────────────────────────────┤
│  BACKEND                                            │
│  ├─ llm_manager.py (orchestration)                 │
│  └─ llm_adapters/                                  │
│       ├─ base_adapter.py (interface ABC)           │
│       ├─ ollama_adapter.py (local, gratuit)        │
│       ├─ openai_adapter.py (GPT-4)                 │
│       └─ anthropic_adapter.py (Claude)             │
├─────────────────────────────────────────────────────┤
│  DATABASE                                           │
│  └─ llm_settings (provider, api_key, model)        │
└─────────────────────────────────────────────────────┘
```

### 3.1 - Settings LLM ✅
| Fichier | Status | Description |
|---------|--------|-------------|
| `src/components/LLMSettings.jsx` | ✅ Créé | Modal config LLM |
| `src/components/HomeScreen.jsx` | ✅ Modifié | Bouton engrenage |
| `src/database/models.py` | ✅ Modifié | Table LLMSettings |
| `src/services/api.py` | ✅ Modifié | CRUD /api/llm-settings |

### 3.2 - LLM Manager ✅
| Fichier | Status | Description |
|---------|--------|-------------|
| `src/services/llm_manager.py` | ✅ Créé | Orchestration |
| `src/services/llm_adapters/__init__.py` | ✅ Créé | Package |
| `src/services/llm_adapters/base_adapter.py` | ✅ Créé | Interface ABC |

### 3.3 - Adapters ✅
| Fichier | Status | Description |
|---------|--------|-------------|
| `src/services/llm_adapters/ollama_adapter.py` | ✅ Créé | Ollama local |
| `src/services/llm_adapters/openai_adapter.py` | ✅ Créé | OpenAI GPT |
| `src/services/llm_adapters/anthropic_adapter.py` | ✅ Créé | Anthropic Claude |

### 3.4 - Endpoint + UI ✅
| Fichier | Status | Description |
|---------|--------|-------------|
| `src/services/api.py` | ✅ Modifié | POST /api/projects/{id}/analyze-llm |
| `src/components/CVAnalyzerForm.jsx` | ✅ Modifié | Mode "Analyse IA" |

---

### v2.1.0 - Optimisations
- Manuel d'utilisation intégré
- Icône personnalisée
- Pondération intelligente des offres
- Splash screen personnalisé
- Amélioration du chargement Electron

### v3.0.0 - Mode LLM
- Configuration LLM (Ollama/OpenAI/Anthropic)
- Analyse IA des CVs vs offre d'emploi
- Support modèles locaux (Ollama) et cloud
- Rapport d'analyse détaillé par l'IA

### v3.1.0 - Améliorations LLM
- Rapport avec classement et synthèse (tableau de ranking)
- Top 3 profils avec résumé
- Sélection de CVs (tous / Top N / manuel)
- Parsing automatique des scores et recommandations

---

## Phase 3.1 - Améliorations LLM ✅

### Objectif
Améliorer l'expérience d'analyse IA avec sélection de CVs et rapport enrichi.

### 3.1.1 - Rapport LLM amélioré ✅
| Fichier | Status | Description |
|---------|--------|-------------|
| `src/services/llm_adapters/base_adapter.py` | ✅ Modifié | Prompt structuré avec SCORE/RECOMMANDATION |
| `src/services/api.py` | ✅ Modifié | parse_llm_response + generate_llm_report amélioré |

**Structure du nouveau rapport:**
```markdown
# Analyse IA - [Projet] - [Date]

## 📊 Synthèse et Classement

| Rang | Candidat | Score | Recommandation |
|------|----------|-------|----------------|
| 1 | cv_dupont.pdf | 85/100 | ✅ Fortement recommandé |
| 2 | cv_martin.pdf | 72/100 | ✅ Recommandé |
| 3 | cv_durand.pdf | 58/100 | ⚠️ À considérer |

### Top 3 Profils
1. **Jean Dupont** - Excellent match technique...
2. **Marie Martin** - Bon profil avec expérience...
3. **Pierre Durand** - Profil junior prometteur...

---

## 📄 Analyses Détaillées

### 1. cv_dupont.pdf (Score: 85/100)
[Analyse complète générée par l'IA]

### 2. cv_martin.pdf (Score: 72/100)
[Analyse complète générée par l'IA]
...
```

### 3.1.2 - Sélection de CVs ✅
| Fichier | Status | Description |
|---------|--------|-------------|
| `src/components/CVAnalyzerForm.jsx` | ✅ Modifié | Mode sélection (All/TopN/Manual) |
| `src/services/api.py` | ✅ Modifié | Paramètre cv_files optionnel |

**Modes de sélection:**
- **Tous les CVs** - Comportement actuel (dossier complet)
- **Top N** - Sélectionner une analyse précédente → prendre les N meilleurs
- **Manuel** - Sélectionner une analyse précédente → checkboxes

**Flow UI:**
```
Mode LLM sélectionné
  └─ Source des CVs:
       ├─ ○ Tous (dossier) [actuel]
       ├─ ○ Top N d'une analyse → [Select analyse] [Slider N]
       └─ ○ Sélection manuelle → [Select analyse] [Checkboxes CVs]
```

---

## Optimisations futures

- [ ] Queue/Worker pour gros batches LLM
- [ ] Tests unitaires
- [ ] CI/CD pipeline
- [ ] Auto-update Electron
