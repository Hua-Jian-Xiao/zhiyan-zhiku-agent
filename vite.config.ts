import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: true,
    port: 5173,
    strictPort: true,
    open: false,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/media': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
    watch: {
      // Avoid EBUSY crashes when archive files are open in another app.
      ignored: [
        '**/*.zip',
        '**/node_modules.zip',
        '**/dist/**',
        '**/server/**',
        '**/.claude/**',
        '**/media/**',
        '**/*.sql',
      ],
    },
  },
  preview: {
    host: true,
    port: 4173,
  },
})
