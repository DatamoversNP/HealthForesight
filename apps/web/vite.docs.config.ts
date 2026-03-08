import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// Documentation portal server configuration
export default defineConfig({
  plugins: [react()],
  root: '.',
  publicDir: 'public',
  server: {
    port: 3051,
    strictPort: true,
    open: '/index-docs.html',
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist-docs',
    rollupOptions: {
      input: path.resolve(__dirname, 'index-docs.html'),
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
