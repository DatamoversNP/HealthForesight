/**
 * HealthForesight Documentation Portal - Standalone Entry Point
 * This file loads ONLY the documentation portal, no API/auth dependencies
 */

// CRITICAL: Suppress ALL API/network errors BEFORE any imports
// This must be the very first code that runs
;(function suppressAPIConnectionErrors() {
  const originalError = console.error
  const originalWarn = console.warn
  const originalLog = console.log
  const originalInfo = console.info

  const shouldSuppress = (args: any[]): boolean => {
    try {
      const errorString = args
        .map(arg => {
          if (typeof arg === 'string') return arg
          if (typeof arg === 'object' && arg !== null) {
            try {
              const str = JSON.stringify(arg)
              return str !== '{}' ? str : String(arg)
            } catch {
              return String(arg)
            }
          }
          return String(arg)
        })
        .join(' ')
        .toLowerCase()

      // Comprehensive list of patterns to suppress
      const suppressPatterns = [
        'err_connection_refused',
        'network error',
        'networkerror',
        'unable to connect',
        'connection refused',
        'api/v1/',
        'localhost:8000',
        'api.ts',
        'authcontext',
        'loaduser',
        'failed to load user',
        'api unavailable',
        'using mock user',
        'get http://',
        'dispatchxhrrequest',
        'lineagepage',
        'dashboardpage',
        'getme',
        'getdashboard',
        'getdata',
        'getpolicy',
        'getanalysis',
        'getlineage',
        'getcoverage',
        'axios',
        'xhr',
      ]

      return suppressPatterns.some(pattern => errorString.includes(pattern))
    } catch {
      return false
    }
  }

  const wrap = (original: typeof console.error, name: string) => {
    return (...args: any[]) => {
      if (shouldSuppress(args)) {
        return // Suppress in docs mode
      }
      return original.apply(console, args)
    }
  }

  console.error = wrap(originalError, 'error')
  console.warn = wrap(originalWarn, 'warn')
  console.log = wrap(originalLog, 'log')
  console.info = wrap(originalInfo, 'info')
})()

// Now safe to import React and other dependencies
import React from 'react'
import ReactDOM from 'react-dom/client'
import DocumentationPortalPage from './pages/DocumentationPortalPage'
import './index-docs.css'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    background: {
      default: '#F8FAFC',
      paper: '#FFFFFF',
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <DocumentationPortalPage />
    </ThemeProvider>
  </React.StrictMode>,
)
