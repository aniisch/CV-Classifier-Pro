// Configuration de l'application
// En production Electron (file://), le port est fourni par le preload (port libre)
// En dev (http://localhost:5173), le proxy Vite redirige vers localhost:8000

const isElectronProd = window.location.protocol === 'file:';
const backendPort = window.electronAPI?.backendPort ?? 8000;

export const API_BASE_URL = isElectronProd
  ? `http://127.0.0.1:${backendPort}`
  : '';

export function apiUrl(path) {
  return `${API_BASE_URL}${path}`;
}
