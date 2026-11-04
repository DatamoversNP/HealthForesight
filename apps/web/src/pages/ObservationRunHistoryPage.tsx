/**
 * Observation Run History – dedicated page listing every observation run
 * (one row per observation: run date, period, days, util, cost).
 * Can be opened from Observation Analysis or directly from nav.
 */
import { useState, useEffect } from 'react'
import {
  Box,
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
  Paper,
} from '@mui/material'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { AccessTime as TimeIcon, ArrowBack as BackIcon, Refresh as RefreshIcon } from '@mui/icons-material'
import { apiClient } from '../lib/api'
import { format } from 'date-fns'
import PolicyAutocomplete from '../components/common/PolicyAutocomplete'

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
        apiClient.getPolicies({ limit: 1000 }),
        apiClient.listObservations({
          include_trends: false,
          latest_only: !filterPolicyId,
          limit: filterPolicyId ? 200 : 100,
          summary: true,
          ...(filterPolicyId ? { policy_id: filterPolicyId } : {}),
        }),
      ])
      const mapped = Array.isArray(policiesData)
        ? policiesData.map((p: any) => ({ id: p.id, name: p.name || p.policy_name || 'Unknown' }))
        : []
      mapped.sort((a, b) => a.name.localeCompare(b.name))
      setPolicies(mapped)
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

  const policyName = (id: string) => policies.find((p) => p.id === id)?.name || id

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

      <Paper elevation={1} sx={{ mb: 2, overflow: 'hidden' }}>
        <Box
          sx={{
            px: 2,
            pt: 1.5,
            pb: 1.25,
            borderBottom: 1,
            borderColor: 'divider',
            bgcolor: 'action.hover',
            display: 'flex',
            flexWrap: 'wrap',
            gap: 1.5,
            alignItems: 'center',
          }}
        >
          <Box sx={{ minWidth: 280, flex: '1 1 280px', bgcolor: 'background.paper', borderRadius: 1 }}>
            <PolicyAutocomplete
              policies={policies}
              value={filterPolicyId}
              label="Filter by policy"
              onChange={setFilterPolicyId}
            />
          </Box>
          <Typography variant="caption" color="text.secondary" sx={{ ml: { sm: 'auto' } }}>
            Showing {sortedObservations.length} run{sortedObservations.length !== 1 ? 's' : ''}
            {filterPolicyId ? ' for selected policy' : ' (latest per policy)'}
          </Typography>
        </Box>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <TableContainer sx={{ maxHeight: '70vh' }}>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>Policy</TableCell>
                  <TableCell>Period start</TableCell>
                  <TableCell>Period end</TableCell>
                  <TableCell>Run date</TableCell>
                  <TableCell align="right">Util / 1k</TableCell>
                  <TableCell align="right">Cost PMPM</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {sortedObservations.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      <Typography color="text.secondary" sx={{ py: 3 }}>
                        No observation runs found
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  sortedObservations.map((obs) => (
                    <TableRow
                      key={obs.observation_id}
                      hover
                      sx={{ cursor: 'pointer' }}
                      onClick={() => handleRowClick(obs)}
                    >
                      <TableCell>{policyName(obs.policy_id)}</TableCell>
                      <TableCell>
                        {obs.observation_period_start
                          ? format(new Date(obs.observation_period_start), 'MMM d, yyyy')
                          : '—'}
                      </TableCell>
                      <TableCell>
                        {obs.observation_period_end
                          ? format(new Date(obs.observation_period_end), 'MMM d, yyyy')
                          : '—'}
                      </TableCell>
                      <TableCell>
                        {obs.computed_at ? format(new Date(obs.computed_at), 'MMM d, yyyy HH:mm') : '—'}
                      </TableCell>
                      <TableCell align="right">
                        {obs.metrics?.utilization_per_1k != null
                          ? Number(obs.metrics.utilization_per_1k).toFixed(1)
                          : '—'}
                      </TableCell>
                      <TableCell align="right">
                        {obs.metrics?.cost_pmpm != null || obs.metrics?.cost_per_member != null
                          ? `$${Number(obs.metrics.cost_pmpm ?? obs.metrics.cost_per_member).toFixed(2)}`
                          : '—'}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>
    </Box>
  )
}
