# CV Classifier Pro

Application desktop multi-projets pour l'analyse et la classification de CV. Trois modes d'analyse disponibles : mots-clés, offre d'emploi, et analyse IA (LLM).

## Fonctionnalités

### Mode Mots-clés
- Gestion multi-projets indépendants
- Analyse par mots-clés avec système de pondération (total = 100%)
- Scoring pondéré basé sur les mots-clés trouvés dans les CVs
- Rapports détaillés en Markdown avec statistiques
- Export PDF des rapports

### Mode Offre d'Emploi
- Upload d'offres d'emploi (PDF/TXT)
- Extraction automatique des requirements techniques (100+ mots-clés)
- Pondération intelligente basée sur fréquence et position
- Édition manuelle des pondérations
- Analyse CVs vs requirements de l'offre

### Mode IA (LLM)
- Support multi-provider : Ollama (local), OpenAI, Anthropic
- Exécution locale avec Ollama (gratuit, données privées)
- Analyse intelligente CV vs Offre par l'IA
- **Rapport avec classement** : tableau de ranking, top 3, synthèse
- Score de correspondance, points forts/faibles, recommandation
- **Sélection de CVs** : tous, top N, ou sélection manuelle

### Général
- Base de données locale SQLite
- Interface Material-UI intuitive
- Manuel d'utilisation intégré
- Splash screen personnalisé
- Application desktop Electron

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
│   │   ├── cv_analyzer.py      # Logique d'analyse
│   │   ├── llm_manager.py      # Orchestration LLM
│   │   └── llm_adapters/       # Adaptateurs LLM
│   │       ├── ollama_adapter.py
│   │       ├── openai_adapter.py
│   │       └── anthropic_adapter.py
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
| POST | /api/projects/{id}/job-offers | Upload une offre d'emploi |
| GET | /api/projects/{id}/job-offers | Liste les offres du projet |
| GET | /api/job-offers/{id} | Detail d'une offre |
| PUT | /api/job-offers/{id} | Modifie les requirements |
| DELETE | /api/job-offers/{id} | Supprime une offre |
| POST | /api/projects/{id}/analyze-offer/{offer_id} | Analyse avec offre |
| POST | /api/projects/{id}/analyze-llm | Analyse IA (LLM) |
| GET | /api/llm-settings | Récupère la config LLM |
| PUT | /api/llm-settings | Met à jour la config LLM |
| GET | /api/llm-settings/test | Teste la connexion LLM |
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

### Phase 2 - Offres d'Emploi (Termine)
- [x] Composant upload d'offre (JobOfferUpload)
- [x] Parser offre (extraction requirements techniques)
- [x] Modele database pour job_offers
- [x] API endpoints CRUD offres
- [x] Analyse basee sur offre
- [x] Integration dans CVAnalyzerForm (choix mode)

### Phase 2.1 - Optimisations (Terminé)
- [x] Manuel d'utilisation intégré
- [x] Icône personnalisée
- [x] Pondération intelligente des offres
- [x] Splash screen personnalisé

### Phase 3 - Mode LLM (Terminé)
- [x] Adaptateurs LLM (Ollama, OpenAI, Anthropic)
- [x] Configuration provider et API keys
- [x] Interface settings LLM
- [x] LLM Manager (orchestration)
- [x] Endpoint analyse IA
- [x] Intégration dans CVAnalyzerForm

### Phase 3.1 - Améliorations LLM (Terminé)
- [x] Rapport avec classement et synthèse
- [x] Top 3 profils avec résumé
- [x] Sélection de CVs (tous / Top N / manuel)
- [x] Parsing automatique scores et recommandations

### Optimisations futures
- [ ] Queue/Worker pour gros batches
- [ ] Tests unitaires
- [ ] CI/CD pipeline

## Licence

MIT
