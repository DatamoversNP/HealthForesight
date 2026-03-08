import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'

export type TourModule = 
  | 'dashboard'
  | 'policies'
  | 'policy-builder'
  | 'policy-workspace'
  | 'ingestions'
  | 'analyses'
  | 'analysis-workspace'
  | 'whatif'
  | 'scorecards'
  | 'cohorts'
  | 'pipelines'
  | 'data-explorer'
  | 'decisions'
  | 'product-manual'

interface TourState {
  isRunning: boolean
  currentTour: TourModule | null
  completedTours: Set<TourModule>
  hasSeenFirstTimeTour: boolean
}

interface TourContextType {
  state: TourState
  startTour: (module: TourModule) => void
  stopTour: () => void
  completeTour: (module: TourModule) => void
  resetFirstTimeTour: () => void
  hasCompletedTour: (module: TourModule) => boolean
}

const TourContext = createContext<TourContextType | undefined>(undefined)

const STORAGE_KEY = 'uepi_tour_state'
const FIRST_TIME_KEY = 'uepi_first_time_tour'

export function TourProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<TourState>(() => {
    // Load from localStorage
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      const completed = stored ? new Set<TourModule>(JSON.parse(stored)) : new Set<TourModule>()
      const hasSeenFirstTime = localStorage.getItem(FIRST_TIME_KEY) === 'true'
      
      return {
        isRunning: false,
        currentTour: null,
        completedTours: completed,
        hasSeenFirstTimeTour: hasSeenFirstTime,
      }
    } catch {
      return {
        isRunning: false,
        currentTour: null,
        completedTours: new Set<TourModule>(),
        hasSeenFirstTimeTour: false,
      }
    }
  })

  const saveState = useCallback((newState: TourState) => {
    setState(newState)
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(newState.completedTours)))
      localStorage.setItem(FIRST_TIME_KEY, newState.hasSeenFirstTimeTour ? 'true' : 'false')
    } catch (error) {
      console.warn('Failed to save tour state:', error)
    }
  }, [])

  const startTour = useCallback((module: TourModule) => {
    saveState({
      ...state,
      isRunning: true,
      currentTour: module,
    })
  }, [state, saveState])

  const stopTour = useCallback(() => {
    saveState({
      ...state,
      isRunning: false,
      currentTour: null,
    })
  }, [state, saveState])

  const completeTour = useCallback((module: TourModule) => {
    const newCompleted = new Set(state.completedTours)
    newCompleted.add(module)
    
    saveState({
      ...state,
      isRunning: false,
      currentTour: null,
      completedTours: newCompleted,
      hasSeenFirstTimeTour: state.hasSeenFirstTimeTour || module === 'dashboard',
    })
  }, [state, saveState])

  const resetFirstTimeTour = useCallback(() => {
    saveState({
      ...state,
      hasSeenFirstTimeTour: false,
    })
  }, [state, saveState])

  const hasCompletedTour = useCallback((module: TourModule) => {
    return state.completedTours.has(module)
  }, [state.completedTours])

  return (
    <TourContext.Provider
      value={{
        state,
        startTour,
        stopTour,
        completeTour,
        resetFirstTimeTour,
        hasCompletedTour,
      }}
    >
      {children}
    </TourContext.Provider>
  )
}

export function useTour() {
  const context = useContext(TourContext)
  if (context === undefined) {
    throw new Error('useTour must be used within a TourProvider')
  }
  return context
}

