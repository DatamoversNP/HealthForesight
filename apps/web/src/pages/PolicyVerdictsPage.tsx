/**
 * Policy Verdicts – One screen that answers the sales question:
 * "Which policies are saving money, which are backfiring, and why?"
 * Verdict (Saving / At risk / Backfire risk) + impact + confidence + one-line reason.
 */
import { useEffect, useState } from 'react'
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Chip,
  Link,
  Alert,
  CircularProgress,
  Button,
} from '@mui/material'
import { apiClient, type PolicyVerdictRow } from '../lib/api'
import { useNavigate } from 'react-router-dom'
import WarningAmberIcon from '@mui/icons-material/WarningAmber'
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline'
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline'
import HelpOutlineIcon from '@mui/icons-material/HelpOutline'
import RefreshIcon from '@mui/icons-material/Refresh'
import { format, parseISO } from 'date-fns'

function VerdictChip({ row }: { row: PolicyVerdictRow }) {
  const isBackfire = row.verdict === 'BACKFIRE'
  const isAtRisk = row.verdict === 'AT_RISK'
  const isOnTrack = row.verdict === 'ON_TRACK'
  const isUnknown = row.verdict === 'UNKNOWN' || row.verdict === 'INCONCLUSIVE'

  const label = row.verdict_label
  const color = isBackfire ? 'error' : isAtRisk ? 'warning' : isOnTrack ? 'success' : 'default'
  const icon = isBackfire ? <WarningAmberIcon fontSize="small" /> : isOnTrack ? <CheckCircleOutlineIcon fontSize="small" /> : isAtRisk ? <ErrorOutlineIcon fontSize="small" /> : <HelpOutlineIcon fontSize="small" />

  return (
    <Chip
      size="small"
      label={label}
      color={color}
      icon={icon}
      sx={{ fontWeight: isBackfire ? 700 : 600 }}
    />
  )
}

export default function PolicyVerdictsPage() {
  const [data, setData] = useState<{ items: PolicyVerdictRow[]; count: number } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  const loadVerdicts = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await apiClient.getPolicyVerdicts()
      setData(res)
    } catch (e: any) {
      setError(e?.message || 'Failed to load policy verdicts')
      setData(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadVerdicts()
  }, [])

  const backfireRows = data?.items?.filter((r) => r.has_backfire_risk) ?? []

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="40vh">
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error">{error}</Alert>
      </Box>
    )
  }

  const rows = data?.items ?? []

  return (
    <Box sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 2, mb: 2 }}>
        <Box>
          <Typography variant="h5" sx={{ mb: 0.5 }}>
            Which policies deliver? Which backfire?
          </Typography>
          <Typography variant="body2" color="text.secondary">
            One view: policy name, verdict, savings or cost impact, confidence, and recommendation. Period = effective date through run date.
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={loading ? <CircularProgress size={18} /> : <RefreshIcon />}
          onClick={loadVerdicts}
          disabled={loading}
          size="medium"
        >
          {loading ? 'Loading...' : 'Refresh'}
        </Button>
      </Box>

      {backfireRows.length > 0 && (
        <Alert
          severity="error"
          icon={<WarningAmberIcon />}
          sx={{ mb: 2 }}
        >
          <strong>Backfire risk:</strong> {backfireRows.length} policy(ies) show early-warning or backfire signals. Review verdict reason and recommendation below.
        </Alert>
      )}

      <TableContainer component={Paper} elevation={1}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell><strong>Policy</strong></TableCell>
              <TableCell><strong>Effective</strong></TableCell>
              <TableCell><strong>Through</strong></TableCell>
              <TableCell><strong>Verdict</strong></TableCell>
              <TableCell align="right"><strong>Cost impact (PMPM)</strong></TableCell>
              <TableCell align="right"><strong>Cost %</strong></TableCell>
              <TableCell align="right"><strong>Confidence</strong></TableCell>
              <TableCell><strong>Reason</strong></TableCell>
              <TableCell><strong>What to do</strong></TableCell>
              <TableCell><strong></strong></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row) => (
              <TableRow
                key={row.policy_id}
                sx={{
                  backgroundColor: row.has_backfire_risk ? 'error.light' : undefined,
                  '&:hover': { backgroundColor: row.has_backfire_risk ? 'error.light' : 'action.hover' },
                }}
              >
                <TableCell>
                  <Box>
                    <Typography variant="body2" fontWeight={600}>{row.policy_name}</Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  {row.policy_effective_date
                    ? format(parseISO(row.policy_effective_date.split('T')[0]), 'MMM d, yyyy')
                    : '—'}
                </TableCell>
                <TableCell>
                  {row.observation_period_end
                    ? format(parseISO(row.observation_period_end.split('T')[0]), 'MMM d, yyyy')
                    : '—'}
                </TableCell>
                <TableCell><VerdictChip row={row} /></TableCell>
                <TableCell align="right">
                  {row.savings_or_cost_impact_pmpm != null
                    ? `$${row.savings_or_cost_impact_pmpm.toFixed(2)}`
                    : '—'}
                </TableCell>
                <TableCell align="right">
                  {row.cost_impact_pct != null ? `${row.cost_impact_pct.toFixed(1)}%` : '—'}
                </TableCell>
                <TableCell align="right">
                  {row.confidence_pct != null ? `${row.confidence_pct.toFixed(0)}%` : '—'}
                </TableCell>
                <TableCell sx={{ maxWidth: 280 }}>{row.verdict_reason || '—'}</TableCell>
                <TableCell sx={{ maxWidth: 220 }}>{row.recommendation || '—'}</TableCell>
                <TableCell>
                  {row.observation_id && (
                    <Link
                      component="button"
                      variant="body2"
                      onClick={() => navigate(`/observation-analysis?observation=${row.observation_id}`)}
                    >
                      View evidence
                    </Link>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {rows.length === 0 && (
        <Typography color="text.secondary" sx={{ mt: 2 }}>
          No policies yet, or no observations. Create a baseline and observations to see verdicts (run demo day or observation analysis).
        </Typography>
      )}
    </Box>
  )
}
