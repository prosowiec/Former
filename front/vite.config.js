import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Proxy /health and /airflow/* to the FastAPI server during development
      "/health": "http://localhost:8000",
      "/airflow": "http://localhost:8000",
    },
  },
});