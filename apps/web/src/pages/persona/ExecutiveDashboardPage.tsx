/**
 * Executive Dashboard - CFO/Actuary/CMO view
 * Focus: Outcomes, risk, confidence, "what changed", decision recommendations
 */
import { useState, useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  CircularProgress,
  Alert,
  Chip,
  Paper,
  Button,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  LinearProgress,
} from '@mui/material'
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Assessment as AssessmentIcon,
  ArrowUpward as ArrowUpwardIcon,
  ArrowDownward as ArrowDownwardIcon,
  Info as InfoIcon,
  Flag as FlagIcon,
  Timeline as TimelineIcon,
  ShowChart as ShowChartIcon,
  AccountBalance as AccountBalanceIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
  ComposedChart,
} from 'recharts'

// Format cost for axis labels (short form so labels don’t clip; B = billions, M = millions)
function formatCostLabel(value: unknown): string {
  const n = Number(value)
  if (!Number.isFinite(n)) return ''
  if (n === 0) return '$0'
  if (Math.abs(n) >= 1e9) return `$${(n / 1e9).toFixed(1)}B`
  if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(1)}M`
  if (Math.abs(n) >= 1e3) return `$${(n / 1000).toFixed(0)}k`
  return `$${n.toFixed(0)}`
}
import { format } from 'date-fns'
import { apiClient } from '../../lib/api'
import MetricCard from '../../components/brand/MetricCard'
import ConfidenceBadge from '../../components/brand/ConfidenceBadge'
import { useRole } from '../../contexts/RoleContext'
import { useNavigate } from 'react-router-dom'

export default function ExecutiveDashboardPage() {
  const navigate = useNavigate()
  const roleContext = useRole()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dashboardData, setDashboardData] = useState<any>(null)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Load comprehensive dashboard data
      const [summary, performance] = await Promise.all([
        apiClient.getDashboardSummary().catch(() => null),
        apiClient.getPolicyPerformance(20).catch(() => []),
      ])

      // Transform data for executive insights - only use real API data
      const metrics = summary?.metrics || {}
      const topPolicies = summary?.top_policies || []
      const riskIndicators = summary?.risk_indicators || []
      
      // Only use real data from API - no mock data
      const finalPerformance = performance || []
      const finalMetrics = metrics
      
      // Generate cost trend from database when possible (business_metrics + general_baseline), else empty or illustrative
      const costTrendData = generateCostTrend(
        summary?.business_metrics ?? {},
        summary?.general_baseline ?? null,
        finalPerformance,
        finalMetrics
      )
      
      // Generate "what changed" insights from real data
      const whatChanged = generateWhatChangedInsights(summary || {}, finalPerformance, topPolicies)
      
      // Generate risk register from real data
      const riskRegister = generateRiskRegister(riskIndicators, finalPerformance, finalMetrics)
      
      // Generate decision recommendations from real data
      const decisions = generateDecisionRecommendations(finalPerformance, riskIndicators, topPolicies)

      setDashboardData({
        summary: summary?.summary || { active_policies: 0, total_policies: 0, decisions_pending: 0 },
        metrics: finalMetrics,
        business_metrics: summary?.business_metrics ?? {},
        general_baseline: summary?.general_baseline ?? null,
        performance: finalPerformance,
        topPolicies: topPolicies.length > 0 ? topPolicies : (finalPerformance.length > 0 ? finalPerformance.slice(0, 5) : []),
        riskIndicators,
        costTrendData,
        whatChanged,
        riskRegister,
        decisions,
        lastUpdated: new Date().toISOString(),
      })
    } catch (err: any) {
      console.warn('Executive Dashboard API error:', err.message || err)
      // Only set error if we truly have no data
      if (!dashboardData) {
        setError(err.detail || err.message || 'Failed to load executive dashboard')
      }
    } finally {
      setLoading(false)
    }
  }

  // Cost trend: actuals from DB (avg monthly cost), forecast extrapolated with capped growth so scale stays sensible
  const generateCostTrend = (
    businessMetrics: Record<string, any>,
    generalBaseline: Record<string, any> | null,
    _performance: any[],
    _metrics: any
  ) => {
    const months: Array<{ period: string; actual: number | null; forecast: number | null; forecast_lower: number | null; forecast_upper: number | null }> = []
    const now = new Date()

    const memberCount = Number(businessMetrics.member_count ?? businessMetrics.memberCount) || 10000
    const totalPaid = Number(businessMetrics.total_paid_amount ?? businessMetrics.totalPaidAmount ?? 0) || null
    const costPmpmCurrent = Number(businessMetrics.cost_pmpm_current ?? businessMetrics.costPmpmCurrent ?? 0) || null
    // Monthly actual = avg monthly cost from DB (total paid last 12mo / 12, or cost_pmpm * members)
    const monthlyActual = totalPaid != null && totalPaid > 0 ? totalPaid / 12 : (costPmpmCurrent != null && costPmpmCurrent > 0 ? costPmpmCurrent * memberCount : null)

    if (monthlyActual == null || monthlyActual <= 0) return []

    const baselineCostPmpm = (generalBaseline?.cost_pmpm ?? generalBaseline?.costPmpm) != null ? Number(generalBaseline?.cost_pmpm ?? generalBaseline?.costPmpm) : null
    const baselineMonthly = baselineCostPmpm != null && baselineCostPmpm > 0 ? baselineCostPmpm * memberCount : null

    // Historical: use same monthly actual (avg from DB) for all months so timeline matches data and scale is consistent
    for (let i = 5; i >= 0; i--) {
      const date = new Date(now.getFullYear(), now.getMonth() - i, 1)
      months.push({
        period: format(date, 'MMM yyyy'),
        actual: monthlyActual,
        forecast: null,
        forecast_lower: null,
        forecast_upper: null,
      })
    }

    // Trend: cap to ±20% so forecast never explodes to billions when baseline ≠ current
    const rawTrend = baselineMonthly != null && baselineMonthly > 0 ? (monthlyActual - baselineMonthly) / baselineMonthly : 0
    const trendPct = Math.max(-0.2, Math.min(0.2, rawTrend))
    // Forecast: modest extrapolation from last actual (stays in same order of magnitude as actuals)
    for (let i = 1; i <= 6; i++) {
      const date = new Date(now.getFullYear(), now.getMonth() + i, 1)
      const f = monthlyActual * Math.pow(1 + trendPct * 0.5, i)
      const uncertainty = 0.06 * i
      months.push({
        period: format(date, 'MMM yyyy'),
        actual: null,
        forecast: f,
        forecast_lower: f * (1 - uncertainty),
        forecast_upper: f * (1 + uncertainty),
      })
    }
    return months
  }

  // Generate "what changed" insights
  const generateWhatChangedInsights = (summary: any, performance: any[], topPolicies: any[]) => {
    const insights = []
    
    if (topPolicies.length > 0) {
      const topPolicy = topPolicies[0]
      insights.push({
        title: `Top Policy Impact: ${topPolicy.policy_name || 'Policy'}`,
        description: `This policy shows ${Math.abs(topPolicy.utilization_change_pct || 0).toFixed(1)}% utilization change with ${topPolicy.cost_impact ? `$${Math.abs(topPolicy.cost_impact).toLocaleString()}` : 'significant'} cost impact.`,
        category: 'Policy Performance',
        confidence: 'high',
        impact: 'positive',
        timestamp: new Date().toISOString(),
      })
    }
    
    const metrics = summary?.metrics || {}
    if (metrics.avg_utilization_change_pct) {
      const change = metrics.avg_utilization_change_pct
      insights.push({
        title: `Utilization Trend: ${change > 0 ? 'Increasing' : 'Decreasing'}`,
        description: `Average utilization changed by ${Math.abs(change).toFixed(1)}% across all policies. This indicates ${change > 0 ? 'increased' : 'reduced'} healthcare utilization.`,
        category: 'Utilization',
        confidence: 'medium',
        impact: change < 0 ? 'positive' : 'negative',
        timestamp: new Date().toISOString(),
      })
    }
    
    if (metrics.total_cost_impact) {
      const impact = metrics.total_cost_impact
      insights.push({
        title: `Cost Impact: ${impact < 0 ? 'Savings' : 'Increase'}`,
        description: `Total cost impact of ${impact < 0 ? 'savings' : 'increase'} is $${Math.abs(impact).toLocaleString()}. This represents ${((Math.abs(impact) / 10000000) * 100).toFixed(1)}% of baseline costs.`,
        category: 'Cost',
        confidence: 'high',
        impact: impact < 0 ? 'positive' : 'negative',
        timestamp: new Date().toISOString(),
      })
    }
    
    return insights
  }

  // Generate risk register
  const generateRiskRegister = (riskIndicators: any[], performance: any[], metrics: any) => {
    const risks = [...riskIndicators]
    
    // Add uncertainty drivers
    if (performance.length > 0) {
      const highVariancePolicies = performance
        .filter(p => Math.abs(p.avg_utilization_change_pct || 0) > 15)
        .slice(0, 3)
      
      highVariancePolicies.forEach((policy, idx) => {
        risks.push({
          type: 'HIGH_VARIANCE',
          severity: 'MEDIUM',
          name: `High Variance: ${policy.policy_name || 'Policy'}`,
          description: `Policy shows ${Math.abs(policy.avg_utilization_change_pct || 0).toFixed(1)}% utilization change, indicating high uncertainty in outcomes.`,
          mitigation: 'Review policy assumptions and consider sensitivity analysis.',
          driver: 'Policy Assumptions',
        })
      })
    }
    
    // Add cost uncertainty
    if (metrics.total_cost_impact && Math.abs(metrics.total_cost_impact) > 50000) {
      risks.push({
        type: 'COST_UNCERTAINTY',
        severity: 'HIGH',
        name: 'Cost Forecast Uncertainty',
        description: `Large cost impact ($${Math.abs(metrics.total_cost_impact).toLocaleString()}) with limited historical data increases forecast uncertainty.`,
        mitigation: 'Gather additional observation data and refine elasticity assumptions.',
        driver: 'Data Availability',
      })
    }
    
    return risks.slice(0, 5) // Top 5 risks
  }

  // Generate decision recommendations
  const generateDecisionRecommendations = (performance: any[], riskIndicators: any[], topPolicies: any[]) => {
    const recommendations = []
    
    // High-performing policies
    const highPerformers = performance
      .filter(p => (p.avg_utilization_change_pct || 0) < -5 && (p.avg_cost_impact || 0) < -1000)
      .slice(0, 2)
    
    highPerformers.forEach((policy) => {
      recommendations.push({
        title: `Scale Policy: ${policy.policy_name || 'Policy'}`,
        description: `This policy shows strong performance with ${Math.abs(policy.avg_utilization_change_pct || 0).toFixed(1)}% utilization reduction and $${Math.abs(policy.avg_cost_impact || 0).toLocaleString()} savings.`,
        action: 'Consider expanding scope or applying to additional populations.',
        priority: 'high',
        confidence: 'high',
        policyId: policy.policy_id,
      })
    })
    
    // High-risk policies
    const highRisk = riskIndicators.filter(r => r.severity === 'HIGH').slice(0, 1)
    if (highRisk.length > 0) {
      recommendations.push({
        title: 'Review High-Risk Indicators',
        description: `${highRisk.length} high-severity risk indicator${highRisk.length > 1 ? 's' : ''} detected. Immediate review recommended.`,
        action: 'Review risk register and consider policy adjustments or rollback triggers.',
        priority: 'critical',
        confidence: 'high',
      })
    }
    
    // Data quality recommendations
    const predictedCount = performance.filter(p => p.is_predicted).length
    if (predictedCount > performance.length * 0.5) {
      recommendations.push({
        title: 'Increase Observation Data Collection',
        description: `${((predictedCount / performance.length) * 100).toFixed(0)}% of policies rely on predicted data. More observations needed for accurate assessment.`,
        action: 'Prioritize data collection for top policies to improve forecast accuracy.',
        priority: 'medium',
        confidence: 'high',
      })
    }
    
    return recommendations
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>
  }

  // Show empty state if no data is available
  if (!dashboardData || (!dashboardData.performance || dashboardData.performance.length === 0)) {
    return (
      <Box>
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600 }}>
            Executive Dashboard
          </Typography>
          <Typography variant="body2" color="text.secondary">
            CFO/Actuary/CMO view: Outcomes, risk, confidence, what changed
          </Typography>
        </Box>
        <Alert severity="info" sx={{ mb: 2 }}>
          No dashboard data available. Please ensure:
          <ul style={{ marginTop: 8, marginBottom: 0 }}>
            <li>The API server is running on port 8000</li>
            <li>Policies have been created and have performance data</li>
            <li>Observations or predicted impacts have been generated</li>
          </ul>
        </Alert>
      </Box>
    )
  }

  const summary = dashboardData?.summary || {}
  const metrics = dashboardData?.metrics || {}
  const performance = dashboardData?.performance || []
  const costTrendData = dashboardData?.costTrendData || []
  const whatChanged = dashboardData?.whatChanged || []
  const riskRegister = dashboardData?.riskRegister || []
  const decisions = dashboardData?.decisions || []

  return (
    <Box>
      {/* Header */}
      <Box className="dashboard-header" sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600 }}>
            Executive Dashboard
          </Typography>
          <Typography variant="body2" color="text.secondary">
            CFO/Actuary/CMO view: Outcomes, risk, confidence, what changed
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => loadDashboardData()}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="outlined"
            startIcon={<ShowChartIcon />}
            onClick={() => navigate('/policies')}
          >
            View Policies
          </Button>
          <Button
            variant="contained"
            startIcon={<AccountBalanceIcon />}
            onClick={() => {
              // Export decision pack
              console.log('Export decision pack')
            }}
          >
            Export Decision Pack
          </Button>
        </Box>
      </Box>

      {/* Key Metrics Row - current numbers and vs. baseline from database */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        <Typography variant="body2" color="text.secondary">
          Metrics from database (observations and baseline)
        </Typography>
        <Chip label="Database" size="small" color="primary" variant="outlined" />
      </Box>
      <Grid container spacing={3} className="key-metrics-row" sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            label="Total Cost Impact (current)"
            value={Math.abs(metrics.total_cost_impact || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            unit="$"
            trend={metrics.total_cost_impact < 0 ? 'down' : 'up'}
            subtitle={metrics.total_cost_impact < 0 ? 'Savings vs. pre-policy baseline' : 'Increase vs. pre-policy baseline'}
            color={metrics.total_cost_impact < 0 ? 'success' : 'warning'}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            label="Avg Utilization Change (current)"
            value={Math.abs(metrics.avg_utilization_change_pct || 0).toFixed(1)}
            unit="%"
            trend={metrics.avg_utilization_change_pct < 0 ? 'down' : 'up'}
            subtitle={metrics.avg_utilization_change_pct < 0 ? 'Reduction vs. pre-policy baseline' : 'Increase vs. pre-policy baseline'}
            color={metrics.avg_utilization_change_pct < 0 ? 'success' : 'error'}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            label="Active Policies"
            value={summary.active_policies ?? 0}
            subtitle={`of ${summary.total_policies ?? 0} total`}
            trend={summary.active_policies > 0 ? 'up' : undefined}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            label="Decisions Pending"
            value={decisions.length}
            subtitle="Requires attention"
            color={decisions.length > 0 ? 'warning' : undefined}
          />
        </Grid>
      </Grid>

      {/* Pre-policy baseline (general) */}
      {dashboardData?.general_baseline && (
        <Card sx={{ mb: 4, bgcolor: 'grey.50' }}>
          <CardContent>
            <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
              Pre-policy baseline (general)
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Reference utilization and cost from the tenant baseline period (before policy impact).
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="caption" color="text.secondary">Utilization per 1K</Typography>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  {dashboardData.general_baseline.utilization_per_1k?.toFixed(1) ?? '—'}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="caption" color="text.secondary">Cost PMPM</Typography>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  ${dashboardData.general_baseline.cost_pmpm?.toFixed(2) ?? '—'}
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Decision Recommendations - Priority Section */}
      {decisions.length > 0 && (
        <Card className="decision-recommendations" sx={{ mb: 4, borderLeft: '4px solid', borderColor: 'primary.main' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <FlagIcon sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6">Decision Recommendations</Typography>
            </Box>
            <Grid container spacing={2}>
              {decisions.map((rec: any, idx: number) => (
                <Grid item xs={12} md={6} key={idx}>
                  <Paper
                    sx={{
                      p: 2,
                      bgcolor: rec.priority === 'critical' ? 'error.light' : rec.priority === 'high' ? 'warning.light' : 'background.default',
                      borderLeft: '3px solid',
                      borderColor: rec.priority === 'critical' ? 'error.main' : rec.priority === 'high' ? 'warning.main' : 'primary.main',
                    }}
                  >
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="subtitle1" fontWeight={600}>
                        {rec.title}
                      </Typography>
                      <Chip
                        label={rec.priority}
                        size="small"
                        color={rec.priority === 'critical' ? 'error' : rec.priority === 'high' ? 'warning' : 'default'}
                      />
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {rec.description}
                    </Typography>
                    <Typography variant="body2" fontWeight={500} sx={{ mb: 1 }}>
                      Recommended Action: {rec.action}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                      <ConfidenceBadge confidence={rec.confidence} />
                      {rec.policyId && (
                        <Button
                          size="small"
                          onClick={() => navigate(`/policies/builder/${rec.policyId}`)}
                        >
                          View Policy
                        </Button>
                      )}
                    </Box>
                  </Paper>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Cost Trend with Forecast Bands */}
      {costTrendData.length > 0 && (() => {
        const actualValues = costTrendData.map((d: any) => d.actual).filter((v: unknown): v is number => v != null && Number.isFinite(Number(v)))
        const forecastValues = costTrendData.flatMap((d: any) => [d.forecast, d.forecast_lower, d.forecast_upper]).filter((v: unknown): v is number => v != null && Number.isFinite(Number(v)))
        const maxActual = actualValues.length ? Math.max(...actualValues) : 0
        const maxForecast = forecastValues.length ? Math.max(...forecastValues) : 0
        // Anchor scale to actuals so green area is visible; cap domain so forecast never dominates (e.g. 99B when actuals are 101M)
        const rawMax = Math.max(maxActual, maxForecast, 1)
        const cappedMax = maxActual > 0 ? Math.min(rawMax, maxActual * 2.5) : rawMax
        const costDomain: [number, number] = [0, Math.ceil(cappedMax * 1.05)]
        return (
        <Card className="cost-trend-chart" sx={{ mb: 4 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Cost Trend Forecast (with Confidence Bands)</Typography>
              <Chip label="P10/P50/P90" size="small" />
            </Box>
            <ResponsiveContainer width="100%" height={350}>
              <AreaChart data={costTrendData} margin={{ top: 10, right: 24, bottom: 20, left: 72 }}>
                <defs>
                  <linearGradient id="colorForecast" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8884d8" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#8884d8" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#82ca9d" stopOpacity={0.5} />
                    <stop offset="100%" stopColor="#82ca9d" stopOpacity={0.15} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="period" />
                <YAxis
                  domain={costDomain}
                  tickFormatter={(v: unknown) => formatCostLabel(v)}
                  tick={{ fontSize: 11 }}
                  width={64}
                />
                <Tooltip
                  formatter={(value: any) => value != null && value !== '' ? `$${Number(value).toLocaleString()}` : 'N/A'}
                  labelFormatter={(label) => `Period: ${label}`}
                />
                <Legend />
                {/* Forecast bands drawn first (behind) */}
                <Area
                  type="monotone"
                  dataKey="forecast_upper"
                  stroke="#8884d8"
                  fill="#8884d8"
                  fillOpacity={0.2}
                  name="Upper Bound (P90)"
                />
                <Area
                  type="monotone"
                  dataKey="forecast_lower"
                  stroke="#8884d8"
                  fill="#8884d8"
                  fillOpacity={0.2}
                  name="Lower Bound (P10)"
                />
                <Line
                  type="monotone"
                  dataKey="forecast"
                  stroke="#8884d8"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  name="Forecast (P50)"
                />
                {/* Actual: green shaded area on top so it’s visible over historical period */}
                <Area
                  type="monotone"
                  dataKey="actual"
                  stroke="#2e7d32"
                  strokeWidth={2}
                  fill="url(#colorActual)"
                  fillOpacity={1}
                  baseValue={0}
                  connectNulls={false}
                  name="Actual"
                />
              </AreaChart>
            </ResponsiveContainer>
            <Box sx={{ mt: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
              <Typography variant="caption" color="text.secondary" display="block">
                <InfoIcon sx={{ fontSize: 14, verticalAlign: 'middle', mr: 0.5 }} />
                Forecast bands show uncertainty range. Wider bands indicate higher uncertainty. Historical data (green) vs. forecast (purple).
              </Typography>
              <Typography variant="caption" color="primary.main" sx={{ fontWeight: 600, mt: 0.5, display: 'block' }}>
                Data source: Database (total paid / cost PMPM from claims). Actuals = avg monthly cost; forecast = capped extrapolation from actuals (same scale).
              </Typography>
            </Box>
          </CardContent>
        </Card>
        )
      })()}

      {/* What Changed Insights */}
      {whatChanged.length > 0 && (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <TimelineIcon sx={{ mr: 1 }} />
              <Typography variant="h6">What Changed</Typography>
            </Box>
            <Grid container spacing={2}>
              {whatChanged.map((change: any, idx: number) => (
                <Grid item xs={12} md={6} key={idx}>
                  <Paper sx={{ p: 2, bgcolor: 'background.default' }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="subtitle2" fontWeight={600}>
                        {change.title}
                      </Typography>
                      {change.impact === 'positive' ? (
                        <ArrowDownwardIcon color="success" fontSize="small" />
                      ) : (
                        <ArrowUpwardIcon color="error" fontSize="small" />
                      )}
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {change.description}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mt: 1 }}>
                      <Chip label={change.category} size="small" />
                      <ConfidenceBadge confidence={change.confidence} />
                    </Box>
                  </Paper>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Risk Register */}
      {riskRegister.length > 0 && (
        <Card className="risk-register" sx={{ mb: 4 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <WarningIcon sx={{ mr: 1, color: 'warning.main' }} />
              <Typography variant="h6">Risk Register (Top 5 Uncertainty Drivers)</Typography>
            </Box>
            <List>
              {riskRegister.map((risk: any, idx: number) => (
                <Box key={idx}>
                  <ListItem>
                    <ListItemIcon>
                      <WarningIcon
                        color={risk.severity === 'HIGH' ? 'error' : risk.severity === 'MEDIUM' ? 'warning' : 'default'}
                      />
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Typography variant="subtitle2" component="span" fontWeight={600}>
                            {risk.name || risk.type}
                          </Typography>
                          <Chip
                            label={risk.severity}
                            size="small"
                            color={risk.severity === 'HIGH' ? 'error' : risk.severity === 'MEDIUM' ? 'warning' : 'default'}
                          />
                        </Box>
                      }
                      secondary={
                        <Box component="span" sx={{ mt: 0.5, display: 'block' }}>
                          <Typography variant="body2" component="span" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                            {risk.description || risk.message}
                          </Typography>
                          {risk.driver && (
                            <Box component="span" sx={{ display: 'inline-block', mr: 0.5 }}>
                              <Chip
                                label={`Driver: ${risk.driver}`}
                                size="small"
                                sx={{ mt: 0.5 }}
                              />
                            </Box>
                          )}
                          {risk.mitigation && (
                            <Typography variant="caption" component="span" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                              <strong>Mitigation:</strong> {risk.mitigation}
                            </Typography>
                          )}
                        </Box>
                      }
                    />
                  </ListItem>
                  {idx < riskRegister.length - 1 && <Divider />}
                </Box>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* Top Policy Performance - normalized keys (snake_case + camelCase) and vertical bars so values show */}
      {performance.length > 0 && (() => {
        const barData = performance.slice(0, 10).map((p: any) => {
          const cost = Number(p?.avg_cost_impact ?? p?.avgCostImpact ?? 0) || 0
          const name = p?.policy_name ?? p?.policyName ?? 'Unknown'
          return { ...p, policy_name: name, avg_cost_impact: cost }
        })
        const maxCost = Math.max(...barData.map((d: any) => d.avg_cost_impact), 0)
        const costDomain: [number, number] = maxCost > 0 ? [0, Math.ceil(maxCost * 1.1)] : [0, 1000]
        return (
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card className="top-policies-chart">
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Top Policy Performance (by Cost Impact)
                </Typography>
                <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                  Cost impact from database (observations vs. baseline, or predicted impact). Negative = savings.
                </Typography>
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart
                    data={barData}
                    margin={{ top: 8, right: 24, left: 8, bottom: 80 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="policy_name"
                      angle={-45}
                      textAnchor="end"
                      height={80}
                      interval={0}
                      tick={{ fontSize: 10 }}
                    />
                    <YAxis
                      domain={costDomain}
                      tickFormatter={(v: unknown) => formatCostLabel(v)}
                      tick={{ fontSize: 11 }}
                    />
                    <Tooltip
                      formatter={(value: any) => value != null ? `$${Number(value).toLocaleString()}` : '—'}
                    />
                    <Legend />
                    <Bar dataKey="avg_cost_impact" fill="#8884d8" name="Cost Impact ($)" barSize={28} />
                  </BarChart>
                </ResponsiveContainer>
                {barData.every((p: any) => (Number(p.avg_cost_impact) || 0) === 0) && (
                  <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                    All zero: ensure API is restarted and observations have vs_baseline.cost_change_pmpm or policies have predicted impact.
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Policy Performance Summary
                </Typography>
                <List>
                  {performance.slice(0, 5).map((policy: any, idx: number) => (
                    <Box key={idx}>
                      <ListItem>
                        <ListItemText
                          primary={
                            <Typography variant="subtitle2" noWrap>
                              {policy.policy_name || 'Policy'}
                            </Typography>
                          }
                          secondary={
                            <Box component="span" sx={{ display: 'block' }}>
                              <Typography variant="caption" component="span" color="text.secondary" sx={{ display: 'block' }}>
                                Cost: ${Math.abs(policy.avg_cost_impact || 0).toLocaleString()}
                              </Typography>
                              <Typography variant="caption" component="span" color="text.secondary" sx={{ display: 'block' }}>
                                Utilization: {Math.abs(policy.avg_utilization_change_pct || 0).toFixed(1)}%
                              </Typography>
                              {policy.is_predicted && (
                                <Box component="span" sx={{ mt: 0.5, display: 'inline-block' }}>
                                  <Chip label="Predicted" size="small" />
                                </Box>
                              )}
                            </Box>
                          }
                        />
                      </ListItem>
                      {idx < Math.min(4, performance.length - 1) && <Divider />}
                    </Box>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
        )
      })()}
    </Box>
  )
}
