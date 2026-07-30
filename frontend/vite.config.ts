import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Tell the browser never to cache dev modules — repeated dev-server restarts
    // this session left the browser serving stale bundles through plain refreshes.
    headers: { "Cache-Control": "no-store" },
  },
});
