/**
 * Policy Workspace Page - Comprehensive policy management interface
 * Epic 2: Policy Lifecycle Management
 * 
 * Features:
 * - Overview tab: Policy summary, current state, key metrics
 * - Scope tab: Policy scope configuration
 * - Levers tab: Policy levers management
 * - Assumptions tab: Assumptions management
 * - Guardrails tab: Guardrails/rollback triggers
 * - Monitoring tab: Performance metrics, guardrail status
 * - Versions tab: Version history and comparison
 * - Decisions tab: Linked decisions (Epic 3)
 * - Evidence tab: Evidence links (Epic 3)
 */
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  CircularProgress,
  Alert,
  Chip,
  Button,
  Grid,
  Paper,
  List,
  ListItem,
  ListItemText,
} from '@mui/material'
import {
  ArrowBack as ArrowBackIcon,
  Edit as EditIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
} from '@mui/icons-material'
import { apiClient } from '../lib/api'
import ScopeSelectorEnhanced from '../components/policy/ScopeSelectorEnhanced'
import LeverList from '../components/policy/LeverList'
import AssumptionsManager from '../components/policy/AssumptionsManager'
import GuardrailsManager from '../components/policy/GuardrailsManager'
import PolicyVersionsList from '../components/policy/PolicyVersionsList'
import PolicyChangelog from '../components/policy/PolicyChangelog'
import DecisionManager from '../components/decision/DecisionManager'
import EvidenceManager from '../components/decision/EvidenceManager'
import ForecastManager from '../components/uncertainty/ForecastManager'
import ScenarioManager from '../components/uncertainty/ScenarioManager'
import RiskRegister from '../components/uncertainty/RiskRegister'
import BehaviorDashboard from '../components/behavior/BehaviorDashboard'
import AlertManager from '../components/behavior/AlertManager'
import CommentsPanel from '../components/collaboration/CommentsPanel'
import TasksPanel from '../components/collaboration/TasksPanel'
import ActivityFeed from '../components/collaboration/ActivityFeed'
import NarrativeView from '../components/narrative/NarrativeView'
import TourButton from '../components/tour/TourButton'
import PolicyClaimCounts from '../components/policy/PolicyClaimCounts'

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

const WORKSPACE_TABS = [
  'Overview',
  'Scope',
  'Levers',
  'Assumptions',
  'Guardrails',
  'Monitoring',
  'Versions',
  'Changelog',
  'Decisions',  // Epic 3
  'Evidence',   // Epic 3
  'Forecasts',  // Epic 4
  'Scenarios',  // Epic 4
  'Risk Register', // Epic 4
  'Behavior',   // Epic 5
  'Alerts',     // Epic 5
  'Comments',   // Epic 6
  'Tasks',      // Epic 6
  'Activity',   // Epic 6
  'Narrative',  // Epic 7
]

export default function PolicyWorkspacePage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState(0)
  const [workspaceData, setWorkspaceData] = useState<any>(null)
  const [policy, setPolicy] = useState<any>(null)

  useEffect(() => {
    if (id) {
      loadWorkspaceData()
    }
  }, [id])

  const loadWorkspaceData = async () => {
    if (!id) return
    
    try {
      setLoading(true)
      setError(null)
      
      // Load workspace data (includes policy, versions, assumptions, guardrails, changelog)
      const data = await apiClient.getPolicyWorkspace(id)
      console.log('PolicyWorkspacePage: Loaded workspace data:', {
        hasPolicy: !!data.policy,
        assumptionsCount: data.assumptions?.length || 0,
        guardrailsCount: data.guardrails?.length || 0,
        versionsCount: data.versions?.length || 0,
        changelogCount: data.changelog?.length || 0,
        fullData: data
      })
      setWorkspaceData(data)
      setPolicy(data.policy)
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to load policy workspace')
      console.error('Failed to load workspace:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleStateChange = async (newState: string, reason: string) => {
    if (!id) return
    
    try {
      // Get current user ID (simplified - would come from auth context)
      const userId = '00000000-0000-0000-0000-000000000001' // Demo user
      await apiClient.updatePolicyState(id, newState, reason, userId)
      await loadWorkspaceData() // Reload to get updated state
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to update policy state')
      console.error('Failed to update state:', err)
    }
  }

  const getStateColor = (state: string) => {
    const colors: Record<string, 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'> = {
      DRAFT: 'default',
      PROPOSED: 'warning',
      APPROVED: 'info',
      ACTIVE: 'success',
      MONITORING: 'primary',
      ITERATING: 'warning',
      SUNSET: 'default',
    }
    return colors[state] || 'default'
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/policies')} sx={{ mt: 2 }}>
          Back to Policies
        </Button>
      </Box>
    )
  }

  if (!policy) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="info">Policy not found</Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/policies')} sx={{ mt: 2 }}>
          Back to Policies
        </Button>
      </Box>
    )
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/policies')}
            sx={{ mb: 2 }}
          >
            Back to Policies
          </Button>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <Typography variant="h4" component="h1" sx={{ fontWeight: 600 }}>
              {policy.name || policy.policy_name || 'Policy Workspace'}
            </Typography>
            <TourButton module="policy-workspace" size="small" />
          </Box>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mt: 1 }}>
            <Chip
              label={policy.status || 'DRAFT'}
              color={getStateColor(policy.status || 'DRAFT')}
              size="small"
            />
            {policy.policy_type && (
              <Chip label={policy.policy_type} variant="outlined" size="small" />
            )}
          </Box>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<EditIcon />}
            onClick={() => navigate(`/policies/builder/${id}`)}
          >
            Edit Policy
          </Button>
        </Box>
      </Box>

      {/* Tabs */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs 
            className="workspace-tabs"
            value={activeTab} 
            onChange={(e, v) => setActiveTab(v)}
            variant="scrollable"
            scrollButtons="auto"
            allowScrollButtonsMobile
          >
            {WORKSPACE_TABS.map((tab) => (
              <Tab key={tab} label={tab} />
            ))}
          </Tabs>
        </Box>

        <CardContent>
          {/* Overview Tab */}
          <TabPanel value={activeTab} index={0}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Policy Information
                    </Typography>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      <strong>Name:</strong> {policy.name || policy.policy_name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      <strong>Type:</strong> {policy.policy_type}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      <strong>Status:</strong> {policy.status || 'DRAFT'}
                    </Typography>
                    {policy.description && (
                      <Typography variant="body2" color="text.secondary" paragraph>
                        <strong>Description:</strong> {policy.description}
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Lifecycle State
                    </Typography>
                    <Box sx={{ mb: 2 }}>
                      <Chip
                        label={policy.status || 'DRAFT'}
                        color={getStateColor(policy.status || 'DRAFT')}
                        sx={{ mb: 2 }}
                      />
                    </Box>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      Current state: <strong>{policy.status || 'DRAFT'}</strong>
                    </Typography>
                    {workspaceData?.versions && workspaceData.versions.length > 0 && (
                      <Typography variant="body2" color="text.secondary">
                        Latest version: <strong>v{workspaceData.versions[0].version_number}</strong>
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Assumptions
                    </Typography>
                    <Typography variant="h4" sx={{ fontWeight: 600 }}>
                      {workspaceData?.assumptions?.length || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total assumptions defined
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Guardrails
                    </Typography>
                    <Typography variant="h4" sx={{ fontWeight: 600 }}>
                      {workspaceData?.guardrails?.length || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {workspaceData?.guardrails?.filter((g: any) => g.triggered).length || 0} triggered
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </TabPanel>

          {/* Scope Tab */}
          <TabPanel value={activeTab} index={1}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Policy Scope
                </Typography>
                <Alert severity="info" sx={{ mb: 2 }}>
                  Scope configuration is read-only in workspace view. Use "Edit Policy" to modify.
                </Alert>
                <Box sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    <strong>LOB:</strong> {policy.scope?.lob?.join(', ') || 'Not specified'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    <strong>Markets:</strong> {policy.scope?.markets?.join(', ') || 'Not specified'}
                  </Typography>
                  {policy.effective_period?.start_date && (
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                      <strong>Effective:</strong> {new Date(policy.effective_period.start_date).toLocaleDateString()}
                      {policy.effective_period.end_date && ` - ${new Date(policy.effective_period.end_date).toLocaleDateString()}`}
                    </Typography>
                  )}
                </Box>
                {id && (
                  <Box sx={{ mt: 3 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Claim counts (scope + levers)
                    </Typography>
                    <PolicyClaimCounts policyId={id} />
                  </Box>
                )}
              </CardContent>
            </Card>
          </TabPanel>

          {/* Levers Tab */}
          <TabPanel value={activeTab} index={2}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Policy Levers
                </Typography>
                <Alert severity="info" sx={{ mb: 2 }}>
                  Lever configuration is read-only in workspace view. Use "Edit Policy" to modify.
                </Alert>
                {(!policy.levers || policy.levers.length === 0) && (!policy.policy_levers || policy.policy_levers.length === 0) ? (
                  <Typography variant="body2" color="text.secondary">
                    No levers defined
                  </Typography>
                ) : (
                  <List>
                    {(policy.levers || policy.policy_levers || []).map((lever: any, idx: number) => (
                      <ListItem key={idx}>
                        <ListItemText
                          primary={lever.lever_type || lever.type || `Lever ${idx + 1}`}
                          secondary={lever.description || JSON.stringify(lever.parameters || {})}
                        />
                      </ListItem>
                    ))}
                  </List>
                )}
              </CardContent>
            </Card>
          </TabPanel>

          {/* Assumptions Tab */}
          <TabPanel value={activeTab} index={3}>
            <Box className="assumptions-manager">
              <AssumptionsManager
                policyId={id!}
                assumptions={workspaceData?.assumptions || []}
                onRefresh={loadWorkspaceData}
              />
            </Box>
          </TabPanel>

          {/* Guardrails Tab */}
          <TabPanel value={activeTab} index={4}>
            <Box className="guardrails-manager">
              <GuardrailsManager
                policyId={id!}
                guardrails={workspaceData?.guardrails || []}
                onRefresh={loadWorkspaceData}
              />
            </Box>
          </TabPanel>

          {/* Monitoring Tab */}
          <TabPanel value={activeTab} index={5}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Performance Metrics
                </Typography>
                <Alert severity="info" sx={{ mb: 2 }}>
                  Performance metrics will be displayed here once observations are available.
                </Alert>
                <Typography variant="body2" color="text.secondary">
                  This tab will show:
                </Typography>
                <ul>
                  <li>Utilization change trends</li>
                  <li>Cost impact metrics</li>
                  <li>Guardrail status</li>
                  <li>Alert history</li>
                </ul>
              </CardContent>
            </Card>
          </TabPanel>

          {/* Versions Tab */}
          <TabPanel value={activeTab} index={6}>
            <Box className="versions-list">
              <PolicyVersionsList
                policyId={id!}
                versions={workspaceData?.versions || []}
                onRefresh={loadWorkspaceData}
              />
            </Box>
          </TabPanel>

          {/* Changelog Tab */}
          <TabPanel value={activeTab} index={7}>
            <PolicyChangelog
              policyId={id!}
              changelog={workspaceData?.changelog || []}
              onRefresh={loadWorkspaceData}
            />
          </TabPanel>

          {/* Decisions Tab - Epic 3 */}
          <TabPanel value={activeTab} index={8}>
            <DecisionManager
              policyId={id!}
              onDecisionCreated={loadWorkspaceData}
            />
          </TabPanel>

          {/* Evidence Tab - Epic 3 */}
          <TabPanel value={activeTab} index={9}>
            <EvidenceManager
              policyId={id!}
              onEvidenceLinked={loadWorkspaceData}
            />
          </TabPanel>

          {/* Forecasts Tab - Epic 4 */}
          <TabPanel value={activeTab} index={10}>
            <ForecastManager policyId={id!} />
          </TabPanel>

          {/* Scenarios Tab - Epic 4 */}
          <TabPanel value={activeTab} index={11}>
            <ScenarioManager policyId={id!} />
          </TabPanel>

          {/* Risk Register Tab - Epic 4 */}
          <TabPanel value={activeTab} index={12}>
            <RiskRegister policyId={id!} />
          </TabPanel>

          {/* Behavior Tab - Epic 5 */}
          <TabPanel value={activeTab} index={13}>
            <BehaviorDashboard policyId={id!} />
          </TabPanel>

          {/* Alerts Tab - Epic 5 */}
          <TabPanel value={activeTab} index={14}>
            <AlertManager policyId={id!} />
          </TabPanel>

          {/* Comments Tab - Epic 6 */}
          <TabPanel value={activeTab} index={15}>
            <CommentsPanel resourceType="POLICY" resourceId={id!} />
          </TabPanel>

          {/* Tasks Tab - Epic 6 */}
          <TabPanel value={activeTab} index={16}>
            <TasksPanel resourceType="POLICY" resourceId={id!} />
          </TabPanel>

          {/* Activity Tab - Epic 6 */}
          <TabPanel value={activeTab} index={17}>
            <ActivityFeed resourceType="POLICY" resourceId={id!} />
          </TabPanel>

          {/* Narrative Tab - Epic 7 */}
          <TabPanel value={activeTab} index={18}>
            <NarrativeView resourceType="POLICY" resourceId={id!} />
          </TabPanel>
        </CardContent>
      </Card>
    </Box>
  )
}

