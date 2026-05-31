import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Build configuration for the LFDS Recettes site.
// Output goes to dist/ (deployed to Netlify as recettes.l-fds.com).
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  server: {
    port: 5174,
    open: false,
  },
});
