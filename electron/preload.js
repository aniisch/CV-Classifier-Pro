const { contextBridge, ipcRenderer } = require('electron');

// Expose des APIs securisees au renderer (frontend)
contextBridge.exposeInMainWorld('electronAPI', {
  // Ouvre un dialog pour selectionner un dossier
  selectFolder: () => ipcRenderer.invoke('select-folder'),

  // Ouvre un dialog pour selectionner un fichier
  selectFile: (options) => ipcRenderer.invoke('select-file', options),

  // Verifie si on est dans Electron
  isElectron: true
});
