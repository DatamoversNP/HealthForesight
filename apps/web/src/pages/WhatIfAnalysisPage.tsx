/**
 * What-If Analysis Page
 * Allows users to adjust policy parameters and see projected impact
 */
import React, { useState, useEffect, useRef } from 'react'
import { combineMultiPolicyResults } from './whatIfMultiPolicy'
import { Link as RouterLink, useSearchParams } from 'react-router-dom'
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  LinearProgress,
  Paper,
  Slider,
  TextField,
  Typography,
  MenuItem,
  Alert,
  Link,
  Tabs,
  Tab,
  FormControl,
  InputLabel,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Checkbox,
  Autocomplete,
} from '@mui/material'
import {
  PlayArrow as RunIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Analytics as AnalyticsIcon,
} from '@mui/icons-material'
import PolicyAutocomplete from '../components/common/PolicyAutocomplete'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { apiClient } from '../lib/api'
import TrustPanel from '../components/TrustPanel'
import ElasticityCurvesDisplay from '../components/ElasticityCurvesDisplay'
import ScenarioComparison from '../components/ScenarioComparison'
import { healthForesightColors } from '../theme/healthForesightTheme'

interface Policy {
  id: string
  name: string
  policy_type: string
  policy_logic?: any
}

interface ScenarioResult {
  scenario_id: string
  scenario_name?: string
  engine_id?: string
  mechanism?: string
  not_utilization_elasticity?: boolean
  limitations?: string[]
  catalog_class?: string
  sign_convention?: Record<string, string>
  calculation_version?: string
  baseline_metrics?: {
    utilization_per_1k?: number
    allowed_pmpm?: number
    paid_pmpm?: number
    claim_count?: number
    member_months?: number
    payer_savings?: number
    payment_impact?: number
    post_policy_paid?: number
    provider_payment_change?: number
    total_paid_baseline_window?: number
    [key: string]: unknown
  }
  projected_metrics?: {
    utilization_per_1k?: number
    allowed_pmpm?: number
    paid_pmpm?: number
    claim_count?: number
    member_months?: number
    payer_savings?: number
    payment_impact?: number
    post_policy_paid?: number
    provider_payment_change?: number
    [key: string]: unknown
  }
  impact_metrics?: {
    utilization_per_1k?: number
    allowed_pmpm?: number
    paid_pmpm?: number
    percent_changes?: {
      utilization_per_1k?: number | null
      allowed_pmpm?: number | null
      paid_pmpm?: number | null
    }
    delta_payer_savings?: number
    delta_payment_impact?: number
    delta_provider_payment_change?: number
    price_effect_delta?: number
    volume_effect?: number
    mix_effect?: number
    tradeoff_analysis?: {
      utilization_change_pct: number
      cost_change_pct: number
      tradeoff_ratio: number
      efficiency_score: number
      efficiency_category: 'HIGH' | 'MEDIUM' | 'LOW' | 'POOR'
      interpretation: string
    }
    risk_analysis?: {
      worst_case: {
        utilization_per_1k?: number
        utilization_change_pct?: number
        cost_pmpm?: number
        cost_change_pct?: number
      }
      best_case: {
        utilization_per_1k?: number
        utilization_change_pct?: number
        cost_pmpm?: number
        cost_change_pct?: number
      }
      confidence_interval_width?: {
        utilization_pct: number
        cost_pct: number
      }
      risk_level: 'HIGH' | 'MEDIUM' | 'LOW' | 'MINIMAL'
      risk_factors: string[]
      risk_summary: string
    }
    [key: string]: unknown
  }
  confidence_intervals?: {
    utilization_per_1k?: [number, number]
    allowed_pmpm?: [number, number]
    paid_pmpm?: [number, number]
  }
  confidence_score?: number
  sensitivity_analysis?: any
  policy_effect_status?: string
  outcome_status?: string
}

function isPaymentRuleWhatIf(result: ScenarioResult | null | undefined): boolean {
  if (!result) return false
  if (result.not_utilization_elasticity) return true
  if (result.engine_id && /reimbursement|coverage|ncci|mppr|mue|ptp|sos|therapy/i.test(result.engine_id)) {
    return true
  }
  const impact = result.impact_metrics || {}
  const hasPaymentDelta =
    impact.delta_payer_savings != null ||
    impact.delta_payment_impact != null ||
    impact.price_effect_delta != null
  const hasUmShape =
    result.baseline_metrics?.utilization_per_1k != null ||
    impact.percent_changes?.utilization_per_1k != null
  return Boolean(hasPaymentDelta && !hasUmShape)
}

function formatConfidencePct(score: number | null | undefined): string {
  if (score == null || Number.isNaN(score)) return 'Unavailable'
  const pct = score <= 1 ? score * 100 : score
  return `${pct.toFixed(0)}%`
}

function syntheticMechanism(name: string): string {
  const text = name.toLowerCase()
  if (text.includes('mri') || text.includes('ncd') || text.includes('lcd')) return 'clinical'
  if (text.includes('infusion')) return 'infusion'
  if (text.includes('multiple procedure')) return 'mppr'
  if (text.includes('site of service')) return 'sos'
  if (text.includes('procedure-to-procedure')) return 'ptp'
  if (text.includes('unit cap')) return 'mue'
  if (text.includes('therapy')) return 'therapy'
  return 'other'
}

function SyntheticParameterFields({
  policyName,
  params,
  onChange,
}: {
  policyName: string
  params: {
    secondary_pct: number
    hospital_pct: number
    modifier_indicator: string
    mue_value: number
    office_allowed: number
    steer_hopd_count: number
  }
  onChange: (next: typeof params) => void
}) {
  const mechanism = syntheticMechanism(policyName)
  if (mechanism === 'clinical') {
    return (
      <Alert severity="warning" sx={{ mt: 2 }} data-testid="synthetic-whatif-clinical">
        {policyName} can show source events. An outcome-based what-if is unavailable. Running it will not produce a dollar result.
      </Alert>
    )
  }
  if (mechanism === 'mppr') {
    return (
      <Box sx={{ mt: 2 }}>
        <Typography variant="body2">Secondary procedure percent of allowed: {params.secondary_pct.toFixed(2)}</Typography>
        <Slider
          min={0}
          max={1}
          step={0.05}
          value={params.secondary_pct}
          onChange={(_, value) => onChange({ ...params, secondary_pct: Number(value) })}
          aria-label="Secondary procedure percent"
        />
      </Box>
    )
  }
  if (mechanism === 'sos') {
    return (
      <Box sx={{ mt: 2 }}>
        <Typography variant="body2">
          Hospital outpatient percent of allowed: {params.hospital_pct.toFixed(2)}. 1.00 is a zero payment difference. Above 1.00 raises simulated allowed.
        </Typography>
        <Slider
          min={0.5}
          max={1.2}
          step={0.05}
          value={params.hospital_pct}
          onChange={(_, value) => onChange({ ...params, hospital_pct: Number(value) })}
          aria-label="Hospital outpatient percent"
        />
      </Box>
    )
  }
  if (mechanism === 'ptp') {
    return (
      <FormControl sx={{ mt: 2, minWidth: 280 }}>
        <InputLabel>Modifier indicator</InputLabel>
        <Select
          label="Modifier indicator"
          value={params.modifier_indicator}
          onChange={(event) => onChange({ ...params, modifier_indicator: String(event.target.value) })}
        >
          <MenuItem value="1">1 — pay column two when a listed modifier is present</MenuItem>
          <MenuItem value="0">0 — deny column two even with a modifier</MenuItem>
          <MenuItem value="9">9 — modifier does not apply</MenuItem>
        </Select>
      </FormControl>
    )
  }
  if (mechanism === 'mue') {
    return (
      <TextField
        sx={{ mt: 2 }}
        type="number"
        label="Demo unit cap (not a CMS MUE)"
        value={params.mue_value}
        onChange={(event) => onChange({ ...params, mue_value: Number(event.target.value) })}
        inputProps={{ min: 0, max: 100 }}
      />
    )
  }
  if (mechanism === 'infusion') {
    return (
      <Box sx={{ mt: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <TextField
          type="number"
          label="Office allowed amount"
          value={params.office_allowed}
          onChange={(event) => onChange({ ...params, office_allowed: Number(event.target.value) })}
        />
        <TextField
          type="number"
          label="HOPD lines steered per claim"
          value={params.steer_hopd_count}
          onChange={(event) => onChange({ ...params, steer_hopd_count: Number(event.target.value) })}
          helperText="The population simulation steers the first HOPD line of each claim."
        />
      </Box>
    )
  }
  if (mechanism === 'therapy') {
    return (
      <Alert severity="info" sx={{ mt: 2 }}>
        Therapy uses the medically necessary units stored on each line. There is no extra scenario percent.
      </Alert>
    )
  }
  return null
}

function SyntheticWhatIfResult({
  result,
  formatCurrency,
}: {
  result: any
  formatCurrency: (value: number | null | undefined) => string
}) {
  const money = (value: number | null | undefined) => formatCurrency(value)
  const rate = (value: number | null | undefined) =>
    value == null || Number.isNaN(value) ? 'Unavailable' : `$${value.toFixed(4)} / enrolled member-month`
  return (
    <Card sx={{ mb: 2 }} data-testid="synthetic-whatif-result">
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {result.scenario_name || result.policy_name}
        </Typography>
        <Alert severity={result.status === 'completed' ? 'info' : result.status === 'unavailable' ? 'warning' : 'error'} sx={{ mb: 2 }}>
          {result.label || result.reason}
          {result.oracle_match === true ? ' Independent oracle agrees with the engine.' : ''}
          {result.oracle_match === false ? ' Independent oracle does not agree. Do not use this result.' : ''}
        </Alert>
        <Typography variant="body2" sx={{ mb: 1 }}>
          {result.policy_name} · {result.lines_included?.toLocaleString?.() ?? result.lines_included} lines · database{' '}
          {result.database_name} · {result.outcome_status}
        </Typography>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Measure</TableCell>
                <TableCell align="right">Value</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow>
                <TableCell>Baseline allowed</TableCell>
                <TableCell align="right">{money(result.baseline_allowed)}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Simulated allowed</TableCell>
                <TableCell align="right">{money(result.simulated_allowed)}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Allowed difference (simulated minus baseline)</TableCell>
                <TableCell align="right">{money(result.allowed_difference)}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Allowed difference per enrolled member-month</TableCell>
                <TableCell align="right">{rate(result.allowed_difference_per_enrolled_member_month)}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Baseline plan paid</TableCell>
                <TableCell align="right">{money(result.baseline_plan_paid)}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Simulated plan paid</TableCell>
                <TableCell align="right">{money(result.simulated_plan_paid)}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Plan-paid difference</TableCell>
                <TableCell align="right">{money(result.plan_paid_difference)}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Payer allowed difference (positive means simulated allowed is lower)</TableCell>
                <TableCell align="right">{money(result.payment_impact_dollars)}</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
        <Typography variant="caption" display="block" sx={{ mt: 1 }}>
          {result.allowed_difference_meaning}
        </Typography>
        <Typography variant="caption" display="block">
          {result.plan_paid_meaning}
        </Typography>
      </CardContent>
    </Card>
  )
}

function PaymentRuleWhatIfResult({
  result,
  formatCurrency,
}: {
  result: ScenarioResult
  formatCurrency: (value: number | null | undefined) => string
}) {
  const baseline = result.baseline_metrics || {}
  const projected = result.projected_metrics || {}
  const impact = result.impact_metrics || {}
  const deltaSavings =
    impact.delta_payer_savings ??
    impact.delta_payment_impact ??
    (typeof projected.payer_savings === 'number' && typeof baseline.payer_savings === 'number'
      ? projected.payer_savings - baseline.payer_savings
      : null)
  const baselinePaid =
    (baseline.total_paid_baseline_window as number | undefined) ??
    (baseline.post_policy_paid as number | undefined)
  const projectedPaid = projected.post_policy_paid as number | undefined
  const metricRows = Object.entries({
    ...baseline,
  })
    .filter(([key]) => !['utilization_per_1k', 'allowed_pmpm', 'paid_pmpm'].includes(key))
    .slice(0, 12)

  return (
    <Grid container spacing={3} data-testid="payment-rule-whatif-result">
      <Grid item xs={12}>
        <Card sx={{ mb: 1, bgcolor: 'primary.main', color: 'primary.contrastText' }}>
          <CardContent>
            <Typography variant="h5" gutterBottom sx={{ color: 'primary.contrastText', fontWeight: 600 }}>
              {result.scenario_name || result.scenario_id || 'Payment-rule what-if'}
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 1 }}>
              {result.mechanism && (
                <Chip label={result.mechanism} size="small" sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'primary.contrastText' }} />
              )}
              {result.engine_id && (
                <Chip label={result.engine_id} size="small" sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'primary.contrastText' }} />
              )}
              {result.catalog_class && (
                <Chip label={result.catalog_class} size="small" sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'primary.contrastText' }} />
              )}
              <Chip
                label={`Confidence ${formatConfidencePct(result.confidence_score)}`}
                size="small"
                sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'primary.contrastText' }}
              />
            </Box>
            <Alert severity="info" sx={{ bgcolor: 'rgba(255,255,255,0.12)', color: 'primary.contrastText' }}>
              This is a payment-rule / reimbursement scenario (not utilization elasticity). Metrics are paid dollars and
              edit hits, not claim-lines per 1,000 claimants.
            </Alert>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={8}>
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Payment impact summary
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={4}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="body2" color="text.secondary">
                    Incremental payer savings
                  </Typography>
                  <Typography variant="h5" color={deltaSavings != null && deltaSavings > 0 ? 'success.main' : 'text.primary'}>
                    {formatCurrency(deltaSavings)}
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="body2" color="text.secondary">
                    Baseline → projected paid
                  </Typography>
                  <Typography variant="h6">
                    {formatCurrency(baselinePaid)} → {formatCurrency(projectedPaid)}
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="body2" color="text.secondary">
                    Provider payment change (Δ)
                  </Typography>
                  <Typography variant="h5">
                    {formatCurrency(
                      (impact.delta_provider_payment_change as number | undefined) ??
                        (typeof projected.provider_payment_change === 'number' &&
                        typeof baseline.provider_payment_change === 'number'
                          ? projected.provider_payment_change - baseline.provider_payment_change
                          : null),
                    )}
                  </Typography>
                </Paper>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Baseline vs projected (payment-rule fields)
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Metric</TableCell>
                    <TableCell align="right">Baseline</TableCell>
                    <TableCell align="right">Projected</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {metricRows.map(([key]) => {
                    const b = baseline[key]
                    const p = projected[key]
                    const isMoney =
                      typeof b === 'number' &&
                      /paid|savings|payment|allowed|impact|change/i.test(key)
                    const fmt = (v: unknown) =>
                      v == null
                        ? '—'
                        : isMoney && typeof v === 'number'
                          ? formatCurrency(v)
                          : String(v)
                    return (
                      <TableRow key={key}>
                        <TableCell>{key.replace(/_/g, ' ')}</TableCell>
                        <TableCell align="right">{fmt(b)}</TableCell>
                        <TableCell align="right">{fmt(p)}</TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>

        {Array.isArray(result.limitations) && result.limitations.length > 0 && (
          <Alert severity="warning">
            <Typography variant="subtitle2" gutterBottom>
              Limitations
            </Typography>
            <ul style={{ margin: 0, paddingLeft: 18 }}>
              {result.limitations.map((item, idx) => (
                <li key={idx}>
                  <Typography variant="body2">{item}</Typography>
                </li>
              ))}
            </ul>
          </Alert>
        )}
      </Grid>

      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Sign convention
            </Typography>
            {result.sign_convention ? (
              Object.entries(result.sign_convention).map(([key, value]) => (
                <Box key={key} sx={{ mb: 1.5 }}>
                  <Typography variant="subtitle2">{key.replace(/_/g, ' ')}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {value}
                  </Typography>
                </Box>
              ))
            ) : (
              <Typography variant="body2" color="text.secondary">
                Positive payer savings means the payer pays less after the rule change.
              </Typography>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  )
}

export default function WhatIfAnalysisPage() {
  const [searchParams] = useSearchParams()
  const urlPolicyId = searchParams.get('policy')
  const urlScenarioId = searchParams.get('scenario')
  const loadedUrlScenarioKey = useRef<string | null>(null)

  const [policies, setPolicies] = useState<Policy[]>([])
  const [selectedPolicy, setSelectedPolicy] = useState<Policy | null>(null)
  const [selectedPolicies, setSelectedPolicies] = useState<Policy[]>([]) // Multi-policy support
  const [multiPolicyMode, setMultiPolicyMode] = useState(false) // Toggle between single and multi-policy
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [scenarioResult, setScenarioResult] = useState<ScenarioResult | null>(null)
  const [scenarios, setScenarios] = useState<ScenarioResult[]>([]) // Store multiple scenarios for comparison
  const [running, setRunning] = useState(false)
  const [workerHint, setWorkerHint] = useState<string | null>(null)
  const [scenarioName, setScenarioName] = useState<string>('')
  const [nameDialogOpen, setNameDialogOpen] = useState(false)
  const [multiPolicyProgress, setMultiPolicyProgress] = useState<{
    current: number
    total: number
    currentPolicyName: string
    completed: number
  } | null>(null)
  const [activeTab, setActiveTab] = useState<'configure' | 'elasticity' | 'results' | 'compare' | 'sensitivity' | 'accuracy'>(
    urlScenarioId ? 'results' : 'configure'
  )
  const [elasticityData, setElasticityData] = useState<any>(null)
  const [elasticityLoading, setElasticityLoading] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  /** Policies with claim counts (sorted by most data). Used to suggest policy for what-if. */
  const [policiesWithClaimCounts, setPoliciesWithClaimCounts] = useState<Array<{ id: string; name: string; policy_type: string; claim_count: number }> | null>(null)
  
  // Scenario Accuracy Tracking (Phase 7)
  const [scenarioAccuracy, setScenarioAccuracy] = useState<any[]>([])
  const [scenarioLinks, setScenarioLinks] = useState<any[]>([])
  const [currentScenarioAnalysisId, setCurrentScenarioAnalysisId] = useState<string | null>(null)
  const [observations, setObservations] = useState<any[]>([])
  const [linkDialogOpen, setLinkDialogOpen] = useState(false)
  const [accuracyDialogOpen, setAccuracyDialogOpen] = useState(false)
  const [selectedObservationId, setSelectedObservationId] = useState<string | null>(null)
  const openingHistoricalRun = Boolean(urlScenarioId)
  
  // Scenario parameters
  const [scenarioParams, setScenarioParams] = useState({
    lever_adjustments: {} as Record<string, any>,
    elasticity_adjustments: {} as Record<string, number>,
    member_count_multiplier: 1.0,
    utilization_trend: 0.0,
    cost_inflation: 0.02,
    projection_months: 12,
  })
  const [syntheticIdentity, setSyntheticIdentity] = useState<any>(null)
  const [syntheticResult, setSyntheticResult] = useState<any>(null)
  const [syntheticParams, setSyntheticParams] = useState({
    secondary_pct: 0.5,
    hospital_pct: 0.8,
    modifier_indicator: '1',
    mue_value: 4,
    office_allowed: 3200,
    steer_hopd_count: 1,
  })
  
  // Baseline filters
  const [baselineFilters, setBaselineFilters] = useState({
    lob: [] as string[],
    markets: [] as string[],
    cpt_codes: [] as string[],
  })

  useEffect(() => {
    loadPolicies()
    apiClient.getSyntheticPayerIdentity().then(setSyntheticIdentity).catch(() => setSyntheticIdentity(null))
  }, [])

  // Open from What-If history: /whatif?policy=…&scenario=<analysis_id>
  // Jump to Results immediately — do not leave the user on a blank Configure form.
  useEffect(() => {
    if (!urlScenarioId) {
      loadedUrlScenarioKey.current = null
      return
    }
    const dedupeKey = `${urlPolicyId || ''}:${urlScenarioId}`
    let cancelled = false
    setError(null)
    setLoading(true)
    setActiveTab('results')
    setScenarioResult(null)
    setCurrentScenarioAnalysisId(urlScenarioId)
    loadedUrlScenarioKey.current = dedupeKey
    ;(async () => {
      try {
        // Load analysis + results in parallel — never block charts on getPolicy
        const [analysis, resultsPrimary] = await Promise.all([
          apiClient.getAnalysis(urlScenarioId),
          apiClient.getAnalysisResults(urlScenarioId, 'whatif_scenario').catch(() => null),
        ])
        if (cancelled) return

        const analysisPolicyId =
          analysis.policy_id != null ? String(analysis.policy_id) : urlPolicyId ? String(urlPolicyId) : null

        // Resolve policy label in the background (optional)
        if (analysisPolicyId) {
          const fromList = policies.find((x) => String(x.id) === analysisPolicyId)
          if (fromList) {
            setSelectedPolicy(fromList)
          } else {
            apiClient
              .getPolicy(analysisPolicyId)
              .then((p) => {
                if (!cancelled && p) setSelectedPolicy(p as Policy)
              })
              .catch(() => {})
          }
        }

        if (analysis.status === 'COMPLETED') {
          let raw = resultsPrimary?.results
          if (
            !raw ||
            (typeof raw === 'object' &&
              !raw.whatif_scenario &&
              !raw.WHATIF_SCENARIO &&
              !raw.impact_metrics)
          ) {
            const resultsFallback = await apiClient.getAnalysisResults(urlScenarioId).catch(() => null)
            if (cancelled) return
            raw = resultsFallback?.results
          }
          if (cancelled) return
          const scenarioData =
            (raw &&
              (raw.whatif_scenario ||
                raw.WHATIF_SCENARIO ||
                raw.scenario ||
                (raw.impact_metrics || raw.projected_metrics || raw.baseline_metrics ? raw : null))) ||
            null
          if (scenarioData && typeof scenarioData === 'object') {
            const normalized = {
              ...scenarioData,
              scenario_id:
                (scenarioData as ScenarioResult).scenario_id ||
                `analysis-${urlScenarioId}`,
              scenario_name:
                (scenarioData as ScenarioResult).scenario_name ||
                analysis.name ||
                `Run ${urlScenarioId.slice(0, 8)}…`,
              _analysis_id: urlScenarioId,
              _created_at: analysis.created_at,
            } as ScenarioResult & { _analysis_id: string; _created_at?: string }
            setScenarioResult(normalized)
            setScenarios([normalized])
            setActiveTab('results')
          } else {
            setError('This run completed but no what-if result payload was found.')
            setActiveTab('configure')
          }
        } else if (analysis.status === 'FAILED') {
          setError(
            `This run failed: ${(analysis as { error_message?: string }).error_message || 'Unknown error'}`
          )
          setActiveTab('configure')
        } else {
          setError(`This run is still ${analysis.status}. Results will appear when it completes.`)
          setActiveTab('configure')
        }
      } catch (e: any) {
        if (!cancelled) {
          console.error('Open scenario from URL failed:', e)
          setError(e?.detail || e?.message || 'Failed to open this scenario run')
          setActiveTab('configure')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
      // React Strict Mode remounts effects; clear so the remount actually loads again
      if (loadedUrlScenarioKey.current === dedupeKey) {
        loadedUrlScenarioKey.current = null
      }
    }
  }, [urlScenarioId, urlPolicyId])

  useEffect(() => {
    if (!selectedPolicy) {
      if (!urlScenarioId) {
        setScenarios([])
        setScenarioResult(null)
        setScenarioAccuracy([])
        setScenarioLinks([])
      }
      return
    }

    // Historical Open: the URL effect already loads THAT run's JSON.
    // Do NOT fan out to elasticity + 30 prior results (that saturates Azure and times out).
    if (urlScenarioId) {
      const t = window.setTimeout(() => {
        // Light extras only after charts are on screen
        loadScenarioAccuracy(selectedPolicy.id, urlScenarioId).catch(() => {})
      }, 2000)
      return () => window.clearTimeout(t)
    }

    loadElasticityData(selectedPolicy.id)
    loadPreviousScenarios(selectedPolicy.id, { preserveCurrent: false, limit: 8 })
    loadScenarioAccuracy(selectedPolicy.id)
    loadObservations(selectedPolicy.id)
  }, [selectedPolicy, urlScenarioId])
  
  useEffect(() => {
    // Skip duplicate accuracy fetch while the historical-open path owns loading
    if (currentScenarioAnalysisId && !urlScenarioId) {
      loadScenarioAccuracy(selectedPolicy?.id, currentScenarioAnalysisId)
    }
  }, [currentScenarioAnalysisId, urlScenarioId])

  const loadPreviousScenarios = async (
    policyId: string,
    opts?: { preserveCurrent?: boolean; limit?: number }
  ) => {
    try {
      const maxResults = opts?.limit ?? 8
      // Get SIMULATE analyses for this policy (list is cheap; per-result payloads are not)
      const analyses = await apiClient.getAnalyses({ analysis_type: 'SIMULATE', limit: 50 })
      const policyScenarios = Array.isArray(analyses)
        ? analyses.filter((a: any) => String(a.policy_id) === String(policyId) && a.status === 'COMPLETED')
        : []

      // Load results for a small set only — sequential to avoid timeout stampede
      const loadedScenarios: ScenarioResult[] = []
      for (const analysis of policyScenarios.slice(0, maxResults)) {
        try {
          const results = await apiClient.getAnalysisResults(analysis.id, 'whatif_scenario')
          if (results.results) {
            const scenarioData = results.results.whatif_scenario || 
                               results.results.WHATIF_SCENARIO ||
                               results.results
            if (scenarioData && typeof scenarioData === 'object') {
              loadedScenarios.push({
                ...scenarioData,
                scenario_id:
                  (scenarioData as ScenarioResult).scenario_id || `analysis-${analysis.id}`,
                scenario_name:
                  (scenarioData as ScenarioResult).scenario_name ||
                  analysis.name ||
                  `Run ${String(analysis.id).slice(0, 8)}…`,
                _analysis_id: analysis.id,
                _created_at: analysis.created_at,
              } as ScenarioResult & { _analysis_id: string; _created_at?: string })
            }
          }
        } catch (err) {
          console.warn(`Failed to load scenario ${analysis.id}:`, err)
          // Continue loading other scenarios
        }
      }

      // Sort by creation date (most recent first)
      loadedScenarios.sort((a: any, b: any) => {
        const dateA = a._created_at ? new Date(a._created_at).getTime() : 0
        const dateB = b._created_at ? new Date(b._created_at).getTime() : 0
        return dateB - dateA
      })

      setScenarios((prev) => {
        // Keep a URL-opened run at the front if it isn't in the loaded set yet
        const opened = prev.find((s) => (s as any)._analysis_id === urlScenarioId)
        if (opened && !loadedScenarios.some((s) => (s as any)._analysis_id === urlScenarioId)) {
          return [opened, ...loadedScenarios]
        }
        return loadedScenarios
      })
      
      // If we have scenarios but no current result, show the most recent one
      // (skip when opening a specific historical run from the history page)
      if (loadedScenarios.length > 0 && !opts?.preserveCurrent) {
        setScenarioResult((current) => current || loadedScenarios[0])
      }
    } catch (err) {
      console.error('Error loading previous scenarios:', err)
      // Don't show error - scenarios are optional
    }
  }

  const loadPolicies = async () => {
    try {
      const data = await apiClient.getPolicies({ limit: 1000 })
      const policiesList = Array.isArray(data) ? data : (data.items || [])
      setPolicies(policiesList)
      // Optional tip only — never block What-If. Prefer Outpatient MRI for the demo path.
      setTimeout(async () => {
        try {
          const withCounts = await apiClient.getPoliciesWithClaimCounts(8)
          setPoliciesWithClaimCounts(Array.isArray(withCounts) ? withCounts : [])
        } catch {
          setPoliciesWithClaimCounts(null)
        }
      }, 2500)
    } catch (err: any) {
      console.error('Error loading policies:', err)
      setError(err.detail || err.message || 'Failed to load policies')
    }
  }

  // Scenario Accuracy Tracking Functions (Phase 7)
  const loadScenarioAccuracy = async (policyId?: string, scenarioAnalysisId?: string) => {
    try {
      const accuracyRecords = await apiClient.getScenarioAccuracy(scenarioAnalysisId || undefined, policyId || undefined)
      setScenarioAccuracy(accuracyRecords || [])
      
      const links = await apiClient.getScenarioLinks(scenarioAnalysisId || undefined, policyId || undefined)
      setScenarioLinks(links || [])
    } catch (err: any) {
      console.error('Error loading scenario accuracy:', err)
      // Don't show error to user - accuracy data may not exist yet
    }
  }
  
  const loadObservations = async (policyId: string) => {
    try {
      const obs = await apiClient.getObservations({ policy_id: policyId })
      setObservations(obs || [])
    } catch (err: any) {
      console.error('Error loading observations:', err)
    }
  }
  
  const handleLinkScenario = async () => {
    if (!currentScenarioAnalysisId || !selectedPolicy) {
      setError('Please select a scenario and policy')
      return
    }
    
    try {
      await apiClient.linkScenarioToPolicy(currentScenarioAnalysisId, selectedPolicy.id, {
        linked_by: 'user',
        linked_at: new Date().toISOString(),
      })
      await loadScenarioAccuracy(selectedPolicy.id, currentScenarioAnalysisId)
      setLinkDialogOpen(false)
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to link scenario')
    }
  }
  
  const handleComputeAccuracy = async () => {
    if (!currentScenarioAnalysisId || !selectedObservationId) {
      setError('Please select a scenario and observation')
      return
    }
    
    try {
      const accuracy = await apiClient.computeScenarioAccuracy(currentScenarioAnalysisId, selectedObservationId)
      await loadScenarioAccuracy(selectedPolicy?.id, currentScenarioAnalysisId)
      setAccuracyDialogOpen(false)
      setActiveTab('accuracy')
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to compute accuracy')
    }
  }
  
  const loadElasticityData = async (policyId: string) => {
    try {
      setElasticityLoading(true)
      const analyses = await apiClient.getAnalyses({ analysis_type: 'ELASTICITY', limit: 50 })
      const forPolicy = Array.isArray(analyses)
        ? analyses.filter((a: any) => a.policy_id === policyId)
        : []

      if (forPolicy.length === 0) {
        setElasticityData(null)
        return
      }

      const parseElasticityPayload = (results: any) => {
        if (results?.status === 'FAILED' && results?.error_message) {
          return { error: results.error_message as string, payload: null }
        }
        let payload: any = null
        if (results?.results?.ELASTICITY) {
          payload = results.results.ELASTICITY
        } else if (results?.service_categories) {
          payload = results
        } else if (results?.results && Object.keys(results.results).length > 0) {
          const k = Object.keys(results.results)[0]
          payload = results.results[k]
        }
        if (payload?.service_categories && Object.keys(payload.service_categories).length > 0) {
          return { error: null, payload }
        }
        return { error: null, payload: null }
      }

      let lastFailedDetail: string | null = null
      for (const row of forPolicy) {
        if (row.status === 'FAILED') {
          const analysisDetail = await apiClient.getAnalysis(row.id).catch(() => ({}))
          lastFailedDetail =
            analysisDetail?.error_message || 'Job failed (check API logs).'
          continue
        }
        if (row.status === 'PENDING' || row.status === 'RUNNING') {
          continue
        }
        if (row.status !== 'COMPLETED') {
          continue
        }
        const results = await apiClient.getAnalysisResults(row.id, 'ELASTICITY')
        const { error, payload } = parseElasticityPayload(results)
        if (error) {
          lastFailedDetail = error
          continue
        }
        if (payload) {
          setElasticityData(payload)
          setError(null)
          return
        }
      }

      const inFlight = forPolicy.some(
        (a: any) => a.status === 'PENDING' || a.status === 'RUNNING',
      )
      if (inFlight) {
        setElasticityData(null)
        return
      }

      if (lastFailedDetail) {
        setElasticityData(null)
        setError(
          `Elasticity: ${lastFailedDetail} Create a new elasticity analysis if you need fresh curves.`,
        )
        return
      }

      setElasticityData(null)
      console.warn(
        'Elasticity: no completed analysis with curve data for this policy. Create a new elasticity analysis if needed.',
      )
    } catch (err) {
      console.error('Error loading elasticity data:', err)
      setElasticityData(null)
    } finally {
      setElasticityLoading(false)
    }
  }

  const handleRunScenario = () => {
    if (!multiPolicyMode && !selectedPolicy) {
      setError('Please select a policy')
      return
    }
    if (multiPolicyMode && selectedPolicies.length === 0) {
      setError('Please select at least one policy')
      return
    }
    // Open dialog to get scenario name
    setNameDialogOpen(true)
  }

  const handleRunScenarioConfirmed = async () => {
    if (!multiPolicyMode && !selectedPolicy) {
      setError('Please select a policy')
      return
    }
    if (multiPolicyMode && selectedPolicies.length === 0) {
      setError('Please select at least one policy')
      return
    }

    // Generate default name if not provided
    const finalName = scenarioName.trim() || `Scenario ${new Date().toLocaleString()}`

    try {
      setRunning(true)
      setError(null)
      setWorkerHint(null)
      setNameDialogOpen(false)

      if (syntheticIdentity?.what_if_engine === 'NOT_THIS_POPULATION') {
        setError(syntheticIdentity.honesty || 'This scenario is not this population\'s result and is not measured savings.')
        setRunning(false)
        return
      }
      const chosen = multiPolicyMode ? selectedPolicies : selectedPolicy ? [selectedPolicy] : []
      const paymentKeys = new Set(syntheticIdentity?.supported_what_if_keys || ['mppr', 'sos', 'ptp', 'mue', 'therapy', 'infusion'])
      const policyKeyOf = (policy: Policy | null | undefined) =>
        String((policy as any)?.metadata?.policy_key || (policy as any)?.policy_key || '')
      const isPopulationWhatIfPolicy = (policy: Policy | null | undefined) =>
        String((policy as { description?: string } | null)?.description || '').includes('Synthetic illustration')
        || (syntheticIdentity?.what_if_engine === 'LONGITUDINAL_PAYMENT' && paymentKeys.has(policyKeyOf(policy)))
      if (chosen.some(isPopulationWhatIfPolicy)) {
        if (!syntheticIdentity?.synthetic) {
          setError(
            'This application instance is not connected to the synthetic population. A legacy scenario is not that population’s result.',
          )
          setRunning(false)
          return
        }
        if (chosen.length > 1) {
          setError(
            'Ordered composition of more than one policy on the same claim line is not supported. Run one payment policy at a time so a shared line is not counted twice.',
          )
          setRunning(false)
          return
        }
        if (syntheticIdentity?.what_if_engine === 'LONGITUDINAL_PAYMENT' && !paymentKeys.has(policyKeyOf(chosen[0]))) {
          setError('Longitudinal what-if supports only the six payment-rule policies. A simulated difference is not measured savings.')
          setRunning(false)
          return
        }
        const populationResult = await apiClient.runSyntheticWhatIf({
          policy_id: chosen[0].id,
          parameters: syntheticParams,
        })
        setSyntheticResult({ ...populationResult, scenario_name: finalName })
        setScenarioResult(null)
        setActiveTab('results')
        return
      }
      
      if (multiPolicyMode && selectedPolicies.length > 1) {
        // Multi-policy scenario: run simulations for each policy and combine results
        const policyResults = []
        const totalPolicies = selectedPolicies.length
        
        // Initialize progress tracking
        setMultiPolicyProgress({
          current: 1,
          total: totalPolicies,
          currentPolicyName: selectedPolicies[0]?.name || 'Unknown',
          completed: 0,
        })
        
        for (let i = 0; i < selectedPolicies.length; i++) {
          const policy = selectedPolicies[i]
          try {
            // Update progress: starting new policy
            setMultiPolicyProgress({
              current: i + 1,
              total: totalPolicies,
              currentPolicyName: policy.name,
              completed: i,
            })
            
            const result = await apiClient.createSimulateAnalysis({
              policy_id: policy.id,
              scenario_params: scenarioParams,
              filters: baselineFilters,
            })
            
            // Poll for completion (what-if can take several minutes per policy)
            let analysis = result
            let attempts = 0
            const maxAttempts = 120 // ~10 min per policy at 5s interval

            while (analysis.status === 'PENDING' || analysis.status === 'RUNNING') {
              if (attempts >= maxAttempts) {
                throw new Error('Analysis timed out for this policy. Large datasets can take 10+ minutes.')
              }
              await new Promise(resolve => setTimeout(resolve, 5000))
              analysis = await apiClient.getAnalysis(analysis.id)
              attempts++
            }
            
            if (analysis.status === 'COMPLETED') {
              const results = await apiClient.getAnalysisResults(analysis.id, 'whatif_scenario')
              if (results.results) {
                const scenarioData = results.results.whatif_scenario || 
                                   results.results.WHATIF_SCENARIO ||
                                   results.results
                if (scenarioData) {
                  policyResults.push({
                    policy,
                    scenario: scenarioData,
                  })
                  
                  // Update progress: policy completed
                  setMultiPolicyProgress({
                    current: i + 1,
                    total: totalPolicies,
                    currentPolicyName: policy.name,
                    completed: i + 1,
                  })
                }
              }
            }
          } catch (err) {
            console.error(`Error simulating policy ${policy.id}:`, err)
            // Continue with other policies, but still update completed count
            setMultiPolicyProgress(prev => prev ? {
              ...prev,
              completed: prev.completed,
            } : null)
          }
        }
        
        // Combine results from multiple policies
        if (policyResults.length > 0) {
          // Update progress: combining results
          setMultiPolicyProgress(prev => prev ? {
            ...prev,
            currentPolicyName: 'Combining results...',
          } : null)
          
          const combinedResult = combineMultiPolicyResults(policyResults, finalName)
          setScenarioResult(combinedResult)
          
          // Clear progress indicator
          setMultiPolicyProgress(null)
          setActiveTab('results')
        } else {
          setMultiPolicyProgress(null)
          throw new Error('Failed to simulate any policies')
        }
      } else {
        // Single policy scenario (existing logic)
        const policy = multiPolicyMode ? selectedPolicies[0] : selectedPolicy!
        const result = await apiClient.createSimulateAnalysis({
          policy_id: policy.id,
          scenario_params: scenarioParams,
          filters: baselineFilters,
        })
        
        console.log('Simulation created:', result)
        
        // Check if result is already in response (synchronous completion)
        if (result.status === 'COMPLETED' && result.result) {
          console.log('Simulation completed synchronously, result:', result.result)
          const newScenario = {
            ...result.result,
            scenario_name: finalName,
            _analysis_id: result.id,
            _created_at: result.created_at,
          } as ScenarioResult & { _analysis_id: string; _created_at?: string }
          setScenarioResult(newScenario)
          setCurrentScenarioAnalysisId(result.id)
          setScenarios((prev) => {
            const exists = prev.some((s) => s.scenario_id === newScenario.scenario_id)
            return exists ? prev : [newScenario, ...prev]  // Add to front (most recent first)
          })
          setActiveTab('results')
          setRunning(false)
          loadScenarioAccuracy(selectedPolicy?.id, result.id)
          return
        }
        
        // Poll for results (if async). What-if with large claims can take 2–5+ minutes.
        let attempts = 0
        const maxAttempts = 450 // ~15 min at 2s interval (large claims / cold DB)
        const pollIntervalMs = 2000
        const workerHintAfterPolls = 15 // ~30s: show hint if Celery worker may not be running

        while (attempts < maxAttempts) {
          await new Promise(resolve => setTimeout(resolve, pollIntervalMs))
          
          try {
            const analysis = await apiClient.getAnalysis(result.id)
            if (attempts < 5 || attempts % 10 === 9) {
              console.log(`Polling attempt ${attempts + 1}: status = ${analysis.status}`)
            }
            if (attempts + 1 >= workerHintAfterPolls && analysis.status === 'PENDING') {
              setWorkerHint(
                'Simulation is still queued or starting. Large scopes can take several minutes on the server. If status stays PENDING for many minutes, check API logs or the analyses list—or run a Celery worker (./apps/worker/start_worker.sh) if your deployment uses UEPI_USE_CELERY_FOR_WHATIF_SIMULATION=true.'
              )
            }
            
            if (analysis.status === 'COMPLETED') {
              const results = await apiClient.getAnalysisResults(result.id, 'whatif_scenario')
              console.log('Analysis results:', results)
              
              let scenarioData = null
              
              // Try multiple result type formats
              if (results.results) {
                scenarioData = results.results.whatif_scenario || 
                              results.results.WHATIF_SCENARIO ||
                              results.results[Object.keys(results.results)[0]] // Get first result if available
              }
              
              // Also check if result is directly in response
              if (!scenarioData && (results.scenario_id || results.baseline_metrics)) {
                scenarioData = results
              }
              
              if (scenarioData) {
                console.log('Found scenario data:', scenarioData)
                const scenarioWithMeta = {
                  ...scenarioData,
                  scenario_name: scenarioData.scenario_name || finalName || `Scenario ${new Date().toLocaleString()}`,
                  _analysis_id: result.id,
                  _created_at: result.created_at,
                } as ScenarioResult & { _analysis_id: string; _created_at?: string }
                setScenarioResult(scenarioWithMeta)
                // Add to scenarios list for comparison (avoid duplicates)
                setScenarios((prev) => {
                  const exists = prev.some((s) => s.scenario_id === scenarioWithMeta.scenario_id)
                  return exists ? prev : [scenarioWithMeta, ...prev]  // Add to front (most recent first)
                })
                setActiveTab('results') // Switch to results tab
                setWorkerHint(null)
                break
              } else {
                console.warn('No scenario data found in results:', results)
              }
            } else if (analysis.status === 'FAILED') {
              setError(`Scenario simulation failed: ${analysis.error_message || 'Unknown error'}`)
              setWorkerHint(null)
              break
            }
          } catch (err: any) {
            if (attempts < 5 || attempts % 10 === 9) console.error('Error polling for results:', err)
            // Continue polling
          }
          
          attempts++
        }
        
        if (attempts >= maxAttempts) {
          setWorkerHint(null)
          setError(
            'Scenario simulation timed out. Check the analyses list for final status (runs can be slow for large policies). If your API is configured to use Celery for simulations (UEPI_USE_CELERY_FOR_WHATIF_SIMULATION=true), ensure the worker is running: ./apps/worker/start_worker.sh with Redis.'
          )
        }
      }
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to run scenario')
    } finally {
      setRunning(false)
      setMultiPolicyProgress(null) // Clear progress on completion or error
    }
  }

  const handleLeverAdjustment = (leverId: string, parameter: string, value: any) => {
    setScenarioParams(prev => ({
      ...prev,
      lever_adjustments: {
        ...prev.lever_adjustments,
        [leverId]: {
          ...prev.lever_adjustments[leverId],
          [parameter]: value,
        },
      },
    }))
  }

  const handleElasticityAdjustment = (category: string, value: number) => {
    setScenarioParams(prev => ({
      ...prev,
      elasticity_adjustments: {
        ...prev.elasticity_adjustments,
        [category]: value,
      },
    }))
  }

  const formatCurrency = (value: number | null | undefined) => {
    if (value == null || Number.isNaN(value)) return 'Unavailable'
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2 }).format(value)
  }

  const formatPercent = (value: number | null | undefined) => {
    if (value == null || Number.isNaN(value)) return 'Unavailable'
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
  }

  const formatFixed = (value: number | null | undefined) => {
    if (value == null || Number.isNaN(value)) return 'Unavailable'
    return value.toFixed(2)
  }

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography
          variant="h4"
          component="h1"
          sx={{
            fontFamily: 'IBM Plex Sans, Inter, sans-serif',
            fontWeight: 600,
            mb: 1,
            color: healthForesightColors.neutral.dark,
          }}
        >
          What-If Scenarios
        </Typography>
        <Typography
          variant="body1"
          sx={{
            color: healthForesightColors.neutral.mid,
            lineHeight: 1.6,
            mb: 1,
          }}
        >
          Adjust policy parameters and examine projected impact before implementation.{' '}
          <Link component={RouterLink} to="/whatif/scenarios" underline="hover" sx={{ fontWeight: 500 }}>
            View all scenario runs
          </Link>
        </Typography>
        {syntheticIdentity?.what_if_engine === 'NOT_THIS_POPULATION' ? (
          <Alert severity="warning" sx={{ mt: 2 }} data-testid="synthetic-whatif-other-population">
            {syntheticIdentity.honesty || 'A legacy scenario is not measured savings.'}
          </Alert>
        ) : syntheticIdentity?.what_if_engine === 'LONGITUDINAL_PAYMENT' ? (
          <Alert severity="info" sx={{ mt: 2 }} data-testid="synthetic-whatif-longitudinal">
            {syntheticIdentity.honesty || 'Payment what-if runs on POST-period longitudinal lines. A simulated difference is not measured savings.'}
          </Alert>
        ) : syntheticIdentity?.synthetic ? (
          <Alert severity="info" sx={{ mt: 2 }} data-testid="synthetic-whatif-ready">
            What-if runs on the synthetic population in database {syntheticIdentity.database_name}:{' '}
            {Number(syntheticIdentity.covered_lives || 0).toLocaleString()} covered lives and{' '}
            {syntheticIdentity.member_months == null
              ? 'unavailable'
              : Number(syntheticIdentity.member_months).toLocaleString(undefined, { maximumFractionDigits: 3 })}{' '}
            enrolled member-months. Each run uses that policy&apos;s own claim lines and the same payment engine as the
            population simulation. A simulated difference is not measured savings. MRI prior authorization, NCD 220.2,
            and LCD L34425 stay unavailable for an outcome. More than one policy at a time is rejected.
          </Alert>
        ) : policies.some((policy) => String((policy as { description?: string }).description || '').includes('Synthetic illustration')) ? (
          <Alert severity="info" sx={{ mt: 2 }}>
            What-if does not calculate the synthetic payer population. No legacy scenario on this page is that population&apos;s result.
          </Alert>
        ) : null}
      </Box>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 3, gap: 1 }}>
          {scenarioResult && scenarios.length > 0 && (
            <Button
              variant="outlined"
              onClick={() => {
                // Switch to comparison tab
                setActiveTab('compare')
              }}
            >
              View Comparison ({scenarios.length})
            </Button>
          )}
          <Button
            variant="contained"
            startIcon={running ? <CircularProgress size={20} /> : <RunIcon />}
            onClick={handleRunScenario}
            disabled={!selectedPolicy || running}
          >
            {running ? 'Running...' : 'Run Scenario'}
          </Button>
          
          {/* Scenario Name Dialog */}
          <Dialog open={nameDialogOpen} onClose={() => setNameDialogOpen(false)}>
            <DialogTitle>Name Your Scenario</DialogTitle>
            <DialogContent>
              <TextField
                autoFocus
                margin="dense"
                label="Scenario Name"
                fullWidth
                variant="outlined"
                value={scenarioName}
                onChange={(e) => setScenarioName(e.target.value)}
                placeholder="e.g., Aggressive Prior Auth, Baseline Comparison, etc."
                sx={{ mt: 1, minWidth: 400 }}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && scenarioName.trim()) {
                    handleRunScenarioConfirmed()
                  }
                }}
              />
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Give your scenario a descriptive name to easily identify it later in comparisons.
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Large datasets may take 2–5 minutes. The page will update automatically when the run completes.
              </Typography>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => {
                setNameDialogOpen(false)
                setScenarioName('')
              }}>
                Cancel
              </Button>
              <Button 
                onClick={handleRunScenarioConfirmed}
                variant="contained"
              >
                Run Scenario
              </Button>
            </DialogActions>
          </Dialog>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {running && !multiPolicyProgress && (
        <Alert severity="info" sx={{ mb: 2 }} icon={<CircularProgress size={20} />}>
          What-if analysis is running. This may take 2–5 minutes for large datasets. Please wait — the page will update when complete.
        </Alert>
      )}
      {workerHint && (
        <Alert severity="warning" sx={{ mb: 2 }} onClose={() => setWorkerHint(null)}>
          {workerHint}
        </Alert>
      )}

      {openingHistoricalRun && loading && (
        <Alert severity="info" sx={{ mb: 2 }} icon={<CircularProgress size={20} />}>
          Loading saved what-if results for this run…
        </Alert>
      )}

      {/* Build visible tabs array */}
      {(() => {
        const visibleTabs: Array<{ label: string; key: typeof activeTab }> = []
        // When opening a past run, Results first so we never strand the user on Configure
        if (scenarioResult || syntheticResult || openingHistoricalRun) {
          visibleTabs.push({ label: 'Results', key: 'results' })
        }
        visibleTabs.push({ label: 'Configure Scenario', key: 'configure' })
        if (selectedPolicy) {
          visibleTabs.push({ label: 'Elasticity Curves', key: 'elasticity' })
        }
        if (scenarios.length > 0) {
          visibleTabs.push({ label: `Compare Scenarios (${scenarios.length})`, key: 'compare' })
        }
        if (scenarioResult && scenarioResult.sensitivity_analysis) {
          visibleTabs.push({ label: 'Sensitivity Analysis', key: 'sensitivity' })
        }
        if (scenarioAccuracy.length > 0 || scenarioLinks.length > 0) {
          visibleTabs.push({ label: `Accuracy (${scenarioAccuracy.length})`, key: 'accuracy' })
        }
        
        const currentTabIndex = visibleTabs.findIndex(t => t.key === activeTab)
        
        return (
          <Tabs 
            value={currentTabIndex >= 0 ? currentTabIndex : 0}
            onChange={(_, newValue) => {
              if (newValue >= 0 && newValue < visibleTabs.length) {
                setActiveTab(visibleTabs[newValue].key)
              }
            }}
            sx={{ mb: 3 }}
          >
            {visibleTabs.map((tab) => (
              <Tab 
                key={tab.key}
                label={tab.label}
              />
            ))}
          </Tabs>
        )
      })()}

      {activeTab === 'results' && openingHistoricalRun && loading && !scenarioResult && (
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, py: 6 }}>
          <CircularProgress />
          <Typography color="text.secondary">Loading past what-if charts…</Typography>
        </Box>
      )}

      {activeTab === 'configure' && (
        <Grid container spacing={3} className="scenario-builder">
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                {!syntheticIdentity?.synthetic && policiesWithClaimCounts && policiesWithClaimCounts.length > 0 && policiesWithClaimCounts[0].claim_count > 0 && (
                  <Alert severity="info" sx={{ mb: 2 }} action={
                    <Button
                      color="inherit"
                      size="small"
                      onClick={() => {
                        const top = policiesWithClaimCounts[0]
                        const policy = policies.find(p => p.id === top.id)
                        if (policy) {
                          setSelectedPolicy(policy)
                          if (multiPolicyMode) setSelectedPolicies([policy])
                        }
                      }}
                    >
                      Use this policy
                    </Button>
                  }>
                    <strong>Policy with most data:</strong> {policiesWithClaimCounts[0].name} ({policiesWithClaimCounts[0].claim_count.toLocaleString()} claims in last 12 months). Use for what-if to get non-zero results.
                  </Alert>
                )}
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">
                    Select {multiPolicyMode ? 'Policies' : 'Policy'}
                  </Typography>
                  <Chip
                    label={multiPolicyMode ? 'Multi-Policy Mode' : 'Single Policy Mode'}
                    color={multiPolicyMode ? 'primary' : 'default'}
                    onClick={() => {
                      setMultiPolicyMode(!multiPolicyMode)
                      if (!multiPolicyMode) {
                        // Switching to multi-policy mode
                        if (selectedPolicy) {
                          setSelectedPolicies([selectedPolicy])
                        }
                      } else {
                        // Switching to single policy mode
                        if (selectedPolicies.length > 0) {
                          setSelectedPolicy(selectedPolicies[0])
                        }
                        setSelectedPolicies([])
                      }
                    }}
                    clickable
                  />
                </Box>
                {multiPolicyMode ? (
                  <Autocomplete
                    multiple
                    fullWidth
                    size="small"
                    sx={{ mb: 2 }}
                    options={[...policies].sort((a, b) => String(a.name).localeCompare(String(b.name)))}
                    value={selectedPolicies}
                    onChange={(_e, selected) => {
                      setSelectedPolicies(selected)
                      setSelectedPolicy(selected[0] || null)
                    }}
                    getOptionLabel={(p) => `${p.name} (${p.policy_type})`}
                    isOptionEqualToValue={(a, b) => a.id === b.id}
                    renderInput={(params) => (
                      <TextField {...params} label="Policies" placeholder="Search & select policies…" />
                    )}
                    renderTags={(value, getTagProps) =>
                      value.map((policy, index) => (
                        <Chip
                          {...getTagProps({ index })}
                          key={policy.id}
                          label={`${policy.name} (${policy.policy_type})`}
                          size="small"
                        />
                      ))
                    }
                  />
                ) : (
                  <Box sx={{ mb: 2 }}>
                    <PolicyAutocomplete
                      policies={policies}
                      value={selectedPolicy?.id || ''}
                      label="Policy"
                      allowAll={false}
                      onChange={(id) => {
                        const policy = policies.find((p) => p.id === id)
                        setSelectedPolicy(policy || null)
                      }}
                    />
                  </Box>
                )}
                {syntheticIdentity?.synthetic && selectedPolicy && !multiPolicyMode && (
                  <SyntheticParameterFields
                    policyName={selectedPolicy.name}
                    params={syntheticParams}
                    onChange={setSyntheticParams}
                  />
                )}
                {multiPolicyMode && selectedPolicies.length > 1 && (
                  <Alert severity="info" sx={{ mt: 2 }}>
                    {selectedPolicies.length} policies selected. The scenario will simulate the combined impact of all selected policies.
                  </Alert>
                )}
                
                {/* Multi-Policy Progress Indicator */}
                {multiPolicyProgress && running && (
                  <Card sx={{ mt: 2, bgcolor: 'primary.main', color: 'primary.contrastText' }}>
                    <CardContent>
                      <Typography variant="h6" gutterBottom sx={{ color: 'primary.contrastText' }}>
                        Processing Multi-Policy Scenario
                      </Typography>
                      <Box sx={{ mb: 2 }}>
                        <LinearProgress 
                          variant="determinate" 
                          value={(multiPolicyProgress.completed / multiPolicyProgress.total) * 100} 
                          sx={{ 
                            height: 8, 
                            borderRadius: 4, 
                            mb: 1,
                            bgcolor: 'rgba(255, 255, 255, 0.3)',
                            '& .MuiLinearProgress-bar': {
                              bgcolor: 'rgba(255, 255, 255, 0.9)'
                            }
                          }}
                        />
                        <Typography variant="body2" sx={{ mt: 1, color: 'primary.contrastText' }}>
                          {multiPolicyProgress.completed} of {multiPolicyProgress.total} policies completed
                        </Typography>
                      </Box>
                      <Typography variant="body2" sx={{ fontStyle: 'italic', color: 'primary.contrastText' }}>
                        Currently processing: <strong>{multiPolicyProgress.currentPolicyName}</strong>
                        {' '}({multiPolicyProgress.current} of {multiPolicyProgress.total})
                      </Typography>
                    </CardContent>
                  </Card>
                )}

                {selectedPolicy && selectedPolicy.policy_logic && (
                  <Box sx={{ mt: 3 }}>
                    <Typography variant="subtitle1" gutterBottom>
                      Policy Levers
                    </Typography>
                    {selectedPolicy.policy_logic.levers?.map((lever: any, idx: number) => {
                      const leverId = `${lever.lever_type}_${idx}`
                      return (
                        <Accordion key={leverId} sx={{ mt: 1 }}>
                          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                            <Typography>{lever.lever_type.replace(/_/g, ' ')}</Typography>
                          </AccordionSummary>
                          <AccordionDetails>
                            {lever.lever_type === 'PRIOR_AUTH' && (
                              <Box>
                                <Typography variant="body2" gutterBottom>
                                  Requires PA: {lever.config?.requires_pa ? 'Yes' : 'No'}
                                </Typography>
                                <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                                  <Typography variant="body2" sx={{ mr: 1 }}>
                                    Override Allowed:
                                  </Typography>
                                  <Checkbox
                                    checked={lever.config?.override_allowed || false}
                                    onChange={(e) => handleLeverAdjustment(leverId, 'override_allowed', e.target.checked)}
                                    size="small"
                                  />
                                </Box>
                              </Box>
                            )}
                            {lever.lever_type === 'COST_SHARING' && (
                              <Box>
                                <Typography variant="body2" gutterBottom>
                                  Copay Adjustment
                                </Typography>
                                <Slider
                                  value={lever.config?.copay || 0}
                                  onChange={(_, value) => handleLeverAdjustment(leverId, 'copay', value)}
                                  min={0}
                                  max={200}
                                  step={5}
                                  marks
                                  valueLabelDisplay="auto"
                                  sx={{ mt: 2 }}
                                />
                                <Typography variant="body2" gutterBottom sx={{ mt: 2 }}>
                                  Coinsurance: {(lever.config?.coinsurance || 0) * 100}%
                                </Typography>
                                <Slider
                                  value={(lever.config?.coinsurance || 0) * 100}
                                  onChange={(_, value) => handleLeverAdjustment(leverId, 'coinsurance', (value as number) / 100)}
                                  min={0}
                                  max={50}
                                  step={1}
                                  marks
                                  valueLabelDisplay="auto"
                                />
                              </Box>
                            )}
                            {lever.lever_type === 'DURATION_FREQUENCY_LIMIT' && (
                              <Box>
                                <Typography variant="body2" gutterBottom>
                                  Max Visits
                                </Typography>
                                <TextField
                                  type="number"
                                  value={lever.config?.max_visits || 0}
                                  onChange={(e) => handleLeverAdjustment(leverId, 'max_visits', parseInt(e.target.value))}
                                  size="small"
                                  fullWidth
                                />
                              </Box>
                            )}
                          </AccordionDetails>
                        </Accordion>
                      )
                    })}
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Environmental Variables
                </Typography>
                
                <Box sx={{ mt: 2 }}>
                  <Typography gutterBottom>
                    Member Count Multiplier: {scenarioParams.member_count_multiplier.toFixed(2)}x
                  </Typography>
                  <Slider
                    value={scenarioParams.member_count_multiplier}
                    onChange={(_, value) => setScenarioParams(prev => ({ ...prev, member_count_multiplier: value as number }))}
                    min={0.5}
                    max={2.0}
                    step={0.1}
                    marks={[
                      { value: 0.5, label: '0.5x' },
                      { value: 1.0, label: '1.0x' },
                      { value: 1.5, label: '1.5x' },
                      { value: 2.0, label: '2.0x' },
                    ]}
                    valueLabelDisplay="auto"
                  />
                </Box>

                <Box sx={{ mt: 3 }}>
                  <Typography gutterBottom>
                    Utilization Trend: {formatPercent(scenarioParams.utilization_trend)} per month
                  </Typography>
                  <Slider
                    value={scenarioParams.utilization_trend}
                    onChange={(_, value) => setScenarioParams(prev => ({ ...prev, utilization_trend: value as number }))}
                    min={-5}
                    max={5}
                    step={0.1}
                    marks
                    valueLabelDisplay="auto"
                  />
                </Box>

                <Box sx={{ mt: 3 }}>
                  <Typography gutterBottom>
                    Cost Inflation: {(scenarioParams.cost_inflation * 100).toFixed(2)}% per month
                  </Typography>
                  <Slider
                    value={scenarioParams.cost_inflation * 100}
                    onChange={(_, value) => setScenarioParams(prev => ({ ...prev, cost_inflation: (value as number) / 100 }))}
                    min={0}
                    max={5}
                    step={0.1}
                    marks
                    valueLabelDisplay="auto"
                  />
                </Box>

                <Box sx={{ mt: 3 }}>
                  <Typography gutterBottom>
                    Projection Horizon: {scenarioParams.projection_months} months
                  </Typography>
                  <Slider
                    value={scenarioParams.projection_months}
                    onChange={(_, value) => setScenarioParams(prev => ({ ...prev, projection_months: value as number }))}
                    min={1}
                    max={24}
                    step={1}
                    marks={[
                      { value: 1, label: '1m' },
                      { value: 6, label: '6m' },
                      { value: 12, label: '12m' },
                      { value: 24, label: '24m' },
                    ]}
                    valueLabelDisplay="auto"
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {activeTab === 'elasticity' && (
        <Box>
          {elasticityLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : elasticityData ? (
            <ElasticityCurvesDisplay
              elasticityData={elasticityData}
              selectedCategory={selectedCategory || undefined}
              onCategoryChange={(category) => setSelectedCategory(category)}
            />
          ) : (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Elasticity Curves
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  Elasticity analysis models utilization sensitivity to policy friction. Create an elasticity analysis for {selectedPolicy?.name || 'the selected policy'} to visualize elasticity curves. This usually completes within 1–2 minutes.
                </Typography>
                <Button
                  variant="contained"
                  onClick={async () => {
                    if (!selectedPolicy) {
                      setError('Please select a policy first')
                      return
                    }
                    try {
                      setElasticityLoading(true)
                      setError(null)
                      const result = await apiClient.createElasticityAnalysis({
                        policy_id: selectedPolicy.id,
                        service_categories: undefined, // Will model all categories
                      })
                      // Poll for results (large tenants / Celery queue: allow up to ~8 min)
                      let attempts = 0
                      const maxAttempts = 240
                      while (attempts < maxAttempts) {
                        await new Promise((resolve) => setTimeout(resolve, 2000))
                        try {
                          const analysis = await apiClient.getAnalysis(result.id)
                          if (analysis.status === 'COMPLETED') {
                            const results = await apiClient.getAnalysisResults(result.id, 'ELASTICITY')
                            const payload = results.results?.ELASTICITY ?? (results.service_categories ? results : results.results?.[Object.keys(results.results || {})[0]])
                            if (payload?.service_categories && Object.keys(payload.service_categories).length > 0) {
                              setElasticityData(payload)
                              setError(null)
                              break
                            }
                            setError(
                              'Elasticity finished but no curve data was returned. Refresh the page or contact support if this persists.',
                            )
                            break
                          } else if (analysis.status === 'FAILED') {
                            setError(analysis.error_message || 'Elasticity analysis failed')
                            break
                          }
                        } catch (err) {
                          // Continue polling
                        }
                        attempts++
                      }
                      if (attempts >= maxAttempts) {
                        setError('Elasticity analysis timed out')
                      }
                    } catch (err: any) {
                      setError(err.detail || err.message || 'Failed to create elasticity analysis')
                    } finally {
                      setElasticityLoading(false)
                    }
                  }}
                  disabled={!selectedPolicy || elasticityLoading}
                  startIcon={elasticityLoading ? <CircularProgress size={20} /> : <AnalyticsIcon />}
                >
                  {elasticityLoading ? 'Creating Analysis...' : 'Create Elasticity Analysis'}
                </Button>
              </CardContent>
            </Card>
          )}
        </Box>
      )}

      {activeTab === 'results' && syntheticResult && (
        <SyntheticWhatIfResult result={syntheticResult} formatCurrency={formatCurrency} />
      )}

      {activeTab === 'results' && scenarioResult && isPaymentRuleWhatIf(scenarioResult) && (
        <PaymentRuleWhatIfResult result={scenarioResult} formatCurrency={formatCurrency} />
      )}

      {activeTab === 'results' && scenarioResult && !isPaymentRuleWhatIf(scenarioResult) && (
        <Grid container spacing={3}>
          {/* Scenario Summary Header */}
          <Grid item xs={12}>
            <Card sx={{ mb: 3, bgcolor: 'primary.main', color: 'primary.contrastText' }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Box>
                    <Typography variant="h5" gutterBottom sx={{ color: 'primary.contrastText', fontWeight: 600 }}>
                      {scenarioResult.scenario_name || 'Unnamed Scenario'}
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                      {multiPolicyMode && selectedPolicies.length > 1 ? (
                        <>
                          <Chip 
                            label={`${selectedPolicies.length} Policies`} 
                            size="small" 
                            sx={{ bgcolor: 'rgba(255, 255, 255, 0.2)', color: 'primary.contrastText' }}
                          />
                          {selectedPolicies.map((policy) => (
                            <Chip 
                              key={policy.id}
                              label={policy.name} 
                              size="small" 
                              sx={{ bgcolor: 'rgba(255, 255, 255, 0.2)', color: 'primary.contrastText' }}
                            />
                          ))}
                        </>
                      ) : selectedPolicy ? (
                        <Chip 
                          label={selectedPolicy.name} 
                          size="small" 
                          sx={{ bgcolor: 'rgba(255, 255, 255, 0.2)', color: 'primary.contrastText' }}
                        />
                      ) : null}
                      {(scenarioResult as any)._created_at && (
                        <Chip 
                          label={new Date((scenarioResult as any)._created_at).toLocaleString()} 
                          size="small" 
                          sx={{ bgcolor: 'rgba(255, 255, 255, 0.2)', color: 'primary.contrastText' }}
                          icon={<span>📅</span>}
                        />
                      )}
                      {(scenarioResult as any)._analysis_id && (
                        <Chip 
                          label={`ID: ${(scenarioResult as any)._analysis_id.substring(0, 8)}...`} 
                          size="small" 
                          sx={{ bgcolor: 'rgba(255, 255, 255, 0.2)', color: 'primary.contrastText' }}
                        />
                      )}
                    </Box>
                  </Box>
                  {scenarioResult.confidence_score !== undefined && (
                    <Box sx={{ textAlign: 'right' }}>
                      <Typography variant="body2" sx={{ color: 'primary.contrastText', mb: 0.5 }}>
                        Confidence (reliability of projection)
                      </Typography>
                      <Typography 
                        variant="h4" 
                        sx={{ 
                          color: scenarioResult.confidence_score == null ? 'primary.contrastText' :
                                 (scenarioResult.confidence_score <= 1 ? scenarioResult.confidence_score * 100 : scenarioResult.confidence_score) >= 80 ? 'success.light' :
                                 (scenarioResult.confidence_score <= 1 ? scenarioResult.confidence_score * 100 : scenarioResult.confidence_score) >= 60 ? 'warning.light' :
                                 (scenarioResult.confidence_score <= 1 ? scenarioResult.confidence_score * 100 : scenarioResult.confidence_score) >= 40 ? 'info.light' : 'error.light',
                          fontWeight: 600
                        }}
                      >
                        {formatConfidencePct(scenarioResult.confidence_score)}
                      </Typography>
                    </Box>
                  )}
                </Box>
                
                {/* Scenario Parameters Summary */}
                <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid rgba(255, 255, 255, 0.2)' }}>
                  <Typography variant="subtitle2" sx={{ color: 'primary.contrastText', mb: 1, opacity: 0.9 }}>
                    Scenario Parameters
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                    <Typography variant="body2" sx={{ color: 'primary.contrastText', opacity: 0.9 }}>
                      <strong>Projection Horizon:</strong> {scenarioParams.projection_months} months
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'primary.contrastText', opacity: 0.9 }}>
                      <strong>Cost Inflation:</strong> {(scenarioParams.cost_inflation * 100).toFixed(1)}%
                    </Typography>
                    {scenarioParams.member_count_multiplier !== 1.0 && (
                      <Typography variant="body2" sx={{ color: 'primary.contrastText', opacity: 0.9 }}>
                        <strong>Member Count:</strong> {scenarioParams.member_count_multiplier.toFixed(2)}x
                      </Typography>
                    )}
                    {scenarioParams.utilization_trend !== 0.0 && (
                      <Typography variant="body2" sx={{ color: 'primary.contrastText', opacity: 0.9 }}>
                        <strong>Utilization Trend:</strong> {formatPercent(scenarioParams.utilization_trend)}/month
                      </Typography>
                    )}
                    {Object.keys(scenarioParams.lever_adjustments || {}).length > 0 && (
                      <Typography variant="body2" sx={{ color: 'primary.contrastText', opacity: 0.9 }}>
                        <strong>Lever Adjustments:</strong> {Object.keys(scenarioParams.lever_adjustments).length} active
                      </Typography>
                    )}
                    {Object.keys(scenarioParams.elasticity_adjustments || {}).length > 0 && (
                      <Typography variant="body2" sx={{ color: 'primary.contrastText', opacity: 0.9 }}>
                        <strong>Elasticity Adjustments:</strong> {Object.keys(scenarioParams.elasticity_adjustments).length} categories
                      </Typography>
                    )}
                    {scenarioResult.impact_metrics?.tradeoff_analysis && (
                      <Typography variant="body2" sx={{ color: 'primary.contrastText', opacity: 0.9 }}>
                        <strong>Efficiency Score (cost vs utilization tradeoff):</strong> {scenarioResult.impact_metrics.tradeoff_analysis.efficiency_score.toFixed(0)}%
                      </Typography>
                    )}
                  </Box>
                  
                  {/* Confidence Score Explanation */}
                  {scenarioResult.confidence_score !== undefined &&
                    (scenarioResult.confidence_score <= 1
                      ? scenarioResult.confidence_score * 100
                      : scenarioResult.confidence_score) < 60 && (
                    <Alert 
                      severity="info" 
                      sx={{ 
                        mt: 2, 
                        bgcolor: 'rgba(255, 255, 255, 0.1)',
                        color: 'primary.contrastText',
                        '& .MuiAlert-icon': { color: 'primary.contrastText' }
                      }}
                    >
                      <Typography variant="body2" sx={{ color: 'primary.contrastText', fontWeight: 600, mb: 0.5 }}>
                        {scenarioResult.confidence_score == null
                          ? 'Confidence unavailable'
                          : `Low Confidence Score (${formatConfidencePct(scenarioResult.confidence_score)})`}
                      </Typography>
                      <Typography variant="body2" sx={{ color: 'primary.contrastText', opacity: 0.9, fontSize: '0.85rem' }}>
                        To improve: Use shorter projection horizon (≤12 months), ensure sufficient baseline data (500+ claims), and run elasticity analysis for more accurate models.
                      </Typography>
                    </Alert>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={8}>
            {/* Explain why all numbers are 0 when no baseline data */}
            {scenarioResult.baseline_metrics?.claim_count === 0 && scenarioResult.projected_metrics?.claim_count === 0 && (
              <Alert severity="info" sx={{ mb: 2 }}>
                All metrics are 0 because no baseline or claims data is loaded for this policy. Load baseline or claims data (Ingestion / Data Health) to see non-zero projections.
              </Alert>
            )}
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Impact Summary
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6} md={4}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="body2" color="text.secondary">
                        Claim lines per 1,000 claimants (not enrolled utilization)
                      </Typography>
                      <Typography variant="h5" color={scenarioResult.impact_metrics?.percent_changes?.utilization_per_1k == null ? 'text.secondary' : scenarioResult.impact_metrics.percent_changes.utilization_per_1k < 0 ? 'success.main' : 'error.main'}>
                        {formatPercent(scenarioResult.impact_metrics?.percent_changes?.utilization_per_1k)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {formatFixed(scenarioResult.baseline_metrics?.utilization_per_1k)} → {formatFixed(scenarioResult.projected_metrics?.utilization_per_1k)}
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} sm={6} md={4}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="body2" color="text.secondary">
                        Allowed $ / claimant-month (not enrolled PMPM)
                      </Typography>
                      <Typography variant="h5" color={scenarioResult.impact_metrics?.percent_changes?.allowed_pmpm == null ? 'text.secondary' : scenarioResult.impact_metrics.percent_changes.allowed_pmpm < 0 ? 'success.main' : 'error.main'}>
                        {formatPercent(scenarioResult.impact_metrics?.percent_changes?.allowed_pmpm)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {formatCurrency(scenarioResult.baseline_metrics?.allowed_pmpm)} → {formatCurrency(scenarioResult.projected_metrics?.allowed_pmpm)}
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} sm={6} md={4}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="body2" color="text.secondary">
                        Paid $ / claimant-month (not enrolled PMPM)
                      </Typography>
                      <Typography variant="h5" color={scenarioResult.impact_metrics?.percent_changes?.paid_pmpm == null ? 'text.secondary' : scenarioResult.impact_metrics.percent_changes.paid_pmpm < 0 ? 'success.main' : 'error.main'}>
                        {formatPercent(scenarioResult.impact_metrics?.percent_changes?.paid_pmpm)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {formatCurrency(scenarioResult.baseline_metrics?.paid_pmpm)} → {formatCurrency(scenarioResult.projected_metrics?.paid_pmpm)}
                      </Typography>
                    </Paper>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>

            {/* Tradeoff Analysis */}
            {scenarioResult.impact_metrics?.tradeoff_analysis && (
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Tradeoff Analysis: Cost vs Utilization
                  </Typography>
                  <Grid container spacing={3} sx={{ mt: 1 }}>
                    <Grid item xs={12} md={6}>
                      <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'background.paper' }}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Efficiency Score
                        </Typography>
                        <Typography 
                          variant="h3" 
                          sx={{ 
                            color: scenarioResult.impact_metrics.tradeoff_analysis.efficiency_score >= 80 ? 'success.main' :
                                   scenarioResult.impact_metrics.tradeoff_analysis.efficiency_score >= 60 ? 'warning.main' :
                                   scenarioResult.impact_metrics.tradeoff_analysis.efficiency_score >= 40 ? 'info.main' : 'error.main',
                            fontWeight: 600,
                          }}
                        >
                          {scenarioResult.impact_metrics.tradeoff_analysis.efficiency_score.toFixed(0)}
                        </Typography>
                        <Chip 
                          label={scenarioResult.impact_metrics.tradeoff_analysis.efficiency_category}
                          color={
                            scenarioResult.impact_metrics.tradeoff_analysis.efficiency_category === 'HIGH' ? 'success' :
                            scenarioResult.impact_metrics.tradeoff_analysis.efficiency_category === 'MEDIUM' ? 'warning' :
                            scenarioResult.impact_metrics.tradeoff_analysis.efficiency_category === 'LOW' ? 'info' : 'error'
                          }
                          size="small"
                          sx={{ mt: 1 }}
                        />
                      </Paper>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Paper sx={{ p: 2 }}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Tradeoff Ratio
                        </Typography>
                        <Typography variant="h6">
                          {scenarioResult.impact_metrics.tradeoff_analysis.tradeoff_ratio.toFixed(2)}%
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                          Cost change per 1% utilization change
                        </Typography>
                        <Typography variant="body2" sx={{ mt: 2, fontStyle: 'italic' }}>
                          {scenarioResult.impact_metrics.tradeoff_analysis.interpretation}
                        </Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={12}>
                      <Paper sx={{ p: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Impact Breakdown
                        </Typography>
                        <Grid container spacing={2}>
                          <Grid item xs={6}>
                            <Typography variant="body2" color="text.secondary">
                              Utilization Change
                            </Typography>
                            <Typography 
                              variant="h6" 
                              color={scenarioResult.impact_metrics.tradeoff_analysis.utilization_change_pct < 0 ? 'success.main' : 'error.main'}
                            >
                              {formatPercent(scenarioResult.impact_metrics.tradeoff_analysis.utilization_change_pct)}
                            </Typography>
                          </Grid>
                          <Grid item xs={6}>
                            <Typography variant="body2" color="text.secondary">
                              Cost Change
                            </Typography>
                            <Typography 
                              variant="h6" 
                              color={scenarioResult.impact_metrics.tradeoff_analysis.cost_change_pct < 0 ? 'success.main' : 'error.main'}
                            >
                              {formatPercent(scenarioResult.impact_metrics.tradeoff_analysis.cost_change_pct)}
                            </Typography>
                          </Grid>
                        </Grid>
                      </Paper>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            )}

            {/* Risk Analysis */}
            {scenarioResult.impact_metrics?.risk_analysis && (
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Risk Analysis
                  </Typography>
                  <Box sx={{ mb: 2 }}>
                    <Chip 
                      label={`Risk Level: ${scenarioResult.impact_metrics.risk_analysis.risk_level}`}
                      color={
                        scenarioResult.impact_metrics.risk_analysis.risk_level === 'HIGH' ? 'error' :
                        scenarioResult.impact_metrics.risk_analysis.risk_level === 'MEDIUM' ? 'warning' :
                        scenarioResult.impact_metrics.risk_analysis.risk_level === 'LOW' ? 'info' : 'success'
                      }
                      sx={{ mb: 2 }}
                    />
                    <Typography variant="body2" color="text.secondary">
                      {scenarioResult.impact_metrics.risk_analysis.risk_summary}
                    </Typography>
                  </Box>
                  
                  <Grid container spacing={3} sx={{ mt: 1 }}>
                    <Grid item xs={12} md={6}>
                      <Paper sx={{ p: 2, border: '2px solid', borderColor: 'error.main' }}>
                        <Typography variant="subtitle1" gutterBottom color="error.main">
                          Worst-Case Scenario
                        </Typography>
                        <Table size="small">
                          <TableBody>
                            <TableRow>
                              <TableCell>Claim lines per 1,000 claimants (not enrolled utilization)</TableCell>
                              <TableCell align="right">
                                {formatFixed(scenarioResult.impact_metrics.risk_analysis.worst_case?.utilization_per_1k)}
                                {' '}
                                <Typography component="span" variant="caption" color="error.main">
                                  ({formatPercent(scenarioResult.impact_metrics.risk_analysis.worst_case?.utilization_change_pct)})
                                </Typography>
                              </TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>Paid $ / claimant-month (not enrolled PMPM)</TableCell>
                              <TableCell align="right">
                                {formatCurrency(scenarioResult.impact_metrics.risk_analysis.worst_case?.cost_pmpm)}
                                {' '}
                                <Typography component="span" variant="caption" color="error.main">
                                  ({formatPercent(scenarioResult.impact_metrics.risk_analysis.worst_case?.cost_change_pct)})
                                </Typography>
                              </TableCell>
                            </TableRow>
                          </TableBody>
                        </Table>
                      </Paper>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Paper sx={{ p: 2, border: '2px solid', borderColor: 'success.main' }}>
                        <Typography variant="subtitle1" gutterBottom color="success.main">
                          Best-Case Scenario
                        </Typography>
                        <Table size="small">
                          <TableBody>
                            <TableRow>
                              <TableCell>Claim lines per 1,000 claimants (not enrolled utilization)</TableCell>
                              <TableCell align="right">
                                {formatFixed(scenarioResult.impact_metrics.risk_analysis.best_case?.utilization_per_1k)}
                                {' '}
                                <Typography component="span" variant="caption" color="success.main">
                                  ({formatPercent(scenarioResult.impact_metrics.risk_analysis.best_case?.utilization_change_pct)})
                                </Typography>
                              </TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>Paid $ / claimant-month (not enrolled PMPM)</TableCell>
                              <TableCell align="right">
                                {formatCurrency(scenarioResult.impact_metrics.risk_analysis.best_case?.cost_pmpm)}
                                {' '}
                                <Typography component="span" variant="caption" color="success.main">
                                  ({formatPercent(scenarioResult.impact_metrics.risk_analysis.best_case?.cost_change_pct)})
                                </Typography>
                              </TableCell>
                            </TableRow>
                          </TableBody>
                        </Table>
                      </Paper>
                    </Grid>
                    {(scenarioResult.impact_metrics.risk_analysis.risk_factors?.length || 0) > 0 && (
                      <Grid item xs={12}>
                        <Paper sx={{ p: 2 }}>
                          <Typography variant="subtitle2" gutterBottom>
                            Risk Factors
                          </Typography>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                            {scenarioResult.impact_metrics.risk_analysis.risk_factors.map((factor, idx) => (
                              <Chip 
                                key={idx}
                                label={factor.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                                color="warning"
                                size="small"
                              />
                            ))}
                          </Box>
                        </Paper>
                      </Grid>
                    )}
                  </Grid>
                </CardContent>
              </Card>
            )}

            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Confidence Intervals (95%)
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Metric</TableCell>
                        <TableCell align="right">Baseline</TableCell>
                        <TableCell align="right">Projected</TableCell>
                        <TableCell align="right">Lower Bound</TableCell>
                        <TableCell align="right">Upper Bound</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      <TableRow>
                        <TableCell>Claim lines per 1,000 claimants (not enrolled utilization)</TableCell>
                        <TableCell align="right">{formatFixed(scenarioResult.baseline_metrics?.utilization_per_1k)}</TableCell>
                        <TableCell align="right">{formatFixed(scenarioResult.projected_metrics?.utilization_per_1k)}</TableCell>
                        <TableCell align="right">{formatFixed(scenarioResult.confidence_intervals?.utilization_per_1k?.[0])}</TableCell>
                        <TableCell align="right">{formatFixed(scenarioResult.confidence_intervals?.utilization_per_1k?.[1])}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Allowed $ / claimant-month (not enrolled PMPM)</TableCell>
                        <TableCell align="right">{formatCurrency(scenarioResult.baseline_metrics?.allowed_pmpm)}</TableCell>
                        <TableCell align="right">{formatCurrency(scenarioResult.projected_metrics?.allowed_pmpm)}</TableCell>
                        <TableCell align="right">{formatCurrency(scenarioResult.confidence_intervals?.allowed_pmpm?.[0])}</TableCell>
                        <TableCell align="right">{formatCurrency(scenarioResult.confidence_intervals?.allowed_pmpm?.[1])}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Paid $ / claimant-month (not enrolled PMPM)</TableCell>
                        <TableCell align="right">{formatCurrency(scenarioResult.baseline_metrics?.paid_pmpm)}</TableCell>
                        <TableCell align="right">{formatCurrency(scenarioResult.projected_metrics?.paid_pmpm)}</TableCell>
                        <TableCell align="right">{formatCurrency(scenarioResult.confidence_intervals?.paid_pmpm?.[0])}</TableCell>
                        <TableCell align="right">{formatCurrency(scenarioResult.confidence_intervals?.paid_pmpm?.[1])}</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <TrustPanel
              confidenceScore={scenarioResult.confidence_score}
              dataCoverage={{
                claimMonths: scenarioParams.projection_months,
              }}
              checks={[]}
              limitations={[
                "Projections based on historical patterns",
                "Does not account for external factors",
                "Elasticity estimates may vary",
              ]}
            />
          </Grid>
        </Grid>
      )}

      {activeTab === 'compare' && scenarios.length > 0 && (
        <Box className="scenario-comparison">
          <ScenarioComparison
            scenarios={scenarios}
            onRemoveScenario={(scenarioId) => {
              setScenarios((prev) => prev.filter((s) => s.scenario_id !== scenarioId))
              if (scenarioResult?.scenario_id === scenarioId) {
                setScenarioResult(scenarios.find((s) => s.scenario_id !== scenarioId) || null)
              }
            }}
            onRenameScenario={(scenarioId, name) => {
              setScenarios((prev) =>
                prev.map((s) => (s.scenario_id === scenarioId ? { ...s, scenario_name: name } : s))
              )
              if (scenarioResult?.scenario_id === scenarioId) {
                // Note: scenario_name is stored in scenarios array, not in scenarioResult
              // The ScenarioResult interface doesn\'t include scenario_name
              }
            }}
          />
        </Box>
      )}

      {activeTab === 'sensitivity' && scenarioResult && scenarioResult.sensitivity_analysis && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Sensitivity Analysis
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Impact of individual parameter adjustments
            </Typography>
            
            {scenarioResult.sensitivity_analysis.lever_adjustments && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Lever Adjustments
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Lever</TableCell>
                        <TableCell align="right">Estimated Impact</TableCell>
                        <TableCell>Parameters</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {Object.entries(scenarioResult.sensitivity_analysis.lever_adjustments).map(([leverId, data]: [string, any]) => (
                        <TableRow key={leverId}>
                          <TableCell>{leverId.replace(/_/g, ' ')}</TableCell>
                          <TableCell align="right">
                            {formatPercent(data.estimated_impact_percent)}
                          </TableCell>
                          <TableCell>
                            {JSON.stringify(data.parameters || {})}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            )}

            {scenarioResult.sensitivity_analysis.environmental_variables && (
              <Box>
                <Typography variant="subtitle1" gutterBottom>
                  Environmental Variables
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Variable</TableCell>
                        <TableCell>Value</TableCell>
                        <TableCell>Impact</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {Object.entries(scenarioResult.sensitivity_analysis.environmental_variables).map(([varName, data]: [string, any]) => (
                        <TableRow key={varName}>
                          <TableCell>{varName.replace(/_/g, ' ')}</TableCell>
                          <TableCell>{data.value}</TableCell>
                          <TableCell>{data.impact}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            )}
          </CardContent>
        </Card>
      )}
      
      {/* Scenario Accuracy Tab (Phase 7) */}
      {activeTab === 'accuracy' && (
        <Box>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  Scenario Accuracy Tracking
                </Typography>
                <Box>
                  {currentScenarioAnalysisId && (
                    <>
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={() => setLinkDialogOpen(true)}
                        sx={{ mr: 1 }}
                      >
                        Link to Policy
                      </Button>
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={() => setAccuracyDialogOpen(true)}
                      >
                        Compute Accuracy
                      </Button>
                    </>
                  )}
                </Box>
              </Box>
              
              {scenarioLinks.length > 0 && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    Scenario Links ({scenarioLinks.length})
                  </Typography>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Scenario ID</TableCell>
                          <TableCell>Policy ID</TableCell>
                          <TableCell>Linked At</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {scenarioLinks.map((link) => (
                          <TableRow key={link.link_id}>
                            <TableCell>{link.scenario_id.substring(0, 8)}...</TableCell>
                            <TableCell>{link.policy_id.substring(0, 8)}...</TableCell>
                            <TableCell>{new Date(link.linked_at).toLocaleString()}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Box>
              )}
              
              {scenarioAccuracy.length > 0 ? (
                <Box>
                  <Typography variant="subtitle1" gutterBottom>
                    Accuracy Records ({scenarioAccuracy.length})
                  </Typography>
                  {scenarioAccuracy.map((acc) => (
                    <Card key={acc.accuracy_id} sx={{ mb: 2 }}>
                      <CardContent>
                        <Grid container spacing={2}>
                          <Grid item xs={12} md={6}>
                            <Typography variant="subtitle2" color="text.secondary">
                              Overall Accuracy
                            </Typography>
                            <Typography variant="h4" color={
                              acc.accuracy_metrics.overall_accuracy_pct >= 80 ? 'success.main' :
                              acc.accuracy_metrics.overall_accuracy_pct >= 60 ? 'warning.main' : 'error.main'
                            }>
                              {acc.accuracy_metrics.overall_accuracy_pct.toFixed(1)}%
                            </Typography>
                          </Grid>
                          <Grid item xs={12} md={6}>
                            <Typography variant="subtitle2" color="text.secondary">
                              Utilization Accuracy
                            </Typography>
                            <Typography variant="h6">
                              {acc.accuracy_metrics.utilization_accuracy.accuracy_pct.toFixed(1)}%
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Predicted: {acc.accuracy_metrics.utilization_accuracy.predicted_pct.toFixed(1)}% | 
                              Observed: {acc.accuracy_metrics.utilization_accuracy.observed_pct.toFixed(1)}% | 
                              Error: {acc.accuracy_metrics.utilization_accuracy.error_pct.toFixed(1)}%
                            </Typography>
                          </Grid>
                          <Grid item xs={12} md={6}>
                            <Typography variant="subtitle2" color="text.secondary">
                              Cost Accuracy
                            </Typography>
                            <Typography variant="h6">
                              {acc.accuracy_metrics.cost_accuracy.accuracy_pct.toFixed(1)}%
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Predicted: {acc.accuracy_metrics.cost_accuracy.predicted_pct.toFixed(1)}% | 
                              Observed: {acc.accuracy_metrics.cost_accuracy.observed_pct.toFixed(1)}% | 
                              Error: {acc.accuracy_metrics.cost_accuracy.error_pct.toFixed(1)}%
                            </Typography>
                          </Grid>
                          <Grid item xs={12}>
                            <Typography variant="caption" color="text.secondary">
                              Computed: {new Date(acc.computed_at).toLocaleString()}
                            </Typography>
                          </Grid>
                        </Grid>
                      </CardContent>
                    </Card>
                  ))}
                </Box>
              ) : (
                <Alert severity="info">
                  No accuracy records found. Link a scenario to a policy and compute accuracy after observations are available.
                </Alert>
              )}
            </CardContent>
          </Card>
        </Box>
      )}
      
      {/* Link Scenario Dialog */}
      <Dialog open={linkDialogOpen} onClose={() => setLinkDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Link Scenario to Policy</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Link this scenario to a policy implementation to enable accuracy tracking.
          </Typography>
          {selectedPolicy && (
            <Alert severity="info" sx={{ mb: 2 }}>
              Policy: {selectedPolicy.name}
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLinkDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleLinkScenario} variant="contained">
            Link
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Compute Accuracy Dialog */}
      <Dialog open={accuracyDialogOpen} onClose={() => setAccuracyDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Compute Scenario Accuracy</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Select an observation to compare against this scenario's predictions.
          </Typography>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Observation</InputLabel>
            <Select
              value={selectedObservationId || ''}
              onChange={(e) => setSelectedObservationId(e.target.value)}
              label="Observation"
            >
              {observations.map((obs) => (
                <MenuItem key={obs.observation_id} value={obs.observation_id}>
                  {new Date(obs.observation_period_start || obs.computed_at).toLocaleDateString()} - 
                  {new Date(obs.observation_period_end || obs.computed_at).toLocaleDateString()}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAccuracyDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleComputeAccuracy} 
            variant="contained"
            disabled={!selectedObservationId}
          >
            Compute Accuracy
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

