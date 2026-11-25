import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // Base path pour Electron (fichiers locaux)
  base: './',
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    // Output dans dist/ pour Electron
    outDir: 'dist',
    emptyOutDir: true,
    // Chemins relatifs pour fonctionner en local
    assetsDir: 'assets',
    rollupOptions: {
      output: {
        // Separe les grosses dependances pour un meilleur cache et un chargement plus rapide
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined;
          if (id.includes('@mui/icons-material')) return 'mui-icons';
          if (/node_modules\/(@mui|@emotion)\//.test(id)) return 'mui';
          if (/node_modules\/(react|react-dom|scheduler)\//.test(id)) return 'react-vendor';
          return undefined;
        }
      }
    }
  }
})
