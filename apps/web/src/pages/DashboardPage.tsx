/**
 * HealthForesight Executive Dashboard Page
 * Phase 9: Enhanced with metrics, visualizations, and insights
 */
import { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Grid,
  Typography,
  Paper,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Link,
  IconButton,
} from '@mui/material'
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Notifications as NotificationsIcon,
  Settings as SettingsIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
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
  AreaChart,
  Area,
} from 'recharts'
import { apiClient } from '../lib/api'
import MetricCard from '../components/brand/MetricCard'
import ConfidenceBadge from '../components/brand/ConfidenceBadge'
import { healthForesightColors } from '../theme/healthForesightTheme'
import { format } from 'date-fns'
import { useRole } from '../contexts/RoleContext'
import TourButton from '../components/tour/TourButton'

export default function DashboardPage() {
  const navigate = useNavigate()
  
  // Always call useRole() - it returns safe defaults if provider isn't available
  const roleContext = useRole()
  const currentPersona = roleContext.currentPersona

  // ALL HOOKS MUST BE CALLED BEFORE ANY CONDITIONAL RETURNS
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dashboardData, setDashboardData] = useState<any>(null)
  const [policyPerformance, setPolicyPerformance] = useState<any[]>([])
  const [widgetConfig, setWidgetConfig] = useState<any[]>([])

  // Route to persona-specific dashboard if persona is set
  useEffect(() => {
    if (currentPersona) {
      const personaRoutes: Record<string, string> = {
        EXECUTIVE: '/dashboard/executive',
        POLICY_OWNER: '/dashboard/policy-owner',
        ANALYST: '/dashboard/analyst',
        OPS_CLINICAL: '/dashboard/ops-clinical',
      }
      const route = personaRoutes[currentPersona]
      const currentPath = window.location.pathname
      
      // Navigate if we're on the root dashboard and persona is set
      if (route && (currentPath === '/' || currentPath === '/dashboard')) {
        console.log('DashboardPage: Navigating to persona dashboard:', route)
        navigate(route, { replace: true })
      }
      // Also navigate if we're on a different persona's dashboard
      else if (route && !currentPath.startsWith(route)) {
        console.log('DashboardPage: Persona changed, navigating to:', route)
        navigate(route, { replace: true })
      }
    }
  }, [currentPersona, navigate])

  // Helper functions (must be defined before useEffect that uses them)
  const loadWidgetConfig = () => {
    try {
      const saved = localStorage.getItem('dashboard_widgets')
      if (saved) {
        const parsed = JSON.parse(saved)
        setWidgetConfig(parsed)
      } else {
        // Default: show all widgets
        setWidgetConfig([])
      }
    } catch (err) {
      console.error('Failed to load widget config:', err)
    }
  }

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Load dashboard summary and policy performance
      const [summary, performance] = await Promise.all([
        apiClient.getDashboardSummary().catch((err) => {
          console.error('Error loading dashboard summary:', err)
          return null
        }),
        apiClient.getPolicyPerformance(50).catch((err) => {
          console.error('Error loading policy performance:', err)
          return []
        }),
      ])

      console.log('Dashboard data loaded:', { 
        summary: summary ? 'present' : 'null', 
        performanceCount: performance?.length || 0 
      })
      
      setDashboardData(summary)
      setPolicyPerformance(performance || [])
    } catch (err: any) {
      console.error('Dashboard API error:', err)
      // Set empty data so page can still render
      setDashboardData(null)
      setPolicyPerformance([])
      // Show error if it's a real error (not just empty data)
      if (err.status !== 0 && err.code !== 'ECONNABORTED' && !err.message?.includes('timeout')) {
        setError(err.detail || err.message || 'Failed to load dashboard data')
      } else {
        setError(null) // Don't show error for network issues
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadWidgetConfig()
    loadDashboardData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // NOW we can do conditional returns AFTER all hooks are called
  // Note: Persona-specific dashboards have their own routes (/dashboard/executive, etc.)
  // This page shows the default executive dashboard
  // The routing logic above will navigate to persona-specific routes when persona is set


  if (loading && !dashboardData) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress />
      </Box>
    )
  }

  const summary = dashboardData?.summary || {}
  const metrics = dashboardData?.metrics || {}
  const riskIndicators = dashboardData?.risk_indicators || []
  const recentActivity = dashboardData?.recent_activity || []

  // Prepare chart data for cost impact visualization
  const costImpactData = policyPerformance
    .slice(0, 5)
    .map((policy) => ({
      name: policy.policy_name?.substring(0, 20) || 'Policy',
      cost: Math.abs(policy.avg_cost_impact || 0),
      utilization: Math.abs(policy.avg_utilization_change_pct || 0),
    }))

  // Prepare utilization trend data
  const utilizationTrendData = policyPerformance.slice(0, 6).map((policy, idx) => ({
    period: `P${idx + 1}`,
    change: policy.avg_utilization_change_pct || 0,
  }))

  return (
    <Box>
      {/* Header */}
      <Box 
        className="dashboard-header"
        sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}
      >
        <Box>
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
            Executive Dashboard
          </Typography>
          <Typography
            variant="body1"
            sx={{
              color: healthForesightColors.neutral.mid,
              lineHeight: 1.6,
            }}
          >
            Real-time insights into policy performance, cost impact, and utilization trends
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          <TourButton module="dashboard" showBadge={true} />
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
            startIcon={<SettingsIcon />}
            onClick={() => navigate('/dashboard/customize')}
          >
            Customize
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error.includes('Connection refused') || error.includes('Network Error') ? (
            <Box>
              <Typography variant="body2" gutterBottom>
                <strong>API Server Not Running</strong>
              </Typography>
              <Typography variant="body2" component="div">
                The API server on port 8000 is not running. Please start it:
                <Box component="pre" sx={{ mt: 1, p: 1, bgcolor: 'background.paper', borderRadius: 1, fontSize: '0.875rem' }}>
                  ./start-api-server.sh
                </Box>
                Or manually:
                <Box component="pre" sx={{ mt: 1, p: 1, bgcolor: 'background.paper', borderRadius: 1, fontSize: '0.875rem' }}>
                  cd apps/api && poetry run uvicorn uepi_api.main:app --reload --port 8000
                </Box>
              </Typography>
            </Box>
          ) : (
            error
          )}
        </Alert>
      )}

      {/* Executive-Level Metrics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }} className="key-metrics-row">
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            label="Active Policies"
            value={summary.active_policies || 0}
            subtitle={`of ${summary.total_policies || 0} total`}
            trend={summary.active_policies > 0 ? 'up' : undefined}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            label="Total Cost Impact"
            value={Math.abs(metrics.total_cost_impact || 0).toLocaleString()}
            unit="$"
            subtitle={
              metrics.total_cost_impact < 0
                ? `Avg savings vs. pre-policy baseline`
                : `Avg impact vs. pre-policy baseline`
            }
            color={metrics.total_cost_impact < 0 ? 'success' : 'warning'}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            label="Avg Utilization Change"
            value={Math.abs(metrics.avg_utilization_change_pct || 0).toFixed(1)}
            unit="%"
            subtitle={
              metrics.avg_utilization_change_pct < 0
                ? 'Reduction vs. pre-policy baseline'
                : 'Increase vs. pre-policy baseline'
            }
            color={metrics.avg_utilization_change_pct < 0 ? 'success' : 'error'}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            label="Recent Analyses"
            value={summary.recent_analyses || 0}
            subtitle="Last 30 days"
            trend={summary.recent_analyses > 5 ? 'up' : undefined}
          />
        </Grid>
      </Grid>

      {/* Enterprise-Grade Business Metrics Section */}
      {dashboardData && (
        <Card sx={{ mb: 4, bgcolor: 'background.paper' }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h5" sx={{ fontWeight: 600, color: healthForesightColors.neutral.dark }}>
                Business Performance Metrics
              </Typography>
              <Chip 
                label="Database-Driven" 
                color="primary" 
                size="small"
                sx={{ fontWeight: 500 }}
              />
            </Box>
            
            <Grid container spacing={3}>
              {/* Member & Claims Metrics */}
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 2 }}>
                  <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600, color: healthForesightColors.neutral.dark }}>
                    Population & Claims Overview
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">Total Members</Typography>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        {dashboardData.business_metrics?.member_count?.toLocaleString() || 'N/A'}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">Total Claims</Typography>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        {dashboardData.business_metrics?.total_claims_count?.toLocaleString() || 'N/A'}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">Claims/Member</Typography>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        {dashboardData.business_metrics?.claims_per_member?.toFixed(1) || 'N/A'}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">Cost/Claim</Typography>
                      <Typography variant="h6" sx={{ fontWeight: 600, color: healthForesightColors.primary.main }}>
                        ${dashboardData.business_metrics?.cost_per_claim?.toFixed(2) || 'N/A'}
                      </Typography>
                    </Grid>
                  </Grid>
                </Paper>
              </Grid>

              {/* Financial Impact Metrics */}
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 2 }}>
                  <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600, color: healthForesightColors.neutral.dark }}>
                    Financial Impact
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">Total Paid</Typography>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        ${(dashboardData.business_metrics?.total_paid_amount || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">Cost PMPM</Typography>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        ${dashboardData.business_metrics?.cost_pmpm_current?.toFixed(2) || 'N/A'}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">Annualized Savings</Typography>
                      <Typography variant="h6" sx={{ fontWeight: 600, color: healthForesightColors.success.main }}>
                        ${(dashboardData.business_metrics?.annualized_savings || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">Savings PMPM</Typography>
                      <Typography variant="h6" sx={{ fontWeight: 600, color: healthForesightColors.success.main }}>
                        ${dashboardData.business_metrics?.savings_pmpm?.toFixed(2) || 'N/A'}
                      </Typography>
                    </Grid>
                  </Grid>
                </Paper>
              </Grid>

              {/* ROI & Efficiency Metrics */}
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 2 }}>
                  <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600, color: healthForesightColors.neutral.dark }}>
                    ROI & Efficiency
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">ROI Estimate</Typography>
                      <Typography variant="h6" sx={{ fontWeight: 600, color: healthForesightColors.success.main }}>
                        {dashboardData.business_metrics?.roi_estimate_pct?.toFixed(1) || 'N/A'}%
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">Payback Period</Typography>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        {dashboardData.business_metrics?.payback_period_months ? `${dashboardData.business_metrics.payback_period_months} months` : 'N/A'}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">Utilization Reduction</Typography>
                      <Typography variant="h6" sx={{ fontWeight: 600, color: healthForesightColors.success.main }}>
                        {dashboardData.business_metrics?.total_utilization_reduction_pct?.toFixed(1) || 'N/A'}%
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">Members Impacted</Typography>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        {dashboardData.business_metrics?.members_impacted?.toLocaleString() || 'N/A'}
                      </Typography>
                    </Grid>
                  </Grid>
                </Paper>
              </Grid>

              {/* Data Coverage */}
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 2 }}>
                  <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600, color: healthForesightColors.neutral.dark }}>
                    Data Coverage
                  </Typography>
                  {dashboardData.business_metrics?.claims_date_range?.start && dashboardData.business_metrics?.claims_date_range?.end ? (
                    <Box>
                      <Typography variant="caption" color="text.secondary">Date Range</Typography>
                      <Typography variant="body1" sx={{ fontWeight: 500 }}>
                        {format(new Date(dashboardData.business_metrics.claims_date_range.start), 'MMM d, yyyy')} - {format(new Date(dashboardData.business_metrics.claims_date_range.end), 'MMM d, yyyy')}
                      </Typography>
                    </Box>
                  ) : (
                    <Typography variant="body2" color="text.secondary">No claims data available</Typography>
                  )}
                </Paper>
              </Grid>

              {/* Pre-policy baseline (general) */}
              {dashboardData.general_baseline && (
                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 2 }}>
                    <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600, color: healthForesightColors.neutral.dark }}>
                      Pre-policy baseline (general)
                    </Typography>
                    <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                      Reference utilization and cost from tenant baseline period.
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <Typography variant="caption" color="text.secondary">Utilization per 1K</Typography>
                        <Typography variant="h6" sx={{ fontWeight: 600 }}>
                          {dashboardData.general_baseline.utilization_per_1k?.toFixed(1) ?? '—'}
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="caption" color="text.secondary">Cost PMPM</Typography>
                        <Typography variant="h6" sx={{ fontWeight: 600 }}>
                          ${dashboardData.general_baseline.cost_pmpm?.toFixed(2) ?? '—'}
                        </Typography>
                      </Grid>
                    </Grid>
                  </Paper>
                </Grid>
              )}
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Risk Indicators */}
      {riskIndicators.length > 0 && (
        <Alert
          severity={riskIndicators.some((r: any) => r.severity === 'HIGH') ? 'warning' : 'info'}
          icon={<WarningIcon />}
          sx={{ mb: 3 }}
          className="risk-register"
        >
          <Typography variant="subtitle2" gutterBottom>
            <strong>Risk Indicators</strong>
          </Typography>
          {riskIndicators.map((indicator: any, idx: number) => (
            <Box key={idx} sx={{ mt: 1 }}>
              <Chip
                label={indicator.severity}
                size="small"
                color={indicator.severity === 'HIGH' ? 'error' : 'warning'}
                sx={{ mr: 1, mb: 0.5 }}
              />
              {indicator.message}
            </Box>
          ))}
        </Alert>
      )}

      {/* Cost Impact & Utilization Trends */}
      <Grid container spacing={3} sx={{ mb: 4 }} className="cost-trend-chart">
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Cost Impact by Policy
              </Typography>
              {costImpactData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={costImpactData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
                    <YAxis />
                    <Tooltip
                      formatter={(value: any) => `$${value.toLocaleString()}`}
                    />
                    <Legend />
                    <Bar dataKey="cost" fill={healthForesightColors.accent.start} name="Cost Impact ($)" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <Box sx={{ py: 4, textAlign: 'center', color: 'text.secondary' }}>
                  No cost impact data available
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Utilization Trends
              </Typography>
              {utilizationTrendData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={utilizationTrendData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="period" />
                    <YAxis />
                    <Tooltip formatter={(value: any) => `${value.toFixed(1)}%`} />
                    <Area
                      type="monotone"
                      dataKey="change"
                      stroke={healthForesightColors.primary}
                      fill={healthForesightColors.primary}
                      fillOpacity={0.3}
                      name="Utilization Change (%)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <Box sx={{ py: 4, textAlign: 'center', color: 'text.secondary' }}>
                  No utilization trend data available
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Policy Performance Table */}
      <Grid container spacing={3} sx={{ mb: 4 }} className="top-policies-chart">
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">Policy Performance</Typography>
                <IconButton size="small" onClick={loadDashboardData}>
                  <Typography variant="caption">Refresh</Typography>
                </IconButton>
              </Box>
              {policyPerformance.length > 0 ? (
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Policy Name</TableCell>
                        <TableCell>Effective</TableCell>
                        <TableCell>Through</TableCell>
                        <TableCell align="right">Status</TableCell>
                        <TableCell align="right">Utilization Change</TableCell>
                        <TableCell align="right">Cost Impact</TableCell>
                        <TableCell align="right">Prediction Accuracy</TableCell>
                        <TableCell align="right">Observations</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {policyPerformance.map((policy: any) => (
                        <TableRow key={policy.policy_id} hover>
                          <TableCell>
                            <Link
                              href={`/policies/builder/${policy.policy_id}`}
                              underline="hover"
                            >
                              {policy.policy_name}
                            </Link>
                          </TableCell>
                          <TableCell>
                            {policy.policy_effective_date
                              ? format(new Date(policy.policy_effective_date.split('T')[0]), 'MMM d, yyyy')
                              : '—'}
                          </TableCell>
                          <TableCell>
                            {policy.latest_observation_period_end
                              ? format(new Date(policy.latest_observation_period_end.split('T')[0]), 'MMM d, yyyy')
                              : '—'}
                          </TableCell>
                          <TableCell align="right">
                            <Chip
                              label={policy.status}
                              size="small"
                              color={policy.status === 'ACTIVE' ? 'success' : 'default'}
                            />
                          </TableCell>
                          <TableCell align="right">
                            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 0.5 }}>
                              {policy.avg_utilization_change_pct < 0 ? (
                                <TrendingDownIcon color="success" fontSize="small" />
                              ) : (
                                <TrendingUpIcon color="error" fontSize="small" />
                              )}
                              {Math.abs(policy.avg_utilization_change_pct || 0).toFixed(1)}%
                            </Box>
                          </TableCell>
                          <TableCell align="right">
                            {policy.avg_cost_impact < 0 ? (
                              <Typography variant="body2" color="success.main">
                                ${Math.abs(policy.avg_cost_impact || 0).toLocaleString()}
                              </Typography>
                            ) : (
                              <Typography variant="body2" color="error.main">
                                ${Math.abs(policy.avg_cost_impact || 0).toLocaleString()}
                              </Typography>
                            )}
                          </TableCell>
                          <TableCell align="right">
                            {policy.avg_prediction_accuracy_pct !== null ? (
                              <ConfidenceBadge score={policy.avg_prediction_accuracy_pct / 100} />
                            ) : (
                              <Typography variant="body2" color="text.secondary">
                                N/A
                              </Typography>
                            )}
                          </TableCell>
                          <TableCell align="right">{policy.observations_count || 0}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Box sx={{ py: 4, textAlign: 'center', color: 'text.secondary' }}>
                  No policy performance data available
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Activity Feed */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6} className="decision-recommendations">
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Activity
              </Typography>
              {recentActivity.length > 0 ? (
                <Box>
                  {recentActivity.map((activity: any, idx: number) => (
                    <Box
                      key={idx}
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 2,
                        py: 1.5,
                        borderBottom: idx < recentActivity.length - 1 ? '1px solid' : 'none',
                        borderColor: 'divider',
                      }}
                    >
                      <CheckCircleIcon color="success" fontSize="small" />
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="body2" fontWeight={500}>
                          {activity.type} Analysis
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {activity.created_at
                            ? format(new Date(activity.created_at), 'MMM d, yyyy HH:mm')
                            : 'Unknown date'}
                        </Typography>
                      </Box>
                      <Chip
                        label={activity.status}
                        size="small"
                        color={activity.status === 'COMPLETED' ? 'success' : 'default'}
                      />
                    </Box>
                  ))}
                </Box>
              ) : (
                <Box sx={{ py: 4, textAlign: 'center', color: 'text.secondary' }}>
                  No recent activity
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* System Status */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Status
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Typography variant="body2">Data Coverage</Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <ConfidenceBadge score={0.98} />
                    <Typography variant="body2" color="text.secondary">
                      98%
                    </Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Typography variant="body2">Completed Analyses</Typography>
                  <Chip
                    label={summary.completed_analyses || 0}
                    size="small"
                    color="success"
                  />
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Typography variant="body2">Total Observations</Typography>
                  <Chip
                    label={summary.total_observations || 0}
                    size="small"
                    color="primary"
                  />
                </Box>
                {dashboardData?.last_updated && (
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Last Updated</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {format(new Date(dashboardData.last_updated), 'MMM d, HH:mm')}
                    </Typography>
                  </Box>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
