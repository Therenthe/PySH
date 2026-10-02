import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  root: "app/ui",
  build: { outDir: "../../dist", emptyOutDir: true },
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    proxy: { '/api': { target: 'http://127.0.0.1:8765', changeOrigin: true } },
  },
});
