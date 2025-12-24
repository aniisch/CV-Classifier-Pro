# Guide d'utilisation - CV Classifier Pro

## Bienvenue

CV Classifier Pro vous permet d'analyser des CVs et de les classer selon vos criteres.

---

## 1. Creer un Projet

1. Sur l'ecran d'accueil, cliquez sur **"Nouveau Projet"**
2. Donnez un nom a votre projet (ex: "Recrutement Developpeur Python")
3. Ajoutez une description (optionnel)
4. Cliquez sur **"Creer"**

---

## 2. Configurer les Mots-cles

Apres avoir cree un projet, configurez les competences recherchees :

1. Cliquez sur **"Editer"** a cote du projet
2. Ajoutez des mots-cles avec leur ponderation :
   - Exemple : `Python` = 30%, `Django` = 20%, `SQL` = 15%
3. Le total doit faire **100%**
4. Cliquez sur **"Sauvegarder"**

> **Astuce** : Mettez une ponderation plus elevee pour les competences essentielles.

---

## 3. Analyser des CVs

### Mode Mots-cles (Simple)

1. Selectionnez votre projet
2. Cliquez sur **"Analyser"**
3. Choisissez le dossier contenant vos CVs (format PDF)
4. Selectionnez le mode **"Mots-cles du projet"**
5. Lancez l'analyse

---

## 4. Comprendre les Resultats

Le rapport affiche :

- **Score global** : Pourcentage de correspondance du CV
- **Details par competence** : Quels mots-cles ont ete trouves
- **Classement** : CVs tries du meilleur au moins bon

### Interpretation des scores

| Score | Interpretation |
|-------|----------------|
| 80-100% | Excellent candidat |
| 60-79% | Bon candidat |
| 40-59% | Candidat moyen |
| 0-39% | Ne correspond pas |

---

## 5. Historique

Toutes vos analyses sont sauvegardees :

1. Allez dans **"Historique"**
2. Consultez les analyses passees
3. Exportez les rapports si besoin
4. Supprimez les anciennes analyses

---

## 6. Importer une Offre d'Emploi (alternative au Configurer les Mots-cles)

1. Cliquez sur **"Importer"** dans la section "Offres d'Emploi"
2. Selectionnez un fichier PDF ou TXT
3. Les competences techniques sont detectees automatiquement
4. La ponderation est calculee selon la frequence d'apparition
5. Utilisez cette offre pour analyser les CVs

---

## 7. Modifier les Ponderations d'une Offre

Apres avoir importe une offre, vous pouvez ajuster les ponderations :

1. Dans la liste des offres, cliquez sur l'icone **crayon** (a cote de la poubelle)
2. Modifiez les pourcentages de chaque competence
3. Supprimez les competences non pertinentes avec l'icone **poubelle**
4. Assurez-vous que le total fait **100%**
5. Cliquez sur **"Sauvegarder"**

> **Note** : Les competences les plus mentionnees dans l'offre ont automatiquement un poids plus eleve.

---

## 8. Configurer l'IA (LLM)

Pour utiliser l'analyse IA, configurez d'abord le provider :

1. Cliquez sur l'icone **engrenage** (en haut a droite de l'ecran d'accueil)
2. Choisissez un provider :
   - **Ollama (Local)** : Gratuit, vos donnees restent sur votre PC
   - **OpenAI** : GPT-4, rapide et fiable (necessite une cle API payante)
   - **Anthropic** : Claude, excellent raisonnement (necessite une cle API payante)
3. Selectionnez un modele
4. Pour OpenAI/Anthropic : entrez votre cle API
5. Cliquez sur **"Tester la connexion"** pour verifier
6. Cliquez sur **"Sauvegarder"**

### Installer Ollama (gratuit)

Pour utiliser l'IA localement sans cle API :

1. Telechargez Ollama : https://ollama.com
2. Installez-le sur votre PC
3. Ouvrez un terminal et tapez : `ollama pull llama3.2`
4. Ollama demarre automatiquement en arriere-plan
5. Dans CV Classifier Pro, selectionnez "Ollama" comme provider

> **Avantage Ollama** : Vos CVs ne quittent jamais votre ordinateur !

---

## 9. Analyse IA (Mode LLM)

L'analyse IA est plus intelligente que l'analyse par mots-cles. Elle comprend le contexte et evalue la correspondance globale.

### Prerequis

- **Une offre d'emploi chargee** : L'IA compare les CVs a l'offre
- **LLM configure** : Via l'icone engrenage (voir section 8)

### Lancer une analyse IA

1. Selectionnez votre projet
2. Cliquez sur **"Analyser"**
3. Choisissez le dossier contenant vos CVs
4. Selectionnez le mode **"Analyse IA"** (icone cerveau)
5. Selectionnez l'offre d'emploi a utiliser
6. Choisissez la source des CVs :
   - **Tous les CVs du dossier** : Analyse tous les fichiers PDF
   - **Top N d'une analyse** : Prend les N meilleurs d'une analyse precedente
   - **Selection manuelle** : Cochez les CVs specifiques a analyser
7. Lancez l'analyse

### Selectionner des CVs specifiques

Pour ne pas analyser tous les CVs (gain de temps et de cout) :

1. **Lancez d'abord** une analyse par mots-cles ou par offre d'emploi
2. Passez ensuite en mode **"Analyse IA"**
3. Choisissez **"Top N"** ou **"Selection manuelle"**
4. Selectionnez l'analyse precedente dans la liste
5. Pour Top N : utilisez le curseur pour choisir combien de CVs
6. Pour manuel : cochez les CVs souhaites (le score precedent est affiche)

> **Astuce** : Faites d'abord un tri rapide par mots-cles, puis analysez les meilleurs profils avec l'IA.

---

## 10. Comprendre le Rapport IA

Le rapport IA contient :

### Synthese et Classement

Un tableau resume tous les CVs analyses :

| Rang | Candidat | Score | Recommandation |
|------|----------|-------|----------------|
| 1 | cv_dupont.pdf | 85/100 | ✅ Fortement recommande |
| 2 | cv_martin.pdf | 72/100 | ⚠️ A considerer |
| 3 | cv_durand.pdf | 45/100 | ❌ Non recommande |

### Signification des recommandations

| Icone | Signification | Score |
|-------|---------------|-------|
| ✅ Fortement recommande | Excellent match, a convoquer | 80-100 |
| ⚠️ A considerer | Profil interessant, a approfondir | 60-79 |
| ❌ Non recommande | Ne correspond pas au poste | 0-59 |
| ❓ Non evalue | L'IA n'a pas pu determiner un score | - |

### Pourquoi "❓ Non evalue" ?

Ce statut apparait quand l'IA n'a pas pu extraire un score clair. Causes possibles :

- **CV illisible** : Le PDF contient des images au lieu de texte
- **Reponse incomplete** : Le modele LLM a ete interrompu
- **Format inattendu** : L'IA n'a pas suivi le format demande
- **Probleme de connexion** : Timeout ou erreur reseau

> **Solution** : Relancez l'analyse pour ce CV specifique, ou verifiez que le PDF contient du texte selectionnable.

### Analyses Detaillees

Pour chaque CV, l'IA fournit :
- Resume du profil
- Points forts
- Points faibles / lacunes
- Analyse detaillee (experience, competences, formation)
- Conclusion et justification

---

## Raccourcis

| Action | Comment |
|--------|---------|
| Nouveau projet | Bouton "+" sur l'accueil |
| Editer projet | Icone crayon |
| Supprimer projet | Icone poubelle |
| Configurer IA | Icone engrenage |
| Aide | Icone "?" |
| Retour accueil | Bouton "Retour" |

---

## Support

En cas de probleme :
- Verifiez que vos CVs sont au format PDF avec texte selectionnable
- Assurez-vous que le dossier contient des fichiers
- Pour l'IA : verifiez que Ollama est lance ou que votre cle API est valide
- Redemarrez l'application si necessaire

---

**Version 3.1.0** - CV Classifier Pro
