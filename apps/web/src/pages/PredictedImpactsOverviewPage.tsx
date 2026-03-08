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
    utilization_change_per_1k: number
    cost_change_pmpm: number
    cost_change_total: number
    utilization_change_pct: number
    cost_change_pct: number
    confidence_score: number
    prediction_method: string
  }
  warnings?: string[]
  limitations?: string[]
}

interface PolicyWithImpact extends Policy {
  predictedImpact?: PredictedImpact
  hasImpact: boolean
  loadingImpact: boolean
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
      const data = await apiClient.getPolicies()
      const policiesList = Array.isArray(data) ? data : (data.items || [])
      
      // Load predicted impacts for all policies
      // First check if predicted impact is already in policy data
      const policiesWithImpacts: PolicyWithImpact[] = await Promise.all(
        policiesList.map(async (policy: Policy) => {
          // Check if predicted impact is already in policy data
          let impact = policy.predicted_impact || policy.predictedImpact || null
          
          // If not in policy data, try to fetch it
          if (!impact) {
            try {
              impact = await apiClient.getPolicyPredictedImpact(policy.id)
            } catch (err) {
              // Policy doesn't have predicted impact yet - that's okay
              impact = null
            }
          }
          
          // Only set hasImpact to true if impact has valid metrics
          const hasValidImpact = impact && impact.metrics && 
            (impact.metrics.cost_change_pmpm !== undefined || 
             impact.metrics.utilization_change_pct !== undefined)
          
          return {
            ...policy,
            predictedImpact: impact,
            hasImpact: hasValidImpact || false,
            loadingImpact: false,
          }
        })
      )

      setPolicies(policiesWithImpacts)
    } catch (err: any) {
      console.error('Error loading policies:', err)
      setError(err.detail || err.message || 'Failed to load policies')
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
        case 'cost_change':
          const costA = a.predictedImpact?.metrics.cost_change_pmpm || 0
          const costB = b.predictedImpact?.metrics.cost_change_pmpm || 0
          return Math.abs(costB) - Math.abs(costA)
        case 'utilization_change':
          const utilA = a.predictedImpact?.metrics.utilization_change_pct || 0
          const utilB = b.predictedImpact?.metrics.utilization_change_pct || 0
          return Math.abs(utilB) - Math.abs(utilA)
        case 'confidence':
          const confA = a.predictedImpact?.metrics.confidence_score || 0
          const confB = b.predictedImpact?.metrics.confidence_score || 0
          return confB - confA
        case 'name':
        default:
          return a.name.localeCompare(b.name)
      }
    })

  const policiesWithImpact = filteredPolicies.filter((p) => p.hasImpact)
  const policiesWithoutImpact = filteredPolicies.filter((p) => !p.hasImpact)

  // Prepare chart data
  const chartData = policiesWithImpact.map((policy) => ({
    name: policy.name.length > 20 ? policy.name.substring(0, 20) + '...' : policy.name,
    fullName: policy.name,
    costChange: policy.predictedImpact?.metrics.cost_change_pmpm || 0,
    utilizationChange: policy.predictedImpact?.metrics.utilization_change_pct || 0,
    confidence: policy.predictedImpact?.metrics.confidence_score || 0,
    policyId: policy.id,
  }))

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
                  <TableCell align="right">Cost Change (PMPM)</TableCell>
                  <TableCell align="right">Utilization Change (%)</TableCell>
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
                  const costChange = impact.metrics.cost_change_pmpm || 0
                  const utilChange = impact.metrics.utilization_change_pct || 0
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
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 0.5 }}>
                          {costChange < 0 ? (
                            <TrendingDownIcon color="success" fontSize="small" />
                          ) : costChange > 0 ? (
                            <TrendingUpIcon color="error" fontSize="small" />
                          ) : null}
                          <Typography
                            variant="body2"
                            color={costChange < 0 ? 'success.main' : costChange > 0 ? 'error.main' : 'text.primary'}
                            fontWeight="medium"
                          >
                            {costChange >= 0 ? '+' : ''}
                            ${costChange.toFixed(2)}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="right">
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 0.5 }}>
                          {utilChange < 0 ? (
                            <TrendingDownIcon color="success" fontSize="small" />
                          ) : utilChange > 0 ? (
                            <TrendingUpIcon color="error" fontSize="small" />
                          ) : null}
                          <Typography
                            variant="body2"
                            color={utilChange < 0 ? 'success.main' : utilChange > 0 ? 'error.main' : 'text.primary'}
                            fontWeight="medium"
                          >
                            {utilChange >= 0 ? '+' : ''}
                            {utilChange.toFixed(1)}%
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="right">
                        <ConfidenceBadge confidence={impact.metrics?.confidence_score || 0} />
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
              const costChange = impact.metrics.cost_change_pmpm || 0
              const utilChange = impact.metrics.utilization_change_pct || 0
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
                            Cost Change (PMPM)
                          </Typography>
                          <Typography
                            variant="h6"
                            color={costChange < 0 ? 'success.main' : costChange > 0 ? 'error.main' : 'text.primary'}
                          >
                            {costChange >= 0 ? '+' : ''}
                            ${costChange.toFixed(2)}
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="caption" color="text.secondary">
                            Utilization Change
                          </Typography>
                          <Typography
                            variant="h6"
                            color={utilChange < 0 ? 'success.main' : utilChange > 0 ? 'error.main' : 'text.primary'}
                          >
                            {utilChange >= 0 ? '+' : ''}
                            {utilChange.toFixed(1)}%
                          </Typography>
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
                    Cost Impact by Policy (PMPM)
                  </Typography>
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                      <YAxis />
                      <RechartsTooltip
                        formatter={(value: number) => `$${value.toFixed(2)}`}
                        labelFormatter={(label, payload) => {
                          if (payload && payload[0]) {
                            return payload[0].payload.fullName
                          }
                          return label
                        }}
                      />
                      <Legend />
                      <Bar dataKey="costChange" name="Cost Change (PMPM)">
                        {chartData.map((entry, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={entry.costChange < 0 ? healthForesightColors.success : healthForesightColors.error}
                          />
                        ))}
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
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                      <YAxis />
                      <RechartsTooltip
                        formatter={(value: number) => `${value.toFixed(1)}%`}
                        labelFormatter={(label, payload) => {
                          if (payload && payload[0]) {
                            return payload[0].payload.fullName
                          }
                          return label
                        }}
                      />
                      <Legend />
                      <Bar dataKey="utilizationChange" name="Utilization Change (%)">
                        {chartData.map((entry, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={entry.utilizationChange < 0 ? healthForesightColors.success : healthForesightColors.error}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
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
