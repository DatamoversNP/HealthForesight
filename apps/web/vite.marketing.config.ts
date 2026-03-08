import { defineConfig, Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'
import fs from 'fs'
import { renameMarketingIndex } from './vite.marketing.build.plugin'

// Marketing website configuration - runs on port 3052
// This is a completely separate website from the main app

// Copy index-marketing.html to index.html BEFORE Vite starts
// This must happen synchronously during config loading
const marketingHtmlPath = resolve(__dirname, 'index-marketing.html')
const indexHtmlPath = resolve(__dirname, 'index.html')

if (fs.existsSync(marketingHtmlPath)) {
  // Backup original index.html if it exists and not already backed up
  if (fs.existsSync(indexHtmlPath) && !fs.existsSync(indexHtmlPath + '.app-backup')) {
    fs.copyFileSync(indexHtmlPath, indexHtmlPath + '.app-backup')
  }
  
  // Copy marketing HTML to index.html for Vite dev server
  fs.copyFileSync(marketingHtmlPath, indexHtmlPath)
}

export default defineConfig({
  plugins: [
    react({
      jsxRuntime: 'automatic',
      jsxImportSource: 'react',
    }),
    renameMarketingIndex(),
  ],
  server: {
    port: 3052,
    strictPort: false, // Allow fallback to next available port if 3052 is taken
  },
  build: {
    outDir: 'dist-marketing',
    rollupOptions: {
      input: resolve(__dirname, 'index-marketing.html'),
    },
    // Ensure proper asset handling
    assetsDir: 'assets',
    // Generate source maps for production debugging (optional)
    sourcemap: false,
    // Optimize chunk size
    chunkSizeWarningLimit: 1000,
  },
  // Base path for production (leave empty for root domain)
  base: '/',
})
