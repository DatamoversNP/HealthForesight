import playwright from '../apps/web/node_modules/playwright/index.js'
const { chromium } = playwright
import { mkdir } from 'node:fs/promises'

const out = 'docs/production/releases/mock_client_r1_browser'
await mkdir(out, { recursive: true })
const browser = await chromium.launch({
  executablePath: '/Users/nileshl/Library/Caches/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-mac-arm64/chrome-headless-shell',
  headless: true,
})
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
await page.goto('http://127.0.0.1:3255/login', { waitUntil: 'domcontentloaded' })
await page.getByLabel('Email').fill('synthetic.local@example.com')
await page.getByLabel('Password').fill('synthetic-local-only')
await page.getByRole('button', { name: 'Sign in with email' }).click()
await page.waitForURL((url) => !url.pathname.endsWith('/login'), { timeout: 30000 })
await page.goto('http://127.0.0.1:3255/policies', { waitUntil: 'domcontentloaded' })
await page.getByText('96 of 287 policies have a configured mechanism result.').waitFor({ timeout: 30000 })
await page.getByRole('columnheader', { name: 'Execution' }).waitFor()
await page.screenshot({ path: `${out}/policies-execution.png`, fullPage: false })
await page.getByText('No candidate code', { exact: true }).first().waitFor({ timeout: 30000 })
await page.screenshot({ path: `${out}/policies-blocked.png`, fullPage: false })
await page.getByLabel('Search policies').fill('Assistant Surgeon')
await page.getByText('Missing parameter', { exact: true }).first().waitFor({ timeout: 15000 })
await page.screenshot({ path: `${out}/policies-payment-blocked.png`, fullPage: false })
await page.getByLabel('Search policies').fill('ACL')
await page.getByText('Review required', { exact: true }).first().waitFor({ timeout: 15000 })
await page.screenshot({ path: `${out}/policies-review.png`, fullPage: false })
await page.goto('http://127.0.0.1:3255/whatif', { waitUntil: 'domcontentloaded' })
await page.waitForTimeout(2000)
await page.screenshot({ path: `${out}/whatif.png`, fullPage: false })
await page.goto('http://127.0.0.1:3255/dashboard/executive', { waitUntil: 'domcontentloaded' })
await page.getByText('Payment-rule simulation and continuation comparisons are separate.').waitFor({ timeout: 30000 })
await page.screenshot({ path: `${out}/executive-separated.png`, fullPage: false })
await browser.close()
console.log('browser-ok')
