/**
 * Process Visualization Component
 * Professional step-by-step process visualization
 */
import React from 'react'
import { Box, Typography } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

interface Step {
  number: number
  title: string
  description: string
  icon?: React.ReactNode
}

interface ProcessVisualizationProps {
  steps: Step[]
  orientation?: 'horizontal' | 'vertical'
}

export default function ProcessVisualization({ steps, orientation = 'horizontal' }: ProcessVisualizationProps) {
  if (orientation === 'vertical') {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {steps.map((step, index) => (
          <Box key={index} sx={{ display: 'flex', gap: 3, alignItems: 'start' }}>
            <Box
              sx={{
                width: 64,
                height: 64,
                borderRadius: '50%',
                backgroundColor: healthForesightColors.primary.main,
                color: '#FFFFFF',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '24px',
                fontWeight: 700,
                flexShrink: 0,
                boxShadow: `0 4px 16px ${healthForesightColors.primary.main}30`,
              }}
            >
              {step.number}
            </Box>
            <Box sx={{ flex: 1 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 1, color: healthForesightColors.neutral.dark }}>
                {step.title}
              </Typography>
              <Typography variant="body1" sx={{ color: healthForesightColors.neutral.mid, lineHeight: 1.7 }}>
                {step.description}
              </Typography>
            </Box>
          </Box>
        ))}
      </Box>
    )
  }

  return (
    <Box sx={{ position: 'relative', py: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', position: 'relative' }}>
        {/* Connection Line */}
        <Box
          sx={{
            position: 'absolute',
            top: 32,
            left: 0,
            right: 0,
            height: 3,
            background: `linear-gradient(90deg, ${healthForesightColors.primary.main} 0%, ${healthForesightColors.accent.main} 100%)`,
            zIndex: 0,
          }}
        />
        
        {steps.map((step, index) => (
          <Box key={index} sx={{ position: 'relative', zIndex: 1, flex: 1, textAlign: 'center', px: 2 }}>
            <Box
              sx={{
                width: 64,
                height: 64,
                borderRadius: '50%',
                backgroundColor: '#FFFFFF',
                border: `4px solid ${healthForesightColors.primary.main}`,
                color: healthForesightColors.primary.main,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '24px',
                fontWeight: 700,
                mx: 'auto',
                mb: 2,
                boxShadow: `0 4px 16px ${healthForesightColors.neutral.dark}15`,
              }}
            >
              {step.number}
            </Box>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 1, fontSize: '1rem', color: healthForesightColors.neutral.dark }}>
              {step.title}
            </Typography>
            <Typography variant="body2" sx={{ color: healthForesightColors.neutral.mid, lineHeight: 1.6 }}>
              {step.description}
            </Typography>
          </Box>
        ))}
      </Box>
    </Box>
  )
}
