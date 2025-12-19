module.exports = {
  packagerConfig: {
    name: 'CV Classifier Pro',
    executableName: 'cv-classifier-pro',
    icon: './public/icon',
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
      /\.log$/
    ],
    // Fichiers supplémentaires à inclure
    extraResource: [
      './src/services',
      './src/database',
      './src/utils'
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
        setupIcon: './public/icon.ico',
        iconUrl: 'https://raw.githubusercontent.com/your-repo/icon.ico'
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
          homepage: 'https://github.com/your-repo',
          icon: './public/icon.png',
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
          icon: './public/icon.png',
          categories: ['Office', 'Utility']
        }
      }
    }
  ]
};
