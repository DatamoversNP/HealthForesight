/**
 * Verify Tour Targeting - Check that all tour target selectors exist in the codebase
 * 
 * Usage: node scripts/verify-tour-targeting.js
 */

const fs = require('fs')
const path = require('path')
const { TOUR_TARGETS } = require('./capture-tour-screenshots-playwright.js')

const SOURCE_DIR = path.join(__dirname, '../src')

// Tour targets from the capture script
const allTargets = Object.values(TOUR_TARGETS).flat().map(t => t.target)

console.log('🔍 Verifying Tour Targeting')
console.log('═'.repeat(60))
console.log('')

// Search for class names in source files
function searchForClass(className) {
  const results = []
  const files = []
  
  function walkDir(dir) {
    const entries = fs.readdirSync(dir, { withFileTypes: true })
    
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name)
      
      if (entry.isDirectory()) {
        // Skip node_modules and other build directories
        if (!['node_modules', 'dist', '.git', '.next'].includes(entry.name)) {
          walkDir(fullPath)
        }
      } else if (entry.isFile() && (entry.name.endsWith('.tsx') || entry.name.endsWith('.ts') || entry.name.endsWith('.jsx') || entry.name.endsWith('.js'))) {
        files.push(fullPath)
      }
    }
  }
  
  walkDir(SOURCE_DIR)
  
  // Search for className in files
  for (const file of files) {
    try {
      const content = fs.readFileSync(file, 'utf8')
      // Remove leading dot from class name for search
      const searchClass = className.replace(/^\./, '')
      
      // Search for className="..." or class="..." or className={...}
      const patterns = [
        new RegExp(`className=["']${searchClass}["']`, 'g'),
        new RegExp(`className=\\{["']${searchClass}["']\\}`, 'g'),
        new RegExp(`class=["']${searchClass}["']`, 'g'),
        new RegExp(`\\.${searchClass}`, 'g'), // CSS class selector
      ]
      
      for (const pattern of patterns) {
        if (pattern.test(content)) {
          results.push({
            file: path.relative(SOURCE_DIR, file),
            found: true,
          })
          break
        }
      }
    } catch (error) {
      // Skip files that can't be read
    }
  }
  
  return results
}

// Verify each target
let foundCount = 0
let missingCount = 0
const missingTargets = []

console.log('Checking tour targets...')
console.log('')

for (const target of allTargets) {
  const className = target.replace(/^\./, '')
  const results = searchForClass(target)
  
  if (results.length > 0) {
    console.log(`✅ ${target}`)
    foundCount++
  } else {
    console.log(`❌ ${target} - NOT FOUND`)
    missingCount++
    missingTargets.push(target)
  }
}

console.log('')
console.log('═'.repeat(60))
console.log('📊 Verification Summary')
console.log('═'.repeat(60))
console.log(`✅ Found: ${foundCount}`)
console.log(`❌ Missing: ${missingCount}`)

if (missingTargets.length > 0) {
  console.log('')
  console.log('⚠️  Missing targets:')
  missingTargets.forEach(target => {
    console.log(`   - ${target}`)
  })
  console.log('')
  console.log('💡 Action required:')
  console.log('   Add these class names to the corresponding components')
  console.log('   or update the tour target selectors.')
}

console.log('')

