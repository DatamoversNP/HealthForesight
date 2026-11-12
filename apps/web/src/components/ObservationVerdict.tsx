import { Box, Chip, Typography } from '@mui/material'

type ObservationVerdictFields = {
  verdict_status?: string | null
  verdict_reason?: string | null
  screen_verdict?: string | null
  screen_verdict_reason?: string | null
  historical_verdict_status?: string | null
  verdict_is_recomputed?: boolean | null
}

function screenLabel(status: string | null | undefined): string {
  if (status === 'BACKFIRE') return 'Backfire risk'
  if (status === 'AT_RISK') return 'At risk'
  if (status === 'ON_TRACK') return 'On track'
  if (status === 'INCONCLUSIVE') return 'Inconclusive'
  return 'Unavailable'
}

function chipColor(status: string | null | undefined): 'error' | 'warning' | 'success' | 'default' {
  if (status === 'BACKFIRE') return 'error'
  if (status === 'AT_RISK') return 'warning'
  if (status === 'ON_TRACK') return 'success'
  return 'default'
}

export default function ObservationVerdict({
  observation,
  compact = false,
}: {
  observation: ObservationVerdictFields
  compact?: boolean
}) {
  const stored = observation.historical_verdict_status || observation.verdict_status || 'not recorded'
  const screen = observation.screen_verdict
  const reason = observation.screen_verdict_reason
    || 'No qualifying endpoint contract or other required evidence.'

  return (
    <Box sx={{ mt: compact ? 1 : 0 }}>
      <Chip
        size="small"
        color={chipColor(screen)}
        label={`Current screen verdict: ${screenLabel(screen)}`}
        sx={{ fontWeight: 600 }}
      />
      <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
        Stored historical verdict: {stored}
      </Typography>
      {!compact && (
        <Typography variant="body2" sx={{ mt: 0.5 }}>
          Reason: {reason}
        </Typography>
      )}
    </Box>
  )
}
