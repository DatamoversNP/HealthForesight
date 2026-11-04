import { defineConfig, mergeConfig } from 'vite'
import base from './vite.config'

// Local Data Voyager UI (:7868).
// Most API traffic → Azure App Service (stable).
// Recommendations → local :7867 (fast dedup + cache; same Azure DB).
// IMPORTANT: more-specific proxy keys must be listed before `/api`, and we
// replace `server.proxy` entirely so mergeConfig does not leave base `/api`
// ahead of the recommendations route.
const demo = defineConfig({
  server: {
    port: 7868,
    strictPort: true,
  },
})

const merged = mergeConfig(base, demo)
merged.server = merged.server || {}
merged.server.proxy = {
  // Local fast paths (same Azure DB) — must be listed before the catch-all `/api`
  '/api/v1/recommendations': {
    target: 'http://127.0.0.1:7867',
    changeOrigin: true,
  },
  '/api/v1/policies/predicted-impacts': {
    target: 'http://127.0.0.1:7867',
    changeOrigin: true,
  },
  // Local API has Tier-6 PolicyType enum; Azure build still drops those policies on response validation
  '/api/v1/policies': {
    target: 'http://127.0.0.1:7867',
    changeOrigin: true,
  },
  // Dec 4 enterprise intelligence (causal / cold-start / applicability) — local only for now
  '/api/v1/enterprise': {
    target: 'http://127.0.0.1:7867',
    changeOrigin: true,
  },
  // Objectives Health authoritative snapshot + stability contract (not yet on Azure)
  '/api/v1/dashboard/objectives-health': {
    target: 'http://127.0.0.1:7867',
    changeOrigin: true,
  },
  '/api': {
    target: 'https://healthforesight-api.azurewebsites.net',
    changeOrigin: true,
    secure: true,
  },
}

export default merged
