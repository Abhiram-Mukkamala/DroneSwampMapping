import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { fileURLToPath } from 'url';

import serveStatic from 'serve-static';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/**
 * Custom Vite plugin that serves the ../web directory at /web/*
 * This allows SimulationContainer to load the Three.js simulator
 * via <iframe src="/web/index.html"> in development.
 */
function serveWebSimulator() {
  return {
    name: 'serve-web-simulator',
    configureServer(server) {
      server.middlewares.use(
        '/web',
        serveStatic(path.resolve(__dirname, '../web'), {
          index: ['index.html'],
        })
      );
    },
  };
}

export default defineConfig({
  plugins: [
    react(),
    serveWebSimulator(),
  ],

  server: {
    port: 5173,
    fs: {
      // Allow Vite to resolve files up to the project root
      allow: [path.resolve(__dirname, '..')],
    },
  },
});
