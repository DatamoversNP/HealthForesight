import React, { useEffect, useState } from 'react'
import Joyride, { CallBackProps, STATUS, Step } from 'react-joyride'
import { useTour } from '../../contexts/TourContext'
import { allTours } from '../../config/tours-simplified'
import { useLocation, useNavigate } from 'react-router-dom'
import TourFeedback from './TourFeedback'

export default function TourManager() {
  const { state, stopTour, completeTour } = useTour()
  const location = useLocation()
  const navigate = useNavigate()
  const [run, setRun] = useState(false)
  const [steps, setSteps] = useState<Step[]>([])
  const [showFeedback, setShowFeedback] = useState(false)
  const [tourStarted, setTourStarted] = useState(false)
  const [stepIndex, setStepIndex] = useState(0)

  // Update tour when currentTour changes
  useEffect(() => {
    if (state.isRunning && state.currentTour) {
      const tourConfig = allTours[state.currentTour]
      if (tourConfig && tourConfig.steps && tourConfig.steps.length > 0) {
        // Process steps with proper placement and styling
        const processedSteps = tourConfig.steps.map((step, index) => {
          // Ensure proper placement - default to 'bottom' if not specified
          const placement = step.placement || 'bottom'
          
          return {
            ...step,
            target: step.target || '',
            placement: placement as 'top' | 'bottom' | 'left' | 'right' | 'center' | 'auto',
            disableBeacon: step.disableBeacon ?? (index !== 0),
            disableOverlayClose: false,
            disableScrolling: false,
          }
        })
        
        setSteps(processedSteps)
        setStepIndex(0)
        
        // Simple delay to ensure page is rendered
        const timer = setTimeout(() => {
          setRun(true)
        }, 500)
        
        return () => clearTimeout(timer)
      } else {
        console.warn(`Tour config not found or has no steps for module: ${state.currentTour}`)
        stopTour()
      }
    } else {
      setRun(false)
      setStepIndex(0)
      if (!state.isRunning && !showFeedback) {
        setTourStarted(false)
      }
    }
  }, [state.isRunning, state.currentTour, stopTour, showFeedback])

  const handleJoyrideCallback = (data: CallBackProps) => {
    const { status, type, index, action } = data

    // Update step index
    if (typeof index === 'number') {
      setStepIndex(index)
    }

    // Mark tour as started when first step is shown
    if (type === 'step:after' && index === 0) {
      setTourStarted(true)
    }

    // Handle errors (target not found)
    if (type === 'error:target_not_found') {
      console.warn(`Tour step target not found at index ${index}`)
      // Continue to next step if possible
      if (action === 'next' && index < steps.length - 1) {
        // Let it continue naturally
      }
    }

    if (status === STATUS.FINISHED || status === STATUS.SKIPPED) {
      if (state.currentTour) {
        // Make feedback completely optional - only show if user explicitly wants it
        // For now, skip feedback by default to avoid interrupting user flow
        // Users can provide feedback via the tours menu if they want
        stopTour()
        setTourStarted(false)
        if (state.currentTour) {
          completeTour(state.currentTour)
        }
      }
      setRun(false)
    }
  }

  const handleFeedbackClose = (skipFeedback: boolean = false) => {
    setShowFeedback(false)
    setTourStarted(false)
    if (state.currentTour) {
      if (!skipFeedback) {
        completeTour(state.currentTour)
      } else {
        // Still mark as completed even if feedback was skipped
        completeTour(state.currentTour)
      }
    }
  }

  const joyrideProps = {
    run,
    steps,
    stepIndex,
    continuous: true,
    showProgress: true,
    showSkipButton: true,
    hideCloseButton: false,
    callback: handleJoyrideCallback,
    disableOverlayClose: false,
    disableScrolling: false,
    scrollOffset: 20,
    scrollToFirstStep: true,
    spotlightClicks: false,
    floaterProps: {
      disableAnimation: false,
      styles: {
        arrow: {
          length: 8,
          spread: 16,
        },
      },
    },
    styles: {
      options: {
        primaryColor: '#1976d2',
        zIndex: 10000,
        arrowColor: '#ffffff',
        overlayColor: 'rgba(0, 0, 0, 0.5)',
        spotlightPadding: 10,
        textColor: '#333333',
        width: 400,
        beaconSize: 40,
      },
      tooltip: {
        borderRadius: 8,
        fontSize: 14,
        padding: '16px',
        boxShadow: '0 4px 16px rgba(0, 0, 0, 0.15)',
        maxWidth: '400px',
        minWidth: '320px',
      },
      tooltipContainer: {
        textAlign: 'left' as const,
        padding: 0,
      },
      tooltipTitle: {
        fontSize: 16,
        fontWeight: 600,
        marginBottom: 8,
        color: '#1a1a1a',
        lineHeight: 1.3,
      },
      tooltipContent: {
        padding: 0,
        fontSize: 14,
        lineHeight: 1.5,
        color: '#4a4a4a',
      },
      buttonNext: {
        backgroundColor: '#1976d2',
        fontSize: 14,
        fontWeight: 500,
        padding: '8px 20px',
        borderRadius: 4,
        textTransform: 'none',
        transition: 'background-color 0.2s',
      },
      buttonBack: {
        marginRight: 8,
        color: '#666',
        fontSize: 14,
        padding: '8px 16px',
        borderRadius: 4,
        textTransform: 'none',
      },
      buttonSkip: {
        color: '#999',
        fontSize: 13,
        padding: '8px 12px',
        textTransform: 'none',
      },
      buttonClose: {
        color: '#999',
        fontSize: 16,
        top: 8,
        right: 8,
      },
      spotlight: {
        borderRadius: 6,
      },
      overlay: {
        mixBlendMode: 'normal' as const,
      },
      beacon: {
        width: 24,
        height: 24,
      },
      beaconInner: {
        backgroundColor: '#1976d2',
        width: '100%',
        height: '100%',
      },
      beaconOuter: {
        backgroundColor: 'rgba(25, 118, 210, 0.3)',
        border: '2px solid #1976d2',
        width: '100%',
        height: '100%',
      },
    },
    locale: {
      back: 'Back',
      close: 'Close',
      last: 'Finish',
      next: 'Next',
      open: 'Open the dialog',
      skip: 'Skip',
    },
  }

  return (
    <>
      <Joyride {...joyrideProps} />
      {state.currentTour && (
        <TourFeedback
          module={state.currentTour}
          open={showFeedback}
          onClose={() => handleFeedbackClose(false)}
          onSkip={() => handleFeedbackClose(true)}
        />
      )}
    </>
  )
}
