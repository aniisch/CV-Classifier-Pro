const { contextBridge, ipcRenderer } = require('electron');

// Expose des APIs sécurisées au renderer (frontend)
contextBridge.exposeInMainWorld('electronAPI', {
  // Ouvre un dialog pour sélectionner un dossier
  selectFolder: () => ipcRenderer.invoke('select-folder'),

  // Vérifie si on est dans Electron
  isElectron: true
});
