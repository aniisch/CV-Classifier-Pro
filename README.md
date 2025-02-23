# CV Classifier Pro

Application de classification automatique de CV basée sur des mots-clés et l'analyse LLM.

## 🚀 Fonctionnalités

- Import multiple de CV (PDF)
- Configuration de mots-clés avec système de pondération
- Analyse de texte et classification automatique
- Génération de rapports détaillés
- Base de données locale pour historique
- Mode hors-ligne disponible
- Interface utilisateur intuitive
- Export des résultats en CSV

## 📋 Prérequis

- Node.js >= 18
- Electron.js pour la version desktop
- Base de données locale (SQLite)

## 🔧 Installation

```bash
# Clone du repository
git clone https://github.com/aniisch/CV-Classifier-Pro.git

# Installation des dépendances
npm install

# Lancement en mode développement web
npm run dev

# Build version desktop
npm run build:electron
```

## 🗂️ Structure du Projet

```
cv-classifier-pro/
├── src/
│   ├── components/         # Composants React
│   ├── services/          # Services métier
│   ├── utils/             # Utilitaires
│   ├── database/         # Configuration DB
│   └── assets/           # Resources statiques
├── electron/             # Configuration Electron
├── scripts/             # Scripts utilitaires
└── tests/              # Tests unitaires
```

## 🛣️ Roadmap

### MVP0.0 (Version Web)
- [x] back python
- [x] lien vers un dossier
- [x] analyse très basique
- [x] interface de base avec React et Material-UI
- [x] génération de rapport Markdown

### MVP0 (Version Web)
- [x] Amélioration de l'interface
- [x] Gestion des erreurs avancée
- [ ] Prévisualisation des CVs
- [x] Export le rapport en pdf
- [x] Historique des analyses
- [x] Suppression d'une analyse
- [ ] Gestions des analyse par offres d'emploi 
- [ ] Charger des cvs
- [ ] Charger des cv apartir de WTG


### Version 1.0 (Desktop)
- [ ] Conversion Electron
- [ ] Base de données locale
- [ ] Gestion hors-ligne
- [ ] Interface améliorée

### Version 2.0 (Intelligence)
- [ ] Intégration LLM
- [ ] Analyse d'offres d'emploi
- [ ] Matching CV-Offre
- [ ] Suggestions intelligentes

## 📝 TODO

- [ ] Ajouter la création du CSV
- [ ] Configurer le bouton "objet précédent"
- [ ] Afficher les images d'objets cibles
- [ ] Implémenter la lecture des fichiers JSON
- [ ] Formatter les données après inférence
- [ ] Créer les bases de données par ligne
- [ ] Gérer le choix du dossier

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