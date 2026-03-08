/**
 * Vite plugin to rename index-marketing.html to index.html after build
 */
import type { Plugin } from 'vite'
import { resolve } from 'path'
import fs from 'fs'

export function renameMarketingIndex(): Plugin {
  return {
    name: 'rename-marketing-index',
    closeBundle() {
      try {
        const distDir = resolve(process.cwd(), 'dist-marketing')
        const sourceFile = resolve(distDir, 'index-marketing.html')
        const targetFile = resolve(distDir, 'index.html')

        if (fs.existsSync(sourceFile)) {
          // Copy content to index.html
          const content = fs.readFileSync(sourceFile, 'utf-8')
          fs.writeFileSync(targetFile, content)
          // Remove the old file
          fs.unlinkSync(sourceFile)
          console.log('✓ Renamed index-marketing.html to index.html')
        }
      } catch (error) {
        console.warn('Warning: Could not rename index-marketing.html:', error)
      }
    },
  }
}
