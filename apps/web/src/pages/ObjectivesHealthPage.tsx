/**
 * Objectives Health – Strategic Objectives (A–F) and policy-level drill-down
 */
import { useState, useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  Grid,
  LinearProgress,
  Paper,
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

interface Policy {
  id: string
  name: string
  policy_type: string
}

interface ObjectiveRow {
  policyId: string
  name: string
  policyType: string
  objectiveLabel: string
  status: HealthStatus
  utilizationChangePct?: number
  costImpactPmpm?: number
  observationCount?: number
  policyEffectiveDate?: string | null
  latestObservationPeriodEnd?: string | null
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

const POLICY_TYPE_OBJECTIVES: Record<string, string> = {
  PRIOR_AUTH: 'Utilization & cost management',
  STEP_THERAPY: 'Appropriate therapy progression',
  SITE_OF_CARE: 'Site-of-care optimization',
  QUANTITY_LIMIT: 'Quantity and cost control',
  UM: 'Utilization management',
  default: 'Policy objective',
}

function getObjectiveLabel(policyType: string): string {
  return POLICY_TYPE_OBJECTIVES[policyType?.toUpperCase()] ?? POLICY_TYPE_OBJECTIVES.default
}

function deriveStatus(perf: {
  avg_utilization_change_pct?: number
  avg_cost_impact?: number
  observation_count?: number
}): HealthStatus {
  if (perf.observation_count === 0 || (perf.avg_utilization_change_pct == null && perf.avg_cost_impact == null)) {
    return 'no_data'
  }
  const util = perf.avg_utilization_change_pct ?? 0
  const cost = perf.avg_cost_impact ?? 0
  const utilizationOk = util <= 0
  const costOk = cost <= 0
  if (utilizationOk && costOk) return 'on_track'
  if (!utilizationOk && !costOk) return 'at_risk'
  return util > 5 || cost > 50 ? 'at_risk' : 'on_track'
}

const STRATEGIC_OBJECTIVE_CONFIG: Record<
  StrategicObjectiveKey,
  { title: string; description: string; icon: React.ReactNode }
> = {
  A: {
    title: 'Predictable Medical Cost Outcomes',
    description: 'Policy-level forecasts with ranges and validity window',
    icon: <ChartIcon />,
  },
  B: {
    title: 'Early Detection of Backfire',
    description: 'Early warning signals (provider resistance, patient deferral, site-of-care)',
    icon: <EarlyWarningIcon />,
  },
  C: {
    title: 'True Measurement of Policy Effectiveness',
    description: 'Single impact verdict per policy (expected vs observed, attribution)',
    icon: <ImpactIcon />,
  },
  D: {
    title: 'Behavioral Transparency',
    description: 'Provider and patient behavior profiles, time-based, linked to outcomes',
    icon: <BehaviorIcon />,
  },
  E: {
    title: 'Executive-Grade Governance',
    description: 'Decision packets: what changed, why, what if no action, recommended action',
    icon: <GovIcon />,
  },
  F: {
    title: 'Employer & Regulator Confidence',
    description: 'Auto-generated evidence packs (pre-policy, observed, mitigations, confidence)',
    icon: <EvidenceIcon />,
  },
}

export default function ObjectivesHealthPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [policies, setPolicies] = useState<Policy[]>([])
  const [objectives, setObjectives] = useState<ObjectiveRow[]>([])
  const [strategic, setStrategic] = useState<StrategicObjective[]>([])
  const [summary, setSummary] = useState({ total: 0, onTrack: 0, atRisk: 0, noData: 0 })
  const [objectivesMetCount, setObjectivesMetCount] = useState(0)
  const [drillDownObjective, setDrillDownObjective] = useState<StrategicObjectiveKey | null>(null)
  const [reviewedToday, setReviewedToday] = useState(false)

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [policiesRes, performanceRes, observationsRes, decisionsRes, verdictsRes] = await Promise.all([
        apiClient.getPolicies().catch(() => null),
        apiClient.getPolicyPerformance(100).catch(() => []),
        apiClient.getObservations().catch(() => []),
        apiClient.getDecisions().catch(() => []),
        apiClient.getPolicyVerdicts().catch(() => ({ items: [] as any[], count: 0 })),
      ])

      const rawPolicies = Array.isArray(policiesRes) ? policiesRes : (policiesRes as any)?.items ?? []
      const policiesList: Policy[] = rawPolicies.map((p: any) => ({
        id: p.id ?? p.policy_id,
        name: p.name ?? p.policy_name ?? 'Unnamed',
        policy_type: p.policy_type ?? 'UM',
      }))
      const performanceList = Array.isArray(performanceRes) ? performanceRes : []
      const observationsList = Array.isArray(observationsRes) ? observationsRes : (observationsRes as any)?.items ?? []
      const decisionsList = Array.isArray(decisionsRes) ? decisionsRes : (decisionsRes as any)?.items ?? []
      const verdictItems = verdictsRes?.items ?? []

      setPolicies(policiesList)
      const totalPolicies = policiesList.length

      const perfByPolicyId: Record<string, any> = {}
      performanceList.forEach((p: any) => {
        const id = p.policy_id ?? p.id
        if (id) perfByPolicyId[id] = p
      })
      const verdictByPolicyId: Record<string, { verdict: string; cost_impact_pct?: number; savings_or_cost_impact_pmpm?: number }> = {}
      verdictItems.forEach((v: any) => {
        const id = v.policy_id
        if (id) verdictByPolicyId[id] = { verdict: v.verdict, cost_impact_pct: v.cost_impact_pct, savings_or_cost_impact_pmpm: v.savings_or_cost_impact_pmpm }
      })

      const verdictToStatus = (verdict: string): HealthStatus => {
        if (verdict === 'ON_TRACK') return 'on_track'
        if (verdict === 'AT_RISK' || verdict === 'BACKFIRE') return 'at_risk'
        return 'no_data'
      }

      const rows: ObjectiveRow[] = policiesList.map((p) => {
        const id = p.id
        const verdictRow = verdictByPolicyId[id]
        const perf = perfByPolicyId[id]
        const status = verdictRow ? verdictToStatus(verdictRow.verdict) : (perf ? deriveStatus(perf) : 'no_data')
        return {
          policyId: id,
          name: p.name,
          policyType: p.policy_type,
          objectiveLabel: getObjectiveLabel(p.policy_type),
          status,
          utilizationChangePct: perf?.avg_utilization_change_pct,
          costImpactPmpm: verdictRow?.savings_or_cost_impact_pmpm ?? perf?.avg_cost_impact,
          observationCount: perf?.observations_count ?? perf?.observation_count,
          policyEffectiveDate: perf?.policy_effective_date ?? null,
          latestObservationPeriodEnd: perf?.latest_observation_period_end ?? null,
        }
      })
      setObjectives(rows)
      setSummary({
        total: rows.length,
        onTrack: rows.filter((r) => r.status === 'on_track').length,
        atRisk: rows.filter((r) => r.status === 'at_risk').length,
        noData: rows.filter((r) => r.status === 'no_data').length,
      })

      const policyIdsWithObservation = new Set<string>()
      const policyIdsWithBackfireRisk = new Set<string>()
      const policyIdsWithBehaviorProfiles = new Set<string>()
      verdictItems.forEach((v: any) => {
        const pid = v.policy_id
        if (!pid) return
        if (v.verdict !== 'UNKNOWN') policyIdsWithObservation.add(pid)
        if (v.verdict === 'BACKFIRE') policyIdsWithBackfireRisk.add(pid)
      })
      observationsList.forEach((obs: any) => {
        const pid = obs.policy_id ?? obs.policyId
        if (!pid) return
        policyIdsWithObservation.add(pid)
        const beh = obs.behavioral_explanation ?? obs.metrics?.behavioral_explanation ?? {}
        if (beh && typeof beh === 'object') {
          if (beh.provider_response || beh.patient_response || beh.provider_archetype_shares || beh.patient_response_shares) {
            policyIdsWithBehaviorProfiles.add(pid)
          }
        }
      })

      const policyIdsWithDecision = new Set<string>()
      decisionsList.forEach((d: any) => {
        const pid = d.policy_id ?? d.policyId
        if (pid) policyIdsWithDecision.add(pid)
      })

      const policyIdsWithForecast: string[] = []
      await Promise.all(
        policiesList.slice(0, 100).map(async (p) => {
          try {
            const impact = await apiClient.getPolicyPredictedImpact(p.id)
            if (impact && impact.metrics) policyIdsWithForecast.push(p.id)
          } catch {
            // no forecast
          }
        })
      )
      const forecastSet = new Set(policyIdsWithForecast)

      const policyIdsEvidenceReady = [...policyIdsWithObservation].filter((pid) => forecastSet.has(pid))

      const strategicData: StrategicObjective[] = [
        {
          key: 'A',
          ...STRATEGIC_OBJECTIVE_CONFIG.A,
          count: policyIdsWithForecast.length,
          total: totalPolicies,
          whyMet:
            totalPolicies === 0
              ? 'No policies in portfolio.'
              : `${policyIdsWithForecast.length} of ${totalPolicies} policies have forecasts; ${totalPolicies - policyIdsWithForecast.length} policies have no forecast yet. Run predicted impact analysis for the remaining policies.`,
          policyIds: policyIdsWithForecast,
        },
        {
          key: 'B',
          ...STRATEGIC_OBJECTIVE_CONFIG.B,
          count: policyIdsWithBackfireRisk.size,
          total: totalPolicies,
          whyMet:
            totalPolicies === 0
              ? 'No policies in portfolio.'
              : `${policyIdsWithBackfireRisk.size} of ${totalPolicies} policies have been flagged as backfire risk (aligned with Policy Verdicts). Review and act on these policies.`,
          policyIds: [...policyIdsWithBackfireRisk],
        },
        {
          key: 'C',
          ...STRATEGIC_OBJECTIVE_CONFIG.C,
          count: policyIdsWithObservation.size,
          total: totalPolicies,
          whyMet:
            totalPolicies === 0
              ? 'No policies in portfolio.'
              : policyIdsWithObservation.size === totalPolicies
                ? `All ${totalPolicies} policies have an impact verdict.`
                : `${policyIdsWithObservation.size} of ${totalPolicies} policies have an impact verdict.`,
          policyIds: [...policyIdsWithObservation],
        },
        {
          key: 'D',
          ...STRATEGIC_OBJECTIVE_CONFIG.D,
          count: policyIdsWithBehaviorProfiles.size,
          total: totalPolicies,
          whyMet:
            totalPolicies === 0
              ? 'No policies in portfolio.'
              : policyIdsWithBehaviorProfiles.size === totalPolicies
                ? `All ${totalPolicies} policies have behavior profiles.`
                : `${policyIdsWithBehaviorProfiles.size} of ${totalPolicies} policies have behavior profiles.`,
          policyIds: [...policyIdsWithBehaviorProfiles],
        },
        {
          key: 'E',
          ...STRATEGIC_OBJECTIVE_CONFIG.E,
          count: policyIdsWithDecision.size,
          total: totalPolicies,
          whyMet:
            totalPolicies === 0
              ? 'No policies in portfolio.'
              : policyIdsWithDecision.size === totalPolicies
                ? `All ${totalPolicies} policies have a decision packet.`
                : `${policyIdsWithDecision.size} of ${totalPolicies} policies have a decision packet.`,
          policyIds: [...policyIdsWithDecision],
        },
        {
          key: 'F',
          ...STRATEGIC_OBJECTIVE_CONFIG.F,
          count: policyIdsEvidenceReady.length,
          total: totalPolicies,
          whyMet:
            totalPolicies === 0
              ? 'No policies in portfolio.'
              : policyIdsEvidenceReady.length === totalPolicies
                ? `All ${totalPolicies} policies have evidence-pack-ready data.`
                : `${policyIdsEvidenceReady.length} of ${totalPolicies} policies have evidence-pack-ready data.`,
          policyIds: policyIdsEvidenceReady,
        },
      ]
      setStrategic(strategicData)
      setObjectivesMetCount(strategicData.filter((s) => s.count > 0).length)
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to load objectives')
      setObjectives([])
      setStrategic([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
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
      {/* Strategic Objectives Health */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5" fontWeight={600} color={healthForesightColors.neutral.dark} gutterBottom>
          Strategic Objectives Health
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Track how objectives A–F are met across the policy portfolio. Drill down to see which policies meet each objective.
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
          <Chip
            label={`${objectivesMetCount} of 6 objectives met`}
            color={objectivesMetCount === 6 ? 'success' : 'default'}
            size="medium"
          />
          <Chip label={`${policies.length} policies in portfolio`} variant="outlined" size="medium" />
        </Box>
      </Box>

      {/* Make objectives monitoring a daily habit */}
      <Paper sx={{ p: 2, mb: 3, bgcolor: '#f0fdf4', border: '1px solid #bbf7d0' }}>
        <Typography variant="subtitle2" fontWeight={600} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <CalendarIcon fontSize="small" /> Make objectives monitoring a daily habit
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
          Use this dashboard every day to spot gaps and drive follow-up. Focus on objectives that are &quot;Not started&quot; or have low policy counts; drill down to see which policies need attention and assign owners.
        </Typography>
        <Box component="ul" sx={{ m: 0, pl: 2.5, mb: 1.5, '& li': { mb: 0.5 } }}>
          <li>Open this page daily (e.g. start of day or standup).</li>
          <li>Note which objectives need attention and drill into &quot;View by policy&quot;.</li>
          <li>Export or screenshot the summary for records or share with stakeholders.</li>
          <li>Optionally set a daily digest reminder so you never miss a review.</li>
        </Box>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Button
            size="small"
            variant="contained"
            color="success"
            onClick={() => setReviewedToday(true)}
            disabled={reviewedToday}
          >
            {reviewedToday ? 'Marked as reviewed today' : 'Mark as reviewed today'}
          </Button>
          <Button size="small" variant="outlined" startIcon={<ExportIcon />} onClick={() => alert('Export summary (CSV) – coming soon')}>
            Export summary (CSV)
          </Button>
          <Button size="small" variant="outlined" startIcon={<CalendarIcon />} onClick={() => alert('Set daily reminder – coming soon')}>
            Set daily reminder
          </Button>
        </Box>
      </Paper>

      {/* Six objective cards */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        {strategic.map((obj) => (
          <Grid item xs={12} md={6} lg={4} key={obj.key}>
            <Card variant="outlined" sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flexGrow: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, mb: 1 }}>
                  <Box sx={{ color: 'primary.main' }}>{obj.icon}</Box>
                  <Box>
                    <Typography variant="subtitle2" fontWeight={600}>
                      Objective {obj.key}: {obj.title}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {obj.description}
                    </Typography>
                  </Box>
                </Box>
                <Chip
                  size="small"
                  label={obj.count >= obj.total && obj.total > 0 ? 'Met' : obj.count > 0 ? 'Partial' : 'Not started'}
                  color={obj.count >= obj.total && obj.total > 0 ? 'success' : obj.count > 0 ? 'default' : 'default'}
                  sx={{ mb: 1 }}
                />
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {obj.whyMet}
                </Typography>
                <Typography variant="body2" fontWeight={500} sx={{ mb: 0.5 }}>
                  {obj.count} of {obj.total} policies
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={obj.total ? Math.round((obj.count / obj.total) * 100) : 0}
                  sx={{ height: 6, borderRadius: 1, mb: 1.5 }}
                />
                <Button
                  size="small"
                  startIcon={<ViewPolicyIcon />}
                  onClick={() => setDrillDownObjective(obj.key)}
                  fullWidth
                  variant="outlined"
                >
                  View by policy
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Policy-level objectives table */}
      <Typography variant="h6" fontWeight={600} sx={{ mb: 1.5 }}>
        Policy-level objectives
      </Typography>
      <TableContainer component={Paper} variant="outlined" sx={{ borderColor: '#e2e8f0', borderRadius: 1, mb: 2 }}>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ bgcolor: '#f1f5f9' }}>
              <TableCell sx={{ fontWeight: 600 }}>Objective / Policy</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Effective</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Through</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Type</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Status</TableCell>
              <TableCell align="right" sx={{ fontWeight: 600 }}>Util change %</TableCell>
              <TableCell align="right" sx={{ fontWeight: 600 }}>Cost impact (PMPM)</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {objectives.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center" sx={{ py: 4 }}>
                  <Typography color="text.secondary">
                    No policies found. Add policies in the Policies section, then run baselines and observations to see objective health.
                  </Typography>
                  <Button sx={{ mt: 2 }} variant="outlined" onClick={() => navigate('/policies')}>
                    Go to Policies
                  </Button>
                </TableCell>
              </TableRow>
            ) : (
              objectives.map((row) => (
                <TableRow key={row.policyId} hover>
                  <TableCell>
                    <Typography fontWeight={500}>{row.name}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {row.objectiveLabel}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {row.policyEffectiveDate
                      ? new Date(row.policyEffectiveDate.split('T')[0]).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
                      : '—'}
                  </TableCell>
                  <TableCell>
                    {row.latestObservationPeriodEnd
                      ? new Date(row.latestObservationPeriodEnd.split('T')[0]).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
                      : '—'}
                  </TableCell>
                  <TableCell>
                    <Chip label={row.policyType.replace(/_/g, ' ')} size="small" variant="outlined" />
                  </TableCell>
                  <TableCell>
                    <StatusChip status={row.status} />
                  </TableCell>
                  <TableCell align="right">
                    {row.utilizationChangePct != null ? `${row.utilizationChangePct.toFixed(1)}%` : '—'}
                  </TableCell>
                  <TableCell align="right">
                    {row.costImpactPmpm != null ? `$${row.costImpactPmpm.toFixed(2)}` : '—'}
                  </TableCell>
                  <TableCell>
                    <Link
                      component="button"
                      variant="body2"
                      onClick={() => navigate('/observation-analysis', { state: { policyId: row.policyId } })}
                      sx={{ mr: 1 }}
                    >
                      Observation
                    </Link>
                    <Link
                      component="button"
                      variant="body2"
                      onClick={() => navigate('/baseline-analysis', { state: { policyId: row.policyId } })}
                      sx={{ mr: 1 }}
                    >
                      Baseline
                    </Link>
                    <Link component="button" variant="body2" onClick={() => navigate('/predicted-impacts')}>
                      Predicted
                    </Link>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Button startIcon={<RefreshIcon />} onClick={loadData} disabled={loading} size="small">
        Refresh
      </Button>

      {/* Drill-down: View by policy dialog */}
      <Dialog open={!!drillDownObjective} onClose={() => setDrillDownObjective(null)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {selectedStrategic ? `Objective ${selectedStrategic.key}: ${selectedStrategic.title} — by policy` : ''}
        </DialogTitle>
        <DialogContent>
          {selectedStrategic && (
            <>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Policies that meet this objective: {selectedStrategic.count} of {selectedStrategic.total}
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Policy</TableCell>
                      <TableCell>Meets objective</TableCell>
                      <TableCell align="right">Action</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {policies.map((p) => {
                      const meets = selectedStrategic.policyIds.includes(p.id)
                      return (
                        <TableRow key={p.id}>
                          <TableCell>{p.name}</TableCell>
                          <TableCell>
                            <Chip size="small" label={meets ? 'Yes' : 'No'} color={meets ? 'success' : 'default'} />
                          </TableCell>
                          <TableCell align="right">
                            <Button
                              size="small"
                              onClick={() => {
                                setDrillDownObjective(null)
                                if (selectedStrategic.key === 'A') navigate('/predicted-impacts')
                                else if (selectedStrategic.key === 'B' || selectedStrategic.key === 'C' || selectedStrategic.key === 'D')
                                  navigate('/observation-analysis', { state: { policyId: p.id } })
                                else if (selectedStrategic.key === 'E') navigate('/decisions')
                                else navigate('/observation-analysis', { state: { policyId: p.id } })
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
              </TableContainer>
            </>
          )}
        </DialogContent>
      </Dialog>
    </Box>
  )
}
