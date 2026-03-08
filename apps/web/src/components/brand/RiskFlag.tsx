/**
 * HealthForesight RiskFlag Component
 * Displays risk indicators with appropriate semantic colors (never pure red/green dominance)
 */
import React from 'react'
import { Chip, Box, Typography } from '@mui/material'
import { Warning, Error, CheckCircle } from '@mui/icons-material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

interface RiskFlagProps {
  level: 'low' | 'moderate' | 'high' | 'critical'
  label?: string
  description?: string
  showIcon?: boolean
}

export default function RiskFlag({ level, label, description, showIcon = true }: RiskFlagProps) {
  const getColor = () => {
    switch (level) {
      case 'low':
        return healthForesightColors.semantic.positive
      case 'moderate':
        return healthForesightColors.semantic.warning
      case 'high':
        return healthForesightColors.semantic.risk
      case 'critical':
        return healthForesightColors.semantic.risk
      default:
        return healthForesightColors.neutral.mid
    }
  }

  const getIcon = () => {
    if (!showIcon) return null
    switch (level) {
      case 'low':
        return <CheckCircle fontSize="small" />
      case 'moderate':
      case 'high':
        return <Warning fontSize="small" />
      case 'critical':
        return <Error fontSize="small" />
      default:
        return null
    }
  }

  const getLabel = () => {
    if (label) return label
    return level.charAt(0).toUpperCase() + level.slice(1) + ' Risk'
  }

  const icon = getIcon()
  
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <Chip
        {...(icon && { icon })}
        label={getLabel()}
        size="small"
        sx={{
          backgroundColor: getColor(),
          color: '#FFFFFF',
          fontWeight: 500,
          fontSize: '11px',
          '& .MuiChip-icon': {
            color: '#FFFFFF',
          },
        }}
      />
      {description && (
        <Typography variant="caption" sx={{ color: healthForesightColors.neutral.mid }}>
          {description}
        </Typography>
      )}
    </Box>
  )
}

