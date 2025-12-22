const { app, BrowserWindow, shell, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

// Chemin de l'icone
const iconPath = path.join(__dirname, '..', 'assets', 'icon.png');

// Garde une référence globale
let mainWindow;
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

function startBackend() {
  return new Promise((resolve, reject) => {
    log('Démarrage du backend...');

    let backendPath;
    let args;

    if (isDev) {
      // En dev : lance Python directement
      backendPath = 'python';
      args = ['-m', 'uvicorn', 'src.services.api:app', '--port', '8000'];
      log(`Dev mode: ${backendPath} ${args.join(' ')}`);
    } else {
      // En production : lance l'exe PyInstaller
      // Cherche dans plusieurs emplacements possibles
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
      // Quand uvicorn est prêt
      if (output.includes('Uvicorn running') || output.includes('Application startup complete')) {
        resolve();
      }
    });

    backendProcess.stderr.on('data', (data) => {
      const output = data.toString();
      log(`Backend stderr: ${output}`);
      // Uvicorn écrit aussi dans stderr
      if (output.includes('Uvicorn running') || output.includes('Application startup complete')) {
        resolve();
      }
    });

    backendProcess.on('error', (err) => {
      log(`Erreur backend: ${err.message}`);
      reject(err);
    });

    backendProcess.on('close', (code) => {
      log(`Backend fermé avec code: ${code}`);
    });

    // Timeout de sécurité - résoudre après 5 secondes si pas de signal
    setTimeout(() => {
      log('Backend timeout - on continue quand même');
      resolve();
    }, 5000);
  });
}

function stopBackend() {
  if (backendProcess) {
    log('Arrêt du backend...');

    // Sur Windows, il faut tuer le processus différemment
    if (process.platform === 'win32') {
      spawn('taskkill', ['/pid', backendProcess.pid, '/f', '/t']);
    } else {
      backendProcess.kill('SIGTERM');
    }

    backendProcess = null;
  }
}

function createWindow() {
  log('Création de la fenêtre...');
  log(`isDev: ${isDev}`);
  log(`__dirname: ${__dirname}`);
  log(`app.getAppPath(): ${app.getAppPath()}`);
  log(`process.resourcesPath: ${process.resourcesPath}`);

  const preloadPath = path.join(__dirname, 'preload.js');
  log(`Preload path: ${preloadPath}`);

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
      webSecurity: false // Permet le chargement depuis localhost en dev
    },
    show: false,
  });

  // URL à charger
  let url;
  if (isDev) {
    url = 'http://localhost:5173';
  } else {
    // En production, dist est à la racine de l'app
    const indexPath = path.join(app.getAppPath(), 'dist', 'index.html');
    log(`Index path: ${indexPath}`);
    url = `file://${indexPath}`;
  }

  log(`Chargement de: ${url}`);
  mainWindow.loadURL(url);

  // Log des erreurs de chargement
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    log(`Erreur de chargement: ${errorCode} - ${errorDescription}`);
  });

  mainWindow.webContents.on('console-message', (event, level, message) => {
    log(`Console [${level}]: ${message}`);
  });

  // Afficher quand prêt
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    log('Fenêtre affichée');
  });

  // DevTools en dev
  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  // Liens externes dans le navigateur
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Démarrage de l'app
app.whenReady().then(async () => {
  try {
    // 1. Lancer le backend
    await startBackend();
    log('Backend prêt');

    // 2. Créer la fenêtre
    createWindow();
  } catch (error) {
    log(`Erreur au démarrage: ${error.message}`);
    // On crée quand même la fenêtre, le backend sera peut-être dispo
    createWindow();
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
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
