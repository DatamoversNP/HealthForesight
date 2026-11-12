import { chromium } from '../../apps/web/node_modules/playwright/index.mjs'
import { readFileSync, mkdirSync } from 'fs'

const plan = JSON.parse(readFileSync(process.argv[2], 'utf8'))
const outPath = process.argv[3]
const email = process.env.HF_QA_EMAIL
const password = process.env.HF_QA_PASSWORD
if (!email || !password) {
  console.error('missing QA credentials in the environment')
  process.exit(2)
}

const executable = process.env.HF_QA_CHROME || '/Users/nileshl/Library/Caches/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-mac-arm64/chrome-headless-shell'
mkdirSync(plan.screenshotDir, { recursive: true })
const browser = await chromium.launch({ executablePath: executable, headless: true })
const results = []

async function login(page, base) {
  const failures = []
  page.on('response', (response) => {
    const url = response.url()
    if (response.status() >= 500 && url.includes('/api/')) {
      failures.push(`${response.status()} ${url.split('?')[0].slice(-80)}`)
    }
  })
  page.on('console', (msg) => {
    if (msg.type() === 'error' && !msg.text().includes('401')) {
      failures.push(`console ${msg.text().slice(0, 180)}`)
    }
  })
  await page.goto(base + '/login', { waitUntil: 'domcontentloaded', timeout: 45000 })
  await page.getByLabel(/email/i).fill(email)
  await page.getByLabel(/password/i).fill(password)
  await page.getByRole('button', { name: /sign in|log in/i }).click()
  await page.waitForURL(/dashboard/, { timeout: 45000 })
  return failures
}

async function visit(page, base, item, failures) {
  const started = Date.now()
  const record = {
    id: item.id,
    url: base + item.path,
    ok: false,
    notes: [],
    failures: [],
    elapsed_ms: 0,
    screenshot: null,
  }
  try {
    await page.goto(base + item.path, { waitUntil: 'domcontentloaded', timeout: 45000 })
    if (item.waitText) {
      await page.getByText(item.waitText, { exact: false }).first().waitFor({ timeout: item.timeout || 20000 })
    } else {
      await page.waitForTimeout(1200)
    }
    const text = await page.locator('body').innerText()
    for (const expected of item.expect || []) {
      if (!text.includes(expected)) record.failures.push(`missing text: ${expected}`)
    }
    for (const forbidden of item.forbid || []) {
      if (text.includes(forbidden)) record.failures.push(`forbidden text: ${forbidden}`)
    }
    if (item.clickText) {
      await page.getByText(item.clickText, { exact: false }).first().click()
      await page.waitForTimeout(1500)
      const after = await page.locator('body').innerText()
      for (const expected of item.expectAfterClick || []) {
        if (!after.includes(expected)) record.failures.push(`after click missing: ${expected}`)
      }
      for (const forbidden of item.forbidAfterClick || []) {
        if (after.includes(forbidden)) record.failures.push(`after click forbidden: ${forbidden}`)
      }
    }
    record.ok = record.failures.length === 0
  } catch (error) {
    record.failures.push(String(error).slice(0, 300))
  }
  record.elapsed_ms = Date.now() - started
  record.failures.push(...failures.splice(0))
  if (!record.ok) record.ok = false
  if (record.failures.length) record.ok = false
  const shot = `${plan.screenshotDir}/${item.id}.png`
  await page.evaluate(() => {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT)
    const nodes = []
    while (walker.nextNode()) nodes.push(walker.currentNode)
    for (const node of nodes) {
      if (node.textContent && node.textContent.includes('@')) node.textContent = node.textContent.replace(/[^\s@]+@[^\s]+/g, '[account]')
    }
  }).catch(() => {})
  await page.screenshot({ path: shot, fullPage: false }).catch(() => {})
  record.screenshot = shot
  results.push(record)
  console.log(`${record.ok ? 'PASS' : 'FAIL'} ${item.id}`)
}

for (const target of plan.targets) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
  const failures = await login(page, target.base)
  for (const item of target.journeys) {
    await visit(page, target.base, item, failures)
  }
  await page.close()
}

await browser.close()
const { writeFileSync } = await import('fs')
writeFileSync(outPath, JSON.stringify({ results }, null, 2))
const failed = results.filter((row) => !row.ok).length
process.exit(failed ? 1 : 0)
