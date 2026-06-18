import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [
    react(),
    {
      name: "spa-fallback",
      configureServer(server) {
        return () => {
          server.middlewares.use((req, res, next) => {
            // Skip if the path looks like a file (has an extension) or is an API route
            if (/\.[a-zA-Z0-9]+$/.test(req.url) || req.url.startsWith("/api")) {
              return next();
            }
            // Rewrite all other GET requests to index.html for React Router to handle
            if (req.method === "GET") {
              req.url = "/index.html";
            }
            next();
          });
        };
      },
    },
  ],
  server: {
    port: 5173,
    proxy: {
      "/health": "http://localhost:8000",
      "/airflow": "http://localhost:8000",
    },
    allowedHosts: [
      "former.com.pl",
      "www.former.com.pl",
      "localhost",
      "127.0.0.1"
    ]
  }
});