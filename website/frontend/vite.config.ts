import { defineConfig } from 'vite';

export default defineConfig({
  test: {
    environment: 'node', // or 'jsdom' if you're testing browser-like environments
    // webAssembly: true,    // Enable WASM support in Vitest
  },
  resolve: {
    alias: {
      'argon2id': '/node_modules/argon2id/dist/simd.wasm',
    },
  },
});
