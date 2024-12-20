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
      input: [
        "src/util.ts",
        "src/ui.ts"
      ],
      output: {
        format: "es",
        entryFileNames: "[name].js",
        chunkFileNames: "[name].js",
        assetFileNames: "[name][extname]"
      }
    },
    minify: false
  }
});
