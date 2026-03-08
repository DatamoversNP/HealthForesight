/**
 * Automated Screenshot Capture for Product Tours using Playwright
 * More reliable than Puppeteer for screenshot capture
 * 
 * Usage: 
 *   npm run capture-screenshots
 *   or
 *   node scripts/capture-tour-screenshots-playwright.js
 * 
 * Requirements:
 *   npm install playwright
 *   npx playwright install chromium
 */

const { chromium } = require('playwright')
const fs = require('fs')
const path = require('path')

const SCREENSHOTS_DIR = path.join(__dirname, '../public/screenshots/tours')
const BASE_URL = 'http://localhost:3050'

// Tour targets and their corresponding screenshot names
const TOUR_TARGETS = {
  dashboard: [
    { target: '.dashboard-header', name: 'dashboard-overview.png', route: '/', wait: 2000 },
    { target: '.key-metrics-row', name: 'dashboard-metrics.png', route: '/', wait: 2000 },
    { target: '.decision-recommendations', name: 'dashboard-decisions.png', route: '/', wait: 2000 },
    { target: '.cost-trend-chart', name: 'dashboard-cost-trend.png', route: '/', wait: 2000 },
    { target: '.risk-register', name: 'dashboard-risk-register.png', route: '/', wait: 2000 },
    { target: '.top-policies-chart', name: 'dashboard-policy-performance.png', route: '/', wait: 2000 },
  ],
  policies: [
    { target: '.policy-catalog-header', name: 'policy-catalog-overview.png', route: '/policies', wait: 2000 },
    { target: '.policy-search-filters', name: 'policy-search-filters.png', route: '/policies', wait: 2000 },
    { target: '.policy-list', name: 'policy-list.png', route: '/policies', wait: 2000 },
    { target: '.create-policy-button', name: 'policy-create-options.png', route: '/policies', wait: 2000 },
  ],
  'policy-builder': [
    { target: '.policy-builder-header', name: 'policy-builder-header.png', route: '/policies/builder', wait: 2000 },
    { target: '.builder-steps', name: 'policy-builder-steps.png', route: '/policies/builder', wait: 2000 },
    { target: '.scope-selector', name: 'policy-builder-scope.png', route: '/policies/builder', wait: 2000, step: 1 },
    { target: '.levers-config', name: 'policy-builder-levers.png', route: '/policies/builder', wait: 2000, step: 2 },
  ],
  'policy-workspace': [
    { target: '.workspace-tabs', name: 'workspace-tabs.png', route: '/policies/workspace/10000000-0000-0000-0000-000000000001', wait: 2000 },
    { target: '.assumptions-manager', name: 'workspace-assumptions.png', route: '/policies/workspace/10000000-0000-0000-0000-000000000001', wait: 2000, tab: 'Assumptions' },
    { target: '.guardrails-manager', name: 'workspace-guardrails.png', route: '/policies/workspace/10000000-0000-0000-0000-000000000001', wait: 2000, tab: 'Guardrails' },
    { target: '.versions-list', name: 'workspace-versions.png', route: '/policies/workspace/10000000-0000-0000-0000-000000000001', wait: 2000, tab: 'Versions' },
  ],
  'analysis-workspace': [
    { target: '.analysis-header', name: 'analysis-overview.png', route: '/analyses', wait: 2000 },
    { target: '.analysis-tabs', name: 'analysis-tabs.png', route: '/analyses', wait: 2000 },
    { target: '.impact-results', name: 'analysis-results.png', route: '/analyses', wait: 2000 },
    { target: '.trust-panel', name: 'analysis-trust-panel.png', route: '/analyses', wait: 2000 },
  ],
  whatif: [
    { target: '.whatif-header', name: 'whatif-overview.png', route: '/whatif', wait: 2000 },
    { target: '.scenario-builder', name: 'whatif-scenario-builder.png', route: '/whatif', wait: 2000 },
    { target: '.scenario-comparison', name: 'whatif-comparison.png', route: '/whatif', wait: 2000 },
  ],
  ingestions: [
    { target: '.ingestion-header', name: 'ingestion-dashboard.png', route: '/ingestions', wait: 2000 },
    { target: '.upload-section', name: 'ingestion-upload.png', route: '/ingestions', wait: 2000 },
    { target: '.ingestion-list', name: 'ingestion-history.png', route: '/ingestions', wait: 2000 },
  ],
}

async function loginIfNeeded(page) {
  try {
    const currentUrl = page.url()
    if (currentUrl.includes('/login')) {
      console.log('  🔐 Attempting login...')
      
      // Wait for login form
      await page.waitForSelector('input[type="email"], input[name="email"], input[type="text"], input[placeholder*="email" i]', { timeout: 5000 })
      
      // Try to find and fill login form
      const emailSelectors = [
        'input[type="email"]',
        'input[name="email"]',
        'input[type="text"]',
        'input[placeholder*="email" i]',
      ]
      
      let emailInput = null
      for (const selector of emailSelectors) {
        emailInput = await page.$(selector)
        if (emailInput) break
      }
      
      const passwordInput = await page.$('input[type="password"]')
      const submitButton = await page.$('button[type="submit"], button:has-text("Login"), button:has-text("Sign In"), button:has-text("Log In")')
      
      if (emailInput && passwordInput && submitButton) {
        await emailInput.fill('demo@healthforesight.com')
        await passwordInput.fill('demo123')
        await submitButton.click()
        
        // Wait for navigation
        await page.waitForURL('**/dashboard**', { timeout: 10000 }).catch(() => {
          // If URL doesn't change, wait a bit anyway
          return page.waitForTimeout(2000)
        })
        console.log('  ✅ Logged in')
      }
    }
  } catch (error) {
    // Login may not be needed or may fail - continue anyway
    console.log('  ℹ️  Login not required or skipped')
  }
}

async function captureScreenshot(page, { target, name, route, wait = 2000, step, tab }) {
  try {
    // Navigate if needed
    const currentUrl = page.url()
    const targetUrl = `${BASE_URL}${route}`
    
    if (!currentUrl.includes(route.split('?')[0])) {
      console.log(`    📍 Navigating to: ${route}`)
      await page.goto(targetUrl, { waitUntil: 'networkidle', timeout: 30000 })
      await loginIfNeeded(page)
    }

    // Handle step navigation for policy builder
    if (step !== undefined) {
      console.log(`    🔄 Navigating to step ${step + 1}`)
      // Click on step in stepper (adjust selector based on your stepper implementation)
      const stepButtons = await page.$$('.MuiStep-root, [role="button"]')
      if (stepButtons[step]) {
        await stepButtons[step].click()
        await page.waitForTimeout(1000)
      }
    }

    // Handle tab navigation for workspace
    if (tab) {
      console.log(`    🔄 Clicking tab: ${tab}`)
      const tabButton = await page.locator(`text=${tab}, [role="tab"]:has-text("${tab}")`).first()
      if (await tabButton.count() > 0) {
        await tabButton.click()
        await page.waitForTimeout(1000)
      }
    }

    // Wait for element
    console.log(`    🔍 Waiting for: ${target}`)
    try {
      await page.waitForSelector(target, { state: 'visible', timeout: 10000 })
    } catch (error) {
      console.log(`    ⚠️  Element not found: ${target}`)
      return false
    }

    // Wait additional time for animations
    await page.waitForTimeout(wait)

    // Scroll element into view
    const element = page.locator(target).first()
    await element.scrollIntoViewIfNeeded()
    await page.waitForTimeout(500)

    // Get element bounding box
    const boundingBox = await element.boundingBox()
    if (!boundingBox) {
      console.log(`    ⚠️  Could not get bounding box`)
      return false
    }

    // Capture screenshot with padding
    const padding = 20
    const filePath = path.join(SCREENSHOTS_DIR, name)
    
    await page.screenshot({
      path: filePath,
      clip: {
        x: Math.max(0, boundingBox.x - padding),
        y: Math.max(0, boundingBox.y - padding),
        width: Math.min(boundingBox.width + (padding * 2), 1920),
        height: Math.min(boundingBox.height + (padding * 2), 1080),
      },
    })

    console.log(`    ✅ Captured: ${name}`)
    return true
  } catch (error) {
    console.log(`    ❌ Error: ${error.message}`)
    return false
  }
}

async function captureAllScreenshots() {
  console.log('🚀 Starting automated screenshot capture...')
  console.log('')

  // Ensure screenshots directory exists
  if (!fs.existsSync(SCREENSHOTS_DIR)) {
    fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true })
    console.log(`📁 Created directory: ${SCREENSHOTS_DIR}`)
  }

  // Launch browser
  console.log('🌐 Launching browser...')
  const browser = await chromium.launch({
    headless: false, // Set to true for headless mode
  })

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
  })

  const page = await context.newPage()

  let totalCaptured = 0
  let totalFailed = 0

  // Capture screenshots for each tour
  for (const [tourModule, targets] of Object.entries(TOUR_TARGETS)) {
    console.log('')
    console.log(`📸 Tour: ${tourModule}`)
    console.log('─'.repeat(60))

    for (const targetConfig of targets) {
      const success = await captureScreenshot(page, targetConfig)
      if (success) {
        totalCaptured++
      } else {
        totalFailed++
      }
    }
  }

  await browser.close()

  console.log('')
  console.log('═'.repeat(60))
  console.log('📊 Screenshot Capture Summary')
  console.log('═'.repeat(60))
  console.log(`✅ Successfully captured: ${totalCaptured}`)
  console.log(`❌ Failed/Missing: ${totalFailed}`)
  console.log(`📁 Screenshots saved to: ${SCREENSHOTS_DIR}`)
  console.log('')
  console.log('💡 Next steps:')
  console.log('   1. Review captured screenshots')
  console.log('   2. Optimize images if needed')
  console.log('   3. Verify all screenshots are correct')
  console.log('')
}

// Run if called directly
if (require.main === module) {
  captureAllScreenshots()
    .then(() => {
      console.log('✅ Screenshot capture complete!')
      process.exit(0)
    })
    .catch((error) => {
      console.error('❌ Fatal error:', error)
      process.exit(1)
    })
}

module.exports = { captureAllScreenshots, TOUR_TARGETS }

