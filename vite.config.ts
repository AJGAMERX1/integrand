import { defineConfig } from 'vite';

// GitHub Pages serves the site under /<repo>/. Override with VITE_BASE for local preview.
export default defineConfig({
  base: process.env.VITE_BASE ?? '/integrand/',
  build: { target: 'es2022', sourcemap: false },
});
