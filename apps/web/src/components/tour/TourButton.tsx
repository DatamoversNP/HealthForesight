import React from 'react'
import { IconButton, Tooltip, Badge } from '@mui/material'
import { HelpOutline as HelpIcon } from '@mui/icons-material'
import { useTour } from '../../contexts/TourContext'
import { TourModule } from '../../contexts/TourContext'

interface TourButtonProps {
  module: TourModule
  size?: 'small' | 'medium' | 'large'
  showBadge?: boolean
  tooltip?: string
}

export default function TourButton({ 
  module, 
  size = 'medium',
  showBadge = false,
  tooltip 
}: TourButtonProps) {
  const { startTour, hasCompletedTour } = useTour()
  const completed = hasCompletedTour(module)

  const handleClick = () => {
    startTour(module)
  }

  const defaultTooltip = tooltip || `Take a tour of this ${module.replace('-', ' ')}`

  const button = (
    <IconButton
      onClick={handleClick}
      size={size}
      color="primary"
      sx={{
        '&:hover': {
          backgroundColor: 'primary.light',
          color: 'primary.contrastText',
        },
      }}
    >
      <HelpIcon />
    </IconButton>
  )

  if (showBadge && !completed) {
    return (
      <Tooltip title={defaultTooltip}>
        <Badge 
          color="error" 
          variant="dot"
          sx={{
            '& .MuiBadge-badge': {
              animation: 'pulse 2s infinite',
              '@keyframes pulse': {
                '0%, 100%': { opacity: 1 },
                '50%': { opacity: 0.5 },
              },
            },
          }}
        >
          {button}
        </Badge>
      </Tooltip>
    )
  }

  return (
    <Tooltip title={defaultTooltip}>
      {button}
    </Tooltip>
  )
}

