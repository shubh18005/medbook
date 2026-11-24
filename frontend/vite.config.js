import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// VITE_BASE is set by the GitHub Pages workflow to "/<repository-name>/".
// Locally it is not set, so the app is served from "/" as usual.
export default defineConfig({
  base: process.env.VITE_BASE || '/',
  plugins: [react()],
})
