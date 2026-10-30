import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The backend URL comes from VITE_API_URL (see .env.example). No proxy: the backend is deployed
// separately and allows this origin through CORS (backend ALLOWED_ORIGINS).
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, strictPort: true },
  preview: { port: 4173 },
  build: { sourcemap: false },
});
