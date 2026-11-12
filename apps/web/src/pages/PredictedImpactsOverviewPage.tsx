/**
 * Predicted Impacts Overview Page
 * Shows all policies with predicted impact scores in one consolidated view
 */
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
  MenuItem,
  Alert,
  Grid,
  IconButton,
  Tooltip,
  Tabs,
  Tab,
  FormControl,
  InputLabel,
  Select,
} from '@mui/material'
import {
  Psychology as PsychologyIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Refresh as RefreshIcon,
  Assessment as AssessmentIcon,
  ArrowForward as ArrowForwardIcon,
  ViewColumn as ViewColumnIcon,
  FilterList as FilterListIcon,
} from '@mui/icons-material'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, Cell } from 'recharts'
import { apiClient } from '../lib/api'
import { format } from 'date-fns'
import { healthForesightColors } from '../theme/healthForesightTheme'
import ConfidenceBadge from '../components/brand/ConfidenceBadge'

interface Policy {
  id: string
  name: string
  policy_type: string
  description?: string
  status?: string
  created_at: string
  updated_at: string
}

interface PredictedImpact {
  policy_id: string
  predicted_at: string
  metrics: {
    utilization_change_per_1k?: number | null
    cost_change_pmpm?: number | null
    payment_impact_dollars?: number | null
    continuation_allowed_change?: number | null
    predicted_allowed?: number | null
    predicted_allowed_pmpm?: number | null
    cost_change_total?: number | null
    utilization_change_pct?: number | null
    cost_change_pct?: number | null
    cost_change_meaning?: string | null
    utilization_change_meaning?: string | null
    measured_vs_baseline_cost_change_pct?: number | null
    measured_vs_baseline_utilization_change_pct?: number | null
    measured_vs_baseline_cost_change_pmpm?: number | null
    measured_vs_baseline_meaning?: string | null
    prediction_type?: string | null
    confidence_score?: number | null
    prediction_method?: string | null
  }
  warnings?: string[]
  limitations?: string[]
}

interface PolicyWithImpact extends Policy {
  predictedImpact?: PredictedImpact
  hasImpact: boolean
  loadingImpact: boolean
}

function isContinuationImpact(impact?: PredictedImpact | null): boolean {
  if (!impact?.metrics) return false
  const m = impact.metrics
  const method = String(m.prediction_method || '').toUpperCase()
  const ptype = String(m.prediction_type || '').toUpperCase()
  return (
    ptype === 'CONTINUATION' ||
    method.startsWith('HISTORICAL_RATE_CONTINUATION') ||
    String(m.cost_change_meaning || '').toUpperCase() === 'UNESTIMATED_POLICY_EFFECT'
  )
}

function estimatedCostChange(impact?: PredictedImpact | null): number | null {
  if (!impact?.metrics || isContinuationImpact(impact)) return null
  const m = impact.metrics
  if (m.cost_change_pmpm != null && Number.isFinite(Number(m.cost_change_pmpm))) {
    return Number(m.cost_change_pmpm)
  }
  if (m.payment_impact_dollars != null && Number.isFinite(Number(m.payment_impact_dollars))) {
    return -Number(m.payment_impact_dollars)
  }
  return null
}

function estimatedUtilChange(impact?: PredictedImpact | null): number | null {
  if (!impact?.metrics || isContinuationImpact(impact)) return null
  const v = impact.metrics.utilization_change_pct
  return v != null && Number.isFinite(Number(v)) ? Number(v) : null
}

export default function PredictedImpactsOverviewPage() {
  const navigate = useNavigate()
  const [policies, setPolicies] = useState<PolicyWithImpact[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [generatingAll, setGeneratingAll] = useState(false)
  const [viewMode, setViewMode] = useState<'table' | 'cards' | 'charts'>('table')
  const [filterType, setFilterType] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<'name' | 'cost_change' | 'utilization_change' | 'confidence'>('cost_change')
  const [selectedTab, setSelectedTab] = useState(0)

  useEffect(() => {
    loadPolicies()
  }, [])

  const loadPolicies = async () => {
    setLoading(true)
    setError(null)
    try {
      // One bulk query (latest impact per policy) — avoids N× predicted-impact stampede
      const summary = await apiClient.listPredictedImpactsSummary(500)
      const rows = Array.isArray(summary) ? summary : []
      const policiesWithImpacts: PolicyWithImpact[] = rows.map((row: any) => {
        const impact = {
          policy_id: row.policy_id,
          predicted_at: row.predicted_at || row.computed_at,
          metrics: row.metrics || {},
          warnings: row.warnings,
          limitations: row.limitations,
        }
        return {
          id: row.policy_id,
          name: row.policy_name || 'Policy',
          policy_type: row.policy_type || 'UNKNOWN',
          status: row.status || 'ACTIVE',
          created_at: row.predicted_at || '',
          updated_at: row.predicted_at || '',
          predictedImpact: impact,
          hasImpact: apiClient.hasUsablePredictedImpact(impact),
          loadingImpact: false,
        }
      })

      setPolicies(policiesWithImpacts)
      if (!policiesWithImpacts.length) {
        setError('No predicted impacts found. Generate them from the Policy Catalog if needed.')
      }
    } catch (err: any) {
      console.error('Error loading predicted impacts:', err)
      setError(err.detail || err.message || 'Failed to load predicted impacts')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateAll = async (force: boolean = false) => {
    const confirmMessage = force
      ? 'Force regenerate predicted impact for ALL policies? This will overwrite existing predictions and may take a few moments.'
      : 'Generate predicted impact for all policies that don\'t have it? This may take a few moments.'

    if (!window.confirm(confirmMessage)) {
      return
    }

    setGeneratingAll(true)
    setError(null)
    try {
      const result = await apiClient.generateAllPoliciesPredictedImpact(force)
      const message = `Predicted impact generation complete!\n` +
        `Successfully generated: ${result.success_count || 0}\n` +
        `Skipped (already exists): ${result.skipped_count || 0}\n` +
        `Errors: ${result.error_count || 0}`
      alert(message)
      
      // Reload policies to show new impacts
      await loadPolicies()
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to generate predicted impact for all policies')
    } finally {
      setGeneratingAll(false)
    }
  }

  const handleViewPolicy = (policyId: string) => {
    navigate(`/policies?highlight=${policyId}`)
  }

  // Filter and sort policies
  const filteredPolicies = policies
    .filter((policy) => {
      // Filter by type
      if (filterType !== 'all' && policy.policy_type !== filterType) {
        return false
      }
      
      // Filter by search query
      if (searchQuery && !policy.name.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false
      }
      
      return true
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'cost_change': {
          const costA = estimatedCostChange(a.predictedImpact)
          const costB = estimatedCostChange(b.predictedImpact)
          if (costA != null || costB != null) {
            return Math.abs(costB ?? 0) - Math.abs(costA ?? 0)
          }
          const predA = Number(a.predictedImpact?.metrics.predicted_allowed_pmpm ?? a.predictedImpact?.metrics.predicted_allowed ?? 0)
          const predB = Number(b.predictedImpact?.metrics.predicted_allowed_pmpm ?? b.predictedImpact?.metrics.predicted_allowed ?? 0)
          return Math.abs(predB) - Math.abs(predA)
        }
        case 'utilization_change': {
          const utilA = estimatedUtilChange(a.predictedImpact)
          const utilB = estimatedUtilChange(b.predictedImpact)
          return Math.abs(utilB ?? 0) - Math.abs(utilA ?? 0)
        }
        case 'confidence': {
          const confA = a.predictedImpact?.metrics.confidence_score || 0
          const confB = b.predictedImpact?.metrics.confidence_score || 0
          return confB - confA
        }
        case 'name':
        default:
          return a.name.localeCompare(b.name)
      }
    })

  const policiesWithImpact = filteredPolicies.filter((p) => p.hasImpact)
  const policiesWithoutImpact = filteredPolicies.filter((p) => !p.hasImpact)
  const continuationOnlyBook = policiesWithImpact.length > 0 && policiesWithImpact.every((p) => isContinuationImpact(p.predictedImpact))

  // Prepare chart data — never coerce UNESTIMATED continuation into +$0 / 0%
  const chartData = policiesWithImpact.map((policy) => {
    const costChange = estimatedCostChange(policy.predictedImpact)
    const utilChange = estimatedUtilChange(policy.predictedImpact)
    const predictedAllowedPmpm = policy.predictedImpact?.metrics.predicted_allowed_pmpm
    return {
      name: policy.name.length > 20 ? policy.name.substring(0, 20) + '...' : policy.name,
      fullName: policy.name,
      costChange: costChange,
      utilizationChange: utilChange,
      predictedAllowedPmpm:
        predictedAllowedPmpm != null && Number.isFinite(Number(predictedAllowedPmpm))
          ? Number(predictedAllowedPmpm)
          : null,
      confidence: policy.predictedImpact?.metrics.confidence_score || 0,
      policyId: policy.id,
      isContinuation: isContinuationImpact(policy.predictedImpact),
    }
  })

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <PsychologyIcon color="primary" />
            Predicted Impacts Overview
          </Typography>
          <Typography variant="body2" color="text.secondary">
            View and compare predicted impact scores across all policies
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadPolicies}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<AssessmentIcon />}
            onClick={() => handleGenerateAll(false)}
            disabled={generatingAll}
          >
            {generatingAll ? 'Generating...' : 'Generate All'}
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Filters and View Controls */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                size="small"
                placeholder="Search policies..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                InputProps={{
                  startAdornment: <FilterListIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Policy Type</InputLabel>
                <Select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  label="Policy Type"
                >
                  <MenuItem value="all">All Types</MenuItem>
                  <MenuItem value="PRIOR_AUTH">Prior Auth</MenuItem>
                  <MenuItem value="SITE_OF_CARE">Site of Care</MenuItem>
                  <MenuItem value="COVERAGE">Coverage</MenuItem>
                  <MenuItem value="STEP_THERAPY">Step Therapy</MenuItem>
                  <MenuItem value="BENEFIT">Benefit</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Sort By</InputLabel>
                <Select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  label="Sort By"
                >
                  <MenuItem value="name">Name</MenuItem>
                  <MenuItem value="cost_change">Cost Impact</MenuItem>
                  <MenuItem value="utilization_change">Utilization Impact</MenuItem>
                  <MenuItem value="confidence">Confidence Score</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <Tabs value={viewMode} onChange={(e, v) => setViewMode(v)} variant="fullWidth" size="small">
                <Tab value="table" icon={<ViewColumnIcon />} label="Table" />
                <Tab value="cards" icon={<AssessmentIcon />} label="Cards" />
                <Tab value="charts" icon={<TrendingUpIcon />} label="Charts" />
              </Tabs>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Tabs for With/Without Impact */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={selectedTab} onChange={(e, v) => setSelectedTab(v)}>
          <Tab label={`With Impact (${policiesWithImpact.length})`} />
          <Tab label={`Without Impact (${policiesWithoutImpact.length})`} />
        </Tabs>
      </Box>

      {/* Content based on selected tab and view mode */}
      {selectedTab === 0 ? (
        // Policies WITH predicted impact
        policiesWithImpact.length === 0 ? (
          <Alert severity="info">
            No policies with predicted impact found. Click "Generate All" to create predicted impacts.
          </Alert>
        ) : viewMode === 'table' ? (
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Policy Name</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell align="right">
                    {continuationOnlyBook ? 'Predicted allowed (continuation)' : 'Cost change'}
                  </TableCell>
                  <TableCell align="right">
                    {continuationOnlyBook ? 'Policy-effect util' : 'Utilization Change (%)'}
                  </TableCell>
                  <TableCell align="right">Confidence</TableCell>
                  <TableCell>Prediction Method</TableCell>
                  <TableCell align="right">Last Updated</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {policiesWithImpact.map((policy) => {
                  const impact = policy.predictedImpact
                  if (!impact || !impact.metrics) {
                    return null
                  }
                  const continuation = isContinuationImpact(impact)
                  const costChange = estimatedCostChange(impact)
                  const utilChange = estimatedUtilChange(impact)
                  const predictedAllowed = impact.metrics.predicted_allowed
                  const predictedAllowedPmpm = impact.metrics.predicted_allowed_pmpm
                  return (
                    <TableRow key={policy.id} hover>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {policy.name}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip label={policy.policy_type} size="small" variant="outlined" />
                      </TableCell>
                      <TableCell align="right">
                        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                          {continuation ? (
                            <>
                              <Typography variant="body2" fontWeight="medium">
                                {predictedAllowedPmpm != null
                                  ? `$${Number(predictedAllowedPmpm).toLocaleString(undefined, { maximumFractionDigits: 2 })} PMPM`
                                  : predictedAllowed != null
                                    ? `$${Number(predictedAllowed).toLocaleString(undefined, { maximumFractionDigits: 0 })}`
                                    : 'UNESTIMATED'}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {predictedAllowed != null || predictedAllowedPmpm != null
                                  ? 'continuation forecast — policy-effect UNESTIMATED'
                                  : 'policy-effect UNESTIMATED (not +$0)'}
                              </Typography>
                              {impact.metrics.measured_vs_baseline_cost_change_pct != null && (
                                <Typography variant="caption" color="text.secondary">
                                  measured vs baseline{' '}
                                  {`${Number(impact.metrics.measured_vs_baseline_cost_change_pct) >= 0 ? '+' : ''}${Number(impact.metrics.measured_vs_baseline_cost_change_pct).toFixed(1)}%`}
                                  {' '}(not attributed)
                                </Typography>
                              )}
                            </>
                          ) : costChange != null ? (
                            <Typography
                              variant="body2"
                              color={costChange < 0 ? 'success.main' : costChange > 0 ? 'error.main' : 'text.primary'}
                              fontWeight="medium"
                            >
                              {costChange >= 0 ? '+' : ''}
                              ${costChange.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                            </Typography>
                          ) : (
                            <Typography variant="body2" color="text.secondary">UNESTIMATED</Typography>
                          )}
                        </Box>
                      </TableCell>
                      <TableCell align="right">
                        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                          {continuation || utilChange == null ? (
                            <>
                              {impact.metrics.measured_vs_baseline_utilization_change_pct != null ? (
                                <>
                                  <Typography variant="body2" fontWeight="medium">
                                    {`${Number(impact.metrics.measured_vs_baseline_utilization_change_pct) >= 0 ? '+' : ''}${Number(impact.metrics.measured_vs_baseline_utilization_change_pct).toFixed(1)}%`}
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary">
                                    measured vs baseline (not attributed)
                                  </Typography>
                                </>
                              ) : (
                                <>
                                  <Typography variant="body2" fontWeight="medium" color="text.secondary">
                                    UNESTIMATED
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary">
                                    {continuation ? 'not a 0% policy-effect' : 'no estimated util change'}
                                  </Typography>
                                </>
                              )}
                            </>
                          ) : (
                            <Typography
                              variant="body2"
                              color={utilChange < 0 ? 'success.main' : utilChange > 0 ? 'error.main' : 'text.primary'}
                              fontWeight="medium"
                            >
                              {`${utilChange >= 0 ? '+' : ''}${Number(utilChange).toFixed(1)}%`}
                            </Typography>
                          )}
                        </Box>
                      </TableCell>
                      <TableCell align="right">
                        <ConfidenceBadge confidence={impact.metrics?.confidence_score ?? null} />
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption" color="text.secondary">
                          {impact.metrics?.prediction_method || 'N/A'}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="caption" color="text.secondary">
                          {impact.predicted_at ? format(new Date(impact.predicted_at), 'MMM d, yyyy') : 'N/A'}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Tooltip title="View Policy Details">
                          <IconButton size="small" onClick={() => handleViewPolicy(policy.id)}>
                            <ArrowForwardIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </TableContainer>
        ) : viewMode === 'cards' ? (
          <Grid container spacing={2}>
            {policiesWithImpact.map((policy) => {
              const impact = policy.predictedImpact
              if (!impact || !impact.metrics) {
                return null
              }
              const continuation = isContinuationImpact(impact)
              const costChange = estimatedCostChange(impact)
              const utilChange = estimatedUtilChange(impact)
              const predictedAllowedPmpm = impact.metrics.predicted_allowed_pmpm
              return (
                <Grid item xs={12} sm={6} md={4} key={policy.id}>
                  <Card sx={{ height: '100%' }}>
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                        <Box>
                          <Typography variant="h6" gutterBottom>
                            {policy.name}
                          </Typography>
                          <Chip label={policy.policy_type} size="small" variant="outlined" />
                        </Box>
                        <IconButton size="small" onClick={() => handleViewPolicy(policy.id)}>
                          <ArrowForwardIcon />
                        </IconButton>
                      </Box>
                      <Grid container spacing={2} sx={{ mt: 1 }}>
                        <Grid item xs={6}>
                          <Typography variant="caption" color="text.secondary">
                            {continuation ? 'Predicted allowed PMPM' : 'Cost Change (PMPM)'}
                          </Typography>
                          {continuation ? (
                            <Typography variant="h6">
                              {predictedAllowedPmpm != null
                                ? `$${Number(predictedAllowedPmpm).toFixed(2)}`
                                : 'UNESTIMATED'}
                            </Typography>
                          ) : (
                            <Typography
                              variant="h6"
                              color={
                                costChange == null
                                  ? 'text.secondary'
                                  : costChange < 0
                                    ? 'success.main'
                                    : costChange > 0
                                      ? 'error.main'
                                      : 'text.primary'
                              }
                            >
                              {costChange == null
                                ? 'UNESTIMATED'
                                : `${costChange >= 0 ? '+' : ''}$${costChange.toFixed(2)}`}
                            </Typography>
                          )}
                          {continuation && (
                            <Typography variant="caption" color="text.secondary" display="block">
                              policy-effect UNESTIMATED
                            </Typography>
                          )}
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="caption" color="text.secondary">
                            Utilization Change
                          </Typography>
                          <Typography
                            variant="h6"
                            color={
                              utilChange == null
                                ? 'text.secondary'
                                : utilChange < 0
                                  ? 'success.main'
                                  : utilChange > 0
                                    ? 'error.main'
                                    : 'text.primary'
                            }
                          >
                            {utilChange == null
                              ? 'UNESTIMATED'
                              : `${utilChange >= 0 ? '+' : ''}${utilChange.toFixed(1)}%`}
                          </Typography>
                          {continuation && (
                            <Typography variant="caption" color="text.secondary" display="block">
                              not +0%
                            </Typography>
                          )}
                        </Grid>
                        <Grid item xs={12}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Typography variant="caption" color="text.secondary">
                              Confidence
                            </Typography>
                            <ConfidenceBadge confidence={impact.metrics?.confidence_score || 0} />
                          </Box>
                        </Grid>
                      </Grid>
                    </CardContent>
                  </Card>
                </Grid>
              )
            })}
          </Grid>
        ) : (
          // Charts view
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {continuationOnlyBook
                      ? 'Continuation predicted allowed PMPM'
                      : 'Cost Impact by Policy (PMPM)'}
                  </Typography>
                  {continuationOnlyBook ? (
                    <Alert severity="info" sx={{ mb: 2 }}>
                      Policy-effect cost change is UNESTIMATED for this book. Chart shows frozen continuation forecast levels, not +$0 savings.
                    </Alert>
                  ) : null}
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart
                      data={
                        continuationOnlyBook
                          ? chartData.filter((d) => d.predictedAllowedPmpm != null)
                          : chartData.filter((d) => d.costChange != null)
                      }
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                      <YAxis />
                      <RechartsTooltip
                        formatter={(value: number) => `$${Number(value).toFixed(2)}`}
                        labelFormatter={(label, payload) => {
                          if (payload && payload[0]) {
                            return payload[0].payload.fullName
                          }
                          return label
                        }}
                      />
                      <Legend />
                      <Bar
                        dataKey={continuationOnlyBook ? 'predictedAllowedPmpm' : 'costChange'}
                        name={continuationOnlyBook ? 'Predicted allowed PMPM' : 'Cost Change (PMPM)'}
                      >
                        {(continuationOnlyBook
                          ? chartData.filter((d) => d.predictedAllowedPmpm != null)
                          : chartData.filter((d) => d.costChange != null)
                        ).map((entry, index) => {
                          const v = continuationOnlyBook ? entry.predictedAllowedPmpm : entry.costChange
                          return (
                            <Cell
                              key={`cell-${index}`}
                              fill={
                                continuationOnlyBook
                                  ? healthForesightColors.primary.main
                                  : (v ?? 0) < 0
                                    ? healthForesightColors.success.main
                                    : healthForesightColors.error.main
                              }
                            />
                          )
                        })}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Utilization Impact by Policy (%)
                  </Typography>
                  {continuationOnlyBook || chartData.every((d) => d.utilizationChange == null) ? (
                    <Alert severity="info">
                      Policy-effect utilization change is UNESTIMATED for continuation forecasts. Showing 0% would be incorrect.
                    </Alert>
                  ) : (
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart data={chartData.filter((d) => d.utilizationChange != null)}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                      <YAxis />
                      <RechartsTooltip
                        formatter={(value: number) => `${Number(value).toFixed(1)}%`}
                        labelFormatter={(label, payload) => {
                          if (payload && payload[0]) {
                            return payload[0].payload.fullName
                          }
                          return label
                        }}
                      />
                      <Legend />
                      <Bar dataKey="utilizationChange" name="Utilization Change (%)">
                        {chartData.filter((d) => d.utilizationChange != null).map((entry, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={(entry.utilizationChange ?? 0) < 0 ? healthForesightColors.success.main : healthForesightColors.error.main}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )
      ) : (
        // Policies WITHOUT predicted impact
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Policy Name</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {policiesWithoutImpact.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} align="center">
                    <Typography variant="body2" color="text.secondary">
                      All policies have predicted impact!
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                policiesWithoutImpact.map((policy) => (
                  <TableRow key={policy.id} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {policy.name}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip label={policy.policy_type} size="small" variant="outlined" />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={policy.status || 'DRAFT'}
                        size="small"
                        color={policy.status === 'ACTIVE' ? 'success' : 'default'}
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Button
                        size="small"
                        onClick={() => handleViewPolicy(policy.id)}
                        endIcon={<ArrowForwardIcon />}
                      >
                        View Policy
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  )
}
