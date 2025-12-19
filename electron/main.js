const { app, BrowserWindow, shell, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

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
      backendPath = path.join(rootPath, 'backend', 'backend.exe');
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

  const preloadPath = path.join(__dirname, 'preload.js');
  log(`Preload path: ${preloadPath}`);

  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 800,
    minHeight: 600,
    icon: path.join(__dirname, '../public/icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: preloadPath,
      webSecurity: false // Permet le chargement depuis localhost en dev
    },
    show: false,
  });

  // URL à charger
  const url = isDev
    ? 'http://localhost:5173'
    : `file://${path.join(__dirname, '../dist/index.html')}`;

  log(`Chargement de: ${url}`);
  mainWindow.loadURL(url);

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

// IPC : Ouvrir le dialog de sélection de dossier
ipcMain.handle('select-folder', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory'],
    title: 'Sélectionner le dossier contenant les CVs'
  });

  if (result.canceled) {
    return null;
  }

  return result.filePaths[0];
});
