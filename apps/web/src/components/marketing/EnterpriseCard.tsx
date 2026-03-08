/**
 * Enterprise-Grade Card Component
 * Professional card with sophisticated shadows, gradients, and animations
 */
import React from 'react'
import { Card, CardContent, Box, SxProps, Theme } from '@mui/material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

interface EnterpriseCardProps {
  children: React.ReactNode
  gradient?: string
  hoverGradient?: string
  sx?: SxProps<Theme>
  variant?: 'default' | 'elevated' | 'outlined'
}

export default function EnterpriseCard({
  children,
  gradient,
  hoverGradient,
  sx,
  variant = 'elevated',
}: EnterpriseCardProps) {
  const baseGradient = gradient || `linear-gradient(135deg, #FFFFFF 0%, ${healthForesightColors.neutral.background} 100%)`
  const baseHoverGradient = hoverGradient || `linear-gradient(135deg, #FFFFFF 0%, ${healthForesightColors.primary.main}05 100%)`

  const variantStyles = {
    default: {
      border: `1px solid ${healthForesightColors.neutral.light}`,
      boxShadow: `0 2px 8px ${healthForesightColors.neutral.dark}08`,
    },
    elevated: {
      border: `1px solid ${healthForesightColors.neutral.light}`,
      boxShadow: `0 8px 32px ${healthForesightColors.neutral.dark}12, 0 2px 8px ${healthForesightColors.neutral.dark}08`,
    },
    outlined: {
      border: `2px solid ${healthForesightColors.neutral.light}`,
      boxShadow: 'none',
    },
  }

  return (
    <Card
      sx={{
        position: 'relative',
        background: baseGradient,
        overflow: 'hidden',
        transition: 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: baseHoverGradient,
          opacity: 0,
          transition: 'opacity 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
          pointerEvents: 'none',
        },
        '&::after': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '2px',
          background: `linear-gradient(90deg, ${healthForesightColors.primary.main}00 0%, ${healthForesightColors.primary.main} 50%, ${healthForesightColors.primary.main}00 100%)`,
          opacity: 0,
          transition: 'opacity 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
        },
        '&:hover': {
          transform: 'translateY(-8px)',
          ...variantStyles.elevated,
          borderColor: healthForesightColors.primary.main + '40',
          boxShadow: `0 16px 64px ${healthForesightColors.primary.main}20, 0 8px 24px ${healthForesightColors.neutral.dark}15`,
          '&::before': {
            opacity: 1,
          },
          '&::after': {
            opacity: 1,
          },
        },
        ...variantStyles[variant],
        ...sx,
      }}
    >
      <CardContent sx={{ p: 4, position: 'relative', zIndex: 1 }}>
        {children}
      </CardContent>
    </Card>
  )
}
