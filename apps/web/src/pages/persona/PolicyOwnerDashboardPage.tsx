/**
 * Policy Owner Dashboard - Policy lifecycle management view
 * Focus: Lifecycle states, assumptions, approvals, compliance signals, rollback triggers
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
  Tabs,
  Tab,
  Badge,
} from '@mui/material'
import {
  Edit as EditIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Schedule as ScheduleIcon,
  Assignment as AssignmentIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Flag as FlagIcon,
  History as HistoryIcon,
  Assessment as AssessmentIcon,
  Gavel as GavelIcon,
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
} from 'recharts'
import { format } from 'date-fns'
import { apiClient } from '../../lib/api'
import { useNavigate } from 'react-router-dom'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  )
}

export default function PolicyOwnerDashboardPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dashboardData, setDashboardData] = useState<any>(null)
  const [tabValue, setTabValue] = useState(0)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)

      try {
        // Try to get policy owner dashboard data from API
        const data = await apiClient.getPolicyOwnerDashboard().catch(() => null) as any
        
        // Load policies, performance, and dashboard summary (for general baseline)
        const [policies, performance, summary] = await Promise.all([
          apiClient.getPolicies().catch(() => []),
          apiClient.getPolicyPerformance(50).catch(() => []),
          apiClient.getDashboardSummary().catch(() => null),
        ])
        
        const policiesListAll = Array.isArray(policies) ? policies : (policies?.items || [])
        const norm = (s: string | undefined) => (s ?? '').toString().toUpperCase().trim()
        
        // Organize policies by lifecycle state (case-insensitive). Empty/missing status = ACTIVE (API default).
        const policiesByState = {
          DRAFT: policiesListAll.filter((p: any) => norm(p.status) === 'DRAFT'),
          PROPOSED: policiesListAll.filter((p: any) => norm(p.status) === 'PROPOSED'),
          APPROVED: policiesListAll.filter((p: any) => norm(p.status) === 'APPROVED'),
          ACTIVE: policiesListAll.filter((p: any) => norm(p.status) === 'ACTIVE' || !norm(p.status)),
          MONITORING: policiesListAll.filter((p: any) => norm(p.status) === 'MONITORING'),
          ITERATING: policiesListAll.filter((p: any) => norm(p.status) === 'ITERATING'),
          SUNSET: policiesListAll.filter((p: any) => norm(p.status) === 'SUNSET'),
        }
        
        const policiesInFlight = [
          ...policiesByState.DRAFT,
          ...policiesByState.PROPOSED,
          ...policiesByState.MONITORING,
          ...policiesByState.ITERATING,
        ]
        
        const assumptionsTracking = generateAssumptionsTracking(policiesListAll, performance)
        const approvalsPending = policiesByState.PROPOSED.map((p: any) => ({
          policyId: p.id || p.policy_id,
          policyName: p.name || p.policy_name,
          status: 'PROPOSED',
          submittedAt: p.created_at || new Date().toISOString(),
          requiresExecutive: (p.cost_impact || 0) > 100000,
          approvers: ['Policy Owner', p.cost_impact > 100000 ? 'Executive' : null].filter(Boolean),
        }))
        const complianceSignals = generateComplianceSignals(policiesListAll, performance)
        const rollbackTriggers = generateRollbackTriggers(policiesListAll, performance)
        const performanceTrends = generatePerformanceTrends(performance)
        
        // Use API data if available, otherwise use generated data
        setDashboardData({
          policiesByState,
          policiesInFlight: (data && data.policies_in_flight && data.policies_in_flight.length > 0)
            ? data.policies_in_flight
            : policiesInFlight,
          assumptionsTracking: (data && data.assumptions_pending && data.assumptions_pending.length > 0)
            ? data.assumptions_pending
            : assumptionsTracking,
          approvalsPending: (data && data.approvals_pending && data.approvals_pending.length > 0)
            ? data.approvals_pending
            : approvalsPending,
          complianceSignals: (data && data.compliance_signals && data.compliance_signals.length > 0)
            ? data.compliance_signals
            : complianceSignals,
          rollbackTriggers,
          performanceTrends,
          totalPolicies: policiesListAll.length,
          generalBaseline: (summary as any)?.general_baseline ?? null,
        })
        return
      } catch (err: any) {
        console.warn('Policy Owner dashboard API not available, using fallback:', err)
        // Fallback: load policies and create dashboard data
      }

      // Load policies, summary (for baseline), and performance
      const [policiesRes, summary, performance] = await Promise.all([
        apiClient.getPolicies().catch(() => []),
        apiClient.getDashboardSummary().catch(() => null),
        apiClient.getPolicyPerformance(50).catch(() => []),
      ])
      const policiesList = Array.isArray(policiesRes) ? policiesRes : (policiesRes?.items || [])
      const norm = (s: string | undefined) => (s ?? '').toString().toUpperCase().trim()

      // Organize policies by lifecycle state (case-insensitive). Empty/missing status = ACTIVE (API default).
      const policiesByState = {
        DRAFT: policiesList.filter((p: any) => norm(p.status) === 'DRAFT'),
        PROPOSED: policiesList.filter((p: any) => norm(p.status) === 'PROPOSED'),
        APPROVED: policiesList.filter((p: any) => norm(p.status) === 'APPROVED'),
        ACTIVE: policiesList.filter((p: any) => norm(p.status) === 'ACTIVE' || !norm(p.status)),
        MONITORING: policiesList.filter((p: any) => norm(p.status) === 'MONITORING'),
        ITERATING: policiesList.filter((p: any) => norm(p.status) === 'ITERATING'),
        SUNSET: policiesList.filter((p: any) => norm(p.status) === 'SUNSET'),
      }

      // Policies in flight (need attention)
      const policiesInFlight = [
        ...policiesByState.DRAFT,
        ...policiesByState.PROPOSED,
        ...policiesByState.MONITORING,
        ...policiesByState.ITERATING,
      ]

      // Generate assumptions tracking
      const assumptionsTracking = generateAssumptionsTracking(policiesList, performance)

      // Generate approval workflows
      const approvalsPending = policiesByState.PROPOSED.map((p: any) => ({
        policyId: p.id || p.policy_id,
        policyName: p.name || p.policy_name,
        status: 'PROPOSED',
        submittedAt: p.created_at || new Date().toISOString(),
        requiresExecutive: (p.cost_impact || 0) > 100000,
        approvers: ['Policy Owner', p.cost_impact > 100000 ? 'Executive' : null].filter(Boolean),
      }))

      // Generate compliance signals
      const complianceSignals = generateComplianceSignals(policiesList, performance)

      // Generate rollback triggers
      const rollbackTriggers = generateRollbackTriggers(policiesList, performance)

      // Policy performance trends
      const performanceTrends = generatePerformanceTrends(performance)

      setDashboardData({
        policiesByState,
        policiesInFlight,
        assumptionsTracking,
        approvalsPending,
        complianceSignals,
        rollbackTriggers,
        performanceTrends,
        totalPolicies: policiesList.length,
        generalBaseline: (summary as any)?.general_baseline ?? null,
      })
    } catch (err: any) {
      console.warn('Policy Owner Dashboard API unavailable, using empty data:', err.message || err)
      // Set empty data so page can still render
      setDashboardData({
        policiesByState: { DRAFT: [], PROPOSED: [], APPROVED: [], ACTIVE: [], MONITORING: [], ITERATING: [], SUNSET: [] },
        policiesInFlight: [],
        assumptionsTracking: [],
        approvalsPending: [],
        complianceSignals: [],
        rollbackTriggers: [],
        performanceTrends: [],
        totalPolicies: 0,
      })
      setError(null) // Don't show error, just use empty data
    } finally {
      setLoading(false)
    }
  }

  const generateAssumptionsTracking = (policies: any[], performance: any[]) => {
    const assumptions = []
    
    policies.slice(0, 10).forEach((policy: any) => {
      const policyPerf = performance.find((p: any) => 
        (p.policy_id === policy.id) || (p.policy_id === policy.policy_id)
      )
      
      if (policyPerf) {
        assumptions.push({
          policyId: policy.id || policy.policy_id,
          policyName: policy.name || policy.policy_name,
          assumption: 'Elasticity Range',
          expected: '-5% to -15%',
          actual: `${policyPerf.avg_utilization_change_pct?.toFixed(1) || 0}%`,
          status: Math.abs(policyPerf.avg_utilization_change_pct || 0) > 15 ? 'out_of_range' : 'within_range',
          confidence: policyPerf.is_predicted ? 'low' : 'high',
        })
      }
    })
    
    return assumptions
  }

  const generateComplianceSignals = (policies: any[], performance: any[]) => {
    const signals = []
    
    // Check for adaptation signals (high variance)
    performance
      .filter((p: any) => Math.abs(p.avg_utilization_change_pct || 0) > 20)
      .slice(0, 3)
      .forEach((p: any) => {
        signals.push({
          type: 'ADAPTATION',
          severity: 'MEDIUM',
          policyId: p.policy_id,
          policyName: p.policy_name,
          description: `High utilization variance (${Math.abs(p.avg_utilization_change_pct || 0).toFixed(1)}%) suggests provider adaptation.`,
          action: 'Review policy assumptions and consider adjustments.',
        })
      })
    
    // Check for resistance signals (low impact)
    performance
      .filter((p: any) => Math.abs(p.avg_utilization_change_pct || 0) < 2 && Math.abs(p.avg_cost_impact || 0) < 1000)
      .slice(0, 2)
      .forEach((p: any) => {
        signals.push({
          type: 'RESISTANCE',
          severity: 'LOW',
          policyId: p.policy_id,
          policyName: p.policy_name,
          description: `Minimal impact suggests provider resistance or policy ineffectiveness.`,
          action: 'Review policy design and provider engagement.',
        })
      })
    
    return signals
  }

  const generateRollbackTriggers = (policies: any[], performance: any[]) => {
    const triggers = []
    
    // High negative utilization (access concerns)
    performance
      .filter((p: any) => (p.avg_utilization_change_pct || 0) < -20)
      .slice(0, 2)
      .forEach((p: any) => {
        triggers.push({
          policyId: p.policy_id,
          policyName: p.policy_name,
          trigger: 'ACCESS_CONCERN',
          threshold: '-20%',
          actual: `${p.avg_utilization_change_pct?.toFixed(1) || 0}%`,
          severity: 'HIGH',
          description: `Utilization drop exceeds threshold, indicating potential access issues.`,
          action: 'Review patient access patterns and consider rollback.',
        })
      })
    
    // High cost increase
    performance
      .filter((p: any) => (p.avg_cost_impact || 0) > 50000)
      .slice(0, 2)
      .forEach((p: any) => {
        triggers.push({
          policyId: p.policy_id,
          policyName: p.policy_name,
          trigger: 'COST_OVERRUN',
          threshold: '$50k',
          actual: `$${Math.abs(p.avg_cost_impact || 0).toLocaleString()}`,
          severity: 'MEDIUM',
          description: `Cost impact exceeds threshold.`,
          action: 'Review cost drivers and consider adjustments.',
        })
      })
    
    return triggers
  }

  const generatePerformanceTrends = (performance: any[]) => {
    // Group by month (simplified - would use actual dates)
    const trends = performance.slice(0, 12).map((p: any, idx: number) => ({
      period: `Month ${idx + 1}`,
      utilization: Math.abs(p.avg_utilization_change_pct || 0),
      cost: Math.abs(p.avg_cost_impact || 0) / 1000, // in thousands
    }))
    
    return trends
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'> = {
      DRAFT: 'default',
      PROPOSED: 'warning',
      APPROVED: 'info',
      ACTIVE: 'success',
      MONITORING: 'primary',
      ITERATING: 'warning',
      SUNSET: 'default',
    }
    return colors[status] || 'default'
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

  if (!dashboardData) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Alert severity="info">No dashboard data available. Please try refreshing.</Alert>
      </Box>
    )
  }

  const {
    policiesByState = {},
    policiesInFlight = [],
    assumptionsTracking = [],
    approvalsPending = [],
    complianceSignals = [],
    rollbackTriggers = [],
    performanceTrends = [],
    totalPolicies = 0,
    generalBaseline = null,
  } = dashboardData

  return (
    <Box>
      {/* Header */}
      <Box className="dashboard-header" sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600 }}>
            Policy Owner Dashboard
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Lifecycle management, assumptions, approvals, compliance signals
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
            variant="contained"
            startIcon={<EditIcon />}
            onClick={() => navigate('/policies/builder')}
          >
            Create Policy
          </Button>
        </Box>
      </Box>

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Policies In Flight
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 600 }}>
                {policiesInFlight?.length || 0}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                of {totalPolicies || 0} total
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Approvals Pending
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 600 }}>
                {approvalsPending?.length || 0}
              </Typography>
              <Badge badgeContent={approvalsPending?.filter((a: any) => a.requiresExecutive).length || 0} color="error">
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                  Require Executive
                </Typography>
              </Badge>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Compliance Signals
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 600 }}>
                {complianceSignals?.length || 0}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Require attention
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Rollback Triggers
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 600 }}>
                {rollbackTriggers?.length || 0}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Threshold exceeded
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Pre-policy baseline (general) */}
      {generalBaseline && (
        <Card sx={{ mb: 4, bgcolor: 'grey.50' }}>
          <CardContent>
            <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
              Pre-policy baseline (general)
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Reference utilization and cost from the tenant baseline period (before policy impact). Used to compare policy outcomes.
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="caption" color="text.secondary">Utilization per 1K</Typography>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  {(generalBaseline as any).utilization_per_1k?.toFixed(1) ?? '—'}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="caption" color="text.secondary">Cost PMPM</Typography>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  ${(generalBaseline as any).cost_pmpm?.toFixed(2) ?? '—'}
                </Typography>
              </Grid>
              {(generalBaseline as any).member_months != null && (
                <Grid item xs={12} sm={6} md={3}>
                  <Typography variant="caption" color="text.secondary">Member months</Typography>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    {(generalBaseline as any).member_months?.toLocaleString() ?? '—'}
                  </Typography>
                </Grid>
              )}
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Tabs for different views */}
      <Card sx={{ mb: 4 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
            <Tab label="Policies In Flight" />
            <Tab label="Assumptions & Risks" />
            <Tab label="Approvals" />
            <Tab label="Monitoring" />
          </Tabs>
        </Box>

        {/* Policies In Flight */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={2}>
            {Object.entries(policiesByState || {}).map(([state, policies]: [string, any]) => {
              return (
                <Grid item xs={12} md={6} key={state}>
                  <Card variant="outlined">
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                        <Typography variant="h6">{state}</Typography>
                        <Chip label={(policies as any[]).length} size="small" color={getStatusColor(state)} />
                      </Box>
                      <List>
                        {(policies as any[]).slice(0, 5).map((policy: any, idx: number) => (
                          <Box key={idx}>
                            <ListItem>
                              <ListItemText
                                primary={
                                  <Typography variant="subtitle2" noWrap>
                                    {policy.name || policy.policy_name || 'Unnamed Policy'}
                                  </Typography>
                                }
                                secondary={
                                  <Box>
                                    <Typography variant="caption" color="text.secondary">
                                      {policy.created_at ? format(new Date(policy.created_at), 'MMM d, yyyy') : 'No date'}
                                    </Typography>
                                  </Box>
                                }
                              />
                              <Button
                                size="small"
                                onClick={() => navigate(`/policies/builder/${policy.id || policy.policy_id}`)}
                              >
                                View
                              </Button>
                            </ListItem>
                            {idx < Math.min(4, (policies as any[]).length - 1) && <Divider />}
                          </Box>
                        ))}
                      </List>
                    </CardContent>
                  </Card>
                </Grid>
              )
            })}
          </Grid>
        </TabPanel>

        {/* Assumptions & Risks */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Assumptions Tracking
                  </Typography>
                  <List>
                    {assumptionsTracking?.slice(0, 10).map((assumption: any, idx: number) => (
                      <Box key={idx}>
                        <ListItem>
                          <ListItemIcon>
                            {assumption.status === 'within_range' ? (
                              <CheckCircleIcon color="success" />
                            ) : (
                              <WarningIcon color="warning" />
                            )}
                          </ListItemIcon>
                          <ListItemText
                            primary={
                              <Typography variant="subtitle2">
                                {assumption.policyName}
                              </Typography>
                            }
                            secondary={
                              <Box>
                                <Typography variant="caption" color="text.secondary">
                                  {assumption.assumption}: Expected {assumption.expected}, Actual {assumption.actual}
                                </Typography>
                                <Box sx={{ mt: 0.5 }}>
                                  <Chip
                                    label={assumption.status === 'within_range' ? 'Within Range' : 'Out of Range'}
                                    size="small"
                                    color={assumption.status === 'within_range' ? 'success' : 'warning'}
                                    sx={{ mr: 0.5 }}
                                  />
                                  <Chip
                                    label={`Confidence: ${assumption.confidence}`}
                                    size="small"
                                  />
                                </Box>
                              </Box>
                            }
                          />
                        </ListItem>
                        {idx < Math.min(9, assumptionsTracking.length - 1) && <Divider />}
                      </Box>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Compliance Signals
                  </Typography>
                  <List>
                    {complianceSignals?.map((signal: any, idx: number) => (
                      <Box key={idx}>
                        <ListItem>
                          <ListItemIcon>
                            <FlagIcon color={signal.severity === 'HIGH' ? 'error' : 'warning'} />
                          </ListItemIcon>
                          <ListItemText
                            primary={
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <Typography variant="subtitle2">
                                  {signal.policyName}
                                </Typography>
                                <Chip label={signal.type} size="small" color={signal.severity === 'HIGH' ? 'error' : 'warning'} />
                              </Box>
                            }
                            secondary={
                              <Box>
                                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                                  {signal.description}
                                </Typography>
                                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                                  <strong>Action:</strong> {signal.action}
                                </Typography>
                              </Box>
                            }
                          />
                        </ListItem>
                        {idx < complianceSignals.length - 1 && <Divider />}
                      </Box>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Approvals */}
        <TabPanel value={tabValue} index={2}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Pending Approvals
              </Typography>
              <List>
                {approvalsPending?.map((approval: any, idx: number) => (
                  <Box key={idx}>
                    <ListItem>
                      <ListItemIcon>
                        <GavelIcon color={approval.requiresExecutive ? 'error' : 'warning'} />
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Typography variant="subtitle2">
                              {approval.policyName}
                            </Typography>
                            <Chip
                              label={approval.status}
                              size="small"
                              color="warning"
                            />
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2" color="text.secondary">
                              Submitted: {format(new Date(approval.submittedAt), 'MMM d, yyyy')}
                            </Typography>
                            <Box sx={{ mt: 0.5 }}>
                              {approval.approvers.map((approver: string, aIdx: number) => (
                                <Chip
                                  key={aIdx}
                                  label={approver}
                                  size="small"
                                  sx={{ mr: 0.5 }}
                                />
                              ))}
                            </Box>
                          </Box>
                        }
                      />
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => navigate(`/policies/builder/${approval.policyId}`)}
                      >
                        Review
                      </Button>
                    </ListItem>
                    {idx < approvalsPending.length - 1 && <Divider />}
                  </Box>
                ))}
              </List>
            </CardContent>
          </Card>
        </TabPanel>

        {/* Monitoring */}
        <TabPanel value={tabValue} index={3}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Policy Performance Trends
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={performanceTrends}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="period" />
                      <YAxis yAxisId="left" />
                      <YAxis yAxisId="right" orientation="right" />
                      <Tooltip />
                      <Legend />
                      <Line
                        yAxisId="left"
                        type="monotone"
                        dataKey="utilization"
                        stroke="#8884d8"
                        name="Utilization Change %"
                      />
                      <Line
                        yAxisId="right"
                        type="monotone"
                        dataKey="cost"
                        stroke="#82ca9d"
                        name="Cost Impact ($k)"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Rollback Triggers
                  </Typography>
                  <List>
                    {rollbackTriggers?.map((trigger: any, idx: number) => (
                      <Box key={idx}>
                        <ListItem>
                          <ListItemIcon>
                            <WarningIcon color={trigger.severity === 'HIGH' ? 'error' : 'warning'} />
                          </ListItemIcon>
                          <ListItemText
                            primary={
                              <Typography variant="subtitle2">
                                {trigger.policyName}
                              </Typography>
                            }
                            secondary={
                              <Box>
                                <Typography variant="caption" color="text.secondary">
                                  {trigger.trigger}: {trigger.actual} (Threshold: {trigger.threshold})
                                </Typography>
                                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                                  {trigger.description}
                                </Typography>
                                <Button
                                  size="small"
                                  color="error"
                                  sx={{ mt: 1 }}
                                  onClick={() => navigate(`/policies/builder/${trigger.policyId}`)}
                                >
                                  Review
                                </Button>
                              </Box>
                            }
                          />
                        </ListItem>
                        {idx < rollbackTriggers.length - 1 && <Divider />}
                      </Box>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Card>
    </Box>
  )
}
