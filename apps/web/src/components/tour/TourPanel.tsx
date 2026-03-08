import React, { useState, useEffect, useRef } from 'react'
import {
  Drawer,
  Box,
  Typography,
  Button,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  IconButton,
  Divider,
  Paper,
} from '@mui/material'
import {
  Close as CloseIcon,
  NavigateNext as NextIcon,
  NavigateBefore as PrevIcon,
  CheckCircle as CheckIcon,
} from '@mui/icons-material'
import { useTour } from '../../contexts/TourContext'
import { allTours } from '../../config/tours-simplified'
import { useNavigate, useLocation } from 'react-router-dom'

export default function TourPanel() {
  const { state, stopTour, completeTour } = useTour()
  const navigate = useNavigate()
  const location = useLocation()
  const [currentStep, setCurrentStep] = useState(0)
  const [highlightedElement, setHighlightedElement] = useState<HTMLElement | null>(null)
  const [isNavigating, setIsNavigating] = useState(false)
  const highlightRef = useRef<HTMLDivElement | null>(null)

  const tourConfig = state.currentTour ? allTours[state.currentTour] : null
  const steps = tourConfig?.steps || []

  // Handle navigation and highlighting
  useEffect(() => {
    if (!state.isRunning || steps.length === 0) {
      // Remove highlight
      if (highlightedElement) {
        highlightedElement.style.outline = ''
        highlightedElement.style.outlineOffset = ''
        highlightedElement.style.transition = ''
        setHighlightedElement(null)
      }
      return
    }

    const step = steps[currentStep]
    if (!step || !step.target) return

    // Check if we need to navigate
    const stepRoute = (step as any).route
    const currentPath = location.pathname
    
    if (stepRoute && stepRoute !== currentPath && !isNavigating) {
      setIsNavigating(true)
      navigate(stepRoute)
      // Wait for navigation to complete before highlighting
      setTimeout(() => {
        setIsNavigating(false)
        // Try to highlight after navigation
        setTimeout(() => {
          const target = typeof step.target === 'string' 
            ? document.querySelector(step.target) as HTMLElement
            : null
          
          if (target) {
            target.style.outline = '3px solid #1976d2'
            target.style.outlineOffset = '4px'
            target.style.transition = 'outline 0.2s ease'
            target.scrollIntoView({ behavior: 'smooth', block: 'center' })
            setHighlightedElement(target)
          }
        }, 500)
      }, 300)
      return
    }

    // If already on correct page or no route specified, highlight immediately
    if (!stepRoute || stepRoute === currentPath || isNavigating) {
      // Wait a bit for page to render if we just navigated
      const delay = isNavigating ? 500 : 100
      setTimeout(() => {
        const target = typeof step.target === 'string' 
          ? document.querySelector(step.target) as HTMLElement
          : null

        // Remove previous highlight
        if (highlightedElement && highlightedElement !== target) {
          highlightedElement.style.outline = ''
          highlightedElement.style.outlineOffset = ''
          highlightedElement.style.transition = ''
        }

        // Add new highlight
        if (target) {
          target.style.outline = '3px solid #1976d2'
          target.style.outlineOffset = '4px'
          target.style.transition = 'outline 0.2s ease'
          target.scrollIntoView({ behavior: 'smooth', block: 'center' })
          setHighlightedElement(target)
        }
        setIsNavigating(false)
      }, delay)
    }

    return () => {
      if (highlightedElement) {
        highlightedElement.style.outline = ''
        highlightedElement.style.outlineOffset = ''
        highlightedElement.style.transition = ''
      }
    }
  }, [currentStep, state.isRunning, steps, highlightedElement, location.pathname, navigate, isNavigating])

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1)
    } else {
      handleFinish()
    }
  }

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleStepClick = (index: number) => {
    setCurrentStep(index)
    setIsNavigating(false)
  }

  const handleFinish = () => {
    if (highlightedElement) {
      highlightedElement.style.outline = ''
      highlightedElement.style.outlineOffset = ''
      highlightedElement.style.transition = ''
    }
    if (state.currentTour) {
      completeTour(state.currentTour)
    }
    stopTour()
    setCurrentStep(0)
  }

  const handleClose = () => {
    if (highlightedElement) {
      highlightedElement.style.outline = ''
      highlightedElement.style.outlineOffset = ''
      highlightedElement.style.transition = ''
    }
    stopTour()
    setCurrentStep(0)
  }

  if (!state.isRunning || !tourConfig) {
    return null
  }

  const currentStepData = steps[currentStep]
  const isFirstStep = currentStep === 0
  const isLastStep = currentStep === steps.length - 1

  return (
    <Drawer
      anchor="left"
      open={state.isRunning}
      variant="persistent"
      sx={{
        width: 420,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: 420,
          boxSizing: 'border-box',
          borderRight: '1px solid #e0e0e0',
          zIndex: (theme) => theme.zIndex.drawer + 1,
        },
      }}
    >
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        {/* Header */}
        <Box sx={{ p: 2, borderBottom: '1px solid #e0e0e0', bgcolor: '#f8f9fa' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="h6" sx={{ fontWeight: 600, fontSize: '18px' }}>
              {tourConfig.title}
            </Typography>
            <IconButton size="small" onClick={handleClose}>
              <CloseIcon />
            </IconButton>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ fontSize: '13px', lineHeight: 1.5 }}>
            {tourConfig.description}
          </Typography>
        </Box>

        {/* Current Step Content */}
        {currentStepData && (() => {
          // Extract content from step structure
          let stepTitle = 'Tour Step'
          let stepDescription = ''
          let businessValue = ''
          let tips = ''
          
          if (typeof currentStepData.content === 'string') {
            stepDescription = currentStepData.content
          } else if (currentStepData.content && typeof currentStepData.content === 'object') {
            // New structure with title, description, businessValue, tips
            stepTitle = currentStepData.content.title || stepTitle
            stepDescription = currentStepData.content.description || ''
            businessValue = currentStepData.content.businessValue || ''
            tips = currentStepData.content.tips || ''
          } else {
            // Legacy React element structure
            const contentProps = (currentStepData.content as any)?.props
            if (contentProps?.children) {
              const children = Array.isArray(contentProps.children) 
                ? contentProps.children 
                : [contentProps.children]
              
              if (children[0]?.props?.children) {
                stepTitle = children[0].props.children
              }
              
              if (children[1]?.props?.children) {
                stepDescription = children[1].props.children
              }
            }
          }
          
          return (
            <Box sx={{ p: 2, overflow: 'auto', flex: 1 }}>
              <Paper
                elevation={0}
                sx={{
                  p: 2.5,
                  bgcolor: '#ffffff',
                  borderRadius: 2,
                  border: '1px solid #e0e0e0',
                  mb: 2,
                }}
              >
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1.5, color: '#1976d2', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Step {currentStep + 1} of {steps.length}
                </Typography>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 1.5, color: '#1a1a1a', fontSize: '18px', lineHeight: 1.3 }}>
                  {stepTitle}
                </Typography>
                {stepDescription && (
                  <Typography variant="body2" sx={{ mb: 2, color: '#4a4a4a', lineHeight: 1.6, fontSize: '14px' }}>
                    {stepDescription}
                  </Typography>
                )}
                {businessValue && (
                  <Box sx={{ mb: 2, p: 1.5, bgcolor: '#f0f7ff', borderRadius: 1, borderLeft: '3px solid #1976d2' }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5, color: '#1976d2', fontSize: '13px' }}>
                      Business Value
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#555', fontSize: '13px', lineHeight: 1.5 }}>
                      {businessValue}
                    </Typography>
                  </Box>
                )}
                {tips && (
                  <Box sx={{ p: 1.5, bgcolor: '#fff9e6', borderRadius: 1, borderLeft: '3px solid #ff9800' }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5, color: '#f57c00', fontSize: '13px' }}>
                      💡 Pro Tip
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#555', fontSize: '13px', lineHeight: 1.5 }}>
                      {tips}
                    </Typography>
                  </Box>
                )}
              </Paper>
            </Box>
          )
        })()}

        {/* Steps List */}
        <Box sx={{ borderTop: '1px solid #e0e0e0', overflow: 'auto' }}>
          <Typography variant="subtitle2" sx={{ px: 2, py: 1.5, fontWeight: 600, color: 'text.secondary', fontSize: '12px', textTransform: 'uppercase' }}>
            Tour Steps
          </Typography>
          <List sx={{ px: 1, pb: 1 }}>
            {steps.map((step, index) => {
              const isActive = index === currentStep
              const isCompleted = index < currentStep
              
              // Extract step title
              let stepTitle = `Step ${index + 1}`
              if (typeof step.content === 'string') {
                stepTitle = step.content
              } else if (step.content && typeof step.content === 'object' && 'title' in step.content) {
                stepTitle = step.content.title || stepTitle
              } else {
                const contentProps = (step.content as any)?.props
                if (contentProps?.children) {
                  const children = Array.isArray(contentProps.children) 
                    ? contentProps.children 
                    : [contentProps.children]
                  if (children[0]?.props?.children) {
                    stepTitle = children[0].props.children
                  }
                }
              }

              return (
                <ListItem key={index} disablePadding>
                  <ListItemButton
                    selected={isActive}
                    onClick={() => handleStepClick(index)}
                    sx={{
                      borderRadius: 1,
                      mb: 0.5,
                      bgcolor: isActive ? '#e3f2fd' : 'transparent',
                      '&:hover': {
                        bgcolor: isActive ? '#e3f2fd' : '#f5f5f5',
                      },
                      '&.Mui-selected': {
                        bgcolor: '#e3f2fd',
                        '&:hover': {
                          bgcolor: '#e3f2fd',
                        },
                      },
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                      <Box
                        sx={{
                          width: 24,
                          height: 24,
                          borderRadius: '50%',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          mr: 1.5,
                          bgcolor: isCompleted
                            ? '#4caf50'
                            : isActive
                            ? '#1976d2'
                            : '#e0e0e0',
                          color: isCompleted || isActive ? 'white' : '#999',
                          fontSize: '12px',
                          fontWeight: 600,
                        }}
                      >
                        {isCompleted ? (
                          <CheckIcon sx={{ fontSize: 16 }} />
                        ) : (
                          index + 1
                        )}
                      </Box>
                      <ListItemText
                        primary={
                          <Typography
                            variant="body2"
                            sx={{
                              fontWeight: isActive ? 600 : 400,
                              color: isActive ? '#1976d2' : 'text.primary',
                            }}
                          >
                            {stepTitle}
                          </Typography>
                        }
                      />
                    </Box>
                  </ListItemButton>
                </ListItem>
              )
            })}
          </List>
        </Box>

        {/* Navigation Footer */}
        <Box sx={{ p: 2, borderTop: '1px solid #e0e0e0' }}>
          <Box sx={{ display: 'flex', gap: 1, justifyContent: 'space-between' }}>
            <Button
              variant="outlined"
              startIcon={<PrevIcon />}
              onClick={handlePrev}
              disabled={isFirstStep}
              sx={{ flex: 1 }}
            >
              Previous
            </Button>
            <Button
              variant="contained"
              endIcon={isLastStep ? <CheckIcon /> : <NextIcon />}
              onClick={handleNext}
              sx={{ flex: 1 }}
            >
              {isLastStep ? 'Finish' : 'Next'}
            </Button>
          </Box>
          <Button
            variant="text"
            onClick={handleClose}
            fullWidth
            sx={{ mt: 1, color: 'text.secondary' }}
          >
            Skip Tour
          </Button>
        </Box>
      </Box>
    </Drawer>
  )
}

