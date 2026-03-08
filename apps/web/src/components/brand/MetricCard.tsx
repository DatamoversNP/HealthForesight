/**
 * HealthForesight MetricCard Component
 * Displays a single metric with value, label, and optional trend indicator
 */
import React from 'react'
import { Card, CardContent, Box, Typography, Chip } from '@mui/material'
import { TrendingUp, TrendingDown, Remove } from '@mui/icons-material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

interface MetricCardProps {
  label: string
  value: string | number
  unit?: string
  trend?: 'up' | 'down' | 'neutral' | null
  trendValue?: string
  subtitle?: string
  confidence?: number // 0-1, optional confidence score
  color?: 'success' | 'warning' | 'error' | 'info' | 'primary'
  onClick?: () => void
}

export default function MetricCard({
  label,
  value,
  unit,
  trend,
  trendValue,
  subtitle,
  confidence,
  color,
  onClick,
}: MetricCardProps) {
  const formatValue = () => {
    if (typeof value === 'number') {
      // Format numbers with proper separators
      return value.toLocaleString('en-US', {
        minimumFractionDigits: value % 1 === 0 ? 0 : 2,
        maximumFractionDigits: 2,
      })
    }
    return value
  }

  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <TrendingUp fontSize="small" sx={{ color: healthForesightColors.semantic.positive }} />
      case 'down':
        return <TrendingDown fontSize="small" sx={{ color: healthForesightColors.semantic.risk }} />
      case 'neutral':
        return <Remove fontSize="small" sx={{ color: healthForesightColors.neutral.mid }} />
      default:
        return null
    }
  }

  const getConfidenceColor = (score: number): 'success' | 'warning' | 'error' | 'default' => {
    if (score >= 0.7) return 'success'
    if (score >= 0.4) return 'warning'
    return 'error'
  }

  return (
    <Card
      onClick={onClick}
      sx={{
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 150ms cubic-bezier(0.4, 0, 0.2, 1)',
        '&:hover': onClick
          ? {
              borderColor: healthForesightColors.accent.main,
              boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
            }
          : {},
      }}
    >
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
          <Typography
            variant="body2"
            sx={{
              color: healthForesightColors.neutral.mid,
              fontWeight: 500,
              fontSize: '12px',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            {label}
          </Typography>
          {confidence !== undefined && (
            <Chip
              label={`${(confidence * 100).toFixed(0)}%`}
              size="small"
              color={getConfidenceColor(confidence)}
              sx={{ height: 20, fontSize: '10px' }}
            />
          )}
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1, mb: 0.5 }}>
          <Typography
            variant="h4"
            sx={{
              fontFamily: 'IBM Plex Sans, Inter, sans-serif',
              fontWeight: 600,
              fontSize: '2rem',
              lineHeight: 1.2,
              color: color
                ? color === 'success'
                  ? healthForesightColors.semantic.positive
                  : color === 'error'
                  ? healthForesightColors.semantic.risk
                  : color === 'warning'
                  ? healthForesightColors.semantic.warning
                  : healthForesightColors.neutral.dark
                : healthForesightColors.neutral.dark,
            }}
          >
            {formatValue()}
          </Typography>
          {unit && (
            <Typography variant="body2" sx={{ color: healthForesightColors.neutral.mid }}>
              {unit}
            </Typography>
          )}
        </Box>
        {(trend || subtitle) && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
            {trend && getTrendIcon()}
            {trendValue && (
              <Typography variant="caption" sx={{ color: healthForesightColors.neutral.mid }}>
                {trendValue}
              </Typography>
            )}
            {subtitle && (
              <Typography variant="caption" sx={{ color: healthForesightColors.neutral.mid }}>
                {subtitle}
              </Typography>
            )}
          </Box>
        )}
      </CardContent>
    </Card>
  )
}

