/**
 * Decorative Visual Pattern Component
 * Abstract patterns for backgrounds and sections
 */
import React from 'react'
import { Box } from '@mui/material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

interface VisualPatternProps {
  variant?: 'dots' | 'grid' | 'waves' | 'circles'
  opacity?: number
  color?: string
}

export default function VisualPattern({
  variant = 'dots',
  opacity = 0.1,
  color,
}: VisualPatternProps) {
  const patternColor = color || healthForesightColors.primary.main

  const renderPattern = () => {
    switch (variant) {
      case 'dots':
        return (
          <svg width="100%" height="100%" style={{ position: 'absolute', top: 0, left: 0 }}>
            <pattern
              id="dots"
              x="0"
              y="0"
              width="40"
              height="40"
              patternUnits="userSpaceOnUse"
            >
              <circle cx="20" cy="20" r="2" fill={patternColor} opacity={opacity} />
            </pattern>
            <rect width="100%" height="100%" fill="url(#dots)" />
          </svg>
        )
      case 'grid':
        return (
          <svg width="100%" height="100%" style={{ position: 'absolute', top: 0, left: 0 }}>
            <pattern
              id="grid"
              x="0"
              y="0"
              width="40"
              height="40"
              patternUnits="userSpaceOnUse"
            >
              <path
                d="M 40 0 L 0 0 0 40"
                fill="none"
                stroke={patternColor}
                strokeWidth="1"
                opacity={opacity}
              />
            </pattern>
            <rect width="100%" height="100%" fill="url(#grid)" />
          </svg>
        )
      case 'waves':
        return (
          <svg width="100%" height="100%" style={{ position: 'absolute', top: 0, left: 0 }}>
            <path
              d="M0,100 Q250,50 500,100 T1000,100"
              fill="none"
              stroke={patternColor}
              strokeWidth="2"
              opacity={opacity}
            />
            <path
              d="M0,150 Q250,200 500,150 T1000,150"
              fill="none"
              stroke={patternColor}
              strokeWidth="2"
              opacity={opacity}
            />
          </svg>
        )
      case 'circles':
        return (
          <svg width="100%" height="100%" style={{ position: 'absolute', top: 0, left: 0 }}>
            <circle cx="10%" cy="20%" r="30" fill={patternColor} opacity={opacity} />
            <circle cx="80%" cy="30%" r="40" fill={patternColor} opacity={opacity * 0.7} />
            <circle cx="50%" cy="70%" r="25" fill={patternColor} opacity={opacity * 0.8} />
            <circle cx="20%" cy="80%" r="35" fill={patternColor} opacity={opacity * 0.6} />
          </svg>
        )
      default:
        return null
    }
  }

  return (
    <Box
      sx={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        overflow: 'hidden',
        pointerEvents: 'none',
        zIndex: 0,
      }}
    >
      {renderPattern()}
    </Box>
  )
}
