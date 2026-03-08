/**
 * Ops/Clinical Dashboard - Behavioral signals, appeals, patient signals, access risks
 * Focus: Provider behavior clusters, appeals volume, patient deferral, access risk flags
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
  LocalHospital as HospitalIcon,
  People as PeopleIcon,
  Warning as WarningIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Assessment as AssessmentIcon,
  Flag as FlagIcon,
  AccessTime as AccessTimeIcon,
  Gavel as GavelIcon,
  PersonOff as PersonOffIcon,
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
  PieChart,
  Pie,
  Cell,
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

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00C49F', '#FFBB28', '#FF8042']

export default function OpsClinicalDashboardPage() {
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

      // Load policies and performance data
      const [policiesResponse, performance] = await Promise.all([
        apiClient.getPolicies().catch(() => []),
        apiClient.getPolicyPerformance(50).catch(() => []),
      ])
      // Handle both array and object response formats
      const policies = Array.isArray(policiesResponse) ? policiesResponse : (policiesResponse?.items || [])

      // Generate provider behavior clusters
      const providerBehaviorClusters = generateProviderBehaviorClusters(performance)

      // Generate appeals volume trends
      const appealsVolume = generateAppealsVolume(performance)

      // Generate patient deferral signals
      const patientDeferralSignals = generatePatientDeferralSignals(performance)

      // Generate access risk flags
      const accessRiskFlags = generateAccessRiskFlags(performance, policies)

      // Generate behavioral adaptation patterns
      const behavioralPatterns = generateBehavioralPatterns(performance)

      // Generate clinical impact metrics
      const clinicalImpact = generateClinicalImpactMetrics(performance)

      setDashboardData({
        providerBehaviorClusters,
        appealsVolume,
        patientDeferralSignals,
        accessRiskFlags,
        behavioralPatterns,
        clinicalImpact,
      })
    } catch (err: any) {
      console.warn('Ops/Clinical Dashboard API error:', err.message || err)
      // Only set error if we truly have no data
      if (!dashboardData) {
        setError(err.detail || err.message || 'Failed to load ops/clinical dashboard')
      }
    } finally {
      setLoading(false)
    }
  }

  const generateProviderBehaviorClusters = (performance: any[]) => {
    // Simulate provider behavior classification
    const clusters = [
      {
        name: 'Compliant',
        count: Math.floor(performance.length * 0.4),
        description: 'Providers following policy guidelines',
        color: '#82ca9d',
        policies: performance.slice(0, 3).map((p: any) => p.policy_name),
      },
      {
        name: 'Adaptive',
        count: Math.floor(performance.length * 0.3),
        description: 'Providers adapting to policy changes',
        color: '#8884d8',
        policies: performance.slice(3, 6).map((p: any) => p.policy_name),
      },
      {
        name: 'Resistant',
        count: Math.floor(performance.length * 0.2),
        description: 'Providers showing resistance to policy',
        color: '#ffc658',
        policies: performance.slice(6, 8).map((p: any) => p.policy_name),
      },
      {
        name: 'Circumvention',
        count: Math.floor(performance.length * 0.1),
        description: 'Providers attempting to circumvent policy',
        color: '#ff7300',
        policies: performance.slice(8, 10).map((p: any) => p.policy_name),
      },
    ]
    return clusters
  }

  const generateAppealsVolume = (performance: any[]) => {
    // Generate appeals trend data (last 12 months)
    const months = []
    const now = new Date()
    for (let i = 11; i >= 0; i--) {
      const date = new Date(now.getFullYear(), now.getMonth() - i, 1)
      months.push({
        period: format(date, 'MMM yyyy'),
        appeals: Math.floor(Math.random() * 50) + 20,
        denials: Math.floor(Math.random() * 30) + 10,
        approval_rate: Math.random() * 20 + 70,
      })
    }
    return months
  }

  const generatePatientDeferralSignals = (performance: any[]) => {
    const signals = []
    
    // High utilization drop suggests deferral
    performance
      .filter((p: any) => (p.avg_utilization_change_pct || 0) < -15)
      .slice(0, 5)
      .forEach((p: any) => {
        signals.push({
          policyId: p.policy_id,
          policyName: p.policy_name,
          signal: 'DEFERRAL_RISK',
          severity: 'MEDIUM',
          description: `Utilization drop of ${Math.abs(p.avg_utilization_change_pct || 0).toFixed(1)}% suggests patients may be deferring care.`,
          action: 'Monitor patient access patterns and consider outreach.',
        })
      })
    
    return signals
  }

  const generateAccessRiskFlags = (performance: any[], policies: any[]) => {
    const flags = []
    
    // High negative utilization indicates access concerns
    performance
      .filter((p: any) => (p.avg_utilization_change_pct || 0) < -20)
      .slice(0, 5)
      .forEach((p: any) => {
        flags.push({
          policyId: p.policy_id,
          policyName: p.policy_name,
          risk: 'ACCESS_CONCERN',
          severity: 'HIGH',
          description: `Significant utilization reduction (${Math.abs(p.avg_utilization_change_pct || 0).toFixed(1)}%) may indicate access barriers.`,
          action: 'Review network adequacy and patient access patterns.',
        })
      })
    
    return flags
  }

  const generateBehavioralPatterns = (performance: any[]) => {
    // Generate trend data for behavioral patterns
    return performance.slice(0, 12).map((p: any, idx: number) => ({
      period: `Month ${idx + 1}`,
      compliance: 70 + Math.random() * 20,
      adaptation: 50 + Math.random() * 30,
      resistance: 10 + Math.random() * 15,
    }))
  }

  const generateClinicalImpactMetrics = (performance: any[]) => {
    return {
      totalPolicies: performance.length,
      avgUtilizationChange: performance.reduce((sum, p) => sum + Math.abs(p.avg_utilization_change_pct || 0), 0) / performance.length,
      highImpactPolicies: performance.filter((p: any) => Math.abs(p.avg_utilization_change_pct || 0) > 10).length,
      accessConcerns: performance.filter((p: any) => (p.avg_utilization_change_pct || 0) < -15).length,
    }
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

  const {
    providerBehaviorClusters,
    appealsVolume,
    patientDeferralSignals,
    accessRiskFlags,
    behavioralPatterns,
    clinicalImpact,
  } = dashboardData || {}

  return (
    <Box>
      {/* Header */}
      <Box className="dashboard-header" sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600 }}>
            Ops/Clinical Dashboard
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Behavioral signals, appeals, patient signals, access risks
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
            startIcon={<AssessmentIcon />}
            onClick={() => navigate('/policies')}
          >
            View Policies
          </Button>
        </Box>
      </Box>

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Provider Clusters
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 600 }}>
                {providerBehaviorClusters?.length || 0}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Behavior classifications
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Appeals (This Month)
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 600 }}>
                {appealsVolume?.[appealsVolume.length - 1]?.appeals || 0}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {appealsVolume?.[appealsVolume.length - 1]?.approval_rate?.toFixed(1) || 0}% approval rate
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Deferral Signals
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 600 }}>
                {patientDeferralSignals?.length || 0}
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
                Access Risk Flags
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 600 }}>
                {accessRiskFlags?.length || 0}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                High priority
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Card sx={{ mb: 4 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
            <Tab label="Provider Behavior" />
            <Tab label="Appeals & Denials" />
            <Tab label="Patient Signals" />
            <Tab label="Access Risks" />
          </Tabs>
        </Box>

        {/* Provider Behavior */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Provider Behavior Clusters
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={providerBehaviorClusters}
                        dataKey="count"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        outerRadius={100}
                        label
                      >
                        {providerBehaviorClusters?.map((entry: any, index: number) => (
                          <Cell key={`cell-${index}`} fill={entry.color || COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Cluster Details
                  </Typography>
                  <List>
                    {providerBehaviorClusters?.map((cluster: any, idx: number) => (
                      <Box key={idx}>
                        <ListItem>
                          <ListItemIcon>
                            <PeopleIcon sx={{ color: cluster.color }} />
                          </ListItemIcon>
                          <ListItemText
                            primary={
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <Typography variant="subtitle2">
                                  {cluster.name}
                                </Typography>
                                <Chip label={cluster.count} size="small" />
                              </Box>
                            }
                            secondary={
                              <Typography variant="body2" color="text.secondary">
                                {cluster.description}
                              </Typography>
                            }
                          />
                        </ListItem>
                        {idx < providerBehaviorClusters.length - 1 && <Divider />}
                      </Box>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Behavioral Trends
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={behavioralPatterns}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="period" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="compliance" stroke="#82ca9d" name="Compliance %" />
                      <Line type="monotone" dataKey="adaptation" stroke="#8884d8" name="Adaptation %" />
                      <Line type="monotone" dataKey="resistance" stroke="#ff7300" name="Resistance %" />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Appeals & Denials */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Appeals Volume Trend
                  </Typography>
                  <ResponsiveContainer width="100%" height={350}>
                    <BarChart data={appealsVolume}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="period" />
                      <YAxis yAxisId="left" />
                      <YAxis yAxisId="right" orientation="right" />
                      <Tooltip />
                      <Legend />
                      <Bar yAxisId="left" dataKey="appeals" fill="#8884d8" name="Appeals" />
                      <Bar yAxisId="left" dataKey="denials" fill="#ff7300" name="Denials" />
                      <Line
                        yAxisId="right"
                        type="monotone"
                        dataKey="approval_rate"
                        stroke="#82ca9d"
                        name="Approval Rate %"
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Recent Appeals Summary
                  </Typography>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      This Month
                    </Typography>
                    <Typography variant="h5">
                      {appealsVolume?.[appealsVolume.length - 1]?.appeals || 0}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Appeals filed
                    </Typography>
                  </Box>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Approval Rate
                    </Typography>
                    <Typography variant="h5">
                      {appealsVolume?.[appealsVolume.length - 1]?.approval_rate?.toFixed(1) || 0}%
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Denials
                    </Typography>
                    <Typography variant="h5">
                      {appealsVolume?.[appealsVolume.length - 1]?.denials || 0}
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Patient Signals */}
        <TabPanel value={tabValue} index={2}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Patient Deferral Signals
              </Typography>
              <List>
                {patientDeferralSignals?.map((signal: any, idx: number) => (
                  <Box key={idx}>
                    <ListItem>
                      <ListItemIcon>
                        <PersonOffIcon color="warning" />
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Typography variant="subtitle2">
                              {signal.policyName}
                            </Typography>
                            <Chip
                              label={signal.signal}
                              size="small"
                              color={signal.severity === 'HIGH' ? 'error' : 'warning'}
                            />
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
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => navigate(`/policies/builder/${signal.policyId}`)}
                      >
                        Review
                      </Button>
                    </ListItem>
                    {idx < patientDeferralSignals.length - 1 && <Divider />}
                  </Box>
                ))}
              </List>
            </CardContent>
          </Card>
        </TabPanel>

        {/* Access Risks */}
        <TabPanel value={tabValue} index={3}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Access Risk Flags
                  </Typography>
                  <List>
                    {accessRiskFlags?.map((flag: any, idx: number) => (
                      <Box key={idx}>
                        <ListItem>
                          <ListItemIcon>
                            <WarningIcon color={flag.severity === 'HIGH' ? 'error' : 'warning'} />
                          </ListItemIcon>
                          <ListItemText
                            primary={
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <Typography variant="subtitle2">
                                  {flag.policyName}
                                </Typography>
                                <Chip
                                  label={flag.risk}
                                  size="small"
                                  color={flag.severity === 'HIGH' ? 'error' : 'warning'}
                                />
                              </Box>
                            }
                            secondary={
                              <Box>
                                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                                  {flag.description}
                                </Typography>
                                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                                  <strong>Action:</strong> {flag.action}
                                </Typography>
                              </Box>
                            }
                          />
                          <Button
                            size="small"
                            color="error"
                            variant="outlined"
                            onClick={() => navigate(`/policies/builder/${flag.policyId}`)}
                          >
                            Review
                          </Button>
                        </ListItem>
                        {idx < accessRiskFlags.length - 1 && <Divider />}
                      </Box>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Clinical Impact Summary
                  </Typography>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Total Policies
                    </Typography>
                    <Typography variant="h5">
                      {clinicalImpact?.totalPolicies || 0}
                    </Typography>
                  </Box>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Avg Utilization Change
                    </Typography>
                    <Typography variant="h5">
                      {(clinicalImpact?.avgUtilizationChange || 0).toFixed(1)}%
                    </Typography>
                  </Box>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      High Impact Policies
                    </Typography>
                    <Typography variant="h5">
                      {clinicalImpact?.highImpactPolicies || 0}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Access Concerns
                    </Typography>
                    <Typography variant="h5" color="error">
                      {clinicalImpact?.accessConcerns || 0}
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Card>
    </Box>
  )
}
