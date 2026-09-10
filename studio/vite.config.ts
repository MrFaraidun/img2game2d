import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';
import fs from 'node:fs';

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    {
      name: 'serve-project-assets',
      configureServer(server) {
        server.middlewares.use((req, res, next) => {
          if (!req.url) return next();
          const cleanUrl = req.url.split('?')[0];

          if (cleanUrl.startsWith('/assets/')) {
            const rel = cleanUrl.replace('/assets/', '');
            const filePath = path.resolve(__dirname, '../exports/viewer/assets', rel);
            if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
              const contentType = filePath.endsWith('.png')
                ? 'image/png'
                : filePath.endsWith('.json')
                ? 'application/json'
                : 'text/plain';

              res.writeHead(200, {
                'Content-Type': contentType,
                'Cache-Control': 'no-store, no-cache, must-revalidate'
              });
              return fs.createReadStream(filePath).pipe(res);
            }
          }

          if (cleanUrl.startsWith('/exports/')) {
            const rel = cleanUrl.replace('/exports/', '');
            const filePath = path.resolve(__dirname, '../exports', rel);
            if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
              const contentType = filePath.endsWith('.png')
                ? 'image/png'
                : filePath.endsWith('.json')
                ? 'application/json'
                : filePath.endsWith('.atlas')
                ? 'text/plain'
                : 'application/octet-stream';

              res.writeHead(200, {
                'Content-Type': contentType,
                'Cache-Control': 'no-store, no-cache, must-revalidate'
              });
              return fs.createReadStream(filePath).pipe(res);
            }
          }

          next();
        });
      }
    }
  ],
  server: {
    port: 3000,
    host: true
  }
});
