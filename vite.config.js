import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Build is configurable via env vars so the same source can be deployed to:
//  - Netlify (sub-path /quiz/ alongside SNB landing): VITE_BASE=/quiz/ VITE_OUT_DIR=docs/quiz
//  - Fly.io / Docker (root path, served by Express):  VITE_BASE=/ VITE_OUT_DIR=dist
//  - Local dev: defaults to /quiz/ + docs/quiz to mirror Netlify behavior
export default defineConfig({
  plugins: [react()],
  base: process.env.VITE_BASE || "/quiz/",
  build: {
    outDir: process.env.VITE_OUT_DIR || "docs/quiz",
    emptyOutDir: true,
  },
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://localhost:3001",
        changeOrigin: true,
      },
    },
  },
});
