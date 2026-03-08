/**
 * Analysis Workspace Page - Enhanced with Cohort Builder
 */
import { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
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
  TextField,
  Typography,
  MenuItem,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Select,
  FormControl,
  InputLabel,
} from '@mui/material'
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
} from '@mui/icons-material'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { apiClient } from '../lib/api'
import { useAnalysisUpdates } from '../hooks/useWebSocket'
import TrustPanel from '../components/TrustPanel'
import ConfidenceInterval from '../components/ConfidenceInterval'
import CohortBuilder from '../components/CohortBuilder'
import MethodChecksDisplay from '../components/MethodChecksDisplay'
import SubstitutionResultsDisplay from '../components/SubstitutionResultsDisplay'
import ProviderSegmentationDisplay from '../components/ProviderSegmentationDisplay'
import { format } from 'date-fns'
import { healthForesightColors } from '../theme/healthForesightTheme'
import TourButton from '../components/tour/TourButton'

interface Analysis {
  id: string
  policy_id: string
  analysis_type: string
  status: string
  created_at: string
  completed_at?: string
}

interface AnalysisResult {
  effect_size?: number
  confidence_interval?: [number, number]
  percent_change?: number
  confidence_score?: number
  methodology?: string
  data_coverage?: any
  checks?: any[]
  limitations?: string[]
}

export default function AnalysisWorkspacePage() {
  const [analyses, setAnalyses] = useState<Analysis[]>([])
  const [selectedAnalysis, setSelectedAnalysis] = useState<Analysis | null>(null)
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [timeseriesData, setTimeseriesData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [cohortBuilderOpen, setCohortBuilderOpen] = useState(false)
  const [tabValue, setTabValue] = useState(0)
  const [policies, setPolicies] = useState<any[]>([])
  const [methodChecks, setMethodChecks] = useState<any>(null)
  const [trustPanel, setTrustPanel] = useState<any>(null)
  const [substitutionResults, setSubstitutionResults] = useState<any>(null)
  const [segmentationResults, setSegmentationResults] = useState<any>(null)
  const [formData, setFormData] = useState({
    policy_id: '',
    treatment_filters: {},
    control_filters: {},
    pre_window_months: 6,
    post_window_months: 6,
    run_substitution: false,
    run_provider_segmentation: false,
  })

  useEffect(() => {
    loadAnalyses()
    loadPolicies()
  }, [])

  const loadPolicies = async () => {
    try {
      const data = await apiClient.getPolicies()
      const policiesList = Array.isArray(data) ? data : (data.items || [])
      setPolicies(policiesList)
    } catch (err: any) {
      console.error('Error loading policies:', err)
    }
  }

  useEffect(() => {
    if (selectedAnalysis) {
      loadAnalysisResults(selectedAnalysis.id)
      loadMethodChecks(selectedAnalysis.id)
      loadTrustPanel(selectedAnalysis.id)
      
      // Load substitution and segmentation if available
      if (selectedAnalysis.analysis_type === 'IMPACT' || selectedAnalysis.analysis_type === 'IMPACT_ANALYSIS') {
        loadSubstitutionResults(selectedAnalysis.id)
        loadSegmentationResults(selectedAnalysis.id)
      }
    }
  }, [selectedAnalysis])

  const loadMethodChecks = async (analysisId: string) => {
    try {
      const checks = await apiClient.getAnalysisMethodChecks(analysisId)
      setMethodChecks(checks)
    } catch (err) {
      console.error('Error loading method checks:', err)
      setMethodChecks(null)
    }
  }

  const loadTrustPanel = async (analysisId: string) => {
    try {
      const panel = await apiClient.getAnalysisTrustPanel(analysisId)
      setTrustPanel(panel)
    } catch (err) {
      console.error('Error loading trust panel:', err)
      setTrustPanel(null)
    }
  }

  const loadSubstitutionResults = async (analysisId: string) => {
    try {
      const results = await apiClient.getAnalysisResults(analysisId, 'SUBSTITUTION')
      // Handle both old and new structure
      if (results.results && results.results.SUBSTITUTION) {
        setSubstitutionResults(results.results.SUBSTITUTION)
      } else if (results.substitutions) {
        setSubstitutionResults(results)
      } else {
        setSubstitutionResults(null)
      }
    } catch (err) {
      console.error('Error loading substitution results:', err)
      setSubstitutionResults(null)
    }
  }

  const loadSegmentationResults = async (analysisId: string) => {
    try {
      const results = await apiClient.getAnalysisResults(analysisId, 'PROVIDER_SEGMENTATION')
      // Handle both old and new structure
      if (results.results && results.results.PROVIDER_SEGMENTATION) {
        setSegmentationResults(results.results.PROVIDER_SEGMENTATION)
      } else if (results.archetypes || results.provider_assignments) {
        setSegmentationResults(results)
      } else {
        setSegmentationResults(null)
      }
    } catch (err) {
      console.error('Error loading segmentation results:', err)
      setSegmentationResults(null)
    }
  }

  // Real-time updates for selected analysis
  useAnalysisUpdates(selectedAnalysis?.id || null, (data) => {
    // Update analysis status in real-time
    setAnalyses((prev) =>
      prev.map((analysis) =>
        analysis.id === data.analysis_id
          ? { ...analysis, status: data.status, ...data }
          : analysis
      )
    )
    if (data.status === 'COMPLETED' || data.status === 'FAILED') {
      if (selectedAnalysis?.id === data.analysis_id) {
        loadAnalysisResults(data.analysis_id)
      }
      loadAnalyses() // Refresh full list
    }
  })

  const loadAnalyses = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.getAnalyses()
      setAnalyses(Array.isArray(data) ? data : [])
    } catch (err: any) {
      console.error('Error loading analyses:', err)
      setError(err.detail || err.message || 'Failed to load analyses')
      setAnalyses([])
    } finally {
      setLoading(false)
    }
  }

  const loadAnalysisResults = async (analysisId: string) => {
    try {
      setError(null)
      const results = await apiClient.getAnalysisResults(analysisId)
      // Handle both old and new API structure
      if (results.impact_result) {
        // New structure: impact_result is separate
        setAnalysisResult(results.impact_result)
      } else if (results.summary) {
        // Old structure: summary field
        setAnalysisResult(results.summary)
      } else if (results.effect_size !== undefined || results.percent_change !== undefined) {
        // Direct result structure
        setAnalysisResult(results)
      } else {
        setAnalysisResult(null)
      }
      
      // Load timeseries if available
      try {
        const ts = await apiClient.getAnalysisTimeseries(analysisId)
        setTimeseriesData(ts.data || ts || [])
      } catch {
        // Timeseries not available
        setTimeseriesData([])
      }
    } catch (err: any) {
      console.error('Error loading analysis results:', err)
      setError(err.detail || err.message || 'Failed to load analysis results')
      setAnalysisResult(null)
    }
  }

  const handleOpenDialog = () => {
    setFormData({
      policy_id: '',
      treatment_filters: {},
      control_filters: {},
      pre_window_months: 6,
      post_window_months: 6,
      run_substitution: false,
      run_provider_segmentation: false,
    })
    setDialogOpen(true)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
  }

  const handleSubmit = async () => {
    try {
      setError(null)
      const result = await apiClient.createImpactAnalysis(formData)
      handleCloseDialog()
      loadAnalyses()
      if (result.id) {
        setSelectedAnalysis(result)
        setTabValue(1)
      }
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to create analysis')
    }
  }

  const handleCohortPreview = async (filters: any) => {
    // Preview cohort counts
    // This would call an API endpoint to get preview counts
    return { memberCount: 0, claimCount: 0 }
  }

  const handleCohortSave = async (filters: any, name: string, description?: string) => {
    await apiClient.createCohort({
      name,
      description,
      filters_json: filters,
    })
  }

  const handleCohortApply = (filters: any) => {
    setFormData({ ...formData, treatment_filters: filters })
    setCohortBuilderOpen(false)
  }

  if (loading && analyses.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <Typography
            variant="h4"
            component="h1"
            className="analysis-header"
            sx={{
              fontFamily: 'IBM Plex Sans, Inter, sans-serif',
              fontWeight: 600,
              color: healthForesightColors.neutral.dark,
            }}
          >
            Analysis Workspace
          </Typography>
          <TourButton module="analysis-workspace" size="small" />
        </Box>
        <Typography
          variant="body1"
          sx={{
            color: healthForesightColors.neutral.mid,
            lineHeight: 1.6,
            mb: 3,
          }}
        >
          Analyze policy impact using causal inference methods. Every analysis includes confidence scores and method checks to ensure reliability.
        </Typography>
      </Box>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 3, gap: 1 }}>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            onClick={() => setCohortBuilderOpen(true)}
          >
            Cohort Builder
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleOpenDialog}
          >
            New Analysis
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)} sx={{ mb: 3 }} className="analysis-tabs">
        <Tab label="Analyses" />
        {selectedAnalysis && <Tab label="Results" />}
        {selectedAnalysis && <Tab label="Method Checks" />}
        {selectedAnalysis && (selectedAnalysis.analysis_type === 'IMPACT' || selectedAnalysis.analysis_type === 'IMPACT_ANALYSIS') && (
          <>
            <Tab label="Substitution" />
            <Tab label="Provider Segmentation" />
          </>
        )}
      </Tabs>

      {tabValue === 0 && (
        <>
          {analyses.length === 0 ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No analyses found
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Create your first analysis to evaluate policy impact
              </Typography>
              <Button variant="contained" startIcon={<AddIcon />} onClick={handleOpenDialog}>
                Create Analysis
              </Button>
            </Paper>
          ) : (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Policy ID</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Created</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {analyses.map((analysis) => (
                    <TableRow
                      key={analysis.id}
                      hover
                      onClick={() => {
                        setSelectedAnalysis(analysis)
                        setTabValue(1)
                      }}
                      sx={{ cursor: 'pointer' }}
                    >
                      <TableCell>{analysis.policy_id}</TableCell>
                      <TableCell>
                        <Chip label={analysis.analysis_type} size="small" />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={analysis.status}
                          color={analysis.status === 'COMPLETED' ? 'success' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {format(new Date(analysis.created_at), 'MMM d, yyyy')}
                      </TableCell>
                      <TableCell align="right">
                        <Button
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation()
                            setSelectedAnalysis(analysis)
                            setTabValue(1)
                          }}
                        >
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </>
      )}

      {tabValue === 1 && selectedAnalysis && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            {analysisResult ? (
              <Box className="impact-results">
                <Card sx={{ mb: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Impact Results
                    </Typography>
                    {analysisResult.effect_size !== undefined && (
                      <Box sx={{ mb: 3 }}>
                        <ConfidenceInterval
                          value={analysisResult.effect_size}
                          lower={analysisResult.confidence_interval?.[0] || 0}
                          upper={analysisResult.confidence_interval?.[1] || 0}
                          unit="per 1k members"
                          label="Effect Size"
                        />
                      </Box>
                    )}
                    {analysisResult.percent_change !== undefined && (
                      <Typography variant="body1" gutterBottom>
                        Percent Change: {analysisResult.percent_change > 0 ? '+' : ''}
                        {analysisResult.percent_change.toFixed(2)}%
                      </Typography>
                    )}
                    {analysisResult.methodology && (
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                        Methodology: {analysisResult.methodology}
                      </Typography>
                    )}
                  </CardContent>
                </Card>

                {timeseriesData.length > 0 && (
                  <Card sx={{ mb: 3 }}>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Time Series
                      </Typography>
                      <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={timeseriesData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="date" />
                          <YAxis />
                          <Tooltip />
                          <Legend />
                          <Line type="monotone" dataKey="utilization" stroke="#8884d8" name="Utilization" />
                          <Line type="monotone" dataKey="allowed_pmpm" stroke="#82ca9d" name="Allowed PMPM" />
                        </LineChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                )}
              </Box>
            ) : selectedAnalysis.status === 'PENDING' || selectedAnalysis.status === 'RUNNING' ? (
              <Paper sx={{ p: 4, textAlign: 'center' }}>
                <CircularProgress />
                <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                  Analysis is {selectedAnalysis.status.toLowerCase()}...
                </Typography>
              </Paper>
            ) : (
              <Paper sx={{ p: 4, textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                  No results available yet. Analysis status: {selectedAnalysis.status}
                </Typography>
              </Paper>
            )}
          </Grid>
          <Grid item xs={12} md={4}>
            {trustPanel ? (
              <TrustPanel
                confidence_score={trustPanel.confidence_score}
                confidenceScore={typeof trustPanel.confidence_score === 'number' ? trustPanel.confidence_score : undefined}
                methodology={trustPanel.methodology || analysisResult?.methodology}
                data_sufficiency={trustPanel.data_sufficiency}
                dataCoverage={analysisResult?.data_coverage}
                validation_checks={trustPanel.validation_checks}
                checks={analysisResult?.checks}
                limitations={trustPanel.limitations || analysisResult?.limitations}
                data_used={trustPanel.data_used}
                model_version={trustPanel.model_version}
                runTimestamp={trustPanel.run_timestamp}
              />
            ) : analysisResult ? (
              <TrustPanel
                confidenceScore={analysisResult.confidence_score || 0}
                methodology={typeof analysisResult.methodology === 'string' ? { method: analysisResult.methodology } : analysisResult.methodology}
                dataCoverage={analysisResult.data_coverage}
                checks={analysisResult.checks}
                limitations={analysisResult.limitations}
              />
            ) : null}
          </Grid>
        </Grid>
      )}

      {tabValue === 2 && selectedAnalysis && (
        <Box>
          {methodChecks ? (
            <MethodChecksDisplay methodChecks={methodChecks} />
          ) : selectedAnalysis.status === 'COMPLETED' ? (
            <Alert severity="info">
              Method checks are being calculated. Please refresh in a moment.
            </Alert>
          ) : (
            <Alert severity="warning">
              Method checks are only available for completed analyses.
            </Alert>
          )}
        </Box>
      )}

      {tabValue === 3 && selectedAnalysis && (selectedAnalysis.analysis_type === 'IMPACT' || selectedAnalysis.analysis_type === 'IMPACT_ANALYSIS') && (
        <Box>
          {substitutionResults ? (
            <SubstitutionResultsDisplay substitutionResults={substitutionResults} />
          ) : selectedAnalysis.status === 'COMPLETED' ? (
            <Alert severity="info">
              Substitution analysis was not run for this analysis. Enable substitution detection when creating a new analysis.
            </Alert>
          ) : (
            <Alert severity="warning">
              Substitution results are only available for completed impact analyses.
            </Alert>
          )}
        </Box>
      )}

      {tabValue === 4 && selectedAnalysis && (selectedAnalysis.analysis_type === 'IMPACT' || selectedAnalysis.analysis_type === 'IMPACT_ANALYSIS') && (
        <Box>
          {segmentationResults ? (
            <ProviderSegmentationDisplay segmentationResults={segmentationResults} />
          ) : selectedAnalysis.status === 'COMPLETED' ? (
            <Alert severity="info">
              Provider segmentation was not run for this analysis. Enable provider segmentation when creating a new analysis.
            </Alert>
          ) : (
            <Alert severity="warning">
              Provider segmentation results are only available for completed impact analyses.
            </Alert>
          )}
        </Box>
      )}

      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>Create Impact Analysis</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <FormControl fullWidth required>
              <InputLabel>Policy</InputLabel>
              <Select
                value={formData.policy_id}
                label="Policy"
                onChange={(e) => setFormData({ ...formData, policy_id: e.target.value })}
              >
                {policies.map((policy) => (
                  <MenuItem key={policy.id} value={policy.id}>
                    {policy.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="Pre Window (months)"
              type="number"
              fullWidth
              value={formData.pre_window_months}
              onChange={(e) => setFormData({ ...formData, pre_window_months: parseInt(e.target.value) })}
            />
            <TextField
              label="Post Window (months)"
              type="number"
              fullWidth
              value={formData.post_window_months}
              onChange={(e) => setFormData({ ...formData, post_window_months: parseInt(e.target.value) })}
            />
            <Button
              variant="outlined"
              onClick={() => {
                setDialogOpen(false)
                setCohortBuilderOpen(true)
              }}
            >
              Build Treatment Cohort
            </Button>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            Create
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={cohortBuilderOpen} onClose={() => setCohortBuilderOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle>Cohort Builder</DialogTitle>
        <DialogContent>
          <CohortBuilder
            initialFilters={formData.treatment_filters}
            onPreview={handleCohortPreview}
            onSave={handleCohortSave}
            onApply={handleCohortApply}
            onCancel={() => setCohortBuilderOpen(false)}
          />
        </DialogContent>
      </Dialog>
    </Box>
  )
}
