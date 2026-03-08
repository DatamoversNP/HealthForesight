/**
 * Observation Run History – dedicated page listing every observation run
 * (one row per observation: run date, period, days, util, cost).
 * Can be opened from Observation Analysis or directly from nav.
 */
import { useState, useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
} from '@mui/material'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { AccessTime as TimeIcon, ArrowBack as BackIcon, Refresh as RefreshIcon } from '@mui/icons-material'
import { apiClient } from '../lib/api'
import { format } from 'date-fns'

interface ObservationRow {
  observation_id: string
  policy_id: string
  observation_period_start?: string
  observation_period_end?: string
  computed_at: string
  metrics?: {
    utilization_per_1k?: number
    cost_per_member?: number
    cost_pmpm?: number
  }
}

interface PolicyOption {
  id: string
  name: string
}

export default function ObservationRunHistoryPage() {
  const [observations, setObservations] = useState<ObservationRow[]>([])
  const [policies, setPolicies] = useState<PolicyOption[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filterPolicyId, setFilterPolicyId] = useState<string>('')
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const policyIdFromUrl = searchParams.get('policy_id')

  useEffect(() => {
    if (policyIdFromUrl) {
      setFilterPolicyId(policyIdFromUrl)
    }
  }, [policyIdFromUrl])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [policiesData, observationsData] = await Promise.all([
        apiClient.getPolicies(),
        apiClient.listObservations({
          include_trends: false,
          ...(filterPolicyId ? { policy_id: filterPolicyId } : {}),
        }),
      ])
      setPolicies(
        Array.isArray(policiesData)
          ? policiesData.map((p: any) => ({ id: p.id, name: p.name || p.policy_name || 'Unknown' }))
          : []
      )
      setObservations(Array.isArray(observationsData) ? observationsData : [])
    } catch (err: any) {
      setError(err.message || 'Failed to load run history')
      setObservations([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [filterPolicyId])

  const sortedObservations = [...observations].sort(
    (a, b) =>
      new Date(a.observation_period_end || a.computed_at).getTime() -
      new Date(b.observation_period_end || b.computed_at).getTime()
  )

  const handleRowClick = (obs: ObservationRow) => {
    navigate(`/observation-analysis?observation=${obs.observation_id}`)
  }

  return (
    <Box sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2, flexWrap: 'wrap' }}>
        <Button
          startIcon={<BackIcon />}
          onClick={() => navigate('/observation-analysis')}
          size="small"
          variant="outlined"
        >
          Back to Observation Analysis
        </Button>
        <Typography variant="h5" fontWeight={600} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <TimeIcon /> Observation Run History
        </Typography>
        <Button startIcon={<RefreshIcon />} onClick={loadData} disabled={loading} size="small">
          Refresh
        </Button>
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Each row is one run: period from policy effective date through run date (cumulative). Click a row to open that
        observation on the Observation Analysis page.
      </Typography>

      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Card component={Paper} elevation={1} sx={{ mb: 2 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2, flexWrap: 'wrap' }}>
            <FormControl size="small" sx={{ minWidth: 220 }}>
              <InputLabel>Filter by policy</InputLabel>
              <Select
                value={filterPolicyId}
                label="Filter by policy"
                onChange={(e) => setFilterPolicyId(e.target.value)}
              >
                <MenuItem value="">All policies</MenuItem>
                {policies.map((p) => (
                  <MenuItem key={p.id} value={p.id}>
                    {p.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : sortedObservations.length === 0 ? (
            <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
              No observations found. Run the daily job or create observations from Observation Analysis.
            </Typography>
          ) : (
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: 'action.hover' }}>
                    <TableCell sx={{ fontWeight: 600 }}>Policy</TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>Run date</TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>Period (effective → through)</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 600 }}>Days</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 600 }}>Util per 1K</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 600 }}>Cost PMPM</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {sortedObservations.map((obs) => {
                    const start = obs.observation_period_start ? new Date(obs.observation_period_start) : null
                    const end = obs.observation_period_end ? new Date(obs.observation_period_end) : null
                    const days =
                      start && end
                        ? Math.round((end.getTime() - start.getTime()) / (24 * 60 * 60 * 1000))
                        : null
                    const policyName = policies.find((p) => p.id === obs.policy_id)?.name || 'Unknown'
                    return (
                      <TableRow
                        key={obs.observation_id}
                        hover
                        onClick={() => handleRowClick(obs)}
                        sx={{ cursor: 'pointer' }}
                      >
                        <TableCell>{policyName}</TableCell>
                        <TableCell>{end ? format(end, 'MMM d, yyyy') : '—'}</TableCell>
                        <TableCell>
                          {start && end ? `${format(start, 'MMM d')} → ${format(end, 'MMM d, yyyy')}` : '—'}
                        </TableCell>
                        <TableCell align="right">{days != null ? days : '—'}</TableCell>
                        <TableCell align="right">{(obs.metrics?.utilization_per_1k ?? 0).toFixed(1)}</TableCell>
                        <TableCell align="right">
                          ${(obs.metrics?.cost_pmpm ?? obs.metrics?.cost_per_member ?? 0).toFixed(2)}
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>
    </Box>
  )
}
