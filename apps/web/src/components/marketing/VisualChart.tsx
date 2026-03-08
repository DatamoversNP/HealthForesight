/**
 * Professional Visual Chart Component
 * Reusable chart visualization for marketing pages
 */
import React from 'react'
import { Box, Typography } from '@mui/material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

interface VisualChartProps {
  title?: string
  data: Array<{ label: string; value: number; color?: string }>
  type?: 'bar' | 'line' | 'area'
  height?: number
}

export default function VisualChart({ title, data, type = 'bar', height = 200 }: VisualChartProps) {
  const maxValue = Math.max(...data.map(d => d.value))
  
  return (
    <Box
      sx={{
        width: '100%',
        p: 3,
        borderRadius: 3,
        backgroundColor: '#FFFFFF',
        border: `1px solid ${healthForesightColors.neutral.light}`,
        boxShadow: `0 4px 16px ${healthForesightColors.neutral.dark}08`,
      }}
    >
      {title && (
        <Typography variant="h6" sx={{ mb: 3, fontWeight: 600, color: healthForesightColors.neutral.dark }}>
          {title}
        </Typography>
      )}
      <Box sx={{ position: 'relative', height, display: 'flex', alignItems: 'flex-end', gap: 2 }}>
        {data.map((item, index) => {
          const heightPercent = (item.value / maxValue) * 100
          const color = item.color || healthForesightColors.primary.main
          
          return (
            <Box key={index} sx={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              {type === 'bar' && (
                <Box
                  sx={{
                    width: '100%',
                    height: `${heightPercent}%`,
                    background: `linear-gradient(180deg, ${color} 0%, ${color}DD 100%)`,
                    borderRadius: '4px 4px 0 0',
                    minHeight: '20px',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      opacity: 0.8,
                      transform: 'scaleY(1.05)',
                    },
                  }}
                />
              )}
              <Typography
                variant="caption"
                sx={{
                  mt: 1,
                  fontSize: '11px',
                  color: healthForesightColors.neutral.mid,
                  fontWeight: 500,
                  textAlign: 'center',
                }}
              >
                {item.label}
              </Typography>
            </Box>
          )
        })}
      </Box>
    </Box>
  )
}
