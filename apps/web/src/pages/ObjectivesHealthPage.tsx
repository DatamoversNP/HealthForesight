/**
 * Objectives Health – Strategic Objectives (A–F) and policy-level drill-down.
 *
 * Stability: loads a single authoritative server snapshot
 * (GET /dashboard/objectives-health). Same tenant + data + calculation_version
 * ⇒ same results. No silent empty fallbacks, no N+1 forecast probes,
 * no treating predicted-only metrics as observed health.
 */
import { useState, useEffect, useMemo, useRef } from 'react'
import {
  Box,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  FormControl,
  Grid,
  InputLabel,
  LinearProgress,
  MenuItem,
  Paper,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Alert,
  Button,
  Link,
} from '@mui/material'
import ListFilterBar from '../components/common/ListFilterBar'
import {
  formatPolicyTypeLabel,
  policyTypesMatch,
  uniquePolicyTypeOptions,
} from '../lib/policyType'
import {
  Flag as FlagIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  HelpOutline as NoDataIcon,
  Refresh as RefreshIcon,
  TrendingUp as ChartIcon,
  Warning as EarlyWarningIcon,
  BarChart as ImpactIcon,
  Settings as BehaviorIcon,
  Description as GovIcon,
  Star as EvidenceIcon,
  CalendarToday as CalendarIcon,
  GetApp as ExportIcon,
  Visibility as ViewPolicyIcon,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { apiClient } from '../lib/api'
import { healthForesightColors } from '../theme/healthForesightTheme'

type HealthStatus = 'on_track' | 'at_risk' | 'no_data'

interface ObjectiveRow {
  policyId: string
  name: string
  policyType: string
  objectiveLabel: string
  status: HealthStatus
  utilizationChangePct?: number | null
  costImpactPmpm?: number | null
  observationCount?: number
  policyEffectiveDate?: string | null
  latestObservationPeriodEnd?: string | null
  verdict?: string
}

type StrategicObjectiveKey = 'A' | 'B' | 'C' | 'D' | 'E' | 'F'

interface StrategicObjective {
  key: StrategicObjectiveKey
  title: string
  description: string
  icon: React.ReactNode
  count: number
  total: number
  whyMet: string
  policyIds: string[]
}

const STRATEGIC_ICONS: Record<StrategicObjectiveKey, React.ReactNode> = {
  A: <ChartIcon />,
  B: <EarlyWarningIcon />,
  C: <ImpactIcon />,
  D: <BehaviorIcon />,
  E: <GovIcon />,
  F: <EvidenceIcon />,
}

export default function ObjectivesHealthPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [objectives, setObjectives] = useState<ObjectiveRow[]>([])
  const [strategic, setStrategic] = useState<StrategicObjective[]>([])
  const [summary, setSummary] = useState({ total: 0, onTrack: 0, atRisk: 0, noData: 0 })
  const [objectivesMetCount, setObjectivesMetCount] = useState(0)
  const [calculationVersion, setCalculationVersion] = useState<string | null>(null)
  const [generatedAt, setGeneratedAt] = useState<string | null>(null)
  const [drillDownObjective, setDrillDownObjective] = useState<StrategicObjectiveKey | null>(null)
  const [reviewedToday, setReviewedToday] = useState(false)
  const [objSearch, setObjSearch] = useState('')
  const [objStatusFilter, setObjStatusFilter] = useState('')
  const [objTypeFilter, setObjTypeFilter] = useState('')
  const [coverage, setCoverage] = useState<any | null>(null)
  const [readiness, setReadiness] = useState<any | null>(null)
  const [coverageError, setCoverageError] = useState<string | null>(null)
  const loadGen = useRef(0)

  const typeOptions = useMemo(
    () => uniquePolicyTypeOptions(objectives.map((o) => o.policyType)),
    [objectives]
  )
  const filteredObjectives = useMemo(() => {
    const q = objSearch.trim().toLowerCase()
    return objectives.filter((row) => {
      if (objStatusFilter && row.status !== objStatusFilter) return false
      if (objTypeFilter && !policyTypesMatch(row.policyType, objTypeFilter)) return false
      if (!q) return true
      const hay = `${row.name} ${row.objectiveLabel} ${row.policyType}`.toLowerCase()
      return hay.includes(q)
    })
  }, [objectives, objSearch, objStatusFilter, objTypeFilter])

  const applySnapshot = (snap: any) => {
    const rows: ObjectiveRow[] = (snap.policy_rows || []).map((r: any) => ({
      policyId: r.policy_id,
      name: r.name,
      policyType: r.policy_type,
      objectiveLabel: r.objective_label,
      status: (r.status || 'no_data') as HealthStatus,
      utilizationChangePct: r.utilization_change_pct,
      costImpactPmpm: r.cost_impact_pmpm,
      observationCount: r.observation_count,
      policyEffectiveDate: r.policy_effective_date ?? null,
      latestObservationPeriodEnd: r.latest_observation_period_end ?? null,
      verdict: r.verdict,
    }))
    setObjectives(rows)
    const s = snap.summary || {}
    setSummary({
      total: s.total ?? rows.length,
      onTrack: s.on_track ?? 0,
      atRisk: s.at_risk ?? 0,
      noData: s.no_data ?? 0,
    })
    setStrategic(
      (snap.strategic || []).map((st: any) => ({
        key: st.key as StrategicObjectiveKey,
        title: st.title,
        description: st.description,
        icon: STRATEGIC_ICONS[st.key as StrategicObjectiveKey] || <FlagIcon />,
        count: st.count,
        total: st.total,
        whyMet: st.why_met,
        policyIds: st.policy_ids || [],
      }))
    )
    setObjectivesMetCount(snap.objectives_met_count ?? 0)
    setCalculationVersion(snap.calculation_version || null)
    setGeneratedAt(snap.generated_at || null)
  }

  const loadData = async () => {
    const gen = ++loadGen.current
    setLoading(true)
    setError(null)
    setCoverageError(null)
    try {
      const snap = await apiClient.getObjectivesHealth()
      if (gen !== loadGen.current) return // stale response — discard
      applySnapshot(snap)
    } catch (err: any) {
      if (gen !== loadGen.current) return
      setError(err.detail || err.message || 'Failed to load objectives health')
      // Do NOT clear prior good data on refresh failure — avoid flickering invented empty state
      if (objectives.length === 0) {
        setStrategic([])
      }
    } finally {
      if (gen === loadGen.current) setLoading(false)
    }

    // Coverage / readiness — separate; failures must not invent placeholder zeros as "complete"
    try {
      const [manifest, ready] = await Promise.all([
        apiClient.getEnterpriseCoverageManifest(),
        apiClient.getEnterpriseAnalyticalReadiness(),
      ])
      if (gen !== loadGen.current) return
      setCoverage(manifest)
      setReadiness(ready)
    } catch (err: any) {
      if (gen !== loadGen.current) return
      setCoverageError(err.detail || err.message || 'Coverage/readiness unavailable')
    }
  }

  useEffect(() => {
    loadData()
    return () => {
      loadGen.current += 1 // invalidate in-flight on unmount
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const StatusChip = ({ status }: { status: HealthStatus }) => {
    const config = {
      on_track: { label: 'On track', color: 'success' as const, icon: <CheckIcon sx={{ fontSize: 16 }} /> },
      at_risk: { label: 'At risk', color: 'warning' as const, icon: <WarningIcon sx={{ fontSize: 16 }} /> },
      no_data: { label: 'No data', color: 'default' as const, icon: <NoDataIcon sx={{ fontSize: 16 }} /> },
    }
    const { label, color, icon } = config[status]
    return (
      <Chip size="small" label={label} color={color} icon={icon} sx={{ '& .MuiChip-icon': { color: 'inherit' } }} />
    )
  }

  const selectedStrategic = drillDownObjective ? strategic.find((s) => s.key === drillDownObjective) : null

  if (loading && objectives.length === 0 && strategic.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 320 }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5" fontWeight={600} color={healthForesightColors.neutral.dark} gutterBottom>
          Strategic Objectives Health
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          Track how objectives A–F are met across the policy portfolio. Drill down to see which policies meet each
          objective. Status uses the same verdict engine as Policy Verdicts.
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', alignItems: 'center', mb: 2 }}>
          <Chip
            label={`${objectivesMetCount} of 6 objectives met`}
            color={objectivesMetCount === 6 ? 'success' : 'default'}
            size="small"
          />
          {calculationVersion && (
            <Chip size="small" variant="outlined" label={`Calc: ${calculationVersion}`} />
          )}
          {generatedAt && (
            <Typography variant="caption" color="text.secondary">
              Snapshot: {new Date(generatedAt).toLocaleString()}
            </Typography>
          )}
          <Button
            size="small"
            startIcon={loading ? <CircularProgress size={14} /> : <RefreshIcon />}
            onClick={() => loadData()}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}. Prior snapshot kept when available — results are not replaced with empty/synthetic data.
        </Alert>
      )}

      <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
        <Typography variant="subtitle1" fontWeight={600} gutterBottom>
          Policy Intelligence Coverage
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          Catalog inventory and analytical readiness are independent. Numbers come from the coverage
          manifest and persisted analysis jobs — never UI placeholders.
        </Typography>
        {coverageError && (
          <Alert severity="warning" sx={{ mb: 1 }}>
            {coverageError}
          </Alert>
        )}
        {coverage && (
          <Alert severity={coverage.complete ? 'success' : 'info'} sx={{ mb: 2 }}>
            Inventory complete: {coverage.complete ? 'Yes' : 'No'}. {coverage.reason_not_complete}
            {coverage.catalog_views && (
              <>
                {' '}
                Views: {coverage.catalog_views.demonstration_policies_default || 'Representative Payer Policies'}{' '}
                vs {coverage.catalog_views.authoritative_policies || 'Authoritative public CMS/NCCI'}.
              </>
            )}
          </Alert>
        )}
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Policy family</TableCell>
                <TableCell>Class</TableCell>
                <TableCell align="right">Catalog rows</TableCell>
                <TableCell>Inventory status</TableCell>
                <TableCell align="right">Baseline ready</TableCell>
                <TableCell align="right">Forecast ready</TableCell>
                <TableCell align="right">Observed</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(coverage?.families || []).map((f: any) => (
                <TableRow key={f.family_id}>
                  <TableCell>{f.label}</TableCell>
                  <TableCell>
                    <Typography variant="caption">
                      {f.catalog_class === 'AUTHORITATIVE_PUBLIC'
                        ? 'Authoritative'
                        : f.catalog_class === 'DEMO_SYNTHETIC'
                          ? 'Demonstration'
                          : f.catalog_class || '—'}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">{f.catalog_rows_classified ?? '—'}</TableCell>
                  <TableCell>
                    <Typography variant="caption">{f.inventory_status}</Typography>
                  </TableCell>
                  <TableCell align="right">—</TableCell>
                  <TableCell align="right">—</TableCell>
                  <TableCell align="right">—</TableCell>
                </TableRow>
              ))}
              {!coverage && !coverageError && (
                <TableRow>
                  <TableCell colSpan={7}>Loading coverage manifest…</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
        {readiness?.totals && (
          <Typography variant="body2" sx={{ mt: 1.5 }}>
            Portfolio analytical readiness (persisted): baseline {readiness.totals.baseline_ready} ·
            forecast {readiness.totals.forecast_ready} · observed {readiness.totals.observation_ready} ·
            impact assessable {readiness.totals.impact_assessable} / {readiness.totals.inventory} catalog
          </Typography>
        )}
      </Paper>

      <Paper variant="outlined" sx={{ p: 2, mb: 3, bgcolor: 'action.hover' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <CalendarIcon fontSize="small" />
          <Typography variant="subtitle2" fontWeight={600}>
            Make objectives monitoring a daily habit
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          Use this dashboard every day to spot gaps and drive follow-up. Focus on objectives that are &quot;Not
          started&quot; or have low policy counts; drill down to see which policies need attention and assign
          owners.
        </Typography>
        <ul style={{ margin: 0, paddingLeft: 20 }}>
          <li>
            <Typography variant="body2">Note which objectives need attention and drill into &quot;View by policy&quot;.</Typography>
          </li>
          <li>
            <Typography variant="body2">
              Align follow-ups with Policy Verdicts — both pages share the same observation verdict source.
            </Typography>
          </li>
        </ul>
        <Box sx={{ mt: 1.5, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Button
            size="small"
            variant={reviewedToday ? 'outlined' : 'contained'}
            onClick={() => setReviewedToday(true)}
          >
            {reviewedToday ? 'Reviewed today' : 'Mark reviewed today'}
          </Button>
          <Button size="small" startIcon={<ExportIcon />} onClick={() => navigate('/policy-verdicts')}>
            Open Policy Verdicts
          </Button>
        </Box>
      </Paper>

      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={6} sm={3}>
          <Paper variant="outlined" sx={{ p: 1.5, textAlign: 'center' }}>
            <Typography variant="h5" fontWeight={700}>
              {summary.total}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Policies
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Paper variant="outlined" sx={{ p: 1.5, textAlign: 'center' }}>
            <Typography variant="h5" fontWeight={700} color="success.main">
              {summary.onTrack}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              On track
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Paper variant="outlined" sx={{ p: 1.5, textAlign: 'center' }}>
            <Typography variant="h5" fontWeight={700} color="warning.main">
              {summary.atRisk}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              At risk
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Paper variant="outlined" sx={{ p: 1.5, textAlign: 'center' }}>
            <Typography variant="h5" fontWeight={700} color="text.secondary">
              {summary.noData}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              No data
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        {strategic.map((s) => {
          const pct = s.total > 0 ? Math.round((s.count / s.total) * 100) : 0
          return (
            <Grid item xs={12} sm={6} md={4} key={s.key}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    {s.icon}
                    <Typography variant="subtitle1" fontWeight={600}>
                      {s.key}. {s.title}
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1, minHeight: 40 }}>
                    {s.description}
                  </Typography>
                  <Typography variant="body2" fontWeight={600} sx={{ mb: 0.5 }}>
                    {s.count} / {s.total} policies
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={pct}
                    sx={{ mb: 1, height: 8, borderRadius: 1 }}
                    color={s.count > 0 ? 'primary' : 'inherit'}
                  />
                  <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                    {s.whyMet}
                  </Typography>
                  <Button size="small" onClick={() => setDrillDownObjective(s.key)}>
                    View by policy
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          )
        })}
      </Grid>

      <Typography variant="h6" fontWeight={600} sx={{ mb: 1 }}>
        Policy-level objectives
      </Typography>
      <ListFilterBar
        search={objSearch}
        onSearchChange={setObjSearch}
        searchPlaceholder="Name, objective, type…"
        filtered={filteredObjectives.length}
        total={objectives.length}
        trailing={
          <>
            <FormControl size="small" sx={{ minWidth: 140 }}>
              <InputLabel>Status</InputLabel>
              <Select
                label="Status"
                value={objStatusFilter}
                onChange={(e) => setObjStatusFilter(e.target.value)}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="on_track">On track</MenuItem>
                <MenuItem value="at_risk">At risk</MenuItem>
                <MenuItem value="no_data">No data</MenuItem>
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 160 }}>
              <InputLabel>Type</InputLabel>
              <Select
                label="Type"
                value={objTypeFilter}
                onChange={(e) => setObjTypeFilter(e.target.value)}
              >
                <MenuItem value="">All</MenuItem>
                {typeOptions.map((t) => (
                  <MenuItem key={t} value={t}>
                    {formatPolicyTypeLabel(t)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </>
        }
      />
      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Policy</TableCell>
              <TableCell>Objective</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Util Δ%</TableCell>
              <TableCell align="right">Cost Δ PMPM</TableCell>
              <TableCell>Obs end</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredObjectives.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8}>
                  {error && objectives.length === 0
                    ? 'Objectives Health could not be loaded. Empty counts below are not a verdict — fix the API error and refresh.'
                    : objectives.length === 0
                      ? 'No policies found. Add policies, then run baselines and observations.'
                      : 'No rows match the current filters.'}
                </TableCell>
              </TableRow>
            ) : (
              filteredObjectives.map((row) => (
                <TableRow key={row.policyId} hover>
                  <TableCell>
                    <Typography variant="body2" fontWeight={600}>
                      {row.name}
                    </Typography>
                  </TableCell>
                  <TableCell>{row.objectiveLabel}</TableCell>
                  <TableCell>{formatPolicyTypeLabel(row.policyType)}</TableCell>
                  <TableCell>
                    <StatusChip status={row.status} />
                  </TableCell>
                  <TableCell align="right">
                    {row.utilizationChangePct == null ? '—' : Number(row.utilizationChangePct).toFixed(1)}
                  </TableCell>
                  <TableCell align="right">
                    {row.costImpactPmpm == null ? '—' : Number(row.costImpactPmpm).toFixed(2)}
                  </TableCell>
                  <TableCell>{row.latestObservationPeriodEnd || '—'}</TableCell>
                  <TableCell align="right">
                    <Button
                      size="small"
                      startIcon={<ViewPolicyIcon />}
                      onClick={() => navigate(`/policies/${row.policyId}`)}
                    >
                      Workspace
                    </Button>
                    <Link
                      component="button"
                      variant="body2"
                      sx={{ ml: 1 }}
                      onClick={() =>
                        navigate('/observation-analysis', { state: { policyId: row.policyId } })
                      }
                    >
                      Observation
                    </Link>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Box sx={{ mt: 2 }}>
        <Link component="button" variant="body2" onClick={() => navigate('/predicted-impacts')}>
          View predicted impacts portfolio →
        </Link>
      </Box>

      <Dialog
        open={!!selectedStrategic}
        onClose={() => setDrillDownObjective(null)}
        maxWidth="md"
        fullWidth
      >
        {selectedStrategic && (
          <>
            <DialogTitle>
              {selectedStrategic.key}. {selectedStrategic.title}
            </DialogTitle>
            <DialogContent>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Policies that meet this objective: {selectedStrategic.count} of {selectedStrategic.total}
              </Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Policy</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Meets objective</TableCell>
                    <TableCell />
                  </TableRow>
                </TableHead>
                <TableBody>
                  {objectives.map((p) => {
                    const meets = selectedStrategic.policyIds.includes(p.policyId)
                    return (
                      <TableRow key={p.policyId} sx={{ opacity: meets ? 1 : 0.5 }}>
                        <TableCell>{p.name}</TableCell>
                        <TableCell>
                          <StatusChip status={p.status} />
                        </TableCell>
                        <TableCell>{meets ? 'Yes' : 'No'}</TableCell>
                        <TableCell>
                          <Button
                            size="small"
                            onClick={() => {
                              if (selectedStrategic.key === 'A') navigate('/predicted-impacts')
                              else
                                navigate('/observation-analysis', {
                                  state: { policyId: p.policyId },
                                })
                            }}
                          >
                            Open
                          </Button>
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </DialogContent>
          </>
        )}
      </Dialog>
    </Box>
  )
}
