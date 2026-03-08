import React, { useEffect, useRef } from 'react'
import { useLocation } from 'react-router-dom'
import { useTour } from '../../contexts/TourContext'

/** Auto-start disabled: tours are available via the Product Tours menu or the ? button on each page. */
const AUTO_START_TOUR = false

/**
 * Optional handler for auto-starting the dashboard tour on first visit.
 * When AUTO_START_TOUR is false (default), this component does nothing.
 * Tours can still be started manually via the Product Tours menu or TourButton.
 */
export default function FirstTimeTourHandler() {
  const location = useLocation()
  const { state, startTour } = useTour()
  const lastPathRef = useRef<string | null>(null)

  useEffect(() => {
    if (!AUTO_START_TOUR) return

    const isDashboardRoute =
      location.pathname === '/' ||
      location.pathname === '/dashboard' ||
      location.pathname.startsWith('/dashboard/')
    const pathChanged = lastPathRef.current !== location.pathname
    const isFirstLoad = lastPathRef.current === null

    if (isDashboardRoute && !state.isRunning && (pathChanged || isFirstLoad)) {
      const checkAndStartTour = (attempt = 1, maxAttempts = 5) => {
        const dashboardHeader = document.querySelector('.dashboard-header')
        if (dashboardHeader) {
          startTour('dashboard')
        } else if (attempt < maxAttempts) {
          const delay = Math.min(500 * Math.pow(2, attempt - 1), 2000)
          setTimeout(() => checkAndStartTour(attempt + 1, maxAttempts), delay)
        }
      }
      const timer = setTimeout(() => checkAndStartTour(), 2000)
      lastPathRef.current = location.pathname
      return () => clearTimeout(timer)
    }
    if (!isDashboardRoute) lastPathRef.current = location.pathname
  }, [location.pathname, state.isRunning, startTour])

  return null
}

