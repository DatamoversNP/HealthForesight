/**
 * Confidence Interval Display Component
 */
import { Box, Typography, Tooltip } from '@mui/material'
import { Info as InfoIcon } from '@mui/icons-material'

interface ConfidenceIntervalProps {
  value: number
  lower: number
  upper: number
  unit?: string
  label?: string
  showBar?: boolean
}

export default function ConfidenceInterval({
  value,
  lower,
  upper,
  unit = '',
  label,
  showBar = true,
}: ConfidenceIntervalProps) {
  const range = upper - lower
  const center = (lower + upper) / 2
  const valuePercent = ((value - lower) / range) * 100
  const lowerPercent = 0
  const upperPercent = 100

  return (
    <Box>
      {label && (
        <Typography variant="body2" color="text.secondary" gutterBottom>
          {label}
        </Typography>
      )}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <Typography variant="h6" component="span">
          {value.toFixed(2)}
          {unit && <Typography component="span" variant="body2" color="text.secondary"> {unit}</Typography>}
        </Typography>
        <Tooltip title={`95% CI: [${lower.toFixed(2)}, ${upper.toFixed(2)}] ${unit}`}>
          <InfoIcon fontSize="small" color="action" />
        </Tooltip>
      </Box>
      {showBar && (
        <Box sx={{ position: 'relative', height: 24, bgcolor: 'grey.200', borderRadius: 1, overflow: 'hidden' }}>
          {/* Confidence interval bar */}
          <Box
            sx={{
              position: 'absolute',
              left: `${lowerPercent}%`,
              width: `${upperPercent - lowerPercent}%`,
              height: '100%',
              bgcolor: 'primary.light',
              opacity: 0.3,
            }}
          />
          {/* Point estimate */}
          <Box
            sx={{
              position: 'absolute',
              left: `${valuePercent}%`,
              width: 2,
              height: '100%',
              bgcolor: 'primary.main',
            }}
          />
          {/* Labels */}
          <Box sx={{ position: 'absolute', left: 4, top: 2 }}>
            <Typography variant="caption" color="text.secondary">
              {lower.toFixed(2)}
            </Typography>
          </Box>
          <Box sx={{ position: 'absolute', right: 4, top: 2 }}>
            <Typography variant="caption" color="text.secondary">
              {upper.toFixed(2)}
            </Typography>
          </Box>
        </Box>
      )}
      <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
        95% Confidence Interval: [{lower.toFixed(2)}, {upper.toFixed(2)}] {unit}
      </Typography>
    </Box>
  )
}

