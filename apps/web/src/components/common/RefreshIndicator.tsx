import React from 'react'
import {
  Chip,
  Tooltip,
  IconButton,
  CircularProgress,
  Box,
  Typography,
} from '@mui/material'
import {
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
} from '@mui/icons-material'

export type RefreshReason =
  | 'NEW_DATA_INGESTED'
  | 'BASELINE_REFRESHED'
  | 'POLICY_UPDATED'
  | 'MODEL_UPDATED'
  | 'OBSERVATION_ADDED'
  | 'MANUAL_REFRESH'
  | 'DATA_PERIOD_CHANGED'
  | 'BASELINE_VERSION_CHANGED'
  | 'POLICY_VERSION_CHANGED'
  | 'ELASTICITY_MODEL_VERSION_CHANGED'
  | string // Allow custom reasons

interface RefreshIndicatorProps {
  needsRefresh: boolean
  refreshReason?: RefreshReason | null
  lastRefreshTimestamp?: string | null
  onRefresh?: () => void
  isRefreshing?: boolean
  variant?: 'chip' | 'icon' | 'full'
  showReason?: boolean // Whether to show the reason explicitly
}

const REFRESH_REASON_LABELS: Record<string, string> = {
  NEW_DATA_INGESTED: 'New data ingested',
  BASELINE_REFRESHED: 'Baseline refreshed',
  POLICY_UPDATED: 'Policy updated',
  MODEL_UPDATED: 'Elasticity model updated',
  OBSERVATION_ADDED: 'New observation added',
  MANUAL_REFRESH: 'Manually refreshed',
  DATA_PERIOD_CHANGED: 'Data period changed',
  BASELINE_VERSION_CHANGED: 'Baseline version changed',
  POLICY_VERSION_CHANGED: 'Policy version changed',
  ELASTICITY_MODEL_VERSION_CHANGED: 'Elasticity model version changed',
}

export const RefreshIndicator: React.FC<RefreshIndicatorProps> = ({
  needsRefresh,
  refreshReason,
  lastRefreshTimestamp,
  onRefresh,
  isRefreshing = false,
  variant = 'chip',
  showReason = true,
}) => {
  const formatTimestamp = (timestamp: string | null | undefined) => {
    if (!timestamp) return 'Never'
    try {
      const date = new Date(timestamp)
      const now = new Date()
      const diffMs = now.getTime() - date.getTime()
      const diffMins = Math.floor(diffMs / 60000)
      const diffHours = Math.floor(diffMs / 3600000)
      const diffDays = Math.floor(diffMs / 86400000)

      if (diffMins < 1) return 'Just now'
      if (diffMins < 60) return `${diffMins}m ago`
      if (diffHours < 24) return `${diffHours}h ago`
      if (diffDays < 7) return `${diffDays}d ago`
      return date.toLocaleDateString()
    } catch {
      return timestamp
    }
  }

  const getRefreshReasonLabel = (reason: RefreshReason | null | undefined): string => {
    if (!reason) return 'Data has changed'
    return REFRESH_REASON_LABELS[reason] || reason.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, (l) => l.toUpperCase())
  }

  if (variant === 'icon') {
    return (
      <Tooltip
        title={
          needsRefresh
            ? `Needs refresh: ${getRefreshReasonLabel(refreshReason)}`
            : showReason && refreshReason
            ? `Last refreshed: ${formatTimestamp(lastRefreshTimestamp)} (${getRefreshReasonLabel(refreshReason)})`
            : `Last refreshed: ${formatTimestamp(lastRefreshTimestamp)}`
        }
      >
        <IconButton
          size="small"
          onClick={onRefresh}
          disabled={isRefreshing}
          color={needsRefresh ? 'warning' : 'default'}
        >
          {isRefreshing ? (
            <CircularProgress size={20} />
          ) : needsRefresh ? (
            <WarningIcon fontSize="small" />
          ) : (
            <CheckCircleIcon fontSize="small" color="success" />
          )}
        </IconButton>
      </Tooltip>
    )
  }

  if (variant === 'chip') {
    return (
      <Tooltip
        title={
          needsRefresh
            ? `Needs refresh: ${getRefreshReasonLabel(refreshReason)}`
            : showReason && refreshReason
            ? `Last refreshed: ${formatTimestamp(lastRefreshTimestamp)} (${getRefreshReasonLabel(refreshReason)})`
            : `Last refreshed: ${formatTimestamp(lastRefreshTimestamp)}`
        }
      >
        <Chip
          icon={
            isRefreshing ? (
              <CircularProgress size={16} />
            ) : needsRefresh ? (
              <WarningIcon fontSize="small" />
            ) : (
              <CheckCircleIcon fontSize="small" />
            )
          }
          label={
            needsRefresh
              ? `Refresh Needed${showReason && refreshReason ? `: ${getRefreshReasonLabel(refreshReason)}` : ''}`
              : `Updated ${formatTimestamp(lastRefreshTimestamp)}${showReason && refreshReason ? ` (${getRefreshReasonLabel(refreshReason)})` : ''}`
          }
          color={needsRefresh ? 'warning' : 'default'}
          variant={needsRefresh ? 'filled' : 'outlined'}
          size="small"
          onClick={onRefresh}
          disabled={isRefreshing}
        />
      </Tooltip>
    )
  }

  // Full variant
  return (
    <Box display="flex" alignItems="center" gap={1}>
      {isRefreshing ? (
        <CircularProgress size={20} />
      ) : needsRefresh ? (
        <WarningIcon color="warning" fontSize="small" />
      ) : (
        <CheckCircleIcon color="success" fontSize="small" />
      )}
      <Typography variant="body2" color="text.secondary">
        {needsRefresh
          ? `Refresh needed: ${getRefreshReasonLabel(refreshReason)}`
          : `Last updated: ${formatTimestamp(lastRefreshTimestamp)}${showReason && refreshReason ? ` (${getRefreshReasonLabel(refreshReason)})` : ''}`}
      </Typography>
      {onRefresh && (
        <IconButton
          size="small"
          onClick={onRefresh}
          disabled={isRefreshing}
          title="Refresh"
        >
          <RefreshIcon fontSize="small" />
        </IconButton>
      )}
    </Box>
  )
}
