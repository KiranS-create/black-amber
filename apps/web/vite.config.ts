import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/documents': 'http://localhost:8000',
      '/leaks': 'http://localhost:8000',
      '/releases': 'http://localhost:8000',
      '/recipients': 'http://localhost:8000',
      '/analyze': 'http://localhost:8000',
      '/analysis': 'http://localhost:8000',
      '/evidence': 'http://localhost:8000',
      '/ledger': 'http://localhost:8000',
      '/auth': 'http://localhost:8000',
      '/directory': 'http://localhost:8000',
      '/capabilities': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    }
  }
});
