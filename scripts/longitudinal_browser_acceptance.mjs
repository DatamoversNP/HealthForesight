import playwright from '../apps/web/node_modules/playwright/index.js'
const { chromium } = playwright
import { mkdir } from 'node:fs/promises'

const out = 'docs/production/releases/longitudinal_500k_browser'
await mkdir(out, { recursive: true })
const browser = await chromium.launch({
  executablePath: '/Users/nileshl/Library/Caches/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-mac-arm64/chrome-headless-shell',
  headless: true,
})
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
const notes = []
async function shot(name) {
  await page.screenshot({ path: `${out}/${name}.png`, fullPage: false })
  notes.push({ name, url: page.url(), title: await page.title() })
}
await page.goto('http://127.0.0.1:3255/login', { waitUntil: 'domcontentloaded' })
await page.getByLabel('Email').fill('synthetic.local@example.com')
await page.getByLabel('Password').fill('synthetic-local-only')
await page.getByRole('button', { name: 'Sign in with email' }).click()
await page.waitForURL('**/', { timeout: 30000 })
await page.getByText('Metrics from database').waitFor({ timeout: 30000 }).catch(() => {})
await page.waitForTimeout(1500)
await shot('dashboard')
await page.goto('http://127.0.0.1:3255/dashboard/executive', { waitUntil: 'domcontentloaded' })
await page.getByText('Observed post-period allowed difference').waitFor({ timeout: 30000 })
await shot('executive')
await page.goto('http://127.0.0.1:3255/policies', { waitUntil: 'domcontentloaded' })
await page.waitForTimeout(2000)
await shot('policies')
await page.goto('http://127.0.0.1:3255/predicted-impacts', { waitUntil: 'domcontentloaded' })
await page.waitForTimeout(2000)
await shot('predicted-impacts')
await page.goto('http://127.0.0.1:3255/observation-analysis', { waitUntil: 'domcontentloaded' })
await page.waitForTimeout(2000)
await shot('observations')
await page.goto('http://127.0.0.1:3255/policy-verdicts', { waitUntil: 'domcontentloaded' })
await page.waitForTimeout(2000)
await shot('verdicts')
await page.goto('http://127.0.0.1:3255/policies/workspace/d0eeb370-df14-4478-8755-dad6c3a35a47', { waitUntil: 'domcontentloaded' })
await page.waitForTimeout(2500)
await shot('mppr-workspace')
await page.goto('http://127.0.0.1:3255/audit-log', { waitUntil: 'domcontentloaded' })
await page.waitForTimeout(2000)
await shot('audit')
const phone = await browser.newPage({ viewport: { width: 390, height: 844 } })
await phone.goto('http://127.0.0.1:3255/login', { waitUntil: 'domcontentloaded' })
await phone.getByLabel('Email').fill('synthetic.local@example.com')
await phone.getByLabel('Password').fill('synthetic-local-only')
await phone.getByRole('button', { name: 'Sign in with email' }).click()
await phone.waitForTimeout(2000)
await phone.goto('http://127.0.0.1:3255/dashboard/executive', { waitUntil: 'domcontentloaded' })
await phone.getByText('Observed post-period allowed difference').waitFor({ timeout: 30000 })
await phone.screenshot({ path: `${out}/executive-mobile.png` })
await browser.close()
console.log(JSON.stringify(notes, null, 2))
