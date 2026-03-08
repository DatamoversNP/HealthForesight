/**
 * Section Divider Component
 * Smooth visual transition between sections
 */
import { Box } from '@mui/material'
import { healthForesightColors } from '../theme/healthForesightTheme'

interface SectionDividerProps {
  variant?: 'wave' | 'slope' | 'curve'
  color?: string
  height?: number
}

export default function SectionDivider({
  variant = 'wave',
  color,
  height = 100,
}: SectionDividerProps) {
  const dividerColor = color || healthForesightColors.neutral.background

  const renderDivider = () => {
    switch (variant) {
      case 'wave':
        return (
          <svg
            width="100%"
            height={height}
            viewBox="0 0 1440 100"
            preserveAspectRatio="none"
            style={{ display: 'block' }}
          >
            <path
              d="M0,50 Q360,0 720,50 T1440,50 L1440,100 L0,100 Z"
              fill={dividerColor}
            />
          </svg>
        )
      case 'slope':
        return (
          <svg
            width="100%"
            height={height}
            viewBox="0 0 1440 100"
            preserveAspectRatio="none"
            style={{ display: 'block' }}
          >
            <path
              d="M0,0 L1440,100 L1440,100 L0,100 Z"
              fill={dividerColor}
            />
          </svg>
        )
      case 'curve':
        return (
          <svg
            width="100%"
            height={height}
            viewBox="0 0 1440 100"
            preserveAspectRatio="none"
            style={{ display: 'block' }}
          >
            <path
              d="M0,100 Q360,0 720,50 T1440,50 L1440,100 Z"
              fill={dividerColor}
            />
          </svg>
        )
      default:
        return null
    }
  }

  return (
    <Box
      sx={{
        width: '100%',
        height: height,
        overflow: 'hidden',
        lineHeight: 0,
      }}
    >
      {renderDivider()}
    </Box>
  )
}
