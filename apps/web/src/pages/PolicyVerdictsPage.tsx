/**
 * Policy Verdicts – One screen that answers the sales question:
 * "Which policies are saving money, which are backfiring, and why?"
 * Verdict (Saving / At risk / Backfire risk) + impact + confidence + one-line reason.
 */
import { useEffect, useMemo, useState } from 'react'
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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
  Stack,
} from '@mui/material'
import ListFilterBar from '../components/common/ListFilterBar'
import { apiClient, type PolicyVerdictRow } from '../lib/api'
import { useNavigate } from 'react-router-dom'
import WarningAmberIcon from '@mui/icons-material/WarningAmber'
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline'
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline'
import HelpOutlineIcon from '@mui/icons-material/HelpOutline'
import RefreshIcon from '@mui/icons-material/Refresh'
import LightbulbIcon from '@mui/icons-material/Lightbulb'
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
  const [search, setSearch] = useState('')
  const [verdictFilter, setVerdictFilter] = useState('')
  const [evidenceRow, setEvidenceRow] = useState<PolicyVerdictRow | null>(null)
  const [evidencePack, setEvidencePack] = useState<any | null>(null)
  const [evidenceLoading, setEvidenceLoading] = useState(false)
  const [evidenceError, setEvidenceError] = useState<string | null>(null)
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

  const openEvidence = async (row: PolicyVerdictRow) => {
    setEvidenceRow(row)
    setEvidencePack(null)
    setEvidenceError(null)
    if (!row.observation_id) {
      setEvidenceError('No observation is linked to this verdict yet.')
      return
    }
    setEvidenceLoading(true)
    try {
      const pack = await apiClient.getObservationEvidencePack(row.observation_id)
      setEvidencePack(pack)
    } catch (e: any) {
      // Row-level verdict still shows; pack is enrichment
      setEvidenceError(e?.detail || e?.message || 'Could not load the full evidence pack.')
    } finally {
      setEvidenceLoading(false)
    }
  }

  const closeEvidence = () => {
    setEvidenceRow(null)
    setEvidencePack(null)
    setEvidenceError(null)
  }

  const backfireRows = data?.items?.filter((r) => r.has_backfire_risk) ?? []
  const allRows = data?.items ?? []
  const verdictOptions = useMemo(
    () => Array.from(new Set(allRows.map((r) => r.verdict).filter(Boolean))).sort(),
    [allRows]
  )
  const filteredRows = useMemo(() => {
    const q = search.trim().toLowerCase()
    return allRows.filter((r) => {
      if (verdictFilter && r.verdict !== verdictFilter) return false
      if (!q) return true
      const hay = `${r.policy_name || ''} ${r.verdict_label || ''} ${r.verdict_reason || ''} ${r.recommendation || ''}`.toLowerCase()
      return hay.includes(q)
    })
  }, [allRows, search, verdictFilter])

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
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Button
            variant="contained"
            color="secondary"
            startIcon={<LightbulbIcon />}
            onClick={() => navigate('/policy-rollout-recommendations')}
            size="medium"
          >
            Policy rollout ideas
          </Button>
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

      <Paper elevation={1} sx={{ overflow: 'hidden' }}>
        <ListFilterBar
          search={search}
          onSearchChange={setSearch}
          searchLabel="Search policies"
          searchPlaceholder="Name, verdict, reason…"
          shown={filteredRows.length}
          total={allRows.length}
          onClear={() => {
            setSearch('')
            setVerdictFilter('')
          }}
          clearDisabled={!search && !verdictFilter}
        >
          <FormControl size="small" sx={{ minWidth: 160, bgcolor: 'background.paper' }}>
            <InputLabel>Verdict</InputLabel>
            <Select
              label="Verdict"
              value={verdictFilter}
              onChange={(e) => setVerdictFilter(e.target.value)}
            >
              <MenuItem value="">All verdicts</MenuItem>
              {verdictOptions.map((v) => (
                <MenuItem key={v} value={v}>
                  {v.replace(/_/g, ' ')}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </ListFilterBar>

        {allRows.length === 0 ? (
          <Box sx={{ p: 3 }}>
            <Typography color="text.secondary">
              No policies yet, or no observations. Create a baseline and observations to see verdicts (run demo day or observation analysis).
            </Typography>
          </Box>
        ) : filteredRows.length === 0 ? (
          <Box sx={{ p: 3 }}>
            <Typography color="text.secondary">No policies match these filters.</Typography>
          </Box>
        ) : (
          <TableContainer sx={{ maxHeight: '70vh' }}>
            <Table size="small" stickyHeader>
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
                {filteredRows.map((row) => (
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
                      <Link
                        component="button"
                        variant="body2"
                        onClick={() => openEvidence(row)}
                      >
                        View evidence
                      </Link>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      <Dialog open={!!evidenceRow} onClose={closeEvidence} maxWidth="md" fullWidth>
        <DialogTitle>
          Why is this policy {evidenceRow?.verdict_label?.toLowerCase() || 'flagged'}?
        </DialogTitle>
        <DialogContent dividers>
          {evidenceRow && (
            <Stack spacing={2}>
              <Box>
                <Typography variant="h6" fontWeight={700}>
                  {evidenceRow.policy_name}
                </Typography>
                <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 1, alignItems: 'center' }}>
                  <VerdictChip row={evidenceRow} />
                  {evidenceRow.confidence_pct != null && (
                    <Chip size="small" label={`Confidence ${evidenceRow.confidence_pct.toFixed(0)}%`} />
                  )}
                  {evidenceRow.observation_period_end && (
                    <Chip
                      size="small"
                      variant="outlined"
                      label={`Through ${format(parseISO(evidenceRow.observation_period_end.split('T')[0]), 'MMM d, yyyy')}`}
                    />
                  )}
                </Box>
              </Box>

              <Alert severity={evidenceRow.has_backfire_risk ? 'error' : evidenceRow.verdict === 'AT_RISK' ? 'warning' : 'info'}>
                <Typography variant="subtitle2" fontWeight={700} gutterBottom>
                  Verdict reason
                </Typography>
                <Typography variant="body2">{evidenceRow.verdict_reason || '—'}</Typography>
              </Alert>

              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle2" fontWeight={700} gutterBottom>
                  What to do
                </Typography>
                <Typography variant="body2">{evidenceRow.recommendation || '—'}</Typography>
              </Paper>

              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr 1fr' }, gap: 2 }}>
                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="caption" color="text.secondary">
                    Cost impact (PMPM)
                  </Typography>
                  <Typography variant="h6">
                    {evidenceRow.savings_or_cost_impact_pmpm != null
                      ? `$${evidenceRow.savings_or_cost_impact_pmpm.toFixed(2)}`
                      : '—'}
                  </Typography>
                </Paper>
                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="caption" color="text.secondary">
                    Cost change
                  </Typography>
                  <Typography variant="h6">
                    {evidenceRow.cost_impact_pct != null ? `${evidenceRow.cost_impact_pct.toFixed(1)}%` : '—'}
                  </Typography>
                </Paper>
                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="caption" color="text.secondary">
                    Utilization change
                  </Typography>
                  <Typography variant="h6">
                    {evidenceRow.utilization_impact_pct != null
                      ? `${evidenceRow.utilization_impact_pct.toFixed(1)}%`
                      : '—'}
                  </Typography>
                </Paper>
              </Box>

              <Divider />

              <Typography variant="subtitle1" fontWeight={700}>
                Supporting evidence
              </Typography>
              {evidenceLoading && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CircularProgress size={20} />
                  <Typography variant="body2" color="text.secondary">
                    Loading observation evidence pack…
                  </Typography>
                </Box>
              )}
              {evidenceError && !evidenceLoading && (
                <Alert severity="warning">{evidenceError}</Alert>
              )}
              {evidencePack && !evidenceLoading && (
                <Stack spacing={1.5}>
                  {(evidencePack.behavioral_summary?.summary ||
                    (evidencePack.behavioral_summary?.risk_factors || []).length > 0) && (
                    <Paper variant="outlined" sx={{ p: 2 }}>
                      <Typography variant="subtitle2" fontWeight={700} gutterBottom>
                        Behavioral / risk factors
                      </Typography>
                      {evidencePack.behavioral_summary?.summary && (
                        <Typography variant="body2" sx={{ mb: 1 }}>
                          {evidencePack.behavioral_summary.summary}
                        </Typography>
                      )}
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
                        {(evidencePack.behavioral_summary?.risk_factors || []).map((f: string) => (
                          <Chip key={f} size="small" label={f} color="warning" variant="outlined" />
                        ))}
                      </Box>
                    </Paper>
                  )}
                  <Paper variant="outlined" sx={{ p: 2 }}>
                    <Typography variant="subtitle2" fontWeight={700} gutterBottom>
                      Observed vs baseline / predicted
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      Key measures from the linked observation window.
                    </Typography>
                    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 1 }}>
                      {Object.entries(
                        (evidencePack.observation_summary?.observed_measures ||
                          evidencePack.observation_summary?.metrics ||
                          {}) as Record<string, unknown>
                      )
                        .filter(([, v]) => typeof v === 'number')
                        .slice(0, 8)
                        .map(([k, v]) => (
                          <Typography key={k} variant="body2">
                            <strong>{k.replace(/_/g, ' ')}:</strong>{' '}
                            {Number(v).toLocaleString(undefined, { maximumFractionDigits: 2 })}
                          </Typography>
                        ))}
                    </Box>
                    {evidencePack.executive_summary?.one_line_reason && (
                      <Typography variant="body2" sx={{ mt: 1.5 }}>
                        <strong>Executive one-liner:</strong> {evidencePack.executive_summary.one_line_reason}
                      </Typography>
                    )}
                  </Paper>
                </Stack>
              )}
            </Stack>
          )}
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2, justifyContent: 'space-between' }}>
          <Button onClick={closeEvidence}>Close</Button>
          <Box sx={{ display: 'flex', gap: 1 }}>
            {evidenceRow?.policy_id && (
              <Button
                variant="outlined"
                onClick={() => {
                  const oid = evidenceRow.observation_id
                  const q = new URLSearchParams({ policy: evidenceRow.policy_id })
                  if (oid) q.set('observation', oid)
                  navigate(`/observation-analysis?${q.toString()}`)
                }}
              >
                Open full observation analysis
              </Button>
            )}
          </Box>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
