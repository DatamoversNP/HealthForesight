/**
 * Policy Catalog Page
 */
import { useState, useEffect, useMemo, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
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
  CircularProgress,
  Select,
  FormControl,
  InputLabel,
  Tabs,
  Tab,
  Autocomplete,
} from '@mui/material'
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  PlayArrow as ActivateIcon,
  Stop as DeactivateIcon,
  CloudUpload as ImportIcon,
  Psychology as PsychologyIcon,
  Refresh as RefreshIcon,
  Settings as BuildIcon,
  Assignment as AssignmentIcon,
  Lightbulb as LightbulbIcon,
} from '@mui/icons-material'
import { apiClient } from '../lib/api'
import { format } from 'date-fns'
import { healthForesightColors } from '../theme/healthForesightTheme'
import PredictedImpactDisplay from '../components/policy/PredictedImpactDisplay'
import PolicyClaimCounts from '../components/policy/PolicyClaimCounts'
import { RefreshIndicator } from '../components/common/RefreshIndicator'
import { TraceabilityDisplay } from '../components/common/TraceabilityDisplay'
import { LearningMetricsDashboard } from '../components/learning/LearningMetricsDashboard'
import PolicyScopeDisplay from '../components/policy/PolicyScopeDisplay'
import TourButton from '../components/tour/TourButton'
import ListFilterBar from '../components/common/ListFilterBar'
import {
  CATALOG_POLICY_TYPES,
  formatPolicyTypeLabel,
  policyTypesMatch,
  uniquePolicyTypeOptions,
} from '../lib/policyType'

interface Policy {
  id: string
  name: string
  policy_type: string
  description?: string
  owner_role?: string
  status?: string
  created_at: string
  updated_at: string
  scope?: any
}

const POLICY_TYPES = [...CATALOG_POLICY_TYPES]

export default function PolicyCatalogPage() {
  const navigate = useNavigate()
  const [policies, setPolicies] = useState<Policy[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingPolicy, setEditingPolicy] = useState<Policy | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    policy_type: 'PRIOR_AUTH',
    description: '',
    owner_role: '',
  })
  const [predictedImpactDialogOpen, setPredictedImpactDialogOpen] = useState(false)
  const [selectedPolicyId, setSelectedPolicyId] = useState<string | null>(null)
  const [predictedImpact, setPredictedImpact] = useState<any>(null)
  const [loadingPredictedImpact, setLoadingPredictedImpact] = useState(false)
  const [predictedImpactError, setPredictedImpactError] = useState<string | null>(null)
  const [generatingPredictedImpact, setGeneratingPredictedImpact] = useState(false)
  const [generatingAllPredictedImpact, setGeneratingAllPredictedImpact] = useState(false)
  const [completingConfigurations, setCompletingConfigurations] = useState(false)
  const [dialogTab, setDialogTab] = useState(0)
  const [refreshStatuses, setRefreshStatuses] = useState<Record<string, any>>({})
  const [selectedPolicy, setSelectedPolicy] = useState<Policy | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState<string>('')
  const [filterStatus, setFilterStatus] = useState<string>('')
  const [filterOwner, setFilterOwner] = useState<string>('')
  const [jumpPolicy, setJumpPolicy] = useState<Policy | null>(null)
  const [highlightPolicyId, setHighlightPolicyId] = useState<string | null>(null)
  const rowRefs = useRef<Record<string, HTMLTableRowElement | null>>({})

  useEffect(() => {
    loadPolicies()
  }, [])

  const policyTypeOptions = useMemo(
    () => uniquePolicyTypeOptions(policies.map((p) => p.policy_type), POLICY_TYPES),
    [policies]
  )

  const statusOptions = useMemo(() => {
    const set = new Set(policies.map((p) => (p.status || 'ACTIVE').trim().toUpperCase()).filter(Boolean))
    return Array.from(set).sort()
  }, [policies])

  const ownerOptions = useMemo(() => {
    const set = new Set(
      policies.map((p) => (p.owner_role || '').trim()).filter(Boolean)
    )
    return Array.from(set).sort((a, b) => a.localeCompare(b))
  }, [policies])

  const filteredPolicies = useMemo(() => {
    const q = searchTerm.trim().toLowerCase()
    return policies
      .filter((p) => {
        if (filterType && !policyTypesMatch(p.policy_type, filterType)) return false
        if (filterStatus && (p.status || 'ACTIVE').trim().toUpperCase() !== filterStatus) return false
        if (filterOwner && (p.owner_role || '').trim() !== filterOwner) return false
        if (!q) return true
        const hay = `${p.name || ''} ${p.description || ''} ${p.policy_type || ''} ${p.owner_role || ''}`.toLowerCase()
        return hay.includes(q)
      })
      .sort((a, b) => String(a.name || '').localeCompare(String(b.name || '')))
  }, [policies, searchTerm, filterType, filterStatus, filterOwner])

  const clearFilters = () => {
    setSearchTerm('')
    setFilterType('')
    setFilterStatus('')
    setFilterOwner('')
    setJumpPolicy(null)
    setHighlightPolicyId(null)
  }

  const jumpToPolicy = (policy: Policy | null) => {
    setJumpPolicy(policy)
    if (!policy) {
      setHighlightPolicyId(null)
      return
    }
    // Align filters so the selected policy is visible
    setSearchTerm('')
    setFilterType(policy.policy_type || '')
    setFilterStatus((policy.status || 'ACTIVE').toUpperCase())
    setFilterOwner(policy.owner_role?.trim() || '')
    setHighlightPolicyId(policy.id)
    // Scroll after paint
    requestAnimationFrame(() => {
      const el = rowRefs.current[policy.id]
      el?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    })
  }

  // Do NOT prefetch predicted-impact / refresh-status for every catalog row.
  // That N× round-trip saturates Azure and times out the rest of the demo UI.
  // Refresh status is loaded lazily when the user opens predicted impact for a policy.

  const loadPolicies = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.getPolicies({ limit: 1000 })
      // Hide retired seed/junk policies from the default catalog (demo-safe).
      const raw = Array.isArray(data) ? data : (data && Array.isArray(data.items) ? data.items : [])
      const visible = raw.filter((p: Policy) => (p.status || 'ACTIVE') !== 'RETIRED')
      setPolicies(visible)
    } catch (err: any) {
      // Don't log timeout errors - they're expected when API is unavailable
      if (err.code !== 'ECONNABORTED' && !err.message?.includes('timeout')) {
        console.error('Error loading policies:', err)
      }
      // Show helpful error message for timeout/network issues
      if (err.status === 0 || err.code === 'ECONNABORTED' || err.message?.includes('timeout') || err.code === 'ECONNREFUSED' || err.code === 'ERR_NETWORK') {
        setError('API server is not responding. Please ensure the API server is running on port 8000.')
        setPolicies([]) // Show empty state
      } else if (err.status >= 500) {
        setError('Server error: ' + (err.detail || err.message || 'Failed to load policies'))
        setPolicies([])
      } else {
        setError(err.detail || err.message || 'Failed to load policies')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleOpenDialog = (policy?: Policy) => {
    if (policy) {
      setEditingPolicy(policy)
      setFormData({
        name: policy.name,
        policy_type: policy.policy_type,
        description: policy.description || '',
        owner_role: policy.owner_role || '',
      })
    } else {
      setEditingPolicy(null)
      setFormData({
        name: '',
        policy_type: 'PRIOR_AUTH',
        description: '',
        owner_role: '',
      })
    }
    setDialogOpen(true)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
    setEditingPolicy(null)
  }

  const handleSubmit = async () => {
    try {
      setError(null)
      if (editingPolicy) {
        await apiClient.updatePolicy(editingPolicy.id, formData)
      } else {
        await apiClient.createPolicy(formData)
      }
      handleCloseDialog()
      loadPolicies()
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to save policy')
    }
  }

  const handleDelete = async (_id: string) => {
    if (!window.confirm('Are you sure you want to delete this policy?')) {
      return
    }
    try {
      // Note: Delete endpoint may not be implemented yet
      setError(null)
      await loadPolicies()
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to delete policy')
    }
  }

  const handleActivate = async (policyId: string) => {
    try {
      setError(null)
      await apiClient.activatePolicy(policyId)
      await loadPolicies()
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to activate policy')
    }
  }

  const handleDeactivate = async (policyId: string) => {
    if (!window.confirm('Are you sure you want to deactivate this policy?')) {
      return
    }
    try {
      setError(null)
      await apiClient.deactivatePolicy(policyId)
      await loadPolicies()
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to deactivate policy')
    }
  }

  const handleViewPredictedImpact = async (policyId: string) => {
    const policy = policies.find(p => p.id === policyId) || null
    setSelectedPolicy(policy)
    setSelectedPolicyId(policyId)
    setPredictedImpactDialogOpen(true)
    setDialogTab(0) // Reset to first tab
    setLoadingPredictedImpact(true)
    setGeneratingPredictedImpact(false)
    setPredictedImpactError(null)
    setPredictedImpact(null)
    
    try {
      // First check if predicted impact is already in policy data
      let impact = policy?.predicted_impact || policy?.predictedImpact || null
      if (!apiClient.hasUsablePredictedImpact(impact)) {
        impact = await apiClient.getPolicyPredictedImpact(policyId)
      }
      
      if (!apiClient.hasUsablePredictedImpact(impact)) {
        setPredictedImpactError('Predicted impact not available for this policy. Click "Generate" to create it.')
        setPredictedImpact(null)
        return
      }
      
      // Include policy scope in predicted impact display
      if (policy && impact) {
        impact.policy_scope = policy.scope || policy.logic?.scope || policy.metadata?.scope
      }
      setPredictedImpact(impact)

      // Check refresh status (non-blocking for display)
      if (impact?.computed_at) {
        apiClient
          .getRefreshStatus({
            entityType: 'prediction',
            entityId: policyId,
            lastRefreshTimestamp: impact.computed_at,
          })
          .then((refreshStatus) => {
            setRefreshStatuses((prev) => ({
              ...prev,
              [policyId]: refreshStatus,
            }))
          })
          .catch(() => {})
      }
    } catch (err: any) {
      if (err.status === 404 || err.response?.status === 404) {
        setPredictedImpactError('Predicted impact not available for this policy. Click "Generate" to create it.')
      } else if (err.code === 'ECONNABORTED' || err.status === 0) {
        setPredictedImpactError('Timed out loading predicted impact. Retry in a moment — data is stored; the API was busy.')
      } else {
        setPredictedImpactError(err.detail || err.message || 'Failed to load predicted impact')
      }
      setPredictedImpact(null)
    } finally {
      setLoadingPredictedImpact(false)
    }
  }

  const handleClosePredictedImpactDialog = () => {
    setPredictedImpactDialogOpen(false)
    setSelectedPolicyId(null)
    setSelectedPolicy(null)
    setPredictedImpact(null)
    setPredictedImpactError(null)
    setDialogTab(0)
  }

  const handleGeneratePredictedImpact = async (policyId: string, showDialog: boolean = true) => {
    setSelectedPolicyId(policyId)
    if (showDialog) setPredictedImpactDialogOpen(true)
    setGeneratingPredictedImpact(true)
    setLoadingPredictedImpact(true)
    setPredictedImpactError(null)
    setPredictedImpact(null)
    setError(null)
    
    try {
      // Prefer existing stored prediction (do not treat empty/timeout as success)
      try {
        const existingImpact = await apiClient.getPolicyPredictedImpact(policyId)
        if (apiClient.hasUsablePredictedImpact(existingImpact)) {
          setPredictedImpact(existingImpact)
          setPredictedImpactError(null)
          return
        }
      } catch (getErr: any) {
        // Timeout → show retry; don't auto-generate (slow + can thrash Azure)
        if (getErr?.code === 'ECONNABORTED' || getErr?.status === 0) {
          setPredictedImpactError('Timed out loading predicted impact. Retry — generation is not required if it already exists.')
          return
        }
      }
      const impact = await apiClient.generatePolicyPredictedImpact(policyId)
      if (!apiClient.hasUsablePredictedImpact(impact)) {
        setPredictedImpactError('Generation finished but no usable metrics were returned.')
        setPredictedImpact(null)
        return
      }
      setPredictedImpact(impact)
      setPredictedImpactError(null)
      ;(apiClient as any)._policiesCache = null
      await loadPolicies()
    } catch (err: any) {
      console.error('Error generating/loading predicted impact:', err)
      console.error('Error details:', JSON.stringify(err, null, 2))
      
      let errorMessage = 'Failed to generate predicted impact'
      
      // Try multiple ways to extract error message
      if (err.detail) {
        errorMessage = err.detail
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail
      } else if (err.response?.data?.message) {
        errorMessage = err.response.data.message
      } else if (err.message) {
        errorMessage = err.message
      } else if (typeof err === 'string') {
        errorMessage = err
      }
      
      // Check if policy doesn't have levers
      if (errorMessage.toLowerCase().includes('policy levers') || errorMessage.toLowerCase().includes('levers')) {
        errorMessage = 'This policy does not have policy levers defined. Predicted impact requires policy levers. Please edit the policy using the Policy Builder to add levers first.'
      }
      
      setError(errorMessage)
      setPredictedImpactError(errorMessage)
    } finally {
      setGeneratingPredictedImpact(false)
      setLoadingPredictedImpact(false)
    }
  }

  const handleGenerateAllPredictedImpact = async (force: boolean = false) => {
    const message = force 
      ? 'Force regenerate predicted impact for ALL policies? This will overwrite existing predictions and may take a few moments.'
      : 'Generate predicted impact for all policies that don\'t have it? This may take a few moments.'
    
    if (!window.confirm(message)) {
      return
    }
    setGeneratingAllPredictedImpact(true)
    setError(null)
    try {
      const result = await apiClient.generateAllPoliciesPredictedImpact(force)
      const message = `Predicted impact generation complete!\n` +
        `Total: ${result.total_policies}\n` +
        `Generated: ${result.generated}\n` +
        `Skipped: ${result.skipped}\n` +
        `Errors: ${result.errors}`
      
      if (result.skipped > 0 && !force) {
        const skippedDetails = result.details?.filter((d: any) => d.status === 'skipped').map((d: any) => `  - ${d.policy_name}: ${d.reason}`).join('\n')
        if (skippedDetails) {
          alert(message + `\n\nSkipped policies:\n${skippedDetails}\n\nTip: Use "Force Regenerate All" to overwrite existing predictions.`)
        } else {
          alert(message)
        }
      } else {
        alert(message)
      }
      await loadPolicies()
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to generate predicted impact for all policies')
    } finally {
      setGeneratingAllPredictedImpact(false)
    }
  }

  const handleCompleteConfigurations = async () => {
    if (!window.confirm('Complete configurations (levers, scope, conditions, exceptions) for all policies? This will add default configurations to policies that are missing them.')) {
      return
    }
    try {
      setCompletingConfigurations(true)
      setError(null)
      const result = await apiClient.completePolicyConfigurations()
      alert(`Completed configurations for ${result.updated} policies. ${result.skipped} were skipped (already complete).`)
      await loadPolicies()
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to complete policy configurations')
    } finally {
      setCompletingConfigurations(false)
    }
  }

  const getPolicyTypeColor = (type: string) => {
    const colors: Record<string, 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'error'> = {
      PRIOR_AUTH: 'primary',
      SITE_OF_CARE: 'secondary',
      COVERAGE: 'success',
      STEP_THERAPY: 'warning',
      BENEFIT: 'error',
    }
    return colors[type] || 'default'
  }

  if (loading && policies.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Box 
        className="policy-catalog-header"
        sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}
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
            Policy Catalog
          </Typography>
          <Typography
            variant="body1"
            sx={{
              color: healthForesightColors.neutral.mid,
              lineHeight: 1.6,
              mb: 3,
            }}
          >
            Manage and track policies that are being analyzed for downstream impact assessment.
          </Typography>
        </Box>
        <Box sx={{ mt: 1, display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 1 }}>
          <Button
            variant="contained"
            color="secondary"
            size="medium"
            startIcon={<LightbulbIcon />}
            onClick={() => navigate('/policy-rollout-recommendations')}
          >
            Policy rollout ideas
          </Button>
          <TourButton module="policies" showBadge={true} />
        </Box>
      </Box>

      <Alert severity="info" sx={{ mb: 3 }} icon={<LightbulbIcon />}>
        <Typography variant="body2" component="span" sx={{ display: 'block', mb: 1 }}>
          <strong>Net-new policy recommendations</strong> — data-driven rollout ideas with explainability, deduplicated
          against policies you already have. Also in the left nav under &quot;Policy rollout ideas&quot;.
        </Typography>
        <Button size="small" variant="outlined" startIcon={<LightbulbIcon />} onClick={() => navigate('/policy-rollout-recommendations')}>
          Open policy rollout ideas
        </Button>
      </Alert>
      
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', mb: 2, gap: 2, flexWrap: 'wrap' }}>
        <Button
          variant="outlined"
          startIcon={<BuildIcon />}
          onClick={handleCompleteConfigurations}
          disabled={completingConfigurations || policies.length === 0}
          sx={{ minWidth: 220 }}
        >
          {completingConfigurations ? 'Completing...' : 'Complete Configurations (All)'}
        </Button>
        <Button
          variant="contained"
          startIcon={<PsychologyIcon />}
          onClick={() => handleGenerateAllPredictedImpact(false)}
          disabled={generatingAllPredictedImpact || policies.length === 0}
          sx={{ minWidth: 200 }}
        >
          {generatingAllPredictedImpact ? 'Generating...' : 'Generate Predicted Impact (All)'}
        </Button>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={() => handleGenerateAllPredictedImpact(true)}
          disabled={generatingAllPredictedImpact || policies.length === 0}
          sx={{ minWidth: 220 }}
          title="Force regenerate predicted impact for all policies, even if it already exists"
        >
          {generatingAllPredictedImpact ? 'Regenerating...' : 'Force Regenerate All'}
        </Button>
        <Button
          variant="outlined"
          onClick={() => navigate('/policies/builder')}
          sx={{ minWidth: 160 }}
        >
          Create with Builder
        </Button>
        <Button
          variant="outlined"
          startIcon={<ImportIcon />}
          onClick={() => navigate('/policies/import')}
          sx={{ minWidth: 160 }}
        >
          Import Policy
        </Button>
        <Button
          className="create-policy-button"
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
          sx={{ minWidth: 140 }}
        >
          Quick Create
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {policies.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography
            variant="h6"
            sx={{
              color: healthForesightColors.neutral.mid,
              mb: 1,
            }}
            gutterBottom
          >
            No policies found
          </Typography>
          <Typography
            variant="body2"
            sx={{
              color: healthForesightColors.neutral.mid,
              mb: 3,
            }}
          >
            Create your first policy to begin impact analysis
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
            <Button
              variant="outlined"
              onClick={() => navigate('/policies/builder')}
            >
              Create with Builder
            </Button>
            <Button
              variant="outlined"
              color="secondary"
              startIcon={<ImportIcon />}
              onClick={() => navigate('/policies/import')}
            >
              Import Policy
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => handleOpenDialog()}
            >
              Quick Create
            </Button>
          </Box>
        </Paper>
      ) : (
        <Paper className="policy-list policy-search-filters" variant="outlined" sx={{ overflow: 'hidden' }}>
          <ListFilterBar
            search={searchTerm}
            onSearchChange={setSearchTerm}
            searchLabel="Search policies"
            searchPlaceholder="Name, description, type…"
            shown={filteredPolicies.length}
            total={policies.length}
            onClear={clearFilters}
            clearDisabled={!searchTerm && !filterType && !filterStatus && !filterOwner && !jumpPolicy}
          >
            <Box sx={{ minWidth: 200, flex: '1 1 180px', bgcolor: 'background.paper', borderRadius: 1 }}>
              <Autocomplete
                size="small"
                options={[...policies].sort((a, b) => String(a.name).localeCompare(String(b.name)))}
                getOptionLabel={(p) => p.name || p.id}
                value={jumpPolicy}
                onChange={(_e, value) => jumpToPolicy(value)}
                isOptionEqualToValue={(a, b) => a.id === b.id}
                renderInput={(params) => (
                  <TextField {...params} label="Jump to policy" placeholder="Pick a policy…" />
                )}
              />
            </Box>
            <FormControl size="small" sx={{ minWidth: 140, bgcolor: 'background.paper' }}>
              <InputLabel>Type</InputLabel>
              <Select
                label="Type"
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
              >
                <MenuItem value="">All types</MenuItem>
                {policyTypeOptions.map((t) => (
                  <MenuItem key={t} value={t}>
                    {formatPolicyTypeLabel(t)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 130, bgcolor: 'background.paper' }}>
              <InputLabel>Status</InputLabel>
              <Select
                label="Status"
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
              >
                <MenuItem value="">All statuses</MenuItem>
                {statusOptions.map((s) => (
                  <MenuItem key={s} value={s}>
                    {s}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 140, bgcolor: 'background.paper' }} disabled={ownerOptions.length === 0}>
              <InputLabel>Owner</InputLabel>
              <Select
                label="Owner"
                value={filterOwner}
                onChange={(e) => setFilterOwner(e.target.value)}
              >
                <MenuItem value="">All owners</MenuItem>
                {ownerOptions.map((o) => (
                  <MenuItem key={o} value={o}>
                    {o}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </ListFilterBar>
          {filteredPolicies.length === 0 ? (
            <Box sx={{ p: 4, textAlign: 'center' }}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No policies match these filters
              </Typography>
              <Button variant="outlined" onClick={clearFilters} sx={{ mt: 1 }}>
                Clear filters
              </Button>
            </Box>
          ) : (
          <TableContainer sx={{ maxHeight: '70vh', overflowX: 'auto' }}>
          <Table
            stickyHeader
            size="small"
            sx={{
              width: '100%',
              tableLayout: 'fixed',
              minWidth: 0,
              '& .MuiTableCell-root': { py: 0.75, px: 1 },
            }}
          >
            <TableHead>
              <TableRow>
                <TableCell sx={{ width: '22%' }}>Name</TableCell>
                <TableCell sx={{ width: '14%' }}>Type</TableCell>
                <TableCell sx={{ width: '16%' }}>Scope</TableCell>
                <TableCell sx={{ width: '10%' }}>Status</TableCell>
                <TableCell sx={{ width: '18%' }}>Description</TableCell>
                <TableCell sx={{ width: '8%' }}>Updated</TableCell>
                <TableCell
                  align="right"
                  sx={{
                    width: 168,
                    position: 'sticky',
                    right: 0,
                    bgcolor: 'background.paper',
                    zIndex: 3,
                    boxShadow: '-6px 0 8px -6px rgba(0,0,0,0.18)',
                  }}
                >
                  Actions
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredPolicies.map((policy) => (
                <TableRow
                  key={policy.id}
                  hover
                  selected={highlightPolicyId === policy.id}
                  ref={(el) => {
                    rowRefs.current[policy.id] = el
                  }}
                  sx={
                    highlightPolicyId === policy.id
                      ? { backgroundColor: 'action.selected' }
                      : undefined
                  }
                >
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium" noWrap title={policy.name}>
                      {policy.name}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={formatPolicyTypeLabel(policy.policy_type)}
                      color={getPolicyTypeColor(policy.policy_type)}
                      size="small"
                      sx={{ maxWidth: '100%', '& .MuiChip-label': { overflow: 'hidden', textOverflow: 'ellipsis' } }}
                    />
                  </TableCell>
                  <TableCell sx={{ overflow: 'hidden' }}>
                    <Box sx={{ maxWidth: '100%', overflow: 'hidden', '& *': { maxWidth: '100%' } }}>
                      <PolicyScopeDisplay
                        scope={policy.scope || policy.logic?.scope || policy.metadata?.scope}
                        compact
                        showLabel={false}
                      />
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={policy.status || 'ACTIVE'}
                      color={policy.status === 'ACTIVE' ? 'success' : policy.status === 'INACTIVE' ? 'default' : 'warning'}
                      size="small"
                      icon={policy.status === 'ACTIVE' ? <CheckCircleIcon /> : <CancelIcon />}
                    />
                  </TableCell>
                  <TableCell>
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      noWrap
                      title={policy.description || undefined}
                    >
                      {policy.description || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" noWrap>
                      {policy.updated_at ? (() => {
                        try {
                          const date = new Date(policy.updated_at);
                          return isNaN(date.getTime()) ? 'N/A' : format(date, 'MMM d, yyyy');
                        } catch {
                          return 'N/A';
                        }
                      })() : 'N/A'}
                    </Typography>
                  </TableCell>
                  <TableCell
                    align="right"
                    sx={{
                      position: 'sticky',
                      right: 0,
                      bgcolor: highlightPolicyId === policy.id ? 'action.selected' : 'background.paper',
                      zIndex: 1,
                      whiteSpace: 'nowrap',
                      boxShadow: '-6px 0 8px -6px rgba(0,0,0,0.12)',
                      '.MuiTableRow-root:hover &': {
                        bgcolor: highlightPolicyId === policy.id ? 'action.selected' : 'action.hover',
                      },
                    }}
                  >
                    <IconButton
                      size="small"
                      onClick={() => handleViewPredictedImpact(policy.id)}
                      title="View Predicted Impact (Stage 3.5)"
                      color="info"
                      disabled={loadingPredictedImpact && selectedPolicyId === policy.id}
                    >
                      <PsychologyIcon fontSize="small" />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => navigate(`/policies/workspace/${policy.id}`)}
                      title="Open Workspace"
                      color="info"
                    >
                      <AssignmentIcon fontSize="small" />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => navigate(`/policies/builder/${policy.id}`)}
                      title="Edit Policy"
                      color="primary"
                    >
                      <EditIcon fontSize="small" />
                    </IconButton>
                    {policy.status === 'ACTIVE' ? (
                      <IconButton
                        size="small"
                        onClick={() => handleDeactivate(policy.id)}
                        title="Deactivate Policy"
                        color="warning"
                      >
                        <DeactivateIcon fontSize="small" />
                      </IconButton>
                    ) : (
                      <IconButton
                        size="small"
                        onClick={() => handleActivate(policy.id)}
                        title="Activate Policy"
                        color="success"
                      >
                        <ActivateIcon fontSize="small" />
                      </IconButton>
                    )}
                    <IconButton
                      size="small"
                      onClick={() => handleDelete(policy.id)}
                      title="Delete Policy"
                      color="error"
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
          )}
        </Paper>
      )}

      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingPolicy ? 'Edit Policy' : 'Create New Policy'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField
              label="Policy Name"
              fullWidth
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
            <TextField
              label="Policy Type"
              select
              fullWidth
              required
              value={formData.policy_type}
              onChange={(e) => setFormData({ ...formData, policy_type: e.target.value })}
            >
              {POLICY_TYPES.map((type) => (
                <MenuItem key={type} value={type}>
                  {type.replace(/_/g, ' ')}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="Description"
              fullWidth
              multiline
              rows={3}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />
            <TextField
              label="Owner Role"
              fullWidth
              value={formData.owner_role}
              onChange={(e) => setFormData({ ...formData, owner_role: e.target.value })}
              helperText="e.g., POLICY_ADMIN, UM_LEADER"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingPolicy ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Predicted Impact Dialog */}
      <Dialog
        open={predictedImpactDialogOpen}
        onClose={handleClosePredictedImpactDialog}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: { maxHeight: '90vh' }
        }}
      >
        <DialogTitle>
          Predicted Impact (Stage 3.5)
        </DialogTitle>
        <DialogContent dividers>
          {loadingPredictedImpact || generatingPredictedImpact ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', p: 4, gap: 2 }}>
              <CircularProgress />
              <Typography variant="body2" color="text.secondary">
                {generatingPredictedImpact ? 'Generating predicted impact...' : 'Loading predicted impact...'}
              </Typography>
            </Box>
          ) : predictedImpactError ? (
            <Box>
              <Alert severity="warning" sx={{ mb: 2 }}>
                {predictedImpactError}
              </Alert>
              {selectedPolicyId && (
                <Button
                  variant="contained"
                  startIcon={<PsychologyIcon />}
                  onClick={() => {
                    setPredictedImpactError(null)
                    handleGeneratePredictedImpact(selectedPolicyId, true)
                  }}
                  disabled={generatingPredictedImpact}
                >
                  Generate Predicted Impact
                </Button>
              )}
            </Box>
          ) : predictedImpact ? (
            <Box>
              <Tabs value={dialogTab} onChange={(_, v) => setDialogTab(v)} sx={{ mb: 2, borderBottom: 1, borderColor: 'divider' }}>
                <Tab label="Predicted Impact" />
                <Tab label="Scope Data" />
                <Tab label="Traceability" />
                <Tab label="Learning Metrics" />
              </Tabs>
              
              {/* Predicted Impact Tab */}
              <Box sx={{ display: dialogTab === 0 ? 'block' : 'none' }}>
                <Box display="flex" justifyContent="flex-end" mb={2}>
                  <RefreshIndicator
                    needsRefresh={refreshStatuses[selectedPolicyId || '']?.needsRefresh || false}
                    refreshReason={refreshStatuses[selectedPolicyId || '']?.refreshReason}
                    lastRefreshTimestamp={predictedImpact?.computed_at}
                    variant="chip"
                    onRefresh={() => selectedPolicyId && handleGeneratePredictedImpact(selectedPolicyId, true)}
                  />
                </Box>
                <PredictedImpactDisplay predictedImpact={predictedImpact} />
              </Box>

              {/* Scope Data Tab */}
              <Box sx={{ display: dialogTab === 1 ? 'block' : 'none' }}>
                {selectedPolicyId && <PolicyClaimCounts policyId={selectedPolicyId} />}
              </Box>

              {/* Traceability Tab */}
              <Box sx={{ display: dialogTab === 2 ? 'block' : 'none' }}>
                <TraceabilityDisplay
                  policyVersionId={predictedImpact?.policy_version_id || selectedPolicy?.id}
                  baselineVersionId={predictedImpact?.baseline_version_id}
                  predictionId={predictedImpact?.prediction_id || selectedPolicyId}
                  dataPeriodId={predictedImpact?.data_period_id}
                />
              </Box>
              
              {/* Learning Metrics Tab */}
              <Box sx={{ display: dialogTab === 3 ? 'block' : 'none' }}>
                {selectedPolicyId ? (
                  <LearningMetricsDashboard policyId={selectedPolicyId} />
                ) : (
                  <Alert severity="info">No policy selected</Alert>
                )}
              </Box>
            </Box>
          ) : (
            <Box sx={{ textAlign: 'center', p: 4 }}>
              <Typography variant="body1" color="text.secondary" gutterBottom>
                Predicted impact not available for this policy.
              </Typography>
              {selectedPolicyId && (
                <Button
                  variant="contained"
                  startIcon={<PsychologyIcon />}
                  onClick={() => handleGeneratePredictedImpact(selectedPolicyId, true)}
                  disabled={generatingPredictedImpact}
                  sx={{ mt: 2 }}
                >
                  Generate Predicted Impact
                </Button>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          {selectedPolicyId && predictedImpact && (
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={() => handleGeneratePredictedImpact(selectedPolicyId, true)}
              disabled={generatingPredictedImpact}
            >
              Regenerate
            </Button>
          )}
          <Button onClick={handleClosePredictedImpactDialog}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
