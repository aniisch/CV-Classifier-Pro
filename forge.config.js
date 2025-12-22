const path = require('path');

module.exports = {
  packagerConfig: {
    name: 'CV Classifier Pro',
    executableName: 'cv-classifier-pro',
    asar: true,
    // Icone de l'application
    icon: path.join(__dirname, 'assets', 'icon'),
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
        description: 'Application desktop pour analyser et classifier des CVs',
        iconUrl: 'file://' + path.join(__dirname, 'assets', 'icon.ico'),
        setupIcon: path.join(__dirname, 'assets', 'icon.ico')
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
