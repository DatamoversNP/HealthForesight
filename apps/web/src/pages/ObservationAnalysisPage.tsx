/**
 * Observation Analysis Page - Compare Predicted vs Observed Outcomes
 */
import { useState, useEffect } from 'react'
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
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Alert,
  Tabs,
  Tab,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  LinearProgress,
  Link,
} from '@mui/material'
import {
  CompareArrows as CompareIcon,
  TrendingUp as TrendingIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Assessment as AssessmentIcon,
  Refresh as RefreshIcon,
  PlayArrow as RunIcon,
  AttachMoney as MoneyIcon,
  People as PeopleIcon,
  ShowChart as ChartIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  CalendarToday as CalendarIcon,
  AccessTime as TimeIcon,
} from '@mui/icons-material'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  ComposedChart,
  Area,
  AreaChart,
} from 'recharts'
import { useNavigate } from 'react-router-dom'
import { apiClient } from '../lib/api'
import { format } from 'date-fns'

interface Observation {
  observation_id: string
  policy_id: string
  policy_version_id?: string
  data_period_id?: string
  observation_type: string
  observation_period_start?: string
  observation_period_end?: string
  baseline_version_id?: string
  prediction_id?: string
  analysis_id?: string
  computed_at: string
  verdict_status?: string
  verdict_reason?: string
  recommendation?: string
  verdict_rule_version?: string
  analytics_run_id?: string
  metrics: {
    utilization_per_1k?: number
    cost_per_member?: number
    cost_pmpm?: number
    total_claims?: number
    observed_effect_size?: number
    observed_percent_change?: number
    member_months?: number
    unique_members?: number
  }
  /** Unified measure framework: same canonical keys as baseline/prediction */
  observed_measures?: Record<string, number>
  comparisons: {
    vs_baseline?: {
      baseline_utilization_per_1k?: number
      baseline_utilization?: number
      observed_utilization_per_1k?: number
      observed_utilization?: number
      change_from_baseline?: number
      change_from_baseline_pct?: number
      utilization_change?: number
      utilization_change_pct?: number
      baseline_cost_pmpm?: number
      baseline_cost?: number
      observed_cost_pmpm?: number
      observed_cost?: number
      cost_change_pmpm?: number
      cost_change_pct?: number
      baseline_measures?: Record<string, number>
      comparison_by_measure?: Record<string, { baseline?: number; observed?: number; change?: number; change_pct?: number | null }>
    }
    vs_policy_baseline?: {
      baseline_utilization_per_1k?: number
      observed_utilization_per_1k?: number
      utilization_change?: number
      utilization_change_pct?: number
      baseline_cost_pmpm?: number
      observed_cost_pmpm?: number
      cost_change_pmpm?: number
      cost_change_pct?: number
      baseline_version_id?: string
    }
    vs_predicted?: {
      predicted_utilization?: number
      observed_utilization?: number
      predicted_utilization_per_1k?: number
      observed_utilization_per_1k?: number
      predicted_utilization_change?: number
      predicted_utilization_change_pct?: number
      utilization_prediction_error?: number
      utilization_prediction_error_pct?: number
      predicted_cost_pmpm?: number
      observed_cost_pmpm?: number
      predicted_cost_change_pmpm?: number
      predicted_cost_change_pct?: number
      cost_prediction_error?: number
      cost_prediction_error_pct?: number
      predicted_effect_size?: number
      observed_effect_size?: number
      prediction_error?: number
      prediction_error_pct?: number
      prediction_accuracy_pct?: number
      within_predicted_range?: boolean
      predicted_measures?: Record<string, number>
      comparison_by_measure?: Record<string, { predicted?: number; observed?: number; error?: number; error_pct?: number }>
      confidence_intervals?: {
        utilization?: {
          predicted_value?: number
          lower_bound?: number
          upper_bound?: number
          interval_width?: number
          interval_width_pct?: number
        }
        cost?: {
          predicted_value?: number
          lower_bound?: number
          upper_bound?: number
          interval_width?: number
          interval_width_pct?: number
        }
      }
      ramp_up_projections?: {
        utilization?: {
          baseline_value?: number
          full_effect_value?: number
          full_effect_change?: number
          ramp_up_values?: Array<{
            month: number
            ramp_factor: number
            predicted_value: number
            effect_achieved_pct: number
          }>
        }
        cost?: {
          baseline_value?: number
          full_effect_value?: number
          full_effect_change?: number
          ramp_up_values?: Array<{
            month: number
            ramp_factor: number
            predicted_value: number
            effect_achieved_pct: number
          }>
        }
      }
    }
  }
  metadata?: {
    [key: string]: any
  }
  behavioral_explanation?: Record<string, any>
  created_at: string
  updated_at: string
  analysis_created_at?: string  // Analysis creation date
  analysis_executed_at?: string  // Analysis execution date
}

interface Policy {
  id: string
  name: string  // API returns 'name', not 'policy_name'
  policy_type: string
}

export default function ObservationAnalysisPage() {
  const [observations, setObservations] = useState<Observation[]>([])
  const [policies, setPolicies] = useState<Policy[]>([])
  const [selectedObservation, setSelectedObservation] = useState<Observation | null>(null)
  const [selectedPolicy, setSelectedPolicy] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [tabValue, setTabValue] = useState(0)
  const [dailyJobRunning, setDailyJobRunning] = useState(false)
  const [dailyJobStatus, setDailyJobStatus] = useState<string | null>(null)
  const [rerunningObservations, setRerunningObservations] = useState<Set<string>>(new Set())
  const [generatingData, setGeneratingData] = useState(false)
  const [forecastData, setForecastData] = useState<any>(null)
  const [loadingForecast, setLoadingForecast] = useState(false)
  const [forecastMetricType, setForecastMetricType] = useState<'utilization' | 'cost'>('utilization')
  const navigate = useNavigate()

  useEffect(() => {
    loadData()
  }, [])

  // Load forecast when Forecast tab is selected
  useEffect(() => {
    if (tabValue === 5 && selectedObservation && selectedPolicy) {
      loadForecast()
    }
  }, [tabValue, selectedObservation?.observation_id, selectedPolicy, forecastMetricType])

  const loadForecast = async () => {
    if (!selectedObservation || !selectedPolicy) return
    
    try {
      setLoadingForecast(true)
      const forecast = await apiClient.getObservationForecast(
        selectedObservation.observation_id,
        selectedPolicy,
        forecastMetricType,
        12
      )
      setForecastData(forecast)
    } catch (err: any) {
      console.error('Error loading forecast:', err)
      setForecastData(null)
    } finally {
      setLoadingForecast(false)
    }
  }

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Load policies
      const policiesData = await apiClient.getPolicies()
      // Map policies to ensure they have the expected structure
      const mappedPolicies = Array.isArray(policiesData) 
        ? policiesData.map((p: any) => ({
            id: p.id,
            name: p.name || p.policy_name || 'Unknown Policy',
            policy_type: p.policy_type || 'UNKNOWN',
          }))
        : []
      setPolicies(mappedPolicies)

      // Load observations
      await loadObservations()
    } catch (err: any) {
      setError(err.message || 'Failed to load data')
      console.error('Error loading data:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadObservations = async (policyId?: string) => {
    try {
      const params: any = { include_trends: true }  // Request trend data
      if (policyId) {
        params.policy_id = policyId
      }
      console.log('Loading observations with params:', params)
      const data = await apiClient.listObservations(params)
      console.log('Observations API response:', { 
        isArray: Array.isArray(data), 
        length: Array.isArray(data) ? data.length : 'N/A',
        data: data 
      })
      const observationsList = Array.isArray(data) ? data : []
      
      // Enrich observations with analysis dates
      const enrichedObservations = await Promise.all(
        observationsList.map(async (obs: Observation) => {
          if (obs.analysis_id) {
            try {
              const analysis = await apiClient.getAnalysis(obs.analysis_id)
              if (analysis) {
                return {
                  ...obs,
                  analysis_created_at: analysis.created_at,
                  analysis_executed_at: analysis.updated_at || analysis.created_at, // Use updated_at as executed date
                }
              }
            } catch (err) {
              console.error(`Error loading analysis ${obs.analysis_id}:`, err)
            }
          }
          return obs
        })
      )
      
      console.log('Enriched observations:', enrichedObservations.length)
      setObservations(enrichedObservations)
    } catch (err: any) {
      console.error('Error loading observations:', err)
      console.error('Error details:', {
        message: err.message,
        status: err.status,
        code: err.code,
        detail: err.detail,
        response: err.response?.data
      })
      setObservations([])
      // Show error to user if it's not a timeout
      if (err.status !== 0 && err.code !== 'ECONNABORTED' && !err.message?.includes('timeout')) {
        setError(err.detail || err.message || 'Failed to load observations')
      }
    }
  }

  const handleTriggerDailyJob = async () => {
    try {
      setDailyJobRunning(true)
      setDailyJobStatus(null)
      setError(null)
      
      const result = await apiClient.triggerDailyJob(undefined, true)
      setDailyJobStatus(`Daily job started (ID: ${result.job_id}). Check back in a few minutes.`)
      
      // Reload observations after a delay
      setTimeout(() => {
        if (selectedPolicy) {
          loadObservations(selectedPolicy)
        } else {
          loadObservations()
        }
      }, 10000) // 10 seconds delay
      
    } catch (err: any) {
      setError(err.message || 'Failed to trigger daily job')
      console.error('Error triggering daily job:', err)
    } finally {
      setDailyJobRunning(false)
    }
  }

  const handleGenerateClaimsData = async () => {
    try {
      setGeneratingData(true)
      setError(null)
      setDailyJobStatus(null)
      
      const result = await apiClient.generateClaimsDataYesterday()
      setDailyJobStatus(
        `Generated ${result.claims_generated} claims for ${result.target_date}. ` +
        `Covered ${result.members_covered} members. Data loaded to database.`
      )
      
      // Reload observations after a delay
      setTimeout(() => {
        if (selectedPolicy) {
          loadObservations(selectedPolicy)
        } else {
          loadObservations()
        }
      }, 2000)
      
    } catch (err: any) {
      setError(err.message || 'Failed to generate claims data')
      console.error('Error generating claims data:', err)
    } finally {
      setGeneratingData(false)
    }
  }

  const handleCreateObservation = async () => {
    if (!selectedPolicy) {
      setError('Please select a policy')
      return
    }

    try {
      setCreating(true)
      setError(null)

      // Get latest impact analysis for the policy
      const analyses = await apiClient.getAnalyses({ analysis_type: 'IMPACT' })
      const policyAnalyses = Array.isArray(analyses) 
        ? analyses.filter((a: any) => a.policy_id === selectedPolicy && a.status === 'COMPLETED')
        : []

      if (policyAnalyses.length === 0) {
        // Create impact analysis first
        const policy = policies.find(p => p.id === selectedPolicy)
        if (!policy) {
          throw new Error('Policy not found')
        }

        // Get policy details to build filters
        const policyDetails = await apiClient.getPolicy(selectedPolicy)
        const scope = policyDetails.scope || {}

        // Create impact analysis
        const impactAnalysis = await apiClient.createImpactAnalysis({
          policy_id: selectedPolicy,
          treatment_filters: {
            lob: scope.lob || [],
            markets: scope.markets || [],
            in_network_only: scope.network?.includes('IN'),
          },
          control_filters: null,
          pre_window_months: 6,
          post_window_months: 1, // Post-policy period (5 days)
        })

        // Wait a moment for analysis to complete
        await new Promise(resolve => setTimeout(resolve, 2000))

        // Create observation from analysis
        await apiClient.createObservationFromAnalysis(
          impactAnalysis.id || impactAnalysis.result?.id,
          selectedPolicy
        )
      } else {
        // Use latest impact analysis
        const latestAnalysis = policyAnalyses[0]
        await apiClient.createObservationFromAnalysis(
          latestAnalysis.id,
          selectedPolicy
        )
      }

      // Reload observations
      await loadObservations(selectedPolicy)
      setDialogOpen(false)
    } catch (err: any) {
      setError(err.message || 'Failed to create observation')
      console.error('Error creating observation:', err)
    } finally {
      setCreating(false)
    }
  }

  const handleRerunObservation = async (observation: Observation) => {
    if (!observation.analysis_id) {
      setError('Cannot rerun observation: No analysis ID found')
      return
    }

    try {
      setRerunningObservations(prev => new Set(prev).add(observation.observation_id))
      setError(null)

      // Rerun by creating a new observation from the same analysis
      await apiClient.createObservationFromAnalysis(
        observation.analysis_id,
        observation.policy_id,
        observation.data_period_id
      )

      // Reload observations
      await loadObservations(selectedPolicy || undefined)
    } catch (err: any) {
      setError(err.message || 'Failed to rerun observation')
      console.error('Error rerunning observation:', err)
    } finally {
      setRerunningObservations(prev => {
        const next = new Set(prev)
        next.delete(observation.observation_id)
        return next
      })
    }
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Observation Analysis
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={generatingData ? <CircularProgress size={16} /> : <CalendarIcon />}
            onClick={handleGenerateClaimsData}
            disabled={generatingData}
            color="secondary"
          >
            {generatingData ? 'Generating...' : 'Generate Claims Data'}
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleTriggerDailyJob}
            disabled={dailyJobRunning}
            title="Generate or load data for yesterday, then create observations for active policies. No manual file upload needed."
          >
            {dailyJobRunning ? 'Running...' : 'Run Daily Job'}
          </Button>
          <Button
            variant="outlined"
            startIcon={<TimeIcon />}
            onClick={() => navigate(`/observation-run-history${selectedPolicy ? `?policy_id=${encodeURIComponent(selectedPolicy)}` : ''}`)}
          >
            View Run History
          </Button>
          <Button
            variant="contained"
            startIcon={<RunIcon />}
            onClick={() => setDialogOpen(true)}
          >
            Create Observation
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {dailyJobStatus && (
        <Alert severity="info" sx={{ mb: 3 }} onClose={() => setDailyJobStatus(null)}>
          {dailyJobStatus}
        </Alert>
      )}

      {/* Policy filter and summary */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Filter by Policy</InputLabel>
                <Select
                  value={selectedPolicy}
                  onChange={(e) => {
                    setSelectedPolicy(e.target.value)
                    loadObservations(e.target.value || undefined)
                  }}
                  label="Filter by Policy"
                >
                  <MenuItem value="">All Policies</MenuItem>
                  {policies.map((policy) => (
                    <MenuItem key={policy.id} value={policy.id}>
                      {policy.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end', flexWrap: 'wrap' }}>
                <Chip 
                  label={`${observations.length} Observation${observations.length !== 1 ? 's' : ''}`}
                  color="primary"
                  variant="outlined"
                />
                {selectedPolicy && observations.length > 0 && (
                  <Chip
                    label={observations[0].metadata?.trend?.trend_direction === 'increasing' ? '📈 Increasing Trend' :
                           observations[0].metadata?.trend?.trend_direction === 'decreasing' ? '📉 Decreasing Trend' :
                           '➡️ Stable Trend'}
                    color={observations[0].metadata?.trend?.trend_direction === 'increasing' ? 'error' :
                           observations[0].metadata?.trend?.trend_direction === 'decreasing' ? 'success' : 'default'}
                    variant="outlined"
                  />
                )}
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Focus Areas - Highlight observations that need attention */}
      {observations.length > 0 && (
        <Card sx={{ mb: 3, bgcolor: 'warning.light', color: 'warning.contrastText' }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AssessmentIcon /> Focus Areas
            </Typography>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              {observations.filter(obs => {
                const vsPred = obs.comparisons?.vs_predicted
                const vsBase = obs.comparisons?.vs_baseline
                return (
                  (vsPred && Math.abs(vsPred.prediction_error_pct || 0) > 15) ||
                  (vsBase && Math.abs(vsBase.change_from_baseline_pct || 0) > 20) ||
                  (vsPred && vsPred.prediction_accuracy_pct && vsPred.prediction_accuracy_pct < 70)
                )
              }).slice(0, 3).map((obs) => {
                const policyName = policies.find(p => p.id === obs.policy_id)?.name || 'Unknown Policy'
                const issues = []
                if (obs.comparisons?.vs_predicted && Math.abs(obs.comparisons.vs_predicted.prediction_error_pct || 0) > 15) {
                  issues.push(`High prediction error: ${Math.abs(obs.comparisons.vs_predicted.prediction_error_pct || 0).toFixed(1)}%`)
                }
                if (obs.comparisons?.vs_baseline && Math.abs(obs.comparisons.vs_baseline.change_from_baseline_pct || 0) > 20) {
                  issues.push(`Significant baseline deviation: ${Math.abs(obs.comparisons.vs_baseline.change_from_baseline_pct || 0).toFixed(1)}%`)
                }
                return (
                  <Grid item xs={12} sm={6} md={4} key={obs.observation_id}>
                    <Paper sx={{ p: 2, bgcolor: 'background.paper' }}>
                      <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                        {policyName}
                      </Typography>
                      {issues.map((issue, idx) => (
                        <Typography key={idx} variant="body2" color="error.main">
                          ⚠️ {issue}
                        </Typography>
                      ))}
                    </Paper>
                  </Grid>
                )
              })}
              {observations.filter(obs => {
                const vsPred = obs.comparisons?.vs_predicted
                const vsBase = obs.comparisons?.vs_baseline
                return (
                  (vsPred && Math.abs(vsPred.prediction_error_pct || 0) > 15) ||
                  (vsBase && Math.abs(vsBase.change_from_baseline_pct || 0) > 20) ||
                  (vsPred && vsPred.prediction_accuracy_pct && vsPred.prediction_accuracy_pct < 70)
                )
              }).length === 0 && (
                <Grid item xs={12}>
                  <Typography variant="body2">
                    ✅ No critical issues found. All observations are within expected ranges.
                  </Typography>
                </Grid>
              )}
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Observation timeline: X = run date (through date), Y = utilization/cost */}
      {selectedPolicy && observations.length > 1 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <TrendingIcon /> Observation Timeline (by run date)
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Each point = one run; X axis is &quot;Through date&quot; (observation period end).
            </Typography>
            <Grid container spacing={3} sx={{ mt: 1 }}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>Utilization (per 1K) vs Through date</Typography>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={observations
                    .sort((a, b) => new Date(a.observation_period_end || a.computed_at).getTime() - 
                                   new Date(b.observation_period_end || b.computed_at).getTime())
                    .map(obs => ({
                      date: format(new Date(obs.observation_period_end || obs.computed_at), 'MMM d'),
                      utilization: obs.metrics?.utilization_per_1k || 0,
                      baseline: obs.comparisons?.vs_baseline?.baseline_utilization_per_1k || null,
                    }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip contentStyle={{ backgroundColor: '#FFFFFF', color: '#0F172A', border: '1px solid #E5E7EB', borderRadius: 6, boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }} />
                    <Legend />
                    <Line type="monotone" dataKey="utilization" stroke="#8884d8" name="Observed" strokeWidth={2} />
                    {observations[0]?.comparisons?.vs_baseline?.baseline_utilization_per_1k && (
                      <Line type="monotone" dataKey="baseline" stroke="#82ca9d" name="Baseline" strokeDasharray="5 5" />
                    )}
                  </LineChart>
                </ResponsiveContainer>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>Cost (PMPM) vs Through date</Typography>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={observations
                    .sort((a, b) => new Date(a.observation_period_end || a.computed_at).getTime() - 
                                   new Date(b.observation_period_end || b.computed_at).getTime())
                    .map(obs => ({
                      date: format(new Date(obs.observation_period_end || obs.computed_at), 'MMM d'),
                      cost: obs.metrics?.cost_per_member ?? obs.metrics?.cost_pmpm ?? 0,
                      baseline: obs.comparisons?.vs_baseline?.baseline_cost_pmpm || null,
                    }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip contentStyle={{ backgroundColor: '#FFFFFF', color: '#0F172A', border: '1px solid #E5E7EB', borderRadius: 6, boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }} formatter={(value: any) => `$${Number(value)?.toFixed(2)}`} />
                    <Legend />
                    <Line type="monotone" dataKey="cost" stroke="#ff7300" name="Observed" strokeWidth={2} />
                    {observations[0]?.comparisons?.vs_baseline?.baseline_cost_pmpm && (
                      <Line type="monotone" dataKey="baseline" stroke="#82ca9d" name="Baseline" strokeDasharray="5 5" />
                    )}
                  </LineChart>
                </ResponsiveContainer>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Observations list */}
      <Grid container spacing={3}>
        {observations.length === 0 ? (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" color="text.secondary" align="center" gutterBottom>
                  No Observations Found
                </Typography>
                <Typography variant="body2" color="text.secondary" align="center">
                  {selectedPolicy
                    ? 'No observations found for the selected policy. Create one using the "Create Observation" button.'
                    : 'No observations found. Create observations by running impact analysis and creating observations from the results.'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ) : (
          observations.map((observation) => (
            <Grid item xs={12} key={observation.observation_id}>
              <Card
                sx={{ cursor: 'pointer' }}
                onClick={() => setSelectedObservation(observation)}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                    <Box sx={{ flex: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Typography variant="h6">
                          {policies.find(p => p.id === observation.policy_id)?.name || 'Unknown Policy'}
                        </Typography>
                        <Chip label={observation.observation_type} size="small" />
                      </Box>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Observation Period: {observation.observation_period_start 
                          ? format(new Date(observation.observation_period_start), 'MMM d, yyyy')
                          : 'N/A'}
                        {observation.observation_period_end && ` - ${format(new Date(observation.observation_period_end), 'MMM d, yyyy')}`}
                      </Typography>
                      {observation.verdict_status && (
                        <Chip
                          size="small"
                          label={observation.verdict_status === 'BACKFIRE' ? 'Backfire risk' : observation.verdict_status === 'AT_RISK' ? 'At risk' : observation.verdict_status === 'ON_TRACK' ? 'On track' : observation.verdict_status}
                          color={observation.verdict_status === 'BACKFIRE' ? 'error' : observation.verdict_status === 'AT_RISK' ? 'warning' : observation.verdict_status === 'ON_TRACK' ? 'success' : 'default'}
                          sx={{ mt: 0.5, fontWeight: 600 }}
                        />
                      )}
                      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mt: 1 }}>
                        {observation.analysis_created_at && (
                          <Typography variant="caption" color="text.secondary">
                            Analysis Created: {format(new Date(observation.analysis_created_at), 'MMM d, yyyy HH:mm')}
                          </Typography>
                        )}
                        {observation.computed_at && (
                          <Typography variant="caption" color="text.secondary">
                            Executed: {format(new Date(observation.computed_at), 'MMM d, yyyy HH:mm')}
                          </Typography>
                        )}
                      </Box>
                    </Box>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={<RefreshIcon />}
                        onClick={(e) => {
                          e.stopPropagation()
                          handleRerunObservation(observation)
                        }}
                        disabled={rerunningObservations.has(observation.observation_id)}
                      >
                        {rerunningObservations.has(observation.observation_id) ? 'Rerunning...' : 'Rerun'}
                      </Button>
                    </Box>
                  </Box>

                  {/* Metrics summary */}
                  <Grid container spacing={2}>
                    {observation.comparisons.vs_predicted && (
                      <Grid item xs={12} sm={6} md={3}>
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            Prediction Accuracy
                          </Typography>
                          <Typography variant="h6" color={
                            (observation.comparisons.vs_predicted.prediction_accuracy_pct ?? null) == null ? 'text.secondary' :
                            (observation.comparisons.vs_predicted.prediction_accuracy_pct || 0) >= 80 ? 'success.main' :
                            (observation.comparisons.vs_predicted.prediction_accuracy_pct || 0) >= 60 ? 'warning.main' : 'error.main'
                          }>
                            {observation.comparisons.vs_predicted.prediction_accuracy_pct != null ? `${observation.comparisons.vs_predicted.prediction_accuracy_pct.toFixed(1)}%` : 'N/A'}
                          </Typography>
                          {(observation.comparisons.vs_predicted.prediction_accuracy_pct ?? null) == null && (
                            <Typography variant="caption" color="text.secondary" display="block">
                              Prediction not available for this policy yet
                            </Typography>
                          )}
                        </Box>
                      </Grid>
                    )}
                    {observation.metrics.utilization_per_1k && (
                      <Grid item xs={12} sm={6} md={3}>
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            Observed Utilization
                          </Typography>
                          <Typography variant="h6">
                            {observation.metrics.utilization_per_1k.toFixed(1)} per 1K
                          </Typography>
                        </Box>
                      </Grid>
                    )}
                    {observation.comparisons.vs_baseline?.change_from_baseline_pct && (
                      <Grid item xs={12} sm={6} md={3}>
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            Change from Baseline
                          </Typography>
                          <Typography variant="h6" color={
                            (observation.comparisons.vs_baseline.change_from_baseline_pct || 0) > 0 ? 'error.main' : 'success.main'
                          }>
                            {observation.comparisons.vs_baseline.change_from_baseline_pct >= 0 ? '+' : ''}
                            {observation.comparisons.vs_baseline.change_from_baseline_pct.toFixed(1)}%
                          </Typography>
                        </Box>
                      </Grid>
                    )}
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          ))
        )}
      </Grid>

      {/* Observation detail dialog */}
      <Dialog
        open={!!selectedObservation}
        onClose={() => setSelectedObservation(null)}
        maxWidth="xl"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 0,
            boxShadow: 'none',
            maxHeight: '95vh',
            display: 'flex',
            flexDirection: 'column',
          }
        }}
      >
        <DialogTitle sx={{ 
          background: '#E8EDF5',
          color: '#0F172A',
          py: 3,
          px: 4,
          borderBottom: '1px solid #CBD5E1'
        }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <Box>
              <Typography variant="h5" sx={{ fontWeight: 600, mb: 1, letterSpacing: '-0.02em', color: '#0F172A' }}>
                {policies.find(p => p.id === selectedObservation?.policy_id)?.name || 'Observation Details'}
            </Typography>
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mt: 1, flexWrap: 'wrap' }}>
                <Chip 
                  label={selectedObservation?.observation_type || 'N/A'} 
                  size="small" 
                  sx={{ 
                    bgcolor: '#CBD5E1', 
                    color: '#0F172A',
                    fontWeight: 500,
                    fontSize: '0.75rem',
                    height: 24
                  }} 
                />
                {selectedObservation?.verdict_status && (
                  <Chip
                    size="small"
                    label={selectedObservation.verdict_status === 'BACKFIRE' ? 'Backfire risk' : selectedObservation.verdict_status === 'AT_RISK' ? 'At risk' : selectedObservation.verdict_status === 'ON_TRACK' ? 'On track' : selectedObservation.verdict_status}
                    color={selectedObservation.verdict_status === 'BACKFIRE' ? 'error' : selectedObservation.verdict_status === 'AT_RISK' ? 'warning' : selectedObservation.verdict_status === 'ON_TRACK' ? 'success' : 'default'}
                    sx={{ fontWeight: 600, fontSize: '0.75rem', height: 24 }}
                  />
                )}
                <Typography variant="body2" sx={{ opacity: 0.8, fontSize: '0.875rem' }}>
                  {selectedObservation?.observation_period_start 
                    ? format(new Date(selectedObservation.observation_period_start), 'MMM d, yyyy')
                    : 'N/A'}
                </Typography>
                {selectedObservation?.observation_id && (
                  <Link
                    href="#"
                    onClick={(e) => {
                      e.preventDefault()
                      apiClient.getObservationEvidencePack(selectedObservation!.observation_id).then((pack) => {
                        const blob = new Blob([JSON.stringify(pack, null, 2)], { type: 'application/json' })
                        const url = URL.createObjectURL(blob)
                        const a = document.createElement('a')
                        a.href = url
                        a.download = `evidence-pack-${selectedObservation!.observation_id}.json`
                        a.click()
                        URL.revokeObjectURL(url)
                      }).catch(() => {})
                    }}
                    sx={{ fontSize: '0.875rem', ml: 1 }}
                  >
                    Download evidence pack
                  </Link>
                )}
              </Box>
              {selectedObservation?.verdict_reason && (
                <Typography variant="body2" sx={{ mt: 1, color: '#475569', maxWidth: 720 }}>
                  <strong>Verdict:</strong> {selectedObservation.verdict_reason}
                  {selectedObservation.recommendation && ` — ${selectedObservation.recommendation}`}
                </Typography>
              )}
            </Box>
            <Button 
              onClick={() => setSelectedObservation(null)}
              sx={{ 
                color: '#0F172A', 
                minWidth: 'auto',
                px: 2,
                '&:hover': { bgcolor: '#CBD5E1' } 
              }}
            >
              Close
            </Button>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ p: 0, bgcolor: '#F8FAFC', flex: 1, overflow: 'auto' }}>
          {selectedObservation && (
            <Box>
              <Box sx={{ 
                bgcolor: 'white', 
                borderBottom: '1px solid #E5E7EB',
                px: 4,
                pt: 2
              }}>
                <Tabs 
                  value={tabValue} 
                  onChange={(_, v) => setTabValue(v)} 
                  sx={{ 
                    minHeight: 48,
                    '& .MuiTab-root': {
                      textTransform: 'none',
                      fontWeight: 500,
                      minHeight: 48,
                      fontSize: '0.9375rem',
                      color: '#64748B',
                      px: 3,
                      '&.Mui-selected': {
                        color: '#0F172A',
                        fontWeight: 600,
                      }
                    },
                    '& .MuiTabs-indicator': {
                      backgroundColor: '#3B2F8F',
                      height: 3,
                    }
                  }}
                >
                  <Tab label="Overview" icon={<InfoIcon sx={{ fontSize: 18 }} />} iconPosition="start" />
                  <Tab label="General Baseline" icon={<CompareIcon sx={{ fontSize: 18 }} />} iconPosition="start" />
                  <Tab label="Policy Baseline" icon={<CompareIcon sx={{ fontSize: 18 }} />} iconPosition="start" />
                  <Tab label="Predicted Comparison" icon={<ChartIcon sx={{ fontSize: 18 }} />} iconPosition="start" />
                  <Tab label="Behavioral Explanation" icon={<AssessmentIcon sx={{ fontSize: 18 }} />} iconPosition="start" />
                  <Tab label="Forecast" icon={<TrendingIcon sx={{ fontSize: 18 }} />} iconPosition="start" />
              </Tabs>
              </Box>

              <Box sx={{ p: 4 }}>
              {tabValue === 0 && (
                <Box>
                  {/* Unified measures comparison table: Baseline | Predicted | Observed */}
                  {(() => {
                    const vsBaseline = selectedObservation.comparisons?.vs_baseline
                    const vsPredicted = selectedObservation.comparisons?.vs_predicted
                    const byBaseline = vsBaseline?.comparison_by_measure ?? {}
                    const byPredicted = vsPredicted?.comparison_by_measure ?? {}
                    const measureKeys = Array.from(new Set([
                      ...Object.keys(byBaseline),
                      ...Object.keys(byPredicted)
                    ])).filter(Boolean)
                    const measureDisplay: Record<string, string> = {
                      util_rate_target_per_1000_mm: 'Utilization (per 1K MM)',
                      allowed_pmpm_target: 'Cost PMPM (allowed)',
                      allowed_pmpm_total: 'Allowed PMPM (total)',
                      paid_pmpm_total: 'Paid PMPM',
                      member_months: 'Member months',
                      unique_members: 'Unique members',
                      util_rate_total_per_1000_mm: 'Utilization total (per 1K MM)',
                      allowed_total_annualized: 'Allowed total (annualized)'
                    }
                    const formatVal = (v: number | undefined | null, key: string): string => {
                      if (v === undefined || v === null) return '—'
                      if (key.includes('pmpm') || key.includes('allowed') || key.includes('paid')) return `$${v.toFixed(2)}`
                      if (key.includes('rate') || key.includes('util')) return v.toFixed(2)
                      return String(v)
                    }
                    if (measureKeys.length > 0) {
                      return (
                        <Box sx={{ mb: 4 }}>
                          <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>Compare measures</Typography>
                          <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: 0, border: '1px solid #CBD5E1' }}>
                            <Table size="small">
                              <TableHead>
                                <TableRow sx={{ bgcolor: '#E8EDF5' }}>
                                  <TableCell sx={{ fontWeight: 600 }}>Measure</TableCell>
                                  <TableCell align="right" sx={{ fontWeight: 600 }}>Baseline</TableCell>
                                  <TableCell align="right" sx={{ fontWeight: 600 }}>Predicted</TableCell>
                                  <TableCell align="right" sx={{ fontWeight: 600 }}>Observed</TableCell>
                                </TableRow>
                              </TableHead>
                              <TableBody>
                                {measureKeys.map((key) => (
                                  <TableRow key={key}>
                                    <TableCell>{measureDisplay[key] ?? key}</TableCell>
                                    <TableCell align="right">{formatVal(byBaseline[key]?.baseline, key)}</TableCell>
                                    <TableCell align="right">{formatVal(byPredicted[key]?.predicted, key)}</TableCell>
                                    <TableCell align="right">
                                      {formatVal(byBaseline[key]?.observed ?? byPredicted[key]?.observed ?? selectedObservation.observed_measures?.[key], key)}
                                    </TableCell>
                                  </TableRow>
                                ))}
                              </TableBody>
                            </Table>
                          </TableContainer>
                        </Box>
                      )
                    }
                    return null
                  })()}
                  {/* Key Metrics Cards */}
                  <Grid container spacing={2.5} sx={{ mb: 4 }}>
                    <Grid item xs={12} sm={6} md={3}>
                      <Card sx={{ 
                        bgcolor: '#E8EDF5',
                        color: '#0F172A',
                        height: '100%',
                        borderRadius: 0,
                        boxShadow: 'none',
                        border: '1px solid #CBD5E1'
                      }}>
                        <CardContent sx={{ p: 3 }}>
                          <Typography variant="overline" sx={{ 
                            fontSize: '0.6875rem',
                            fontWeight: 600,
                            letterSpacing: '0.08em',
                            color: '#64748B',
                            textTransform: 'uppercase',
                            mb: 1.5,
                            display: 'block'
                          }}>
                            Utilization (per 1K)
                          </Typography>
                          <Typography variant="h3" sx={{ 
                            fontWeight: 700,
                            letterSpacing: '-0.02em',
                            lineHeight: 1.2,
                            color: '#0F172A'
                          }}>
                                {selectedObservation.metrics.utilization_per_1k?.toFixed(1) || 'N/A'}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Card sx={{ 
                        bgcolor: '#E0F7F8',
                        color: '#0F172A',
                        height: '100%',
                        borderRadius: 0,
                        boxShadow: 'none',
                        border: '1px solid #B2E5E7'
                      }}>
                        <CardContent sx={{ p: 3 }}>
                          <Typography variant="overline" sx={{ 
                            fontSize: '0.6875rem',
                            fontWeight: 600,
                            letterSpacing: '0.08em',
                            color: 'rgba(15,23,42,0.7)',
                            textTransform: 'uppercase',
                            mb: 1.5,
                            display: 'block'
                          }}>
                            Cost per Member
                          </Typography>
                          <Typography variant="h3" sx={{ 
                            fontWeight: 700,
                            letterSpacing: '-0.02em',
                            lineHeight: 1.2
                          }}>
                                ${selectedObservation.metrics.cost_per_member?.toFixed(2) || 'N/A'}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Card sx={{ 
                        bgcolor: '#E8E5F5',
                        color: '#0F172A',
                        height: '100%',
                        borderRadius: 0,
                        boxShadow: 'none',
                        border: '1px solid #D4CEE8'
                      }}>
                        <CardContent sx={{ p: 3 }}>
                          <Typography variant="overline" sx={{ 
                            fontSize: '0.6875rem',
                            fontWeight: 600,
                            letterSpacing: '0.08em',
                            color: '#64748B',
                            textTransform: 'uppercase',
                            mb: 1.5,
                            display: 'block'
                          }}>
                            Effect Size
                          </Typography>
                          <Typography variant="h3" sx={{ 
                            fontWeight: 700,
                            letterSpacing: '-0.02em',
                            lineHeight: 1.2,
                            color: '#3B2F8F'
                          }}>
                                {selectedObservation.metrics.observed_effect_size?.toFixed(2) || 'N/A'}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Card sx={{ 
                        bgcolor: selectedObservation.metrics.observed_percent_change && selectedObservation.metrics.observed_percent_change < 0
                          ? '#E8F5E9'
                          : '#FFEBEE',
                        color: selectedObservation.metrics.observed_percent_change && selectedObservation.metrics.observed_percent_change < 0
                          ? '#1B5E20'
                          : '#B71C1C',
                        height: '100%',
                        borderRadius: 0,
                        boxShadow: 'none',
                        border: selectedObservation.metrics.observed_percent_change && selectedObservation.metrics.observed_percent_change < 0
                          ? '1px solid #C8E6C9'
                          : '1px solid #FFCDD2'
                      }}>
                        <CardContent sx={{ p: 3 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
                            {selectedObservation.metrics.observed_percent_change && selectedObservation.metrics.observed_percent_change < 0 ? (
                              <TrendingDownIcon sx={{ mr: 1, fontSize: 20, color: '#2E8B57' }} />
                            ) : (
                              <TrendingUpIcon sx={{ mr: 1, fontSize: 20, color: '#C04A4A' }} />
                            )}
                            <Typography variant="overline" sx={{ 
                              fontSize: '0.6875rem',
                              fontWeight: 600,
                              letterSpacing: '0.08em',
                              color: selectedObservation.metrics.observed_percent_change && selectedObservation.metrics.observed_percent_change < 0
                                ? '#1B5E20'
                                : '#B71C1C',
                              textTransform: 'uppercase'
                            }}>
                              Percent Change
                            </Typography>
                          </Box>
                          <Typography variant="h3" sx={{ 
                            fontWeight: 700,
                            letterSpacing: '-0.02em',
                            lineHeight: 1.2,
                            color: selectedObservation.metrics.observed_percent_change && selectedObservation.metrics.observed_percent_change < 0
                              ? '#2E8B57'
                              : '#C04A4A'
                          }}>
                                {selectedObservation.metrics.observed_percent_change?.toFixed(1) || 'N/A'}%
                          </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  </Grid>

                  {/* Additional Metrics */}
                  <Grid container spacing={2.5}>
                  <Grid item xs={12} md={6}>
                      <Card sx={{ 
                        height: '100%', 
                        bgcolor: 'white', 
                        borderRadius: 0,
                        boxShadow: 'none',
                        border: '1px solid #E5E7EB'
                      }}>
                        <CardContent sx={{ p: 3 }}>
                          <Typography variant="h6" gutterBottom sx={{ 
                            mb: 3, 
                            color: '#0F172A', 
                            fontWeight: 600,
                            fontSize: '1rem',
                            letterSpacing: '-0.01em'
                          }}>
                            Observed Metrics
                          </Typography>
                          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                            <Box sx={{ 
                              display: 'flex', 
                              justifyContent: 'space-between', 
                              alignItems: 'center',
                              py: 2,
                              px: 0,
                              borderBottom: '1px solid #F1F5F9'
                            }}>
                              <Typography variant="body2" sx={{ 
                                color: '#64748B', 
                                fontWeight: 500,
                                fontSize: '0.875rem'
                              }}>
                                Utilization (per 1K)
                              </Typography>
                              <Typography variant="h6" fontWeight={600} sx={{ 
                                color: '#0F172A',
                                fontSize: '1.125rem'
                              }}>
                                {selectedObservation.metrics.utilization_per_1k?.toFixed(1) || 'N/A'}
                              </Typography>
                            </Box>
                            <Box sx={{ 
                              display: 'flex', 
                              justifyContent: 'space-between', 
                              alignItems: 'center',
                              py: 2,
                              px: 0,
                              borderBottom: '1px solid #F1F5F9'
                            }}>
                              <Typography variant="body2" sx={{ 
                                color: '#64748B', 
                                fontWeight: 500,
                                fontSize: '0.875rem'
                              }}>
                                Cost PMPM
                              </Typography>
                              <Typography variant="h6" fontWeight={600} sx={{ 
                                color: '#0F172A',
                                fontSize: '1.125rem'
                              }}>
                                ${selectedObservation.metrics.cost_pmpm?.toFixed(2) || selectedObservation.metrics.cost_per_member?.toFixed(2) || 'N/A'}
                              </Typography>
                            </Box>
                            <Box sx={{ 
                              display: 'flex', 
                              justifyContent: 'space-between', 
                              alignItems: 'center',
                              py: 2,
                              px: 0,
                              borderBottom: '1px solid #F1F5F9'
                            }}>
                              <Typography variant="body2" sx={{ 
                                color: '#64748B', 
                                fontWeight: 500,
                                fontSize: '0.875rem'
                              }}>
                                Total Claims
                              </Typography>
                              <Typography variant="h6" fontWeight={600} sx={{ 
                                color: '#0F172A',
                                fontSize: '1.125rem'
                              }}>
                                {selectedObservation.metrics.total_claims?.toLocaleString() ?? '0'}
                              </Typography>
                            </Box>
                            <Box sx={{ 
                              display: 'flex', 
                              justifyContent: 'space-between', 
                              alignItems: 'center',
                              py: 2,
                              px: 0,
                              borderBottom: '1px solid #F1F5F9'
                            }}>
                              <Typography variant="body2" sx={{ 
                                color: '#64748B', 
                                fontWeight: 500,
                                fontSize: '0.875rem'
                              }}>
                                Member Months
                              </Typography>
                              <Typography variant="h6" fontWeight={600} sx={{ 
                                color: '#0F172A',
                                fontSize: '1.125rem'
                              }}>
                                {selectedObservation.metrics.member_months?.toLocaleString() ?? '0'}
                              </Typography>
                            </Box>
                            {selectedObservation.metrics.unique_members && (
                              <Box sx={{ 
                                display: 'flex', 
                                justifyContent: 'space-between', 
                                alignItems: 'center',
                                py: 2,
                                px: 0,
                                borderBottom: '1px solid #F1F5F9'
                              }}>
                                <Typography variant="body2" sx={{ 
                                  color: '#64748B', 
                                  fontWeight: 500,
                                  fontSize: '0.875rem'
                                }}>
                                  Unique Members
                                </Typography>
                                <Typography variant="h6" fontWeight={600} sx={{ 
                                  color: '#0F172A',
                                  fontSize: '1.125rem'
                                }}>
                                  {selectedObservation.metrics.unique_members?.toLocaleString() || 'N/A'}
                                </Typography>
                              </Box>
                            )}
                          </Box>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Card sx={{ 
                        height: '100%', 
                        bgcolor: 'white',
                        borderRadius: 0,
                        boxShadow: 'none',
                        border: '1px solid #E5E7EB'
                      }}>
                        <CardContent sx={{ p: 3 }}>
                          <Typography variant="h6" gutterBottom sx={{ 
                            mb: 3, 
                            color: '#0F172A', 
                            fontWeight: 600,
                            fontSize: '1rem',
                            letterSpacing: '-0.01em'
                          }}>
                            Period Information
                          </Typography>
                          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
                            <Box sx={{ 
                              display: 'flex', 
                              justifyContent: 'space-between', 
                              alignItems: 'center',
                              py: 2,
                              borderBottom: '1px solid #F1F5F9'
                            }}>
                              <Typography variant="body2" sx={{ 
                                color: '#64748B', 
                                fontWeight: 500,
                                fontSize: '0.875rem'
                              }}>
                                Observation Type
                              </Typography>
                              <Chip 
                                label={selectedObservation.observation_type} 
                                size="small" 
                                sx={{ 
                                  bgcolor: '#3B2F8F', 
                                  color: 'white', 
                                  fontWeight: 500,
                                  fontSize: '0.75rem',
                                  height: 24
                                }} 
                              />
                            </Box>
                            <Box sx={{ 
                              display: 'flex', 
                              justifyContent: 'space-between', 
                              alignItems: 'center',
                              py: 2,
                              borderBottom: '1px solid #F1F5F9'
                            }}>
                              <Typography variant="body2" sx={{ 
                                color: '#64748B', 
                                fontWeight: 500,
                                fontSize: '0.875rem'
                              }}>
                                Period
                              </Typography>
                              <Typography variant="body2" fontWeight={600} sx={{ 
                                color: '#0F172A',
                                fontSize: '0.875rem'
                              }}>
                                {selectedObservation.observation_period_start
                                  ? format(new Date(selectedObservation.observation_period_start), 'MMM d, yyyy')
                                  : 'N/A'}
                                {selectedObservation.observation_period_end && 
                                  ` - ${format(new Date(selectedObservation.observation_period_end), 'MMM d, yyyy')}`}
                              </Typography>
                            </Box>
                            <Box sx={{ 
                              display: 'flex', 
                              justifyContent: 'space-between', 
                              alignItems: 'center',
                              py: 2,
                              borderBottom: '1px solid #F1F5F9'
                            }}>
                              <Typography variant="body2" sx={{ 
                                color: '#64748B', 
                                fontWeight: 500,
                                fontSize: '0.875rem',
                                display: 'flex',
                                alignItems: 'center',
                                gap: 0.5
                              }}>
                                <TimeIcon fontSize="small" />
                                Computed At
                              </Typography>
                              <Typography variant="body2" fontWeight={600} sx={{ 
                                color: '#0F172A',
                                fontSize: '0.875rem'
                              }}>
                                {format(new Date(selectedObservation.computed_at), 'MMM d, yyyy HH:mm')}
                              </Typography>
                            </Box>
                            {selectedObservation.analysis_created_at && (
                              <Box sx={{ 
                                display: 'flex', 
                                justifyContent: 'space-between', 
                                alignItems: 'center',
                                py: 2
                              }}>
                                <Typography variant="body2" sx={{ 
                                  color: '#64748B', 
                                  fontWeight: 500,
                                  fontSize: '0.875rem'
                                }}>
                                  Analysis Created
                                </Typography>
                                <Typography variant="body2" fontWeight={600} sx={{ 
                                  color: '#0F172A',
                                  fontSize: '0.875rem'
                                }}>
                                  {format(new Date(selectedObservation.analysis_created_at), 'MMM d, yyyy HH:mm')}
                                </Typography>
                              </Box>
                            )}
                          </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
                </Box>
              )}

              {tabValue === 1 && selectedObservation.comparisons.vs_baseline && (
                <Box>
                  <Typography variant="h5" gutterBottom sx={{ mb: 3, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1, color: '#0F172A' }}>
                    <CompareIcon sx={{ color: '#3B2F8F' }} />
                    Baseline vs Observed Comparison
                  </Typography>
                  
                  <Grid container spacing={3}>
                    {/* Utilization Metrics */}
                      <Grid item xs={12} md={6}>
                      <Card sx={{ 
                        height: '100%',
                        bgcolor: 'white',
                        borderRadius: 0,
                        boxShadow: 'none',
                        border: '1px solid #E5E7EB'
                      }}>
                        <CardContent sx={{ p: 3 }}>
                          <Typography variant="h6" gutterBottom sx={{ 
                            mb: 3, 
                            color: '#0F172A', 
                            fontWeight: 600,
                            fontSize: '1rem',
                            letterSpacing: '-0.01em'
                          }}>
                            Utilization Metrics
                          </Typography>
                          
                          {(() => {
                            const baselineUtil = selectedObservation.comparisons.vs_baseline?.baseline_utilization_per_1k ?? 
                                                 selectedObservation.comparisons.vs_baseline?.baseline_utilization ?? null
                            const observedUtil = selectedObservation.comparisons.vs_baseline?.observed_utilization_per_1k ?? 
                                                 selectedObservation.comparisons.vs_baseline?.observed_utilization ??
                                                 selectedObservation.metrics?.utilization_per_1k ?? null
                            
                            return (
                              <>
                                <Box sx={{ mb: 3 }}>
                                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1.5 }}>
                                    <Typography variant="body2" sx={{ 
                                      color: '#64748B', 
                                      fontWeight: 500,
                                      fontSize: '0.875rem'
                                    }}>
                                      Baseline
                                    </Typography>
                                    <Typography variant="h6" fontWeight={600} sx={{ 
                                      color: '#0F172A',
                                      fontSize: '1.125rem'
                                    }}>
                                      {baselineUtil !== null && baselineUtil !== undefined ? baselineUtil.toFixed(1) : 'N/A'}
                                    </Typography>
                                  </Box>
                                  <LinearProgress 
                                    variant="determinate" 
                                    value={Math.min((baselineUtil || 0) / 200 * 100, 100)}
                                    sx={{ 
                                      height: 6, 
                                      borderRadius: 0, 
                                      mb: 3, 
                                      bgcolor: '#F1F5F9', 
                                      '& .MuiLinearProgress-bar': { bgcolor: '#1E2A44' } 
                                    }}
                                  />
                                </Box>

                                <Box sx={{ mb: 3 }}>
                                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1.5 }}>
                                    <Typography variant="body2" sx={{ 
                                      color: '#64748B', 
                                      fontWeight: 500,
                                      fontSize: '0.875rem'
                                    }}>
                                      Observed
                                    </Typography>
                                    <Typography variant="h6" fontWeight={600} sx={{ 
                                      color: '#3B2F8F',
                                      fontSize: '1.125rem'
                                    }}>
                                      {observedUtil !== null && observedUtil !== undefined ? observedUtil.toFixed(1) : 'N/A'}
                                    </Typography>
                                  </Box>
                                  <LinearProgress 
                                    variant="determinate" 
                                    value={Math.min((observedUtil || 0) / 200 * 100, 100)}
                                    sx={{ 
                                      height: 6, 
                                      borderRadius: 0, 
                                      mb: 3, 
                                      bgcolor: '#F1F5F9', 
                                      '& .MuiLinearProgress-bar': { bgcolor: '#3B2F8F' } 
                                    }}
                                  />
                                </Box>
                              </>
                            )
                          })()}

                          <Box sx={{ 
                            p: 3, 
                            bgcolor: (selectedObservation.comparisons.vs_baseline.utilization_change_pct || selectedObservation.comparisons.vs_baseline.change_from_baseline_pct || 0) < 0
                              ? '#E8F5E9'
                              : '#FFEBEE',
                            color: (selectedObservation.comparisons.vs_baseline.utilization_change_pct || selectedObservation.comparisons.vs_baseline.change_from_baseline_pct || 0) < 0
                              ? '#1B5E20'
                              : '#B71C1C',
                            border: '1px solid',
                            borderColor: (selectedObservation.comparisons.vs_baseline.utilization_change_pct || selectedObservation.comparisons.vs_baseline.change_from_baseline_pct || 0) < 0
                              ? '#C8E6C9'
                              : '#FFCDD2'
                          }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                {(selectedObservation.comparisons.vs_baseline.utilization_change_pct || selectedObservation.comparisons.vs_baseline.change_from_baseline_pct || 0) < 0 ? (
                                  <TrendingDownIcon sx={{ fontSize: 20, color: '#2E8B57' }} />
                                ) : (
                                  <TrendingUpIcon sx={{ fontSize: 20, color: '#C04A4A' }} />
                                )}
                                <Typography variant="body2" fontWeight={600} sx={{ 
                                  fontSize: '0.875rem', 
                                  color: (selectedObservation.comparisons.vs_baseline.utilization_change_pct || selectedObservation.comparisons.vs_baseline.change_from_baseline_pct || 0) < 0
                                    ? '#1B5E20'
                                    : '#B71C1C'
                                }}>
                                  Change
                                </Typography>
                              </Box>
                              <Typography variant="h6" fontWeight={700} sx={{ 
                                fontSize: '1.125rem', 
                                color: (selectedObservation.comparisons.vs_baseline.utilization_change_pct || selectedObservation.comparisons.vs_baseline.change_from_baseline_pct || 0) < 0
                                  ? '#2E8B57'
                                  : '#C04A4A'
                              }}>
                                {((selectedObservation.comparisons.vs_baseline?.utilization_change ?? selectedObservation.comparisons.vs_baseline?.change_from_baseline ?? 0) >= 0) ? '+' : ''}
                                {(selectedObservation.comparisons.vs_baseline?.utilization_change ?? selectedObservation.comparisons.vs_baseline?.change_from_baseline)?.toFixed(2) || 'N/A'}
                                </Typography>
                            </Box>
                            <Typography variant="h4" fontWeight={700} sx={{ 
                              letterSpacing: '-0.02em',
                              lineHeight: 1.2,
                              color: (selectedObservation.comparisons.vs_baseline.utilization_change_pct || selectedObservation.comparisons.vs_baseline.change_from_baseline_pct || 0) < 0
                                ? '#2E8B57'
                                : '#C04A4A'
                            }}>
                                  {((selectedObservation.comparisons.vs_baseline?.utilization_change_pct ?? selectedObservation.comparisons.vs_baseline?.change_from_baseline_pct ?? 0) >= 0) ? '+' : ''}
                                  {(selectedObservation.comparisons.vs_baseline?.utilization_change_pct ?? selectedObservation.comparisons.vs_baseline?.change_from_baseline_pct)?.toFixed(1) || 'N/A'}%
                                </Typography>
                          </Box>
                        </CardContent>
                      </Card>
                      </Grid>

                    {/* Cost Metrics */}
                      <Grid item xs={12} md={6}>
                      <Card sx={{ 
                        height: '100%',
                        bgcolor: 'white',
                        borderRadius: 0,
                        boxShadow: 'none',
                        border: '1px solid #E5E7EB'
                      }}>
                        <CardContent sx={{ p: 3 }}>
                          <Typography variant="h6" gutterBottom sx={{ 
                            mb: 3, 
                            color: '#0F172A', 
                            fontWeight: 600,
                            fontSize: '1rem',
                            letterSpacing: '-0.01em'
                          }}>
                            Cost Metrics
                                </Typography>
                          
                          {(() => {
                            const baselineCost = selectedObservation.comparisons.vs_baseline?.baseline_cost_pmpm ?? 
                                                  selectedObservation.comparisons.vs_baseline?.baseline_cost ?? null
                            const observedCost = selectedObservation.comparisons.vs_baseline?.observed_cost_pmpm ?? 
                                                 selectedObservation.comparisons.vs_baseline?.observed_cost ??
                                                 selectedObservation.metrics?.cost_pmpm ??
                                                 selectedObservation.metrics?.cost_per_member ?? null
                            
                            return (
                              <>
                                <Box sx={{ mb: 3 }}>
                                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1.5 }}>
                                    <Typography variant="body2" sx={{ 
                                      color: '#64748B', 
                                      fontWeight: 500,
                                      fontSize: '0.875rem'
                                    }}>
                                      Baseline (PMPM)
                                    </Typography>
                                    <Typography variant="h6" fontWeight={600} sx={{ 
                                      color: '#0F172A',
                                      fontSize: '1.125rem'
                                    }}>
                                      ${baselineCost !== null && baselineCost !== undefined ? baselineCost.toFixed(2) : 'N/A'}
                                    </Typography>
                                  </Box>
                                  <LinearProgress 
                                    variant="determinate" 
                                    value={Math.min(((baselineCost ?? 0) / 100) * 100, 100)}
                                    sx={{ 
                                      height: 6, 
                                      borderRadius: 0, 
                                      mb: 3, 
                                      bgcolor: '#F1F5F9', 
                                      '& .MuiLinearProgress-bar': { bgcolor: '#1E2A44' } 
                                    }}
                                  />
                                </Box>

                                <Box sx={{ mb: 3 }}>
                                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1.5 }}>
                                    <Typography variant="body2" sx={{ 
                                      color: '#64748B', 
                                      fontWeight: 500,
                                      fontSize: '0.875rem'
                                    }}>
                                      Observed (PMPM)
                                    </Typography>
                                    <Typography variant="h6" fontWeight={600} sx={{ 
                                      color: '#2EC4C6',
                                      fontSize: '1.125rem'
                                    }}>
                                      ${observedCost !== null && observedCost !== undefined ? observedCost.toFixed(2) : 'N/A'}
                                    </Typography>
                                  </Box>
                                  <LinearProgress 
                                    variant="determinate" 
                                    value={Math.min(((observedCost ?? 0) / 100) * 100, 100)}
                                    sx={{ 
                                      height: 6, 
                                      borderRadius: 0, 
                                      mb: 3, 
                                      bgcolor: '#F1F5F9', 
                                      '& .MuiLinearProgress-bar': { bgcolor: '#2EC4C6' } 
                                    }}
                                  />
                                </Box>
                              </>
                            )
                          })()}

                          <Box sx={{ 
                            p: 3, 
                            bgcolor: (selectedObservation.comparisons.vs_baseline.cost_change_pct || 0) < 0
                              ? '#E8F5E9'
                              : '#FFEBEE',
                            color: (selectedObservation.comparisons.vs_baseline.cost_change_pct || 0) < 0
                              ? '#1B5E20'
                              : '#B71C1C',
                            border: '1px solid',
                            borderColor: (selectedObservation.comparisons.vs_baseline.cost_change_pct || 0) < 0
                              ? '#C8E6C9'
                              : '#FFCDD2'
                          }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                {(selectedObservation.comparisons.vs_baseline.cost_change_pct || 0) < 0 ? (
                                  <TrendingDownIcon sx={{ fontSize: 20, color: '#2E8B57' }} />
                                ) : (
                                  <TrendingUpIcon sx={{ fontSize: 20, color: '#C04A4A' }} />
                                )}
                                <Typography variant="body2" fontWeight={600} sx={{ 
                                  fontSize: '0.875rem', 
                                  color: (selectedObservation.comparisons.vs_baseline.cost_change_pct || 0) < 0
                                    ? '#1B5E20'
                                    : '#B71C1C'
                                }}>
                                  Change (PMPM)
                                </Typography>
                              </Box>
                              <Typography variant="h6" fontWeight={700} sx={{ 
                                fontSize: '1.125rem', 
                                color: (selectedObservation.comparisons.vs_baseline.cost_change_pct || 0) < 0
                                  ? '#2E8B57'
                                  : '#C04A4A'
                              }}>
                              {((selectedObservation.comparisons.vs_baseline?.cost_change_pmpm ?? 0) >= 0) ? '+' : ''}
                                ${selectedObservation.comparisons.vs_baseline?.cost_change_pmpm?.toFixed(2) || 'N/A'}
                                </Typography>
                            </Box>
                            <Typography variant="h4" fontWeight={700} sx={{ 
                              letterSpacing: '-0.02em',
                              lineHeight: 1.2,
                              color: (selectedObservation.comparisons.vs_baseline.cost_change_pct || 0) < 0
                                ? '#2E8B57'
                                : '#C04A4A'
                            }}>
                              {((selectedObservation.comparisons.vs_baseline?.cost_change_pct ?? 0) >= 0) ? '+' : ''}
                              {selectedObservation.comparisons.vs_baseline?.cost_change_pct?.toFixed(1) || 'N/A'}%
                                </Typography>
                          </Box>
                  </CardContent>
                </Card>
                    </Grid>
                  </Grid>
                </Box>
              )}

              {tabValue === 2 && (
                <Box>
                  <Typography variant="h5" gutterBottom sx={{ mb: 3, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1, color: '#0F172A' }}>
                    <CompareIcon sx={{ color: '#3B2F8F' }} />
                    Policy-Specific Baseline vs Observed Comparison
                  </Typography>
                  
                  {!selectedObservation.comparisons.vs_policy_baseline ? (
                    <Alert severity="info" sx={{ mb: 3 }}>
                      <Typography variant="body2">
                        Policy-specific baseline data is not available for this observation. 
                        This may occur if:
                      </Typography>
                      <Typography component="ul" variant="body2" sx={{ mt: 1, pl: 2 }}>
                        <li>No policy-specific baseline has been computed yet</li>
                        <li>The policy baseline analysis is still in progress</li>
                        <li>The observation was created before policy-specific baselines were available</li>
                      </Typography>
                      <Typography variant="body2" sx={{ mt: 1 }}>
                        Please run a policy-specific baseline analysis from the Baseline Analysis page to generate this comparison.
                      </Typography>
                    </Alert>
                  ) : (
                  <Grid container spacing={3}>
                    {/* Utilization Metrics */}
                      <Grid item xs={12} md={6}>
                      <Card sx={{ 
                        height: '100%',
                        bgcolor: 'white',
                        borderRadius: 0,
                        boxShadow: 'none',
                        border: '1px solid #E5E7EB'
                      }}>
                        <CardContent sx={{ p: 3 }}>
                          <Typography variant="h6" gutterBottom sx={{ 
                            mb: 3, 
                            color: '#0F172A', 
                            fontWeight: 600,
                            fontSize: '1rem',
                            letterSpacing: '-0.01em'
                          }}>
                            Utilization Metrics
                          </Typography>
                          
                          {(() => {
                            const baselineUtil = selectedObservation.comparisons.vs_policy_baseline?.baseline_utilization_per_1k ?? null
                            const observedUtil = selectedObservation.comparisons.vs_policy_baseline?.observed_utilization_per_1k ??
                                                 selectedObservation.metrics?.utilization_per_1k ?? null
                            
                            return (
                              <>
                                <Box sx={{ mb: 3 }}>
                                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1.5 }}>
                                    <Typography variant="body2" sx={{ 
                                      color: '#64748B', 
                                      fontWeight: 500,
                                      fontSize: '0.875rem'
                                    }}>
                                      Policy Baseline
                                    </Typography>
                                    <Typography variant="h6" fontWeight={600} sx={{ 
                                      color: '#0F172A',
                                      fontSize: '1.125rem'
                                    }}>
                                      {baselineUtil !== null && baselineUtil !== undefined ? baselineUtil.toFixed(1) : 'N/A'}
                                    </Typography>
                                  </Box>
                                  <LinearProgress 
                                    variant="determinate" 
                                    value={Math.min((baselineUtil || 0) / 200 * 100, 100)}
                                    sx={{ 
                                      height: 6, 
                                      borderRadius: 0, 
                                      mb: 3, 
                                      bgcolor: '#F1F5F9', 
                                      '& .MuiLinearProgress-bar': { bgcolor: '#1E2A44' } 
                                    }}
                                  />
                                </Box>

                                <Box sx={{ mb: 3 }}>
                                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1.5 }}>
                                    <Typography variant="body2" sx={{ 
                                      color: '#64748B', 
                                      fontWeight: 500,
                                      fontSize: '0.875rem'
                                    }}>
                                      Observed
                                    </Typography>
                                    <Typography variant="h6" fontWeight={600} sx={{ 
                                      color: '#3B2F8F',
                                      fontSize: '1.125rem'
                                    }}>
                                      {observedUtil !== null && observedUtil !== undefined ? observedUtil.toFixed(1) : 'N/A'}
                                    </Typography>
                                  </Box>
                                  <LinearProgress 
                                    variant="determinate" 
                                    value={Math.min((observedUtil || 0) / 200 * 100, 100)}
                                    sx={{ 
                                      height: 6, 
                                      borderRadius: 0, 
                                      mb: 3, 
                                      bgcolor: '#F1F5F9', 
                                      '& .MuiLinearProgress-bar': { bgcolor: '#3B2F8F' } 
                                    }}
                                  />
                                </Box>
                              </>
                            )
                          })()}

                          <Box sx={{ 
                            p: 3, 
                            bgcolor: (selectedObservation.comparisons.vs_policy_baseline?.utilization_change_pct || 0) < 0
                              ? '#E8F5E9'
                              : '#FFEBEE',
                            color: (selectedObservation.comparisons.vs_policy_baseline?.utilization_change_pct || 0) < 0
                              ? '#1B5E20'
                              : '#B71C1C',
                            border: '1px solid',
                            borderColor: (selectedObservation.comparisons.vs_policy_baseline?.utilization_change_pct || 0) < 0
                              ? '#C8E6C9'
                              : '#FFCDD2'
                          }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                {(selectedObservation.comparisons.vs_policy_baseline?.utilization_change_pct || 0) < 0 ? (
                                  <TrendingDownIcon sx={{ fontSize: 20, color: '#2E8B57' }} />
                                ) : (
                                  <TrendingUpIcon sx={{ fontSize: 20, color: '#C04A4A' }} />
                                )}
                                <Typography variant="body2" fontWeight={600} sx={{ 
                                  fontSize: '0.875rem', 
                                  color: (selectedObservation.comparisons.vs_policy_baseline?.utilization_change_pct || 0) < 0
                                    ? '#1B5E20'
                                    : '#B71C1C'
                                }}>
                                  Change
                                </Typography>
                              </Box>
                              <Typography variant="h6" fontWeight={700} sx={{ 
                                fontSize: '1.125rem', 
                                color: (selectedObservation.comparisons.vs_policy_baseline?.utilization_change_pct || 0) < 0
                                  ? '#2E8B57'
                                  : '#C04A4A'
                              }}>
                                {((selectedObservation.comparisons.vs_policy_baseline?.utilization_change ?? 0) >= 0) ? '+' : ''}
                                {selectedObservation.comparisons.vs_policy_baseline?.utilization_change?.toFixed(2) || 'N/A'}
                                </Typography>
                            </Box>
                            <Typography variant="h4" fontWeight={700} sx={{ 
                              letterSpacing: '-0.02em',
                              lineHeight: 1.2,
                              color: (selectedObservation.comparisons.vs_policy_baseline?.utilization_change_pct || 0) < 0
                                ? '#2E8B57'
                                : '#C04A4A'
                            }}>
                                  {((selectedObservation.comparisons.vs_policy_baseline?.utilization_change_pct ?? 0) >= 0) ? '+' : ''}
                                  {selectedObservation.comparisons.vs_policy_baseline?.utilization_change_pct?.toFixed(1) || 'N/A'}%
                                </Typography>
                          </Box>
                        </CardContent>
                      </Card>
                      </Grid>

                    {/* Cost Metrics */}
                      <Grid item xs={12} md={6}>
                      <Card sx={{ 
                        height: '100%',
                        bgcolor: 'white',
                        borderRadius: 0,
                        boxShadow: 'none',
                        border: '1px solid #E5E7EB'
                      }}>
                        <CardContent sx={{ p: 3 }}>
                          <Typography variant="h6" gutterBottom sx={{ 
                            mb: 3, 
                            color: '#0F172A', 
                            fontWeight: 600,
                            fontSize: '1rem',
                            letterSpacing: '-0.01em'
                          }}>
                            Cost Metrics
                                </Typography>
                          
                          {(() => {
                            const baselineCost = selectedObservation.comparisons.vs_policy_baseline?.baseline_cost_pmpm ?? null
                            const observedCost = selectedObservation.comparisons.vs_policy_baseline?.observed_cost_pmpm ??
                                                 selectedObservation.metrics?.cost_pmpm ??
                                                 selectedObservation.metrics?.cost_per_member ?? null
                            
                            return (
                              <>
                                <Box sx={{ mb: 3 }}>
                                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1.5 }}>
                                    <Typography variant="body2" sx={{ 
                                      color: '#64748B', 
                                      fontWeight: 500,
                                      fontSize: '0.875rem'
                                    }}>
                                      Policy Baseline (PMPM)
                                    </Typography>
                                    <Typography variant="h6" fontWeight={600} sx={{ 
                                      color: '#0F172A',
                                      fontSize: '1.125rem'
                                    }}>
                                      ${baselineCost !== null && baselineCost !== undefined ? baselineCost.toFixed(2) : 'N/A'}
                                    </Typography>
                                  </Box>
                                  <LinearProgress 
                                    variant="determinate" 
                                    value={Math.min(((baselineCost ?? 0) / 100) * 100, 100)}
                                    sx={{ 
                                      height: 6, 
                                      borderRadius: 0, 
                                      mb: 3, 
                                      bgcolor: '#F1F5F9', 
                                      '& .MuiLinearProgress-bar': { bgcolor: '#1E2A44' } 
                                    }}
                                  />
                                </Box>

                                <Box sx={{ mb: 3 }}>
                                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1.5 }}>
                                    <Typography variant="body2" sx={{ 
                                      color: '#64748B', 
                                      fontWeight: 500,
                                      fontSize: '0.875rem'
                                    }}>
                                      Observed (PMPM)
                                    </Typography>
                                    <Typography variant="h6" fontWeight={600} sx={{ 
                                      color: '#2EC4C6',
                                      fontSize: '1.125rem'
                                    }}>
                                      ${observedCost !== null && observedCost !== undefined ? observedCost.toFixed(2) : 'N/A'}
                                    </Typography>
                                  </Box>
                                  <LinearProgress 
                                    variant="determinate" 
                                    value={Math.min(((observedCost ?? 0) / 100) * 100, 100)}
                                    sx={{ 
                                      height: 6, 
                                      borderRadius: 0, 
                                      mb: 3, 
                                      bgcolor: '#F1F5F9', 
                                      '& .MuiLinearProgress-bar': { bgcolor: '#2EC4C6' } 
                                    }}
                                  />
                                </Box>
                              </>
                            )
                          })()}

                          <Box sx={{ 
                            p: 3, 
                            bgcolor: (selectedObservation.comparisons.vs_policy_baseline.cost_change_pct || 0) < 0
                              ? '#E8F5E9'
                              : '#FFEBEE',
                            color: (selectedObservation.comparisons.vs_policy_baseline.cost_change_pct || 0) < 0
                              ? '#1B5E20'
                              : '#B71C1C',
                            border: '1px solid',
                            borderColor: (selectedObservation.comparisons.vs_policy_baseline.cost_change_pct || 0) < 0
                              ? '#C8E6C9'
                              : '#FFCDD2'
                          }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                {(selectedObservation.comparisons.vs_policy_baseline.cost_change_pct || 0) < 0 ? (
                                  <TrendingDownIcon sx={{ fontSize: 20, color: '#2E8B57' }} />
                                ) : (
                                  <TrendingUpIcon sx={{ fontSize: 20, color: '#C04A4A' }} />
                                )}
                                <Typography variant="body2" fontWeight={600} sx={{ 
                                  fontSize: '0.875rem', 
                                  color: (selectedObservation.comparisons.vs_policy_baseline.cost_change_pct || 0) < 0
                                    ? '#1B5E20'
                                    : '#B71C1C'
                                }}>
                                  Change (PMPM)
                                </Typography>
                              </Box>
                              <Typography variant="h6" fontWeight={700} sx={{ 
                                fontSize: '1.125rem', 
                                color: (selectedObservation.comparisons.vs_policy_baseline.cost_change_pct || 0) < 0
                                  ? '#2E8B57'
                                  : '#C04A4A'
                              }}>
                              {((selectedObservation.comparisons.vs_policy_baseline?.cost_change_pmpm ?? 0) >= 0) ? '+' : ''}
                                ${selectedObservation.comparisons.vs_policy_baseline?.cost_change_pmpm?.toFixed(2) || 'N/A'}
                                </Typography>
                            </Box>
                            <Typography variant="h4" fontWeight={700} sx={{ 
                              letterSpacing: '-0.02em',
                              lineHeight: 1.2,
                              color: (selectedObservation.comparisons.vs_policy_baseline.cost_change_pct || 0) < 0
                                ? '#2E8B57'
                                : '#C04A4A'
                            }}>
                              {((selectedObservation.comparisons.vs_policy_baseline?.cost_change_pct ?? 0) >= 0) ? '+' : ''}
                              {selectedObservation.comparisons.vs_policy_baseline?.cost_change_pct?.toFixed(1) || 'N/A'}%
                                </Typography>
                          </Box>
                  </CardContent>
                </Card>
                    </Grid>
                  </Grid>
                  )}
                </Box>
              )}

              {tabValue === 3 && selectedObservation.comparisons.vs_predicted && (
                <Box>
                  <Typography variant="h6" gutterBottom sx={{ 
                    mb: 4, 
                    fontWeight: 600, 
                    color: '#0F172A',
                    fontSize: '1.25rem',
                    letterSpacing: '-0.01em'
                  }}>
                    Predicted vs Observed Comparison
                                </Typography>

                  {/* Prediction Accuracy Card - Prominent */}
                  <Card sx={{ 
                    mb: 4,
                    bgcolor: (selectedObservation.comparisons.vs_predicted.prediction_accuracy_pct || 0) >= 80
                      ? '#E8F5E9'
                      : (selectedObservation.comparisons.vs_predicted.prediction_accuracy_pct || 0) >= 60
                      ? '#FFF3E0'
                      : '#FFEBEE',
                    color: (selectedObservation.comparisons.vs_predicted.prediction_accuracy_pct || 0) >= 80
                      ? '#1B5E20'
                      : (selectedObservation.comparisons.vs_predicted.prediction_accuracy_pct || 0) >= 60
                      ? '#E65100'
                      : '#B71C1C',
                    borderRadius: 0,
                    boxShadow: 'none',
                    border: '1px solid',
                    borderColor: (selectedObservation.comparisons.vs_predicted.prediction_accuracy_pct || 0) >= 80
                      ? '#C8E6C9'
                      : (selectedObservation.comparisons.vs_predicted.prediction_accuracy_pct || 0) >= 60
                      ? '#FFE0B2'
                      : '#FFCDD2'
                  }}>
                    <CardContent sx={{ p: 4 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                        <Box>
                          <Typography variant="overline" sx={{ 
                            fontSize: '0.6875rem',
                            fontWeight: 600,
                            letterSpacing: '0.08em',
                            color: (selectedObservation.comparisons.vs_predicted.prediction_accuracy_pct || 0) >= 80
                              ? '#2E7D32'
                              : (selectedObservation.comparisons.vs_predicted.prediction_accuracy_pct || 0) >= 60
                              ? '#F57C00'
                              : '#C62828',
                            textTransform: 'uppercase',
                            mb: 1.5,
                            display: 'block'
                          }}>
                            Overall Prediction Accuracy
                                </Typography>
                            <Typography variant="h2" sx={{ 
                            fontWeight: 700,
                            letterSpacing: '-0.03em',
                            lineHeight: 1.1,
                            color: (selectedObservation.comparisons.vs_predicted.prediction_accuracy_pct ?? null) == null
                              ? 'text.secondary'
                              : (selectedObservation.comparisons.vs_predicted.prediction_accuracy_pct || 0) >= 80
                              ? '#2E8B57'
                              : (selectedObservation.comparisons.vs_predicted.prediction_accuracy_pct || 0) >= 60
                              ? '#E6A23C'
                              : '#C04A4A'
                          }}>
                                  {(selectedObservation.comparisons.vs_predicted.prediction_accuracy_pct != null
                                    ? `${selectedObservation.comparisons.vs_predicted.prediction_accuracy_pct.toFixed(1)}%`
                                    : 'N/A')}
                                </Typography>
                          {(selectedObservation.comparisons.vs_predicted.prediction_accuracy_pct ?? null) == null && (
                            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                              Prediction not available for this policy yet
                            </Typography>
                          )}
                        </Box>
                        {(selectedObservation.comparisons.vs_predicted.prediction_accuracy_pct ?? null) != null && (selectedObservation.comparisons.vs_predicted.prediction_accuracy_pct || 0) >= 80 ? (
                          <CheckCircleIcon sx={{ fontSize: 64, opacity: 0.9, color: '#2E8B57' }} />
                        ) : (
                          <WarningIcon sx={{ fontSize: 64, opacity: 0.9, color: '#E6A23C' }} />
                        )}
                      </Box>
                                <LinearProgress
                                  variant="determinate"
                                  value={Math.min(Math.max(selectedObservation.comparisons.vs_predicted.prediction_accuracy_pct || 0, 0), 100)}
                        sx={{ 
                          height: 8, 
                          borderRadius: 0,
                          bgcolor: (selectedObservation.comparisons.vs_predicted.prediction_accuracy_pct || 0) >= 80
                            ? 'rgba(46, 125, 50, 0.2)'
                            : (selectedObservation.comparisons.vs_predicted.prediction_accuracy_pct || 0) >= 60
                            ? 'rgba(230, 81, 0, 0.2)'
                            : 'rgba(198, 40, 40, 0.2)',
                          '& .MuiLinearProgress-bar': {
                            bgcolor: (selectedObservation.comparisons.vs_predicted.prediction_accuracy_pct || 0) >= 80
                              ? '#2E8B57'
                              : (selectedObservation.comparisons.vs_predicted.prediction_accuracy_pct || 0) >= 60
                              ? '#E6A23C'
                              : '#C04A4A'
                          }
                        }}
                      />
                      <Typography variant="body2" sx={{ 
                        mt: 2.5, 
                        fontSize: '0.875rem',
                        fontWeight: 500,
                        color: (selectedObservation.comparisons.vs_predicted.prediction_accuracy_pct || 0) >= 80
                          ? '#1B5E20'
                          : (selectedObservation.comparisons.vs_predicted.prediction_accuracy_pct || 0) >= 60
                          ? '#E65100'
                          : '#B71C1C'
                      }}>
                                  {selectedObservation.comparisons.vs_predicted.within_predicted_range 
                                    ? 'Within predicted range' 
                                    : selectedObservation.comparisons.vs_predicted.within_predicted_range === false
                                    ? 'Outside predicted range'
                                    : 'Range not determined'}
                                </Typography>
                    </CardContent>
                  </Card>

                  <Grid container spacing={2.5}>
                    {/* Utilization Metrics */}
                    <Grid item xs={12} md={6}>
                      <Card sx={{ 
                        height: '100%',
                        bgcolor: 'white',
                        borderRadius: 0,
                        boxShadow: 'none',
                        border: '1px solid #E5E7EB'
                      }}>
                        <CardContent sx={{ p: 3 }}>
                          <Typography variant="h6" gutterBottom sx={{ 
                            mb: 3, 
                            color: '#0F172A', 
                            fontWeight: 600,
                            fontSize: '1rem',
                            letterSpacing: '-0.01em'
                          }}>
                            Utilization Metrics
                          </Typography>
                          
                          {(() => {
                            const predictedUtil = selectedObservation.comparisons.vs_predicted?.predicted_utilization ?? null
                            const observedUtil = selectedObservation.comparisons.vs_predicted?.observed_utilization ?? 
                                                 selectedObservation.metrics?.utilization_per_1k ?? null
                            
                            return (
                              <>
                                <Box sx={{ mb: 3, pb: 3, borderBottom: '1px solid #F1F5F9' }}>
                                  <Typography variant="body2" sx={{ 
                                    color: '#64748B', 
                                    fontWeight: 500,
                                    fontSize: '0.875rem',
                                    mb: 1
                                  }}>
                                    Predicted
                                  </Typography>
                                  <Typography variant="h6" fontWeight={600} sx={{ 
                                    color: '#0F172A',
                                    fontSize: '1.125rem'
                                  }}>
                                    {predictedUtil !== null && predictedUtil !== undefined ? predictedUtil.toFixed(1) : 'N/A'}
                                  </Typography>
                                  {/* Confidence Interval */}
                                  {selectedObservation.comparisons.vs_predicted?.confidence_intervals?.utilization && (
                                    <Typography variant="body2" sx={{ 
                                      color: '#64748B', 
                                      fontSize: '0.8125rem',
                                      mt: 0.5,
                                      fontStyle: 'italic'
                                    }}>
                                      Range: {selectedObservation.comparisons.vs_predicted.confidence_intervals.utilization.lower_bound?.toFixed(1) || 'N/A'} - {selectedObservation.comparisons.vs_predicted.confidence_intervals.utilization.upper_bound?.toFixed(1) || 'N/A'}
                                    </Typography>
                                  )}
                                </Box>

                                <Box sx={{ mb: 3, pb: 3, borderBottom: '1px solid #F1F5F9' }}>
                                  <Typography variant="body2" sx={{ 
                                    color: '#64748B', 
                                    fontWeight: 500,
                                    fontSize: '0.875rem',
                                    mb: 1
                                  }}>
                                    Observed
                                  </Typography>
                                  <Typography variant="h6" fontWeight={600} sx={{ 
                                    color: '#3B2F8F',
                                    fontSize: '1.125rem'
                                  }}>
                                    {observedUtil !== null && observedUtil !== undefined ? observedUtil.toFixed(1) : 'N/A'}
                                  </Typography>
                                </Box>
                              </>
                            )
                          })()}

                          <Box sx={{ 
                            p: 3, 
                            bgcolor: Math.abs(selectedObservation.comparisons.vs_predicted.utilization_prediction_error || 0) < 10
                              ? '#2E8B57'
                              : '#C04A4A',
                            color: 'white',
                            border: 'none',
                            mb: 2
                          }}>
                            <Typography variant="overline" sx={{ 
                              fontSize: '0.6875rem',
                              fontWeight: 600,
                              letterSpacing: '0.08em',
                              color: 'rgba(255,255,255,0.8)',
                              textTransform: 'uppercase',
                              mb: 1,
                              display: 'block'
                            }}>
                              Prediction Error
                            </Typography>
                            <Typography variant="h4" fontWeight={700} sx={{ 
                              letterSpacing: '-0.02em',
                              lineHeight: 1.2,
                              mb: 0.5
                            }}>
                              {selectedObservation.comparisons.vs_predicted.utilization_prediction_error?.toFixed(2) || 'N/A'}
                            </Typography>
                            <Typography variant="body1" sx={{ opacity: 0.9, fontSize: '0.9375rem' }}>
                              {selectedObservation.comparisons.vs_predicted.utilization_prediction_error_pct?.toFixed(1) || 'N/A'}%
                            </Typography>
                          </Box>

                          <Box sx={{ 
                            p: 2, 
                            bgcolor: '#F8FAFC', 
                            border: '1px solid #E5E7EB'
                          }}>
                            <Typography variant="body2" sx={{ 
                              color: '#64748B', 
                              fontWeight: 500,
                              fontSize: '0.875rem',
                              mb: 0.5
                            }}>
                              Predicted Change
                            </Typography>
                            <Typography variant="body1" fontWeight={600} sx={{ 
                              color: '#0F172A',
                              fontSize: '1rem'
                            }}>
                              {selectedObservation.comparisons.vs_predicted.predicted_utilization_change?.toFixed(2) || 'N/A'}
                            </Typography>
                          </Box>
                        </CardContent>
                      </Card>
                              </Grid>

                    {/* Cost Metrics */}
                    <Grid item xs={12} md={6}>
                      <Card sx={{ 
                        height: '100%',
                        bgcolor: 'white',
                        borderRadius: 0,
                        boxShadow: 'none',
                        border: '1px solid #E5E7EB'
                      }}>
                        <CardContent sx={{ p: 3 }}>
                          <Typography variant="h6" gutterBottom sx={{ 
                            mb: 3, 
                            color: '#0F172A', 
                            fontWeight: 600,
                            fontSize: '1rem',
                            letterSpacing: '-0.01em'
                          }}>
                            Cost Metrics
                          </Typography>
                          
                          {(() => {
                            const predictedCost = selectedObservation.comparisons.vs_predicted?.predicted_cost_pmpm ?? null
                            const observedCost = selectedObservation.comparisons.vs_predicted?.observed_cost_pmpm ?? 
                                                 selectedObservation.metrics?.cost_pmpm ??
                                                 selectedObservation.metrics?.cost_per_member ?? null
                            
                            return (
                              <>
                                <Box sx={{ mb: 3, pb: 3, borderBottom: '1px solid #F1F5F9' }}>
                                  <Typography variant="body2" sx={{ 
                                    color: '#64748B', 
                                    fontWeight: 500,
                                    fontSize: '0.875rem',
                                    mb: 1
                                  }}>
                                    Predicted (PMPM)
                                  </Typography>
                                  <Typography variant="h6" fontWeight={600} sx={{ 
                                    color: '#0F172A',
                                    fontSize: '1.125rem'
                                  }}>
                                    ${predictedCost !== null && predictedCost !== undefined ? predictedCost.toFixed(2) : 'N/A'}
                                  </Typography>
                                  {/* Confidence Interval */}
                                  {selectedObservation.comparisons.vs_predicted?.confidence_intervals?.cost && (
                                    <Typography variant="body2" sx={{ 
                                      color: '#64748B', 
                                      fontSize: '0.8125rem',
                                      mt: 0.5,
                                      fontStyle: 'italic'
                                    }}>
                                      Range: ${selectedObservation.comparisons.vs_predicted.confidence_intervals.cost.lower_bound?.toFixed(2) || 'N/A'} - ${selectedObservation.comparisons.vs_predicted.confidence_intervals.cost.upper_bound?.toFixed(2) || 'N/A'}
                                    </Typography>
                                  )}
                                </Box>

                                <Box sx={{ mb: 3, pb: 3, borderBottom: '1px solid #F1F5F9' }}>
                                  <Typography variant="body2" sx={{ 
                                    color: '#64748B', 
                                    fontWeight: 500,
                                    fontSize: '0.875rem',
                                    mb: 1
                                  }}>
                                    Observed (PMPM)
                                  </Typography>
                                  <Typography variant="h6" fontWeight={600} sx={{ 
                                    color: '#2EC4C6',
                                    fontSize: '1.125rem'
                                  }}>
                                    ${observedCost !== null && observedCost !== undefined ? observedCost.toFixed(2) : 'N/A'}
                                  </Typography>
                                </Box>
                              </>
                            )
                          })()}

                          <Box sx={{ 
                            p: 3, 
                            bgcolor: Math.abs(selectedObservation.comparisons.vs_predicted.cost_prediction_error || 0) < 10
                              ? '#2E8B57'
                              : '#C04A4A',
                            color: 'white',
                            border: 'none',
                            mb: 2
                          }}>
                            <Typography variant="overline" sx={{ 
                              fontSize: '0.6875rem',
                              fontWeight: 600,
                              letterSpacing: '0.08em',
                              color: 'rgba(255,255,255,0.8)',
                              textTransform: 'uppercase',
                              mb: 1,
                              display: 'block'
                            }}>
                              Prediction Error
                            </Typography>
                            <Typography variant="h4" fontWeight={700} sx={{ 
                              letterSpacing: '-0.02em',
                              lineHeight: 1.2,
                              mb: 0.5
                            }}>
                              ${selectedObservation.comparisons.vs_predicted.cost_prediction_error?.toFixed(2) || 'N/A'}
                            </Typography>
                            <Typography variant="body1" sx={{ opacity: 0.9, fontSize: '0.9375rem' }}>
                              {selectedObservation.comparisons.vs_predicted.cost_prediction_error_pct?.toFixed(1) || 'N/A'}%
                            </Typography>
                          </Box>

                          <Box sx={{ 
                            p: 2, 
                            bgcolor: '#F8FAFC', 
                            border: '1px solid #E5E7EB'
                          }}>
                            <Typography variant="body2" sx={{ 
                              color: '#64748B', 
                              fontWeight: 500,
                              fontSize: '0.875rem',
                              mb: 0.5
                            }}>
                              Predicted Change (PMPM)
                            </Typography>
                            <Typography variant="body1" fontWeight={600} sx={{ 
                              color: '#0F172A',
                              fontSize: '1rem'
                            }}>
                              ${selectedObservation.comparisons.vs_predicted.predicted_cost_change_pmpm?.toFixed(2) || 'N/A'}
                            </Typography>
                          </Box>
                          </CardContent>
                        </Card>
                    </Grid>

                    {/* Effect Size */}
                    <Grid item xs={12}>
                      <Card sx={{ 
                        bgcolor: 'white',
                        borderRadius: 0,
                        boxShadow: 'none',
                        border: '1px solid #E5E7EB'
                      }}>
                        <CardContent sx={{ p: 3 }}>
                          <Typography variant="h6" gutterBottom sx={{ 
                            mb: 3, 
                            color: '#0F172A', 
                            fontWeight: 600,
                            fontSize: '1rem',
                            letterSpacing: '-0.01em'
                          }}>
                            Overall Effect Size
                          </Typography>
                          <Grid container spacing={2.5}>
                            <Grid item xs={12} md={4}>
                              <Box sx={{ 
                                textAlign: 'center', 
                                p: 3, 
                                bgcolor: '#F8FAFC', 
                                border: '1px solid #E5E7EB'
                              }}>
                                <Typography variant="overline" sx={{ 
                                  fontSize: '0.6875rem',
                                  fontWeight: 600,
                                  letterSpacing: '0.08em',
                                  color: '#64748B',
                                  textTransform: 'uppercase',
                                  mb: 1.5,
                                  display: 'block'
                                }}>
                                  Predicted
                                </Typography>
                                <Typography variant="h4" fontWeight={700} sx={{ 
                                  color: '#0F172A',
                                  letterSpacing: '-0.02em',
                                  lineHeight: 1.2
                                }}>
                                  {selectedObservation.comparisons.vs_predicted.predicted_effect_size?.toFixed(2) || 'N/A'}
                                </Typography>
                              </Box>
                            </Grid>
                            <Grid item xs={12} md={4}>
                              <Box sx={{ 
                                textAlign: 'center', 
                                p: 3, 
                                bgcolor: '#E8E5F5',
                                color: '#3B2F8F',
                                border: '1px solid #D4CEE8'
                              }}>
                                <Typography variant="overline" sx={{ 
                                  fontSize: '0.6875rem',
                                  fontWeight: 600,
                                  letterSpacing: '0.08em',
                                  color: '#64748B',
                                  textTransform: 'uppercase',
                                  mb: 1.5,
                                  display: 'block'
                                }}>
                                  Observed
                                </Typography>
                                <Typography variant="h4" fontWeight={700} sx={{ 
                                  letterSpacing: '-0.02em',
                                  lineHeight: 1.2,
                                  color: '#3B2F8F'
                                }}>
                                  {selectedObservation.comparisons.vs_predicted.observed_effect_size?.toFixed(2) || 'N/A'}
                                </Typography>
                              </Box>
                            </Grid>
                            <Grid item xs={12} md={4}>
                              <Box sx={{ 
                                textAlign: 'center', 
                                p: 3, 
                                bgcolor: Math.abs(selectedObservation.comparisons.vs_predicted.prediction_error || 0) < 0.1
                                  ? '#2E8B57'
                                  : '#C04A4A',
                                color: 'white',
                                border: 'none'
                              }}>
                                <Typography variant="overline" sx={{ 
                                  fontSize: '0.6875rem',
                                  fontWeight: 600,
                                  letterSpacing: '0.08em',
                                  color: 'rgba(255,255,255,0.8)',
                                  textTransform: 'uppercase',
                                  mb: 1.5,
                                  display: 'block'
                                }}>
                                  Error
                                </Typography>
                                <Typography variant="h4" fontWeight={700} sx={{ 
                                  letterSpacing: '-0.02em',
                                  lineHeight: 1.2
                                }}>
                                  {selectedObservation.comparisons.vs_predicted.prediction_error?.toFixed(2) || 'N/A'}
                                </Typography>
                              </Box>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
                    </Grid>
                  </Grid>

                  {/* Ramp-Up Projections */}
                  {selectedObservation.comparisons.vs_predicted?.ramp_up_projections && (
                    <Card sx={{ 
                      mt: 4,
                      bgcolor: 'white',
                      borderRadius: 0,
                      boxShadow: 'none',
                      border: '1px solid #E5E7EB'
                    }}>
                      <CardContent sx={{ p: 3 }}>
                        <Typography variant="h6" gutterBottom sx={{ 
                          mb: 3, 
                          color: '#0F172A', 
                          fontWeight: 600,
                          fontSize: '1rem',
                          letterSpacing: '-0.01em'
                        }}>
                          Time-Based Ramp-Up Projections
                        </Typography>
                        <Typography variant="body2" sx={{ 
                          color: '#64748B', 
                          mb: 3,
                          fontSize: '0.875rem'
                        }}>
                          Policy effects typically ramp up gradually over time. Below shows the projected effect at different time horizons.
                        </Typography>
                        
                        {selectedObservation.comparisons.vs_predicted?.ramp_up_projections?.utilization?.ramp_up_values && (
                          <Box sx={{ mb: 4 }}>
                            <Typography variant="subtitle2" sx={{ 
                              mb: 2, 
                              color: '#0F172A', 
                              fontWeight: 600,
                              fontSize: '0.9375rem'
                            }}>
                              Utilization Ramp-Up
                            </Typography>
                            <ResponsiveContainer width="100%" height={300}>
                              <LineChart data={selectedObservation.comparisons.vs_predicted.ramp_up_projections!.utilization!.ramp_up_values!.map((rv: any) => ({
                                month: rv.month,
                                value: rv.predicted_value,
                                effect: rv.effect_achieved_pct,
                              }))}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                                <XAxis dataKey="month" label={{ value: 'Month', position: 'insideBottom', offset: -5 }} stroke="#64748B" />
                                <YAxis label={{ value: 'Utilization per 1K', angle: -90, position: 'insideLeft' }} stroke="#64748B" />
                                <Tooltip 
                                  contentStyle={{ 
                                    backgroundColor: '#FFFFFF', 
                                    color: '#0F172A',
                                    border: '1px solid #E5E7EB',
                                    borderRadius: 6,
                                    boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -2px rgba(0,0,0,0.1)'
                                  }}
                                  formatter={(value: any) => [value.toFixed(1), 'Utilization']}
                                />
                                <Line 
                                  type="monotone" 
                                  dataKey="value" 
                                  stroke="#3B2F8F" 
                                  strokeWidth={3}
                                  dot={{ fill: '#3B2F8F', r: 4 }}
                                  name="Predicted Utilization"
                                />
                              </LineChart>
                            </ResponsiveContainer>
                            <Box sx={{ mt: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                              {[1, 3, 6, 12].map(month => {
                                const rampValue = selectedObservation.comparisons.vs_predicted?.ramp_up_projections?.utilization?.ramp_up_values?.find((rv: any) => rv.month === month)
                                if (!rampValue) return null
                                return (
                                  <Chip
                                    key={month}
                                    label={`Month ${month}: ${rampValue.predicted_value.toFixed(1)} (${rampValue.effect_achieved_pct.toFixed(0)}% effect)`}
                                    sx={{
                                      bgcolor: '#E8E5F5',
                                      color: '#3B2F8F',
                                      fontWeight: 500,
                                      fontSize: '0.8125rem'
                                    }}
                                  />
                                )
                              })}
                            </Box>
                          </Box>
                        )}

                        {selectedObservation.comparisons.vs_predicted.ramp_up_projections.cost && (
                          <Box>
                            <Typography variant="subtitle2" sx={{ 
                              mb: 2, 
                              color: '#0F172A', 
                              fontWeight: 600,
                              fontSize: '0.9375rem'
                            }}>
                              Cost Ramp-Up
                            </Typography>
                            <ResponsiveContainer width="100%" height={300}>
                              <LineChart data={selectedObservation.comparisons.vs_predicted.ramp_up_projections.cost.ramp_up_values.map((rv: any) => ({
                                month: rv.month,
                                value: rv.predicted_value,
                                effect: rv.effect_achieved_pct,
                              }))}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                                <XAxis dataKey="month" label={{ value: 'Month', position: 'insideBottom', offset: -5 }} stroke="#64748B" />
                                <YAxis label={{ value: 'Cost PMPM', angle: -90, position: 'insideLeft' }} stroke="#64748B" />
                                <Tooltip 
                                  contentStyle={{ 
                                    backgroundColor: '#FFFFFF', 
                                    color: '#0F172A',
                                    border: '1px solid #E5E7EB',
                                    borderRadius: 6,
                                    boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -2px rgba(0,0,0,0.1)'
                                  }}
                                  formatter={(value: any) => [`$${value.toFixed(2)}`, 'Cost PMPM']}
                                />
                                <Line 
                                  type="monotone" 
                                  dataKey="value" 
                                  stroke="#2EC4C6" 
                                  strokeWidth={3}
                                  dot={{ fill: '#2EC4C6', r: 4 }}
                                  name="Predicted Cost"
                                />
                              </LineChart>
                            </ResponsiveContainer>
                            <Box sx={{ mt: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                              {[1, 3, 6, 12].map(month => {
                                const rampValue = selectedObservation.comparisons.vs_predicted.ramp_up_projections.cost.ramp_up_values.find((rv: any) => rv.month === month)
                                if (!rampValue) return null
                                return (
                                  <Chip
                                    key={month}
                                    label={`Month ${month}: $${rampValue.predicted_value.toFixed(2)} (${rampValue.effect_achieved_pct.toFixed(0)}% effect)`}
                                    sx={{
                                      bgcolor: '#E0F7F8',
                                      color: '#0F172A',
                                      fontWeight: 500,
                                      fontSize: '0.8125rem'
                                    }}
                                  />
                                )
                              })}
                            </Box>
                          </Box>
                        )}
                      </CardContent>
                    </Card>
                  )}
                </Box>
              )}

              {tabValue === 4 && selectedObservation.behavioral_explanation && (
                <Box>
                  <Typography variant="h6" gutterBottom sx={{ 
                    mb: 4, 
                    fontWeight: 600, 
                    color: '#0F172A',
                    fontSize: '1.25rem',
                    letterSpacing: '-0.01em'
                  }}>
                    Behavioral Explanation
                  </Typography>
                    {(() => {
                      const explanation = selectedObservation.behavioral_explanation
                      if (!explanation || Object.keys(explanation).length === 0) {
                        return (
                          <Typography color="text.secondary" sx={{ mt: 2 }}>
                            No behavioral explanation available for this observation.
                          </Typography>
                        )
                      }
                      
                      // Always render summary first if available, then metrics
                      const hasMetrics = explanation.effect_size !== undefined || 
                                         explanation.percent_change !== undefined ||
                                         explanation.substitution_patterns ||
                                         explanation.provider_archetype_shares ||
                                         explanation.provider_ordering_intensity_target_per_1000_mm !== undefined ||
                                         explanation.patient_response_shares ||
                                         explanation.provider_segmentation ||
                                         explanation.mix_shifts ||
                                         explanation.performance_narrative ||
                                         explanation.provider_response ||
                                         explanation.patient_response ||
                                         explanation.cost_impact ||
                                         explanation.utilization_trend ||
                                         explanation.strategic_considerations ||
                                         explanation.key_success_factors ||
                                         explanation.risk_factors ||
                                         explanation.actionable_insights ||
                                         explanation.recommendations
                      
                      return (
                        <Box>
                          {(explanation.interpretation_note || explanation.model_inferred_sections?.length) && (
                            <Alert severity="info" sx={{ mb: 3, bgcolor: '#F8FAFC', border: '1px solid #E5E7EB' }}>
                              {explanation.interpretation_note}
                              {explanation.model_inferred_sections?.length > 0 && (
                                <Typography variant="caption" display="block" sx={{ mt: 1, color: '#64748B' }}>
                                  Model-inferred: {explanation.model_inferred_sections.join(', ')}
                                </Typography>
                              )}
                            </Alert>
                          )}
                          {explanation.summary && (
                            <Card sx={{ 
                              mb: 4, 
                              bgcolor: '#E8EDF5',
                              color: '#0F172A',
                              borderRadius: 0,
                              boxShadow: 'none',
                              border: '1px solid #CBD5E1'
                            }}>
                              <CardContent sx={{ p: 4 }}>
                                <Typography variant="overline" sx={{ 
                                  fontSize: '0.6875rem',
                                  fontWeight: 600,
                                  letterSpacing: '0.08em',
                                  color: '#64748B',
                                  textTransform: 'uppercase',
                                  mb: 2,
                                  display: 'block'
                                }}>
                                Executive Summary
                              </Typography>
                                <Typography variant="body1" sx={{ 
                                  lineHeight: 1.8, 
                                  fontSize: '1rem',
                                  color: '#0F172A',
                                  mb: 2,
                                  fontWeight: 500
                                }}>
                                {explanation.summary}
                              </Typography>
                                {explanation.detailed_analysis && Array.isArray(explanation.detailed_analysis) && explanation.detailed_analysis.length > 0 && (
                                  <Box sx={{ mt: 3 }}>
                                    {explanation.detailed_analysis.map((detail: string, idx: number) => (
                                      <Typography key={idx} variant="body2" sx={{ 
                                        lineHeight: 1.7, 
                                        fontSize: '0.9375rem',
                                        color: '#475569',
                                        mb: 1.5
                                      }}>
                                        {detail}
                                      </Typography>
                                    ))}
                                  </Box>
                                )}
                              </CardContent>
                            </Card>
                          )}
                          
                          {hasMetrics && (
                            <>
                            {explanation.effect_size !== undefined && (
                              <Grid container spacing={2.5} sx={{ mb: 4 }}>
                                <Grid item xs={12} sm={6} md={3}>
                                  <Card sx={{ 
                                    p: 3, 
                                    textAlign: 'center', 
                                    height: '100%', 
                                    bgcolor: 'white', 
                                    border: '1px solid #E5E7EB',
                                    borderRadius: 0,
                                    boxShadow: 'none'
                                  }}>
                                    <Typography variant="overline" sx={{ 
                                      fontSize: '0.6875rem',
                                      fontWeight: 600,
                                      letterSpacing: '0.08em',
                                      color: '#64748B',
                                      textTransform: 'uppercase',
                                      mb: 1.5,
                                      display: 'block'
                                    }}>
                                      Effect Size
                                    </Typography>
                                    <Typography variant="h4" fontWeight={700} sx={{ 
                                      color: '#0F172A',
                                      letterSpacing: '-0.02em',
                                      lineHeight: 1.2
                                    }}>
                                    {explanation.effect_size.toFixed(2)}
                                  </Typography>
                                  </Card>
                                </Grid>
                                {explanation.percent_change !== undefined && (
                                  <Grid item xs={12} sm={6} md={3}>
                                    <Card sx={{ 
                                      p: 3, 
                                      textAlign: 'center', 
                                      height: '100%',
                                      bgcolor: explanation.percent_change < 0 ? '#2E8B57' : '#C04A4A',
                                      color: 'white',
                                      border: 'none',
                                      borderRadius: 0,
                                      boxShadow: 'none'
                                    }}>
                                      <Typography variant="overline" sx={{ 
                                        fontSize: '0.6875rem',
                                        fontWeight: 600,
                                        letterSpacing: '0.08em',
                                        color: 'rgba(255,255,255,0.8)',
                                        textTransform: 'uppercase',
                                        mb: 1.5,
                                        display: 'block'
                                      }}>
                                        Percent Change
                                      </Typography>
                                      <Typography variant="h4" fontWeight={700} sx={{ 
                                        letterSpacing: '-0.02em',
                                        lineHeight: 1.2,
                                        color: 'white'
                                      }}>
                                      {explanation.percent_change.toFixed(1)}%
                                    </Typography>
                                    </Card>
                                  </Grid>
                                )}
                              </Grid>
                            )}
                            
                            {explanation.substitution_patterns && Array.isArray(explanation.substitution_patterns) && explanation.substitution_patterns.length > 0 && (
                              <Card sx={{ 
                                mt: 0, 
                                mb: 4, 
                                bgcolor: 'white',
                                borderRadius: 0,
                                boxShadow: 'none',
                                border: '1px solid #E5E7EB'
                              }}>
                                <CardContent sx={{ p: 0 }}>
                                  <Box sx={{ p: 3, borderBottom: '1px solid #E5E7EB' }}>
                                    <Typography variant="h6" sx={{ 
                                      color: '#0F172A', 
                                      fontWeight: 600,
                                      fontSize: '1rem',
                                      letterSpacing: '-0.01em'
                                    }}>
                                  Substitution Patterns
                                </Typography>
                                  </Box>
                                  <TableContainer>
                                    <Table>
                                  <TableHead>
                                        <TableRow sx={{ bgcolor: '#F8FAFC' }}>
                                          <TableCell sx={{ 
                                            fontWeight: 600, 
                                            color: '#0F172A',
                                            fontSize: '0.875rem',
                                            py: 2,
                                            borderBottom: '1px solid #E5E7EB'
                                          }}>
                                            From Service
                                          </TableCell>
                                          <TableCell sx={{ 
                                            fontWeight: 600, 
                                            color: '#0F172A',
                                            fontSize: '0.875rem',
                                            py: 2,
                                            borderBottom: '1px solid #E5E7EB'
                                          }}>
                                            To Service
                                          </TableCell>
                                          <TableCell align="right" sx={{ 
                                            fontWeight: 600, 
                                            color: '#0F172A',
                                            fontSize: '0.875rem',
                                            py: 2,
                                            borderBottom: '1px solid #E5E7EB'
                                          }}>
                                            Count
                                          </TableCell>
                                    </TableRow>
                                  </TableHead>
                                  <TableBody>
                                    {explanation.substitution_patterns.slice(0, 5).map((pattern: any, idx: number) => (
                                          <TableRow 
                                            key={idx} 
                                            hover 
                                            sx={{ 
                                              '&:hover': { bgcolor: '#F8FAFC' },
                                              '&:last-child td': { borderBottom: 'none' }
                                            }}
                                          >
                                            <TableCell sx={{ 
                                              color: '#0F172A',
                                              fontSize: '0.875rem',
                                              py: 2
                                            }}>
                                              {pattern.from_code || pattern.from || 'N/A'}
                                            </TableCell>
                                            <TableCell sx={{ 
                                              color: '#0F172A',
                                              fontSize: '0.875rem',
                                              py: 2
                                            }}>
                                              {pattern.to_code || pattern.to || 'N/A'}
                                            </TableCell>
                                            <TableCell align="right" sx={{ py: 2 }}>
                                              <Chip 
                                                label={pattern.count || pattern.frequency || 'N/A'} 
                                                size="small" 
                                                sx={{ 
                                                  bgcolor: '#3B2F8F', 
                                                  color: 'white', 
                                                  fontWeight: 500,
                                                  fontSize: '0.75rem',
                                                  height: 24
                                                }} 
                                              />
                                            </TableCell>
                                      </TableRow>
                                    ))}
                                  </TableBody>
                                </Table>
                                  </TableContainer>
                                </CardContent>
                              </Card>
                            )}
                            
                            {explanation.provider_archetype_shares && Object.keys(explanation.provider_archetype_shares).length > 0 && (
                              <Card sx={{ 
                                mt: 0, 
                                mb: 4, 
                                bgcolor: 'white',
                                borderRadius: 0,
                                boxShadow: 'none',
                                border: '1px solid #E5E7EB'
                              }}>
                                <CardContent sx={{ p: 0 }}>
                                  <Box sx={{ p: 3, borderBottom: '1px solid #E5E7EB' }}>
                                    <Typography variant="h6" sx={{ 
                                      color: '#0F172A', 
                                      fontWeight: 600,
                                      fontSize: '1rem',
                                      letterSpacing: '-0.01em'
                                    }}>
                                  Provider Archetype Distribution (M17)
                                </Typography>
                                  </Box>
                                  <TableContainer>
                                    <Table>
                                  <TableHead>
                                        <TableRow sx={{ bgcolor: '#F8FAFC' }}>
                                          <TableCell sx={{ 
                                            fontWeight: 600, 
                                            color: '#0F172A',
                                            fontSize: '0.875rem',
                                            py: 2,
                                            borderBottom: '1px solid #E5E7EB'
                                          }}>
                                            Archetype Type
                                          </TableCell>
                                          <TableCell align="right" sx={{ 
                                            fontWeight: 600, 
                                            color: '#0F172A',
                                            fontSize: '0.875rem',
                                            py: 2,
                                            borderBottom: '1px solid #E5E7EB'
                                          }}>
                                            Share (%)
                                          </TableCell>
                                    </TableRow>
                                  </TableHead>
                                  <TableBody>
                                    {Object.entries(explanation.provider_archetype_shares).map(([key, value]: [string, any]) => {
                                      const typeName = key.replace('provider_archetype_share_', '').replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
                                          const shareValue = typeof value === 'number' ? value : parseFloat(value) || 0
                                      return (
                                            <TableRow 
                                              key={key} 
                                              hover 
                                              sx={{ 
                                                '&:hover': { bgcolor: '#F8FAFC' },
                                                '&:last-child td': { borderBottom: 'none' }
                                              }}
                                            >
                                              <TableCell sx={{ 
                                                color: '#0F172A',
                                                fontSize: '0.875rem',
                                                py: 2
                                              }}>
                                                {typeName}
                                              </TableCell>
                                              <TableCell align="right" sx={{ py: 2 }}>
                                                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 2 }}>
                                                  <LinearProgress 
                                                    variant="determinate" 
                                                    value={shareValue} 
                                                    sx={{ 
                                                      width: 120, 
                                                      height: 6, 
                                                      borderRadius: 0, 
                                                      bgcolor: '#F1F5F9', 
                                                      '& .MuiLinearProgress-bar': { bgcolor: '#3B2F8F' } 
                                                    }}
                                                  />
                                                  <Typography variant="body2" fontWeight={600} sx={{ 
                                                    minWidth: 50, 
                                                    color: '#0F172A',
                                                    fontSize: '0.875rem'
                                                  }}>
                                                    {shareValue.toFixed(1)}%
                                                  </Typography>
                                                </Box>
                                              </TableCell>
                                        </TableRow>
                                      )
                                    })}
                                  </TableBody>
                                </Table>
                                  </TableContainer>
                                </CardContent>
                              </Card>
                            )}
                            
                            {explanation.provider_ordering_intensity_target_per_1000_mm !== undefined && (
                              <Card sx={{ 
                                mt: 0, 
                                mb: 4, 
                                bgcolor: 'white',
                                borderRadius: 0,
                                boxShadow: 'none',
                                border: '1px solid #E5E7EB'
                              }}>
                                <CardContent sx={{ p: 3 }}>
                                  <Typography variant="h6" gutterBottom sx={{ 
                                    mb: 3, 
                                    color: '#0F172A', 
                                    fontWeight: 600,
                                    fontSize: '1rem',
                                    letterSpacing: '-0.01em'
                                  }}>
                                  Provider Ordering Intensity (M18)
                                </Typography>
                                  <Box sx={{ 
                                    textAlign: 'center', 
                                    p: 4, 
                                    bgcolor: '#F8FAFC', 
                                    border: '1px solid #E5E7EB'
                                  }}>
                                    <Typography variant="h3" fontWeight={700} sx={{ 
                                      color: '#3B2F8F',
                                      letterSpacing: '-0.02em',
                                      lineHeight: 1.2,
                                      mb: 1
                                    }}>
                                      {explanation.provider_ordering_intensity_target_per_1000_mm.toFixed(2)}
                                </Typography>
                                    <Typography variant="body1" sx={{ 
                                      color: '#64748B', 
                                      mt: 1, 
                                      fontWeight: 500,
                                      fontSize: '0.9375rem'
                                    }}>
                                      per 1,000 member-months
                                    </Typography>
                                    <Typography variant="caption" sx={{ 
                                      color: '#64748B', 
                                      mt: 1.5, 
                                      display: 'block',
                                      fontSize: '0.8125rem'
                                    }}>
                                  Average ordering intensity for targeted services
                                </Typography>
                              </Box>
                                </CardContent>
                              </Card>
                            )}
                            
                            {explanation.patient_response_shares && Object.keys(explanation.patient_response_shares).length > 0 && (
                              <Card sx={{ 
                                mt: 0, 
                                mb: 4, 
                                bgcolor: 'white',
                                borderRadius: 0,
                                boxShadow: 'none',
                                border: '1px solid #E5E7EB'
                              }}>
                                <CardContent sx={{ p: 0 }}>
                                  <Box sx={{ p: 3, borderBottom: '1px solid #E5E7EB' }}>
                                    <Typography variant="h6" sx={{ 
                                      color: '#0F172A', 
                                      fontWeight: 600,
                                      fontSize: '1rem',
                                      letterSpacing: '-0.01em'
                                    }}>
                                  Patient Segment Response Share (M19)
                                </Typography>
                                  </Box>
                                  <TableContainer>
                                    <Table>
                                  <TableHead>
                                        <TableRow sx={{ bgcolor: '#F8FAFC' }}>
                                          <TableCell sx={{ 
                                            fontWeight: 600, 
                                            color: '#0F172A',
                                            fontSize: '0.875rem',
                                            py: 2,
                                            borderBottom: '1px solid #E5E7EB'
                                          }}>
                                            Response Type
                                          </TableCell>
                                          <TableCell align="right" sx={{ 
                                            fontWeight: 600, 
                                            color: '#0F172A',
                                            fontSize: '0.875rem',
                                            py: 2,
                                            borderBottom: '1px solid #E5E7EB'
                                          }}>
                                            Share (%)
                                          </TableCell>
                                    </TableRow>
                                  </TableHead>
                                  <TableBody>
                                    {Object.entries(explanation.patient_response_shares).map(([key, value]: [string, any]) => {
                                      const responseName = key.replace('patient_response_share_', '').replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
                                          const shareValue = typeof value === 'number' ? value : parseFloat(value) || 0
                                      return (
                                            <TableRow 
                                              key={key} 
                                              hover 
                                              sx={{ 
                                                '&:hover': { bgcolor: '#F8FAFC' },
                                                '&:last-child td': { borderBottom: 'none' }
                                              }}
                                            >
                                              <TableCell sx={{ 
                                                color: '#0F172A',
                                                fontSize: '0.875rem',
                                                py: 2
                                              }}>
                                                {responseName}
                                              </TableCell>
                                              <TableCell align="right" sx={{ py: 2 }}>
                                                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 2 }}>
                                                  <LinearProgress 
                                                    variant="determinate" 
                                                    value={shareValue} 
                                                    sx={{ 
                                                      width: 120, 
                                                      height: 6, 
                                                      borderRadius: 0, 
                                                      bgcolor: '#F1F5F9', 
                                                      '& .MuiLinearProgress-bar': { bgcolor: '#2EC4C6' } 
                                                    }}
                                                  />
                                                  <Typography variant="body2" fontWeight={600} sx={{ 
                                                    minWidth: 50, 
                                                    color: '#0F172A',
                                                    fontSize: '0.875rem'
                                                  }}>
                                                    {shareValue.toFixed(1)}%
                                                  </Typography>
                                                </Box>
                                              </TableCell>
                                        </TableRow>
                                      )
                                    })}
                                  </TableBody>
                                </Table>
                                  </TableContainer>
                                </CardContent>
                              </Card>
                            )}

                            {/* Mix Shifts Section */}
                            {explanation.mix_shifts && Object.keys(explanation.mix_shifts).length > 0 && (
                              <Card sx={{ 
                                mt: 0, 
                                mb: 4, 
                                bgcolor: 'white',
                                borderRadius: 0,
                                boxShadow: 'none',
                                border: '1px solid #E5E7EB'
                              }}>
                                <CardContent sx={{ p: 0 }}>
                                  <Box sx={{ p: 3, borderBottom: '1px solid #E5E7EB' }}>
                                    <Typography variant="h6" sx={{ 
                                      color: '#0F172A', 
                                      fontWeight: 600,
                                      fontSize: '1rem',
                                      letterSpacing: '-0.01em'
                                    }}>
                                      Service Mix Shifts
                                    </Typography>
                              </Box>
                                  <Box sx={{ p: 3 }}>
                                    <Grid container spacing={2}>
                                      {Object.entries(explanation.mix_shifts).map(([key, value]: [string, any]) => {
                                        if (typeof value !== 'number' && typeof value !== 'string') return null
                                        const label = key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
                                        const numValue = typeof value === 'number' ? value : parseFloat(value) || 0
                                        const isPositive = numValue > 0
                                        return (
                                          <Grid item xs={12} sm={6} md={4} key={key}>
                                            <Box sx={{ 
                                              p: 2, 
                                              bgcolor: '#F8FAFC', 
                                              border: '1px solid #E5E7EB',
                                              borderRadius: 0
                                            }}>
                                              <Typography variant="caption" sx={{ 
                                                color: '#64748B',
                                                fontSize: '0.75rem',
                                                fontWeight: 500,
                                                display: 'block',
                                                mb: 1
                                              }}>
                                                {label}
                                              </Typography>
                                              <Typography variant="h6" fontWeight={600} sx={{ 
                                                color: isPositive ? '#2E8B57' : '#C04A4A',
                                                fontSize: '1rem'
                                              }}>
                                                {isPositive ? '+' : ''}{numValue.toFixed(1)}{typeof value === 'number' && (key.includes('pct') || key.includes('percent') || key.includes('share')) ? '%' : ''}
                                              </Typography>
                                            </Box>
                                          </Grid>
                                        )
                                      })}
                                    </Grid>
                                  </Box>
                                </CardContent>
                              </Card>
                            )}

                            {/* Pathway Changes Section */}
                            {explanation.pathway_changes && Object.keys(explanation.pathway_changes).length > 0 && (
                              <Card sx={{ 
                                mt: 0, 
                                mb: 4, 
                                bgcolor: 'white',
                                borderRadius: 0,
                                boxShadow: 'none',
                                border: '1px solid #E5E7EB'
                              }}>
                                <CardContent sx={{ p: 0 }}>
                                  <Box sx={{ p: 3, borderBottom: '1px solid #E5E7EB' }}>
                                    <Typography variant="h6" sx={{ 
                                      color: '#0F172A', 
                                      fontWeight: 600,
                                      fontSize: '1rem',
                                      letterSpacing: '-0.01em'
                                    }}>
                                      Care Pathway Changes
                                    </Typography>
                                  </Box>
                                  <Box sx={{ p: 3 }}>
                                    {Array.isArray(explanation.pathway_changes) ? (
                                      <TableContainer>
                                        <Table>
                                          <TableHead>
                                            <TableRow sx={{ bgcolor: '#F8FAFC' }}>
                                              <TableCell sx={{ fontWeight: 600, color: '#0F172A', fontSize: '0.875rem', py: 2, borderBottom: '1px solid #E5E7EB' }}>
                                                Pathway
                                              </TableCell>
                                              <TableCell align="right" sx={{ fontWeight: 600, color: '#0F172A', fontSize: '0.875rem', py: 2, borderBottom: '1px solid #E5E7EB' }}>
                                                Change
                                              </TableCell>
                                            </TableRow>
                                          </TableHead>
                                          <TableBody>
                                            {explanation.pathway_changes.slice(0, 10).map((pathway: any, idx: number) => (
                                              <TableRow key={idx} hover sx={{ '&:hover': { bgcolor: '#F8FAFC' }, '&:last-child td': { borderBottom: 'none' } }}>
                                                <TableCell sx={{ color: '#0F172A', fontSize: '0.875rem', py: 2 }}>
                                                  {pathway.pathway || pathway.name || `Pathway ${idx + 1}`}
                                                </TableCell>
                                                <TableCell align="right" sx={{ py: 2 }}>
                                                  <Typography variant="body2" fontWeight={600} sx={{ 
                                                    color: (pathway.change || pathway.delta || 0) > 0 ? '#2E8B57' : '#C04A4A',
                                                    fontSize: '0.875rem'
                                                  }}>
                                                    {(pathway.change || pathway.delta || 0) > 0 ? '+' : ''}
                                                    {(pathway.change || pathway.delta || 0).toFixed(1)}%
                                                  </Typography>
                                                </TableCell>
                                              </TableRow>
                                            ))}
                                          </TableBody>
                                        </Table>
                                      </TableContainer>
                                    ) : (
                                      <Typography variant="body2" sx={{ color: '#64748B' }}>
                                        {JSON.stringify(explanation.pathway_changes, null, 2)}
                                      </Typography>
                                    )}
                                  </Box>
                                </CardContent>
                              </Card>
                            )}

                            {/* Performance Assessment */}
                            {(explanation.performance_narrative && Array.isArray(explanation.performance_narrative) && explanation.performance_narrative.length > 0) || explanation.summary ? (
                              <Card sx={{ mt: 0, mb: 4, bgcolor: 'white', borderRadius: 0, boxShadow: 'none', border: '1px solid #E5E7EB' }}>
                                <CardContent sx={{ p: 0 }}>
                                  <Box sx={{ p: 3, borderBottom: '1px solid #E5E7EB' }}>
                                    <Typography variant="h6" sx={{ color: '#0F172A', fontWeight: 600, fontSize: '1rem', letterSpacing: '-0.01em' }}>
                                      Performance Assessment
                                    </Typography>
                                  </Box>
                                  <Box sx={{ p: 3 }}>
                                    {explanation.performance_narrative && Array.isArray(explanation.performance_narrative) && explanation.performance_narrative.length > 0 ? (
                                      <Grid container spacing={3}>
                                        {explanation.performance_narrative.map((narrative: any, idx: number) => {
                                          const assessmentColor = 
                                            narrative.assessment === 'EXCELLENT' || narrative.assessment === 'STRONG' || narrative.assessment === 'POSITIVE' || narrative.assessment === 'HIGHLY FAVORABLE' ? '#2E8B57' :
                                            narrative.assessment === 'GOOD' || narrative.assessment === 'MODERATE' || narrative.assessment === 'MIXED' || narrative.assessment === 'FAVORABLE' ? '#E6A23C' :
                                            narrative.assessment === 'NEEDS IMPROVEMENT' || narrative.assessment === 'NEEDS ATTENTION' || narrative.assessment === 'CONCERNING' || narrative.assessment === 'UNFAVORABLE' ? '#C04A4A' : '#64748B'
                                          return (
                                            <Grid item xs={12} md={6} key={idx}>
                                              <Box sx={{ p: 3, bgcolor: '#F8FAFC', border: '1px solid #E5E7EB', borderRadius: 0, height: '100%' }}>
                                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                                                  <Chip label={narrative.aspect} size="small" sx={{ bgcolor: '#E8EDF5', color: '#0F172A', fontWeight: 600, fontSize: '0.75rem' }} />
                                                  <Chip label={narrative.assessment} size="small" sx={{ bgcolor: assessmentColor, color: 'white', fontWeight: 600, fontSize: '0.75rem' }} />
                                                </Box>
                                                <Typography variant="body2" sx={{ color: '#0F172A', lineHeight: 1.7, fontSize: '0.9375rem', mb: 1.5 }}>
                                                  {narrative.description}
                                                </Typography>
                                                {narrative.evidence && (
                                                  <Typography variant="caption" sx={{ color: '#64748B', fontSize: '0.8125rem', fontStyle: 'italic' }}>
                                                    {narrative.evidence}
                                                  </Typography>
                                                )}
                                              </Box>
                                            </Grid>
                                          )
                                        })}
                                      </Grid>
                                    ) : (
                                      <Alert severity="info">
                                        Performance assessment data will be available after the next observation analysis is completed.
                                      </Alert>
                                    )}
                                  </Box>
                                </CardContent>
                              </Card>
                            ) : null}

                            {/* Provider Response Analysis */}
                            {explanation.provider_response && (
                              <Card sx={{ mt: 0, mb: 4, bgcolor: 'white', borderRadius: 0, boxShadow: 'none', border: '1px solid #E5E7EB' }}>
                                <CardContent sx={{ p: 0 }}>
                                  <Box sx={{ p: 3, borderBottom: '1px solid #E5E7EB' }}>
                                    <Typography variant="h6" sx={{ color: '#0F172A', fontWeight: 600, fontSize: '1rem', letterSpacing: '-0.01em' }}>
                                      Provider Response Analysis
                                    </Typography>
                                  </Box>
                                  <Box sx={{ p: 3 }}>
                                    {explanation.provider_response.analysis && Array.isArray(explanation.provider_response.analysis) && explanation.provider_response.analysis.length > 0 && (
                                      <Box sx={{ mb: 3 }}>
                                        {explanation.provider_response.analysis.map((analysis: string, idx: number) => (
                                          <Box key={idx} sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5, mb: 1.5, p: 2, bgcolor: '#F8FAFC', border: '1px solid #E5E7EB', borderRadius: 0 }}>
                                            <CheckCircleIcon sx={{ color: '#3B2F8F', fontSize: 20, mt: 0.5, flexShrink: 0 }} />
                                            <Typography variant="body2" sx={{ color: '#0F172A', lineHeight: 1.6, fontSize: '0.9375rem' }}>
                                              {analysis}
                                            </Typography>
                                          </Box>
                                        ))}
                                      </Box>
                                    )}
                                    {explanation.provider_response.recommendations && Array.isArray(explanation.provider_response.recommendations) && explanation.provider_response.recommendations.length > 0 && (
                                      <Box>
                                        <Typography variant="subtitle2" sx={{ color: '#0F172A', fontWeight: 600, mb: 1.5, fontSize: '0.875rem' }}>
                                          Recommendations:
                                        </Typography>
                                        {explanation.provider_response.recommendations.map((rec: string, idx: number) => (
                                          <Box key={idx} sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, mb: 1, pl: 2 }}>
                                            <Typography variant="body2" sx={{ color: '#64748B' }}>•</Typography>
                                            <Typography variant="body2" sx={{ color: '#475569', lineHeight: 1.6, fontSize: '0.9375rem' }}>
                                              {rec}
                                            </Typography>
                                          </Box>
                                        ))}
                                      </Box>
                                    )}
                                  </Box>
                                </CardContent>
                              </Card>
                            )}

                            {/* Patient Response Analysis */}
                            {explanation.patient_response && (
                              <Card sx={{ mt: 0, mb: 4, bgcolor: 'white', borderRadius: 0, boxShadow: 'none', border: '1px solid #E5E7EB' }}>
                                <CardContent sx={{ p: 0 }}>
                                  <Box sx={{ p: 3, borderBottom: '1px solid #E5E7EB' }}>
                                    <Typography variant="h6" sx={{ color: '#0F172A', fontWeight: 600, fontSize: '1rem', letterSpacing: '-0.01em' }}>
                                      Patient Response Analysis
                                    </Typography>
                                  </Box>
                                  <Box sx={{ p: 3 }}>
                                    {explanation.patient_response.analysis && Array.isArray(explanation.patient_response.analysis) && explanation.patient_response.analysis.length > 0 && (
                                      <Box sx={{ mb: 3 }}>
                                        {explanation.patient_response.analysis.map((analysis: string, idx: number) => (
                                          <Box key={idx} sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5, mb: 1.5, p: 2, bgcolor: '#F8FAFC', border: '1px solid #E5E7EB', borderRadius: 0 }}>
                                            <CheckCircleIcon sx={{ color: '#2EC4C6', fontSize: 20, mt: 0.5, flexShrink: 0 }} />
                                            <Typography variant="body2" sx={{ color: '#0F172A', lineHeight: 1.6, fontSize: '0.9375rem' }}>
                                              {analysis}
                                            </Typography>
                                          </Box>
                                        ))}
                                      </Box>
                                    )}
                                    {explanation.patient_response.recommendations && Array.isArray(explanation.patient_response.recommendations) && explanation.patient_response.recommendations.length > 0 && (
                                      <Box>
                                        <Typography variant="subtitle2" sx={{ color: '#0F172A', fontWeight: 600, mb: 1.5, fontSize: '0.875rem' }}>
                                          Recommendations:
                                        </Typography>
                                        {explanation.patient_response.recommendations.map((rec: string, idx: number) => (
                                          <Box key={idx} sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, mb: 1, pl: 2 }}>
                                            <Typography variant="body2" sx={{ color: '#64748B' }}>•</Typography>
                                            <Typography variant="body2" sx={{ color: '#475569', lineHeight: 1.6, fontSize: '0.9375rem' }}>
                                              {rec}
                                            </Typography>
                                          </Box>
                                        ))}
                                      </Box>
                                    )}
                                  </Box>
                                </CardContent>
                              </Card>
                            )}

                            {/* Cost Impact Analysis */}
                            {explanation.cost_impact && (
                              <Card sx={{ mt: 0, mb: 4, bgcolor: 'white', borderRadius: 0, boxShadow: 'none', border: '1px solid #E5E7EB' }}>
                                <CardContent sx={{ p: 0 }}>
                                  <Box sx={{ p: 3, borderBottom: '1px solid #E5E7EB' }}>
                                    <Typography variant="h6" sx={{ color: '#0F172A', fontWeight: 600, fontSize: '1rem', letterSpacing: '-0.01em' }}>
                                      Cost Impact Analysis
                                    </Typography>
                                  </Box>
                                  <Box sx={{ p: 3 }}>
                                    <Grid container spacing={3} sx={{ mb: 3 }}>
                                      <Grid item xs={12} sm={6} md={3}>
                                        <Box sx={{ textAlign: 'center', p: 2, bgcolor: '#F8FAFC', border: '1px solid #E5E7EB' }}>
                                          <Typography variant="caption" sx={{ color: '#64748B', fontSize: '0.75rem' }}>Pre-Policy Cost PMPM</Typography>
                                          <Typography variant="h6" sx={{ color: '#0F172A', fontWeight: 600, mt: 0.5 }}>
                                            ${explanation.cost_impact.pre_cost_pmpm?.toFixed(2) || 'N/A'}
                                          </Typography>
                                        </Box>
                                      </Grid>
                                      <Grid item xs={12} sm={6} md={3}>
                                        <Box sx={{ textAlign: 'center', p: 2, bgcolor: '#F8FAFC', border: '1px solid #E5E7EB' }}>
                                          <Typography variant="caption" sx={{ color: '#64748B', fontSize: '0.75rem' }}>Post-Policy Cost PMPM</Typography>
                                          <Typography variant="h6" sx={{ color: '#0F172A', fontWeight: 600, mt: 0.5 }}>
                                            ${explanation.cost_impact.post_cost_pmpm?.toFixed(2) || 'N/A'}
                                          </Typography>
                                        </Box>
                                      </Grid>
                                      <Grid item xs={12} sm={6} md={3}>
                                        <Box sx={{ textAlign: 'center', p: 2, bgcolor: '#F8FAFC', border: '1px solid #E5E7EB' }}>
                                          <Typography variant="caption" sx={{ color: '#64748B', fontSize: '0.75rem' }}>Cost Change</Typography>
                                          <Typography variant="h6" sx={{ color: (explanation.cost_impact.cost_change_pmpm || 0) < 0 ? '#2E8B57' : '#C04A4A', fontWeight: 600, mt: 0.5 }}>
                                            ${explanation.cost_impact.cost_change_pmpm?.toFixed(2) || 'N/A'}
                                          </Typography>
                                        </Box>
                                      </Grid>
                                      <Grid item xs={12} sm={6} md={3}>
                                        <Box sx={{ textAlign: 'center', p: 2, bgcolor: '#F8FAFC', border: '1px solid #E5E7EB' }}>
                                          <Typography variant="caption" sx={{ color: '#64748B', fontSize: '0.75rem' }}>Annual Savings (10K members)</Typography>
                                          <Typography variant="h6" sx={{ color: (explanation.cost_impact.financial_impact?.annual_savings_per_10k_members || 0) > 0 ? '#2E8B57' : '#C04A4A', fontWeight: 600, mt: 0.5 }}>
                                            ${explanation.cost_impact.financial_impact?.annual_savings_per_10k_members?.toLocaleString(undefined, { maximumFractionDigits: 0 }) || 'N/A'}
                                          </Typography>
                                        </Box>
                                      </Grid>
                                    </Grid>
                                    {explanation.cost_impact.analysis && Array.isArray(explanation.cost_impact.analysis) && explanation.cost_impact.analysis.length > 0 && (
                                      <Box>
                                        {explanation.cost_impact.analysis.map((analysis: string, idx: number) => (
                                          <Box key={idx} sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5, mb: 1.5, p: 2, bgcolor: '#F8FAFC', border: '1px solid #E5E7EB', borderRadius: 0 }}>
                                            <MoneyIcon sx={{ color: '#3B2F8F', fontSize: 20, mt: 0.5, flexShrink: 0 }} />
                                            <Typography variant="body2" sx={{ color: '#0F172A', lineHeight: 1.6, fontSize: '0.9375rem' }}>
                                              {analysis}
                                            </Typography>
                                          </Box>
                                        ))}
                                      </Box>
                                    )}
                                  </Box>
                                </CardContent>
                              </Card>
                            )}

                            {/* Strategic Considerations */}
                            {explanation.strategic_considerations && Array.isArray(explanation.strategic_considerations) && explanation.strategic_considerations.length > 0 && (
                              <Card sx={{ mt: 0, mb: 4, bgcolor: '#FFF7ED', borderRadius: 0, boxShadow: 'none', border: '1px solid #FED7AA' }}>
                                <CardContent sx={{ p: 4 }}>
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
                                    <InfoIcon sx={{ color: '#E6A23C', fontSize: 24 }} />
                                    <Typography variant="h6" sx={{ color: '#0F172A', fontWeight: 600, fontSize: '1rem', letterSpacing: '-0.01em' }}>
                                      Strategic Considerations
                                    </Typography>
                                  </Box>
                                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                    {explanation.strategic_considerations.map((consideration: string, idx: number) => (
                                      <Box key={idx} sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5, p: 2, bgcolor: 'white', border: '1px solid #FED7AA', borderRadius: 0 }}>
                                        <Box sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: '#E6A23C', mt: 1, flexShrink: 0 }} />
                                        <Typography variant="body2" sx={{ color: '#0F172A', lineHeight: 1.6, fontSize: '0.9375rem' }}>
                                          {consideration}
                                        </Typography>
                                      </Box>
                                    ))}
                                  </Box>
                                </CardContent>
                              </Card>
                            )}

                            {/* Key Success Factors */}
                            {explanation.key_success_factors && Array.isArray(explanation.key_success_factors) && explanation.key_success_factors.length > 0 && (
                              <Card sx={{ mt: 0, mb: 4, bgcolor: '#F0FDF4', borderRadius: 0, boxShadow: 'none', border: '1px solid #BBF7D0' }}>
                                <CardContent sx={{ p: 4 }}>
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
                                    <CheckCircleIcon sx={{ color: '#2E8B57', fontSize: 24 }} />
                                    <Typography variant="h6" sx={{ color: '#0F172A', fontWeight: 600, fontSize: '1rem', letterSpacing: '-0.01em' }}>
                                      Key Success Factors
                                    </Typography>
                                  </Box>
                                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                                    {explanation.key_success_factors.map((factor: string, idx: number) => (
                                      <Box key={idx} sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5, p: 2, bgcolor: 'white', border: '1px solid #BBF7D0', borderRadius: 0 }}>
                                        <CheckCircleIcon sx={{ color: '#2E8B57', fontSize: 18, mt: 0.5, flexShrink: 0 }} />
                                        <Typography variant="body2" sx={{ color: '#0F172A', lineHeight: 1.6, fontSize: '0.9375rem' }}>
                                          {factor}
                                        </Typography>
                                      </Box>
                                    ))}
                                  </Box>
                                </CardContent>
                              </Card>
                            )}

                            {/* Risk Factors */}
                            {explanation.risk_factors && Array.isArray(explanation.risk_factors) && explanation.risk_factors.length > 0 && (
                              <Card sx={{ mt: 0, mb: 4, bgcolor: '#FEF2F2', borderRadius: 0, boxShadow: 'none', border: '1px solid #FECACA' }}>
                                <CardContent sx={{ p: 4 }}>
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
                                    <WarningIcon sx={{ color: '#C04A4A', fontSize: 24 }} />
                                    <Typography variant="h6" sx={{ color: '#0F172A', fontWeight: 600, fontSize: '1rem', letterSpacing: '-0.01em' }}>
                                      Risk Factors
                                    </Typography>
                                  </Box>
                                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                                    {explanation.risk_factors.map((risk: string, idx: number) => (
                                      <Box key={idx} sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5, p: 2, bgcolor: 'white', border: '1px solid #FECACA', borderRadius: 0 }}>
                                        <WarningIcon sx={{ color: '#C04A4A', fontSize: 18, mt: 0.5, flexShrink: 0 }} />
                                        <Typography variant="body2" sx={{ color: '#0F172A', lineHeight: 1.6, fontSize: '0.9375rem' }}>
                                          {risk}
                                        </Typography>
                                      </Box>
                                    ))}
                                  </Box>
                                </CardContent>
                              </Card>
                            )}

                            {/* Key Insights Section - Computed from available data */}
                            {(() => {
                              const insights: string[] = []
                              
                              // Use actionable_insights from backend if available
                              if (explanation.actionable_insights && Array.isArray(explanation.actionable_insights)) {
                                insights.push(...explanation.actionable_insights)
                              }
                              
                              // Insight 1: Provider behavior
                              if (explanation.provider_archetype_shares) {
                                const compliant = explanation.provider_archetype_shares.provider_archetype_share_compliant || 0
                                const resistant = explanation.provider_archetype_shares.provider_archetype_share_resistant || 0
                                const circumvention = explanation.provider_archetype_shares.provider_archetype_share_circumvention_prone || 0
                                
                                if (compliant > 50) {
                                  insights.push(`Strong provider compliance: ${compliant.toFixed(1)}% of providers show compliant behavior`)
                                } else if (resistant + circumvention > 40) {
                                  insights.push(`Significant provider resistance: ${(resistant + circumvention).toFixed(1)}% of providers show resistant or circumvention behavior`)
                                }
                              }
                              
                              // Insight 2: Substitution patterns
                              if (explanation.substitution_patterns && Array.isArray(explanation.substitution_patterns) && explanation.substitution_patterns.length > 0) {
                                insights.push(`${explanation.substitution_patterns.length} substitution pattern${explanation.substitution_patterns.length > 1 ? 's' : ''} detected, indicating service substitution behavior`)
                              }
                              
                              // Insight 3: Patient responses
                              if (explanation.patient_response_shares) {
                                const comply = explanation.patient_response_shares.patient_response_share_overall_comply || 0
                                const substitute = explanation.patient_response_shares.patient_response_share_overall_substitute || 0
                                
                                if (comply > 60) {
                                  insights.push(`High patient compliance: ${comply.toFixed(1)}% of patients followed the policy`)
                                } else if (substitute > 20) {
                                  insights.push(`Notable substitution behavior: ${substitute.toFixed(1)}% of patients substituted services`)
                                }
                              }
                              
                              // Insight 4: Effect size
                              if (explanation.effect_size !== undefined) {
                                const effectSize = Math.abs(explanation.effect_size)
                                if (effectSize > 0.8) {
                                  insights.push(`Large effect size (${effectSize.toFixed(2)}) indicates substantial policy impact`)
                                } else if (effectSize > 0.5) {
                                  insights.push(`Moderate effect size (${effectSize.toFixed(2)}) suggests meaningful policy impact`)
                                }
                              }
                              
                              // Insight 5: Mix shifts
                              if (explanation.mix_shifts) {
                                const hasSignificantShift = Object.values(explanation.mix_shifts).some((v: any) => {
                                  const num = typeof v === 'number' ? v : parseFloat(v) || 0
                                  return Math.abs(num) > 10
                                })
                                if (hasSignificantShift) {
                                  insights.push(`Significant service mix shifts detected, indicating changes in care delivery patterns`)
                                }
                              }
                              
                              return insights.length > 0 ? (
                                <Card sx={{ 
                                  mt: 0, 
                                  mb: 4, 
                                  bgcolor: '#E8EDF5',
                                  borderRadius: 0,
                                  boxShadow: 'none',
                                  border: '1px solid #CBD5E1'
                                }}>
                                  <CardContent sx={{ p: 4 }}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
                                      <InfoIcon sx={{ color: '#3B2F8F', fontSize: 24 }} />
                                      <Typography variant="h6" sx={{ 
                                        color: '#0F172A', 
                                        fontWeight: 600,
                                        fontSize: '1rem',
                                        letterSpacing: '-0.01em'
                                      }}>
                                        Key Insights
                                      </Typography>
                                    </Box>
                                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                      {insights.map((insight, idx) => (
                                        <Box key={idx} sx={{ 
                                          display: 'flex', 
                                          alignItems: 'flex-start', 
                                          gap: 1.5,
                                          p: 2,
                                          bgcolor: 'white',
                                          border: '1px solid #E5E7EB',
                                          borderRadius: 0
                                        }}>
                                          <Box sx={{ 
                                            width: 6, 
                                            height: 6, 
                                            borderRadius: '50%', 
                                            bgcolor: '#3B2F8F', 
                                            mt: 1,
                                            flexShrink: 0
                                          }} />
                                          <Typography variant="body2" sx={{ 
                                            color: '#0F172A',
                                            lineHeight: 1.6,
                                            fontSize: '0.9375rem'
                                          }}>
                                            {insight}
                                          </Typography>
                                        </Box>
                                      ))}
                                    </Box>
                                  </CardContent>
                                </Card>
                              ) : null
                            })()}

                            {/* Risk Indicators Section */}
                            {(() => {
                              const risks: Array<{ severity: 'high' | 'medium' | 'low', message: string }> = []
                              
                              // Risk 1: High circumvention
                              if (explanation.provider_archetype_shares) {
                                const circumvention = explanation.provider_archetype_shares.provider_archetype_share_circumvention_prone || 
                                                      explanation.provider_archetype_shares['provider_archetype_share_circumvention-prone'] ||
                                                      explanation.provider_archetype_shares['provider_archetype_share_circumvention'] || 0
                                if (circumvention > 30) {
                                  risks.push({ 
                                    severity: 'high', 
                                    message: `High circumvention risk: ${circumvention.toFixed(1)}% of providers show circumvention behavior` 
                                  })
                                } else if (circumvention > 15) {
                                  risks.push({ 
                                    severity: 'medium', 
                                    message: `Moderate circumvention risk: ${circumvention.toFixed(1)}% of providers show circumvention behavior` 
                                  })
                                }
                              }
                              
                              // Risk 2: Significant substitution
                              if (explanation.substitution_patterns && Array.isArray(explanation.substitution_patterns) && explanation.substitution_patterns.length > 5) {
                                risks.push({ 
                                  severity: 'medium', 
                                  message: `Multiple substitution patterns (${explanation.substitution_patterns.length}) detected, indicating potential service leakage` 
                                })
                              }
                              
                              // Risk 3: Low compliance
                              if (explanation.patient_response_shares) {
                                const comply = explanation.patient_response_shares.patient_response_share_overall_comply || 0
                                if (comply < 40) {
                                  risks.push({ 
                                    severity: 'high', 
                                    message: `Low patient compliance: Only ${comply.toFixed(1)}% of patients followed the policy` 
                                  })
                                }
                              }
                              
                              // Risk 4: Unexpected increase
                              if (explanation.percent_change !== undefined && explanation.percent_change > 10) {
                                risks.push({ 
                                  severity: 'high', 
                                  message: `Unexpected utilization increase: ${explanation.percent_change.toFixed(1)}% increase may indicate policy ineffectiveness or adverse effects` 
                                })
                              }
                              
                              return risks.length > 0 ? (
                                <Card sx={{ 
                                  mt: 0, 
                                  mb: 4, 
                                  bgcolor: risks.some(r => r.severity === 'high') ? '#FFEBEE' : '#FFF3E0',
                                  borderRadius: 0,
                                  boxShadow: 'none',
                                  border: '1px solid',
                                  borderColor: risks.some(r => r.severity === 'high') ? '#FFCDD2' : '#FFE0B2'
                                }}>
                                  <CardContent sx={{ p: 4 }}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
                                      <WarningIcon sx={{ 
                                        color: risks.some(r => r.severity === 'high') ? '#C04A4A' : '#E6A23C', 
                                        fontSize: 24 
                                      }} />
                                      <Typography variant="h6" sx={{ 
                                        color: '#0F172A', 
                                        fontWeight: 600,
                                        fontSize: '1rem',
                                        letterSpacing: '-0.01em'
                                      }}>
                                        Risk Indicators
                                      </Typography>
                                    </Box>
                                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                      {risks.map((risk, idx) => (
                                        <Box key={idx} sx={{ 
                                          display: 'flex', 
                                          alignItems: 'flex-start', 
                                          gap: 1.5,
                                          p: 2,
                                          bgcolor: 'white',
                                          border: '1px solid',
                                          borderColor: risk.severity === 'high' ? '#FFCDD2' : '#FFE0B2',
                                          borderRadius: 0
                                        }}>
                                          <WarningIcon sx={{ 
                                            color: risk.severity === 'high' ? '#C04A4A' : '#E6A23C', 
                                            fontSize: 20,
                                            mt: 0.5,
                                            flexShrink: 0
                                          }} />
                                          <Typography variant="body2" sx={{ 
                                            color: '#0F172A',
                                            lineHeight: 1.6,
                                            fontSize: '0.9375rem',
                                            fontWeight: risk.severity === 'high' ? 600 : 500
                                          }}>
                                            {risk.message}
                                          </Typography>
                                        </Box>
                                      ))}
                                    </Box>
                                  </CardContent>
                                </Card>
                              ) : null
                            })()}
                            
                            {explanation.provider_segmentation && !explanation.provider_archetype_shares && (
                              <Box sx={{ mt: 3 }}>
                                <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>
                                  Provider Segmentation
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                  {typeof explanation.provider_segmentation === 'string' 
                                    ? explanation.provider_segmentation
                                    : JSON.stringify(explanation.provider_segmentation, null, 2)}
                                </Typography>
                              </Box>
                            )}
                            
                            {explanation.mix_shifts && (
                              <Box sx={{ mt: 3 }}>
                                <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>
                                  Mix Shifts
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                  {typeof explanation.mix_shifts === 'string'
                                    ? explanation.mix_shifts
                                    : JSON.stringify(explanation.mix_shifts, null, 2)}
                                </Typography>
                              </Box>
                            )}
                            </>
                          )}
                          
                          {!hasMetrics && (
                            <Card sx={{ 
                              bgcolor: 'white',
                              borderRadius: 0,
                              boxShadow: 'none',
                              border: '1px solid #E5E7EB'
                            }}>
                              <CardContent sx={{ p: 0 }}>
                                <Box sx={{ p: 3, borderBottom: '1px solid #E5E7EB' }}>
                                  <Typography variant="h6" sx={{ 
                                    color: '#0F172A', 
                                    fontWeight: 600,
                                    fontSize: '1rem',
                                    letterSpacing: '-0.01em'
                                  }}>
                                    Raw Data
                                  </Typography>
                                </Box>
                                <Box sx={{ 
                                  bgcolor: '#F8FAFC', 
                                  p: 3, 
                                  overflow: 'auto',
                                  maxHeight: 500,
                                  border: 'none'
                                }}>
                                  <pre style={{ 
                                    whiteSpace: 'pre-wrap', 
                                    fontSize: '0.8125rem', 
                                    margin: 0,
                                    fontFamily: '"SF Mono", "Monaco", "Inconsolata", "Roboto Mono", "Courier New", monospace',
                                    color: '#0F172A',
                                    lineHeight: 1.7,
                                    letterSpacing: '0.01em'
                                  }}>
                              {JSON.stringify(explanation, null, 2)}
                            </pre>
                                </Box>
                              </CardContent>
                            </Card>
                          )}
                        </Box>
                      )
                    })()}
                </Box>
              )}

              {/* Forecast Tab */}
              {tabValue === 5 && selectedObservation && (
                <Box>
                  <Typography variant="h6" gutterBottom sx={{ 
                    mb: 4, 
                    fontWeight: 600, 
                    color: '#0F172A',
                    fontSize: '1.25rem',
                    letterSpacing: '-0.01em'
                  }}>
                    Forecast Analysis
                  </Typography>

                  {/* Metric Type Selector */}
                  <Box sx={{ mb: 3 }}>
                    <FormControl size="small" sx={{ minWidth: 200 }}>
                      <InputLabel>Metric Type</InputLabel>
                      <Select
                        value={forecastMetricType}
                        onChange={(e) => setForecastMetricType(e.target.value as 'utilization' | 'cost')}
                        label="Metric Type"
                      >
                        <MenuItem value="utilization">Utilization</MenuItem>
                        <MenuItem value="cost">Cost</MenuItem>
                      </Select>
                    </FormControl>
                  </Box>

                  {loadingForecast ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
                      <CircularProgress />
                    </Box>
                  ) : forecastData && !forecastData.error ? (
                    <>
                      {/* Forecast Chart */}
                      {forecastData.forecast_values && forecastData.forecast_values.length > 0 && (
                        <Card sx={{ 
                          mb: 4,
                          bgcolor: 'white',
                          borderRadius: 0,
                          boxShadow: 'none',
                          border: '1px solid #E5E7EB'
                        }}>
                          <CardContent sx={{ p: 3 }}>
                            <Typography variant="h6" gutterBottom sx={{ 
                              mb: 3, 
                              color: '#0F172A', 
                              fontWeight: 600,
                              fontSize: '1rem',
                              letterSpacing: '-0.01em'
                            }}>
                              Forecast Projection ({forecastMetricType === 'utilization' ? 'per 1K' : 'PMPM'})
                            </Typography>
                            <ResponsiveContainer width="100%" height={400}>
                              <LineChart data={forecastData.forecast_values.map((fv: any) => ({
                                month: `Month ${fv.month}`,
                                forecast: fv.forecast_value,
                                trend: fv.trend_projection,
                                predicted: fv.predicted_target,
                              }))}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                                <XAxis dataKey="month" stroke="#64748B" />
                                <YAxis stroke="#64748B" />
                                <Tooltip 
                                  contentStyle={{ 
                                    backgroundColor: '#FFFFFF', 
                                    color: '#0F172A',
                                    border: '1px solid #E5E7EB',
                                    borderRadius: 6,
                                    boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -2px rgba(0,0,0,0.1)'
                                  }}
                                />
                                <Legend />
                                <Line 
                                  type="monotone" 
                                  dataKey="forecast" 
                                  stroke="#3B2F8F" 
                                  strokeWidth={3}
                                  name="Forecast"
                                  dot={{ fill: '#3B2F8F', r: 4 }}
                                />
                                <Line 
                                  type="monotone" 
                                  dataKey="predicted" 
                                  stroke="#2EC4C6" 
                                  strokeWidth={2}
                                  strokeDasharray="5 5"
                                  name="Predicted Target"
                                  dot={{ fill: '#2EC4C6', r: 3 }}
                                />
                                <Line 
                                  type="monotone" 
                                  dataKey="trend" 
                                  stroke="#94A3B8" 
                                  strokeWidth={1}
                                  strokeDasharray="3 3"
                                  name="Trend Projection"
                                  dot={false}
                                />
                              </LineChart>
                            </ResponsiveContainer>
                          </CardContent>
                        </Card>
                      )}

                      {/* Forecast Metrics */}
                      <Grid container spacing={2.5} sx={{ mb: 4 }}>
                        {forecastData.convergence_date && (
                          <Grid item xs={12} md={4}>
                            <Card sx={{ 
                              bgcolor: '#E8E5F5',
                              color: '#3B2F8F',
                              borderRadius: 0,
                              boxShadow: 'none',
                              border: '1px solid #D4CEE8'
                            }}>
                              <CardContent sx={{ p: 3, textAlign: 'center' }}>
                                <Typography variant="overline" sx={{ 
                                  fontSize: '0.6875rem',
                                  fontWeight: 600,
                                  letterSpacing: '0.08em',
                                  color: '#64748B',
                                  textTransform: 'uppercase',
                                  mb: 1.5,
                                  display: 'block'
                                }}>
                                  Convergence Date
                                </Typography>
                                <Typography variant="h5" fontWeight={700} sx={{ 
                                  letterSpacing: '-0.02em',
                                  lineHeight: 1.2,
                                  color: '#3B2F8F'
                                }}>
                                  {format(new Date(forecastData.convergence_date), 'MMM d, yyyy')}
                                </Typography>
                              </CardContent>
                            </Card>
                          </Grid>
                        )}
                        {forecastData.forecast_accuracy_at_6m !== null && forecastData.forecast_accuracy_at_6m !== undefined && (
                          <Grid item xs={12} md={4}>
                            <Card sx={{ 
                              bgcolor: forecastData.forecast_accuracy_at_6m >= 70 ? '#E8F5E9' : '#FFF3E0',
                              color: forecastData.forecast_accuracy_at_6m >= 70 ? '#1B5E20' : '#E65100',
                              borderRadius: 0,
                              boxShadow: 'none',
                              border: '1px solid',
                              borderColor: forecastData.forecast_accuracy_at_6m >= 70 ? '#C8E6C9' : '#FFE0B2'
                            }}>
                              <CardContent sx={{ p: 3, textAlign: 'center' }}>
                                <Typography variant="overline" sx={{ 
                                  fontSize: '0.6875rem',
                                  fontWeight: 600,
                                  letterSpacing: '0.08em',
                                  textTransform: 'uppercase',
                                  mb: 1.5,
                                  display: 'block'
                                }}>
                                  Forecast Accuracy (6M)
                                </Typography>
                                <Typography variant="h5" fontWeight={700} sx={{ 
                                  letterSpacing: '-0.02em',
                                  lineHeight: 1.2
                                }}>
                                  {forecastData.forecast_accuracy_at_6m.toFixed(1)}%
                                </Typography>
                              </CardContent>
                            </Card>
                          </Grid>
                        )}
                        <Grid item xs={12} md={4}>
                          <Card sx={{ 
                            bgcolor: forecastData.trend_direction === 'toward_prediction' ? '#E8F5E9' : '#FFEBEE',
                            color: forecastData.trend_direction === 'toward_prediction' ? '#1B5E20' : '#B71C1C',
                            borderRadius: 0,
                            boxShadow: 'none',
                            border: '1px solid',
                            borderColor: forecastData.trend_direction === 'toward_prediction' ? '#C8E6C9' : '#FFCDD2'
                          }}>
                            <CardContent sx={{ p: 3, textAlign: 'center' }}>
                              <Typography variant="overline" sx={{ 
                                fontSize: '0.6875rem',
                                fontWeight: 600,
                                letterSpacing: '0.08em',
                                textTransform: 'uppercase',
                                mb: 1.5,
                                display: 'block'
                              }}>
                                Trend Direction
                              </Typography>
                              <Typography variant="h6" fontWeight={700} sx={{ 
                                letterSpacing: '-0.02em',
                                lineHeight: 1.2,
                                textTransform: 'capitalize'
                              }}>
                                {forecastData.trend_direction === 'toward_prediction' ? 'Toward Prediction' : 
                                 forecastData.trend_direction === 'away_from_prediction' ? 'Away from Prediction' : 
                                 'Insufficient Data'}
                              </Typography>
                            </CardContent>
                          </Card>
                        </Grid>
                      </Grid>

                      {/* Forecast Insights */}
                      {forecastData.insights && forecastData.insights.length > 0 && (
                        <Card sx={{ 
                          bgcolor: 'white',
                          borderRadius: 0,
                          boxShadow: 'none',
                          border: '1px solid #E5E7EB'
                        }}>
                          <CardContent sx={{ p: 3 }}>
                            <Typography variant="h6" gutterBottom sx={{ 
                              mb: 2, 
                              color: '#0F172A', 
                              fontWeight: 600,
                              fontSize: '1rem',
                              letterSpacing: '-0.01em'
                            }}>
                              Forecast Insights
                            </Typography>
                            {forecastData.insights.map((insight: string, idx: number) => (
                              <Box key={idx} sx={{ 
                                mb: 1.5, 
                                p: 2, 
                                bgcolor: '#F8FAFC', 
                                borderLeft: '3px solid #3B2F8F',
                                borderRadius: 0
                              }}>
                                <Typography variant="body2" sx={{ 
                                  color: '#0F172A',
                                  fontSize: '0.9375rem',
                                  lineHeight: 1.7
                                }}>
                                  {insight}
                                </Typography>
                              </Box>
                            ))}
                          </CardContent>
                        </Card>
                      )}
                    </>
                  ) : (
                    <Alert severity="info" sx={{ bgcolor: '#F8FAFC', border: '1px solid #E5E7EB' }}>
                      {forecastData?.error || (
                        <>
                          Forecast requires at least 2 observations for this policy to calculate trend projections.
                          {observations.length >= 1 ? (
                            <> You have {observations.length} observation(s). Create one more from an impact analysis to enable forecast.</>
                          ) : (
                            <> Create observations from impact analyses (run analysis, then create observation) to enable forecast.</>
                          )}
                        </>
                      )}
                    </Alert>
                  )}
                </Box>
              )}
              </Box>
            </Box>
          )}
        </DialogContent>
      </Dialog>

      {/* Create observation dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create Observation from Impact Analysis</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Select Policy</InputLabel>
            <Select
              value={selectedPolicy}
              onChange={(e) => setSelectedPolicy(e.target.value)}
              label="Select Policy"
            >
              {policies.map((policy) => (
                <MenuItem key={policy.id} value={policy.id}>
                  {policy.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          {creating && (
            <Box sx={{ mt: 2 }}>
              <LinearProgress />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Creating impact analysis and observation...
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)} disabled={creating}>Cancel</Button>
          <Button onClick={handleCreateObservation} variant="contained" disabled={creating || !selectedPolicy}>
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
