/**
 * Serves the SPA and proxies /api/* to the real API (same-origin in the browser → no CORS).
 * Required for Azure App Service when the UI is on healthforesight-web and API on healthforesight-api.
 *
 * Env: API_BACKEND_URL (default https://healthforesight-api.azurewebsites.net)
 *      PORT / WEBSITES_PORT (Azure sets this)
 */
import express from 'express'
import { createProxyMiddleware } from 'http-proxy-middleware'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const API_BACKEND =
  process.env.API_BACKEND_URL?.replace(/\/$/, '') ||
  'https://healthforesight-api.azurewebsites.net'
// Mounting at /api strips that prefix before forwarding; target must include /api so /api/v1/ping → …/api/v1/ping
const PROXY_TARGET = `${API_BACKEND.replace(/\/api\/?$/, '')}/api`

const app = express()

app.use(
  '/api',
  createProxyMiddleware({
    target: PROXY_TARGET,
    changeOrigin: true,
    secure: true,
    ws: true,
    proxyTimeout: 120_000,
    timeout: 120_000,
    onProxyReq: (proxyReq, req) => {
      if (req.headers.authorization) {
        proxyReq.setHeader('authorization', req.headers.authorization)
      }
    },
    logLevel: 'warn',
  }),
)

const dist = path.join(__dirname, 'dist')
const indexPath = path.join(dist, 'index.html')
app.use(express.static(dist, { index: false, setHeaders: (res, filePath) => {
  if (filePath.endsWith('index.html')) res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate')
}}))
app.get('*', (_req, res) => {
  res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate')
  res.sendFile(indexPath)
})

const port = Number(process.env.PORT || process.env.WEBSITES_PORT || 8080)
app.listen(port, '0.0.0.0', () => {
  console.log(`[web] http://0.0.0.0:${port} static + /api/* -> ${PROXY_TARGET}/*`)
})
