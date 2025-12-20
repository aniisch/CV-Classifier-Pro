// Configuration de l'application
// En production Electron (file://), on utilise localhost:8000
// En dev (http://localhost:5173), le proxy Vite redirige vers localhost:8000

const isElectronProd = window.location.protocol === 'file:';

export const API_BASE_URL = isElectronProd
  ? 'http://127.0.0.1:8000'
  : '';

export function apiUrl(path) {
  return `${API_BASE_URL}${path}`;
}
