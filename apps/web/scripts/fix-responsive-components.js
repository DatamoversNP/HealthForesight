#!/usr/bin/env node
/**
 * Script to identify components that need responsive fixes
 * Run: node scripts/fix-responsive-components.js
 */

const fs = require('fs')
const path = require('path')

const componentsDir = path.join(__dirname, '../src/components/marketing')
const pagesDir = path.join(__dirname, '../src/pages/marketing')

console.log('🔍 Responsive Component Audit\n')
console.log('================================\n')

// Find all visual components
const visualComponents = fs.readdirSync(componentsDir)
  .filter(f => f.endsWith('Visual.tsx') || f.endsWith('Visualization.tsx'))

console.log(`Found ${visualComponents.length} visual components:`)
visualComponents.forEach(f => console.log(`  - ${f}`))

console.log('\n📋 Checklist:\n')
console.log('[ ] Add responsive containers to all visual components')
console.log('[ ] Update all Button components with minHeight: 44')
console.log('[ ] Add maxWidth to Typography in long-form content')
console.log('[ ] Test all pages at breakpoints')

console.log('\n✅ Pattern for Visual Components:\n')
console.log(`<Box
  sx={{
    width: '100%',
    maxWidth: { xs: '100%', md: '800px' },
    height: { xs: '250px', md: '400px' },
    p: { xs: 2, md: 3 },
  }}
>
  <svg viewBox="..." preserveAspectRatio="xMidYMid meet">
`)

console.log('\n✅ Pattern for Buttons:\n')
console.log(`<Button
  sx={{
    minHeight: 44,
    py: { xs: 1.5, md: 1 },
    fontSize: { xs: '14px', md: '16px' },
  }}
>`)

console.log('\n✅ Pattern for Typography:\n')
console.log(`<Typography
  sx={{
    maxWidth: { xs: '100%', md: '65ch' },
    fontSize: { xs: '16px', md: '17px' },
    lineHeight: 1.8,
  }}
>`)

console.log('\n✨ Use find/replace with these patterns to update all components!')
