import React from 'react'
import { Box, Typography, BoxProps } from '@mui/material'
import TourButton from './TourButton'
import { TourModule } from '../../contexts/TourContext'

interface PageHeaderWithTourProps extends BoxProps {
  title: string
  subtitle?: string
  module: TourModule
  showTourButton?: boolean
  tourButtonPosition?: 'right' | 'inline'
}

export default function PageHeaderWithTour({
  title,
  subtitle,
  module,
  showTourButton = true,
  tourButtonPosition = 'right',
  sx,
  ...props
}: PageHeaderWithTourProps) {
  return (
    <Box
      {...props}
      sx={{
        mb: 4,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        ...sx,
      }}
      className="dashboard-header"
    >
      <Box sx={{ flex: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: subtitle ? 1 : 0 }}>
          <Typography
            variant="h4"
            component="h1"
            sx={{
              fontFamily: 'IBM Plex Sans, Inter, sans-serif',
              fontWeight: 600,
              color: 'text.primary',
            }}
          >
            {title}
          </Typography>
          {showTourButton && tourButtonPosition === 'inline' && (
            <TourButton module={module} size="small" />
          )}
        </Box>
        {subtitle && (
          <Typography
            variant="body1"
            sx={{
              color: 'text.secondary',
              lineHeight: 1.6,
            }}
          >
            {subtitle}
          </Typography>
        )}
      </Box>
      {showTourButton && tourButtonPosition === 'right' && (
        <Box sx={{ ml: 2 }}>
          <TourButton module={module} showBadge={true} />
        </Box>
      )}
    </Box>
  )
}

