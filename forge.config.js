module.exports = {
  packagerConfig: {
    name: 'CV Classifier Pro',
    executableName: 'cv-classifier-pro',
    asar: true,
    // Fichiers à ignorer lors du packaging
    ignore: [
      /^\/src/,
      /^\/node_modules\/(?!(@electron|electron))/,
      /^\/.git/,
      /^\/\.vscode/,
      /^\/unutil/,
      /^\/Docs/,
      /\.md$/,
      /\.log$/,
      /^\/build$/,
      /\.spec$/
    ],
    // Fichiers supplémentaires à inclure (backend.exe sera ici)
    extraResource: [
      './electron/backend'
    ]
  },
  rebuildConfig: {},
  makers: [
    // Windows - Crée un installateur .exe
    {
      name: '@electron-forge/maker-squirrel',
      config: {
        name: 'CVClassifierPro',
        authors: 'CV Classifier Pro Team',
        description: 'Application desktop pour analyser et classifier des CVs'
        // Pas d'icône pour l'instant - utilisera l'icône par défaut
      }
    },
    // macOS et Linux - Crée un .zip
    {
      name: '@electron-forge/maker-zip',
      platforms: ['darwin', 'linux']
    },
    // Linux - Crée un .deb (Debian/Ubuntu)
    {
      name: '@electron-forge/maker-deb',
      config: {
        options: {
          name: 'cv-classifier-pro',
          productName: 'CV Classifier Pro',
          maintainer: 'CV Classifier Pro Team',
          homepage: 'https://github.com/aniisch/CV-Classifier-Pro',
          categories: ['Office', 'Utility']
        }
      }
    },
    // Linux - Crée un .rpm (Fedora/RedHat)
    {
      name: '@electron-forge/maker-rpm',
      config: {
        options: {
          name: 'cv-classifier-pro',
          productName: 'CV Classifier Pro',
          categories: ['Office', 'Utility']
        }
      }
    }
  ]
};
