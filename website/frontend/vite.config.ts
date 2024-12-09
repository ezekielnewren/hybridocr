import { defineConfig } from 'vite';

export default defineConfig({
  test: {
    environment: 'node', // or 'jsdom' if you're testing browser-like environments
    // webAssembly: true,    // Enable WASM support in Vitest
  },
  resolve: {
  },
  build: {
    outDir: "dist",
    target: "esnext",
    rollupOptions: {
      input: "src/util.ts"
    }
  }
});
