# CV Classifier Pro

Application desktop multi-projets pour l'analyse et la classification de CV. Deux modes disponibles : mode simple avec analyse par mots-clés pondérés, et mode LLM pour comparaison intelligente avec les offres d'emploi.

## 🚀 Fonctionnalités

### Phase 1 - Mode Simple (Actif)
- Gestion multi-projets : créez et gérez plusieurs projets d'analyse indépendants
- Analyse par mots-clés avec système de pondération (total = 100%)
- Scoring pondéré basé sur les mots-clés trouvés dans les CVs
- Rapports détaillés en Markdown avec statistiques
- Base de données locale SQLite pour l'historique persistant
- Interface intuitive avec Material-UI
- Mode hors-ligne complet
- Application desktop (Electron) multi-plateforme

### Phase 2 - Gestion des Offres d'Emploi (Prochain)
- Upload d'offres d'emploi (PDF/TXT)
- Parsing automatique pour extraire les requirements
- Analyse basée sur l'offre avec matching de mots-clés

### Phase 3 - Mode LLM (Futur)
- Support multi-provider LLM : OpenAI, Anthropic, OLLAMA
- Exécution locale avec OLLAMA pour la sécurité
- Analyse intelligente de compatibilité CV-Offre
- Reasoning et suggestions contextuelles

## 📋 Prérequis

- Node.js >= 18
- Python 3.8+
- SQLite (local)

## 🔧 Installation et Développement

```bash
# Clone du repository
git clone https://github.com/aniisch/CV-Classifier-Pro.git
cd CV-Classifier-Pro

# Installation des dépendances
npm install
pip install -r requirements.txt

# Développement en mode web
npm run start              # Frontend (localhost:5173)
cd src/database
python init_db.py # (la premiére fois) a automatiser après
uvicorn src.services.api:app --reload --port 8000  # Backend

# Build desktop
npm run build
```

## 🗂️ Structure du Projet

```
cv-classifier-pro/
├── src/
│   ├── components/         # Composants React
│   │   ├── HomeScreen.jsx       # Accueil et gestion projets (Phase 1)
│   │   ├── ProjectEditor.jsx    # Édition d'un projet (Phase 1)
│   │   ├── CVAnalyzerForm.jsx   # Formulaire analyse mode simple (Phase 1)
│   │   ├── AnalysisReport.jsx   # Affichage rapport (Phase 1)
│   │   ├── AnalysisHistory.jsx  # Historique analyses (Phase 1)
│   │   ├── JobOfferUpload.jsx   # Upload offre (Phase 2)
│   │   └── LLMSettings.jsx      # Configuration LLM (Phase 3)
│   ├── services/
│   │   ├── api.py              # FastAPI
│   │   ├── cv_analyzer.py      # Logique analyse mode simple
│   │   ├── job_offer_parser.py # Parser offres (Phase 2)
│   │   └── llm_manager.py      # Gestion LLMs (Phase 3)
│   ├── database/
│   │   ├── models.py           # Modèles SQLAlchemy
│   │   ├── database.py         # Configuration DB
│   │   └── project_manager.py  # Gestion projets (Phase 1)
│   ├── utils/
│   │   ├── error_handling.py
│   │   └── llm_adapters/       # Adaptateurs LLM (Phase 3)
│   ├── theme/
│   │   └── theme.js
│   ├── hooks/
│   │   └── useProject.js       # Hook gestion projet (Phase 1)
│   └── main.jsx
├── electron/                   # Configuration Electron (Phase 1)
├── requirements.txt
├── package.json
├── vite.config.js
└── index.html
```

## 🛣️ Roadmap Détaillée

### Phase 1 - Mode Simple et Multi-Projet
- [ ] Home screen avec liste des projets
- [ ] CRUD des projets (create, read, update, delete)
- [ ] Persistance des projets en SQLite
- [ ] Refactorisation CVAnalyzerForm pour utiliser le projet sélectionné
- [ ] Export historique des analyses par projet
- [ ] Setup Electron pour build desktop
- [ ] Build et packaging cross-plateforme

### Phase 2 - Offres d'Emploi
- [ ] Composant upload d'offre
- [ ] Parser offre (extraction requirements)
- [ ] Modèle database pour job_offers
- [ ] Analyse simple mode basée sur offre
- [ ] Affichage comparatif CV vs offre

### Phase 3 - Mode LLM
- [ ] Adaptateurs LLM (OpenAI, Anthropic, OLLAMA)
- [ ] Configuration et sauvegarde API keys
- [ ] Guide setup OLLAMA dans l'app
- [ ] LLMAnalyzer service
- [ ] UI pour mode LLM
- [ ] Gestion queue/worker (optim fin)

## 📦 Branches

- `main` : Production stable
- `develop` : Développement principal
- `feature/*` : Nouvelles fonctionnalités
- `hotfix/*` : Corrections urgentes
- `release/*` : Préparation des versions

## 🤝 Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/amelioration`)
3. Commit (`git commit -m 'feat: Ajout nouvelle fonctionnalité'`)
4. Push (`git push origin feature/amelioration`)
5. Créer une Pull Request

## 📄 Licence

MIT
