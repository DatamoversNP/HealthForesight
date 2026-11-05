/**
 * HealthForesight ConfidenceBadge Component
 * Displays confidence score with appropriate color coding.
 * Accepts numeric 0–1 scores, 0–100 percentages, or qualitative labels.
 * Never renders NaN%.
 */
import React from 'react'
import { Chip } from '@mui/material'

interface ConfidenceBadgeProps {
  /** Numeric 0–1 (preferred) or 0–100. Qualitative: high | medium | low. */
  score?: number | null
  /** @deprecated use score; kept for mistaken call sites that pass confidence= */
  confidence?: number | string | null
  showPercentage?: boolean
  size?: 'small' | 'medium'
  variant?: 'filled' | 'outlined'
}

function normalizeScore(raw: number | string | null | undefined): number | null {
  if (raw == null) return null
  if (typeof raw === 'string') {
    const key = raw.trim().toLowerCase()
    if (key === 'high') return 0.85
    if (key === 'medium' || key === 'moderate') return 0.55
    if (key === 'low') return 0.25
    const parsed = Number(raw)
    if (!Number.isFinite(parsed)) return null
    return parsed > 1 ? parsed / 100 : parsed
  }
  if (!Number.isFinite(raw)) return null
  return raw > 1 ? raw / 100 : raw
}

export default function ConfidenceBadge({
  score,
  confidence,
  showPercentage = true,
  size = 'small',
  variant = 'filled',
}: ConfidenceBadgeProps) {
  const normalized = normalizeScore(score ?? confidence)

  if (normalized == null) {
    return (
      <Chip
        label="Unavailable"
        color="default"
        size={size}
        variant="outlined"
        sx={{ fontWeight: 500, fontSize: size === 'small' ? '11px' : '12px' }}
        title="Confidence unavailable"
      />
    )
  }

  const getColor = (): 'success' | 'warning' | 'error' | 'default' => {
    if (normalized >= 0.7) return 'success'
    if (normalized >= 0.4) return 'warning'
    return 'error'
  }

  const getLabel = () => {
    if (!showPercentage) {
      if (normalized >= 0.7) return 'High'
      if (normalized >= 0.4) return 'Moderate'
      return 'Low'
    }
    return `${(normalized * 100).toFixed(0)}%`
  }

  const getDescription = () => {
    if (normalized >= 0.7) return 'High confidence'
    if (normalized >= 0.4) return 'Moderate confidence'
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
