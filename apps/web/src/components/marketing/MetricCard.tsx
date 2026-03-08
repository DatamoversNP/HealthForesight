/**
 * Metric Card Component
 * Professional metric display with visual indicators
 */
import React from 'react'
import { Box, Typography, Card } from '@mui/material'
import { TrendingUp, TrendingDown } from '@mui/icons-material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

interface MetricCardProps {
  label: string
  value: string | number
  change?: number
  trend?: 'up' | 'down'
  icon?: React.ReactNode
  color?: string
}

export default function MetricCard({ label, value, change, trend, icon, color }: MetricCardProps) {
  const primaryColor = color || healthForesightColors.primary.main
  
  return (
    <Card
      sx={{
        p: 3,
        borderRadius: 3,
        backgroundColor: '#FFFFFF',
        border: `1px solid ${healthForesightColors.neutral.light}`,
        boxShadow: `0 4px 16px ${healthForesightColors.neutral.dark}08`,
        transition: 'all 0.3s ease',
        '&:hover': {
          boxShadow: `0 8px 24px ${primaryColor}20`,
          transform: 'translateY(-4px)',
        },
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'start', justifyContent: 'space-between', mb: 2 }}>
        <Typography
          variant="body2"
          sx={{
            color: healthForesightColors.neutral.mid,
            fontWeight: 500,
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            fontSize: '0.75rem',
          }}
        >
          {label}
        </Typography>
        {icon && (
          <Box sx={{ color: primaryColor, opacity: 0.6 }}>
            {icon}
          </Box>
        )}
      </Box>
      <Typography
        variant="h4"
        sx={{
          fontWeight: 700,
          color: healthForesightColors.neutral.dark,
          mb: change !== undefined ? 1 : 0,
        }}
      >
        {value}
      </Typography>
      {change !== undefined && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          {trend === 'up' ? (
            <TrendingUp sx={{ fontSize: 18, color: healthForesightColors.accent.main }} />
          ) : (
            <TrendingDown sx={{ fontSize: 18, color: '#EF4444' }} />
          )}
          <Typography
            variant="body2"
            sx={{
              color: trend === 'up' ? healthForesightColors.accent.main : '#EF4444',
              fontWeight: 600,
            }}
          >
            {Math.abs(change)}%
          </Typography>
        </Box>
      )}
    </Card>
  )
}
