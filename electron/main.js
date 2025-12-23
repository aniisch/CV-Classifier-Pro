const { app, BrowserWindow, shell, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');

// ========================================
// SQUIRREL STARTUP (Windows installer)
// ========================================
// Gère les événements Squirrel sans package externe
if (process.platform === 'win32') {
  const cmd = process.argv[1];
  if (cmd === '--squirrel-install' ||
      cmd === '--squirrel-updated' ||
      cmd === '--squirrel-uninstall' ||
      cmd === '--squirrel-obsolete') {
    app.quit();
  }
}

// ========================================
// OPTIMISATIONS DEMARRAGE
// ========================================
// Désactiver l'accélération hardware pour éviter les flashs GPU
app.disableHardwareAcceleration();
// Empêcher les fenêtres de clignoter
app.commandLine.appendSwitch('disable-gpu');
app.commandLine.appendSwitch('disable-software-rasterizer');

// Chemin de l'icone
const iconPath = path.join(__dirname, '..', 'assets', 'icon.png');

// Garde une reference globale
let mainWindow;
let splashWindow;
let backendProcess;

// Mode dev ou production
const isDev = !app.isPackaged;

// Chemins
const rootPath = isDev
  ? path.join(__dirname, '..')
  : path.join(process.resourcesPath);

function log(message) {
  console.log(`[Main] ${message}`);
}

// Fonction pour verifier si le backend est pret
function checkBackendReady() {
  return new Promise((resolve) => {
    const check = () => {
      const req = http.request({
        hostname: '127.0.0.1',
        port: 8000,
        path: '/api/health',
        method: 'GET',
        timeout: 1000
      }, (res) => {
        if (res.statusCode === 200) {
          resolve(true);
        } else {
          setTimeout(check, 500);
        }
      });

      req.on('error', () => {
        setTimeout(check, 500);
      });

      req.on('timeout', () => {
        req.destroy();
        setTimeout(check, 500);
      });

      req.end();
    };

    check();
  });
}

function createSplashWindow() {
  return new Promise((resolve) => {
    log('Creation du splash screen...');

    splashWindow = new BrowserWindow({
      width: 400,
      height: 500,
      frame: false,
      transparent: false,
      alwaysOnTop: true,
      resizable: false,
      skipTaskbar: true,
      show: false, // NE PAS AFFICHER tant que pas prêt
      icon: iconPath,
      backgroundColor: '#1976d2', // Couleur du splash pour éviter flash
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true
      }
    });

    const splashPath = path.join(__dirname, 'splash.html');

    // Afficher SEULEMENT quand le contenu est prêt
    splashWindow.once('ready-to-show', () => {
      log('Splash pret, affichage...');
      splashWindow.show();
      splashWindow.center();
      resolve();
    });

    splashWindow.on('closed', () => {
      splashWindow = null;
    });

    splashWindow.loadFile(splashPath);
  });
}

function startBackend() {
  return new Promise((resolve, reject) => {
    log('Demarrage du backend...');

    let backendPath;
    let args;

    if (isDev) {
      // En dev : lance Python directement
      backendPath = 'python';
      args = ['-m', 'uvicorn', 'src.services.api:app', '--port', '8000'];
      log(`Dev mode: ${backendPath} ${args.join(' ')}`);
    } else {
      // En production : lance l'exe PyInstaller
      const possiblePaths = [
        path.join(rootPath, 'backend', 'backend.exe'),
        path.join(rootPath, 'electron', 'backend', 'backend.exe'),
        path.join(process.resourcesPath, 'backend', 'backend.exe'),
        path.join(path.dirname(process.execPath), 'backend', 'backend.exe')
      ];

      backendPath = possiblePaths.find(p => {
        try {
          require('fs').accessSync(p);
          return true;
        } catch {
          return false;
        }
      }) || possiblePaths[0];

      args = [];
      log(`Prod mode: ${backendPath}`);
    }

    backendProcess = spawn(backendPath, args, {
      cwd: isDev ? rootPath : undefined,
      stdio: ['pipe', 'pipe', 'pipe'],
      shell: true
    });

    backendProcess.stdout.on('data', (data) => {
      const output = data.toString();
      log(`Backend: ${output}`);
    });

    backendProcess.stderr.on('data', (data) => {
      const output = data.toString();
      log(`Backend stderr: ${output}`);
    });

    backendProcess.on('error', (err) => {
      log(`Erreur backend: ${err.message}`);
      reject(err);
    });

    backendProcess.on('close', (code) => {
      log(`Backend ferme avec code: ${code}`);
    });

    // Resoudre immediatement, on verifiera avec checkBackendReady
    resolve();
  });
}

function stopBackend() {
  if (backendProcess) {
    log('Arret du backend...');

    if (process.platform === 'win32') {
      spawn('taskkill', ['/pid', backendProcess.pid, '/f', '/t']);
    } else {
      backendProcess.kill('SIGTERM');
    }

    backendProcess = null;
  }
}

function createMainWindow() {
  return new Promise((resolve) => {
    log('Creation de la fenetre principale...');

    const preloadPath = path.join(__dirname, 'preload.js');

    mainWindow = new BrowserWindow({
      width: 1400,
      height: 900,
      minWidth: 800,
      minHeight: 600,
      icon: iconPath,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        preload: preloadPath,
        webSecurity: false
      },
      show: false, // IMPORTANT: Ne pas afficher pendant le chargement
      backgroundColor: '#f5f5f5', // Couleur de fond de l'app
    });

    // URL a charger
    let url;
    if (isDev) {
      url = 'http://localhost:5173';
    } else {
      const indexPath = path.join(app.getAppPath(), 'dist', 'index.html');
      log(`Index path: ${indexPath}`);
      url = `file://${indexPath}`;
    }

    log(`Chargement de: ${url}`);

    // Log des erreurs de chargement
    mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
      log(`Erreur de chargement: ${errorCode} - ${errorDescription}`);
    });

    // Quand le contenu est completement charge
    mainWindow.webContents.once('did-finish-load', () => {
      log('Contenu charge completement');
      // Attendre que React soit monte avant de resoudre
      setTimeout(() => {
        resolve();
      }, 500);
    });

    // DevTools en dev (ouvert apres que la fenetre soit prete)
    if (isDev) {
      mainWindow.webContents.once('did-finish-load', () => {
        mainWindow.webContents.openDevTools({ mode: 'detach' });
      });
    }

    // Liens externes dans le navigateur
    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
      shell.openExternal(url);
      return { action: 'deny' };
    });

    mainWindow.on('closed', () => {
      mainWindow = null;
    });

    // Charger l'URL
    mainWindow.loadURL(url);
  });
}

// Demarrage de l'app
app.whenReady().then(async () => {
  try {
    // 1. Creer et attendre que le splash soit prêt avant de l'afficher
    await createSplashWindow();
    log('Splash affiche');

    // 2. Lancer le backend (sans attendre qu'il soit pret)
    startBackend();
    log('Backend lance');

    // 3. Attendre que le backend soit vraiment pret (health check)
    log('Attente du backend...');
    await checkBackendReady();
    log('Backend pret!');

    // 4. Creer la fenetre principale et attendre qu'elle soit chargee
    log('Creation et chargement de la fenetre principale...');
    await createMainWindow();
    log('Fenetre principale chargee!');

    // 5. Fermer le splash et afficher la fenetre principale
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.close();
    }
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.show();
      mainWindow.focus();
    }
    log('Transition terminee!');

  } catch (error) {
    log(`Erreur au demarrage: ${error.message}`);
    // En cas d'erreur, fermer le splash et afficher la fenetre quand meme
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.close();
    }
    if (!mainWindow) {
      await createMainWindow();
    }
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.show();
    }
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow().then(() => {
        if (mainWindow) mainWindow.show();
      });
    }
  });
});

// Fermeture
app.on('window-all-closed', () => {
  stopBackend();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  stopBackend();
});

app.on('quit', () => {
  stopBackend();
});

// IPC : Ouvrir le dialog de selection de dossier
ipcMain.handle('select-folder', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory'],
    title: 'Selectionner le dossier contenant les CVs'
  });

  if (result.canceled) {
    return null;
  }

  return result.filePaths[0];
});

// IPC : Ouvrir le dialog de selection de fichier
ipcMain.handle('select-file', async (event, options) => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    title: 'Selectionner un fichier',
    filters: options?.filters || [
      { name: 'Documents', extensions: ['pdf', 'txt'] },
      { name: 'Tous les fichiers', extensions: ['*'] }
    ]
  });

  if (result.canceled) {
    return null;
  }

  return result.filePaths[0];
});
