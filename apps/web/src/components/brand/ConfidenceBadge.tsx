/**
 * HealthForesight ConfidenceBadge Component
 * Displays confidence score with appropriate color coding
 */
import React from 'react'
import { Chip } from '@mui/material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

interface ConfidenceBadgeProps {
  score: number // 0-1
  showPercentage?: boolean
  size?: 'small' | 'medium'
  variant?: 'filled' | 'outlined'
}

export default function ConfidenceBadge({
  score,
  showPercentage = true,
  size = 'small',
  variant = 'filled',
}: ConfidenceBadgeProps) {
  const getColor = (): 'success' | 'warning' | 'error' | 'default' => {
    if (score >= 0.7) return 'success'
    if (score >= 0.4) return 'warning'
    return 'error'
  }

  const getLabel = () => {
    if (!showPercentage) {
      if (score >= 0.7) return 'High'
      if (score >= 0.4) return 'Moderate'
      return 'Low'
    }
    return `${(score * 100).toFixed(0)}%`
  }

  const getDescription = () => {
    if (score >= 0.7) return 'High confidence'
    if (score >= 0.4) return 'Moderate confidence'
    return 'Low confidence - interpret with caution'
  }

  return (
    <Chip
      label={getLabel()}
      color={getColor()}
      size={size}
      variant={variant}
      sx={{
        fontWeight: 500,
        fontSize: size === 'small' ? '11px' : '12px',
        '& .MuiChip-label': {
          px: size === 'small' ? 1 : 1.5,
        },
      }}
      title={getDescription()}
    />
  )
}

