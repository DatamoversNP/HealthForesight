/**
 * Automated Screenshot Capture for Product Tours
 * Uses Puppeteer to programmatically capture screenshots of all tour targets
 * 
 * Usage: node scripts/capture-tour-screenshots.js
 * 
 * Requirements:
 *   npm install puppeteer
 */

const puppeteer = require('puppeteer')
const fs = require('fs')
const path = require('path')

const SCREENSHOTS_DIR = path.join(__dirname, '../public/screenshots/tours')
const BASE_URL = 'http://localhost:3050'

// Tour targets and their corresponding screenshot names
const TOUR_TARGETS = {
  dashboard: [
    { target: '.dashboard-header', name: 'dashboard-overview.png', description: 'Dashboard header and navigation' },
    { target: '.key-metrics-row', name: 'dashboard-metrics.png', description: 'Key metrics cards' },
    { target: '.decision-recommendations', name: 'dashboard-decisions.png', description: 'Decision recommendations section' },
    { target: '.cost-trend-chart', name: 'dashboard-cost-trend.png', description: 'Cost trend forecast chart' },
    { target: '.risk-register', name: 'dashboard-risk-register.png', description: 'Risk register display' },
    { target: '.top-policies-chart', name: 'dashboard-policy-performance.png', description: 'Top policy performance charts' },
  ],
  policies: [
    { target: '.policy-catalog-header', name: 'policy-catalog-overview.png', description: 'Policy catalog main view' },
    { target: '.policy-search-filters', name: 'policy-search-filters.png', description: 'Search and filter interface' },
    { target: '.policy-list', name: 'policy-list.png', description: 'Policy list with cards' },
    { target: '.create-policy-button', name: 'policy-create-options.png', description: 'Create policy button and options' },
  ],
  'policy-builder': [
    { target: '.policy-builder-header', name: 'policy-builder-header.png', description: 'Policy builder introduction' },
    { target: '.builder-steps', name: 'policy-builder-steps.png', description: 'Step navigation stepper' },
    { target: '.scope-selector', name: 'policy-builder-scope.png', description: 'Scope configuration interface' },
    { target: '.levers-config', name: 'policy-builder-levers.png', description: 'Levers configuration interface' },
  ],
  'policy-workspace': [
    { target: '.workspace-tabs', name: 'workspace-tabs.png', description: 'All workspace tabs overview' },
    { target: '.assumptions-manager', name: 'workspace-assumptions.png', description: 'Assumptions manager' },
    { target: '.guardrails-manager', name: 'workspace-guardrails.png', description: 'Guardrails manager' },
    { target: '.versions-list', name: 'workspace-versions.png', description: 'Version control interface' },
  ],
  'analysis-workspace': [
    { target: '.analysis-header', name: 'analysis-overview.png', description: 'Analysis workspace header' },
    { target: '.analysis-tabs', name: 'analysis-tabs.png', description: 'Analysis tabs navigation' },
    { target: '.impact-results', name: 'analysis-results.png', description: 'Impact results display' },
    { target: '.trust-panel', name: 'analysis-trust-panel.png', description: 'Trust panel interface' },
  ],
  whatif: [
    { target: '.whatif-header', name: 'whatif-overview.png', description: 'What-if analysis header' },
    { target: '.scenario-builder', name: 'whatif-scenario-builder.png', description: 'Scenario builder interface' },
    { target: '.scenario-comparison', name: 'whatif-comparison.png', description: 'Scenario comparison view' },
  ],
  ingestions: [
    { target: '.ingestion-header', name: 'ingestion-dashboard.png', description: 'Ingestion dashboard overview' },
    { target: '.upload-section', name: 'ingestion-upload.png', description: 'Upload interface' },
    { target: '.ingestion-list', name: 'ingestion-history.png', description: 'Ingestion history and monitoring' },
  ],
}

// Page routes for each tour
const TOUR_ROUTES = {
  dashboard: '/',
  policies: '/policies',
  'policy-builder': '/policies/builder',
  'policy-workspace': '/policies/workspace/10000000-0000-0000-0000-000000000001', // Example policy ID
  'analysis-workspace': '/analyses',
  whatif: '/whatif',
  ingestions: '/ingestions',
}

async function waitForElement(page, selector, timeout = 10000) {
  try {
    await page.waitForSelector(selector, { timeout, visible: true })
    // Additional wait for animations/transitions
    await page.waitForTimeout(500)
    return true
  } catch (error) {
    console.warn(`⚠️  Element not found: ${selector}`)
    return false
  }
}

async function captureScreenshot(page, selector, filePath, description) {
  try {
    const element = await page.$(selector)
    if (!element) {
      console.warn(`⚠️  Element ${selector} not found, skipping screenshot`)
      return false
    }

    // Scroll element into view
    await element.scrollIntoView({ behavior: 'smooth', block: 'center' })
    await page.waitForTimeout(500)

    // Get element bounding box
    const boundingBox = await element.boundingBox()
    if (!boundingBox) {
      console.warn(`⚠️  Could not get bounding box for ${selector}`)
      return false
    }

    // Capture screenshot of element with padding
    const padding = 20
    await page.screenshot({
      path: filePath,
      clip: {
        x: Math.max(0, boundingBox.x - padding),
        y: Math.max(0, boundingBox.y - padding),
        width: boundingBox.width + (padding * 2),
        height: boundingBox.height + (padding * 2),
      },
    })

    console.log(`✅ Captured: ${filePath}`)
    return true
  } catch (error) {
    console.error(`❌ Error capturing ${selector}:`, error.message)
    return false
  }
}

async function loginIfNeeded(page) {
  try {
    // Check if we're on login page
    const currentUrl = page.url()
    if (currentUrl.includes('/login')) {
      console.log('🔐 Logging in...')
      
      // Wait for login form
      await page.waitForSelector('input[type="email"], input[name="email"], input[type="text"]', { timeout: 5000 })
      
      // Fill login form (adjust selectors based on your login page)
      const emailInput = await page.$('input[type="email"], input[name="email"], input[type="text"]')
      const passwordInput = await page.$('input[type="password"]')
      const submitButton = await page.$('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")')
      
      if (emailInput && passwordInput && submitButton) {
        await emailInput.type('demo@healthforesight.com')
        await passwordInput.type('demo123')
        await submitButton.click()
        
        // Wait for navigation away from login page
        await page.waitForNavigation({ waitUntil: 'networkidle0', timeout: 10000 })
        console.log('✅ Logged in successfully')
      }
    }
  } catch (error) {
    console.warn('⚠️  Login may not be needed or failed:', error.message)
  }
}

async function captureTourScreenshots() {
  console.log('🚀 Starting automated screenshot capture...')
  console.log('')

  // Ensure screenshots directory exists
  if (!fs.existsSync(SCREENSHOTS_DIR)) {
    fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true })
    console.log(`📁 Created directory: ${SCREENSHOTS_DIR}`)
  }

  // Launch browser
  console.log('🌐 Launching browser...')
  const browser = await puppeteer.launch({
    headless: false, // Set to true for headless mode
    defaultViewport: { width: 1920, height: 1080 },
    args: ['--start-maximized'],
  })

  const page = await browser.newPage()
  
  // Set viewport
  await page.setViewport({ width: 1920, height: 1080 })

  let totalCaptured = 0
  let totalFailed = 0

  // Capture screenshots for each tour
  for (const [tourModule, targets] of Object.entries(TOUR_TARGETS)) {
    console.log('')
    console.log(`📸 Capturing screenshots for: ${tourModule}`)
    console.log('─'.repeat(50))

    const route = TOUR_ROUTES[tourModule]
    if (!route) {
      console.warn(`⚠️  No route defined for ${tourModule}, skipping`)
      continue
    }

    try {
      // Navigate to page
      const url = `${BASE_URL}${route}`
      console.log(`📍 Navigating to: ${url}`)
      await page.goto(url, { waitUntil: 'networkidle0', timeout: 30000 })

      // Login if needed
      await loginIfNeeded(page)

      // Wait for page to load
      await page.waitForTimeout(2000)

      // Capture each target
      for (const { target, name, description } of targets) {
        const filePath = path.join(SCREENSHOTS_DIR, name)
        
        console.log(`  📷 ${name} (${target})...`)
        
        const found = await waitForElement(page, target, 5000)
        if (found) {
          const success = await captureScreenshot(page, target, filePath, description)
          if (success) {
            totalCaptured++
          } else {
            totalFailed++
          }
        } else {
          console.log(`    ⚠️  Element not found, creating placeholder`)
          // Create a placeholder image
          createPlaceholderImage(filePath, name, description)
          totalFailed++
        }
      }
    } catch (error) {
      console.error(`❌ Error processing ${tourModule}:`, error.message)
      totalFailed += targets.length
    }
  }

  await browser.close()

  console.log('')
  console.log('═'.repeat(50))
  console.log('📊 Screenshot Capture Summary')
  console.log('═'.repeat(50))
  console.log(`✅ Successfully captured: ${totalCaptured}`)
  console.log(`❌ Failed/Missing: ${totalFailed}`)
  console.log(`📁 Screenshots saved to: ${SCREENSHOTS_DIR}`)
  console.log('')
  console.log('💡 Next steps:')
  console.log('   1. Review captured screenshots')
  console.log('   2. Replace any placeholders with actual screenshots')
  console.log('   3. Optimize images if needed (compress, resize)')
  console.log('')
}

function createPlaceholderImage(filePath, name, description) {
  // Create a simple placeholder using Node.js (basic implementation)
  // In production, you might want to use a library like sharp or canvas
  const placeholderText = `
    Screenshot Placeholder
    ${name}
    ${description}
    
    To capture this screenshot:
    1. Navigate to the page
    2. Find element: ${name.split('.')[0]}
    3. Take screenshot
    4. Save as: ${name}
  `
  
  // For now, just create an empty file or use a simple text file
  // In a real implementation, you'd generate an actual image
  fs.writeFileSync(filePath.replace('.png', '.txt'), placeholderText)
  console.log(`    📝 Created placeholder: ${filePath.replace('.png', '.txt')}`)
}

// Run if called directly
if (require.main === module) {
  captureTourScreenshots()
    .then(() => {
      console.log('✅ Screenshot capture complete!')
      process.exit(0)
    })
    .catch((error) => {
      console.error('❌ Fatal error:', error)
      process.exit(1)
    })
}

module.exports = { captureTourScreenshots, TOUR_TARGETS, TOUR_ROUTES }

