/**
 * Scorecards Page
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
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  Grid,
  InputLabel,
  LinearProgress,
  MenuItem,
  Paper,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Alert,
} from '@mui/material'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts'
import { PlayArrow as RunIcon, CompareArrows as CompareIcon } from '@mui/icons-material'
import { apiClient } from '../lib/api'
import { healthForesightColors } from '../theme/healthForesightTheme'

interface Scorecard {
  id: string
  policy_id: string
  period: string
  effectiveness_index: number
  cost_impact_score: number
  behavioral_risk_score: number
  access_impact_score: number
  regulatory_defensibility_score: number
  created_at?: string
  updated_at?: string
}

interface Policy {
  id: string
  name: string
}

interface ScorecardTrend {
  period: string
  effectiveness_index: number
  cost_impact_score: number
  behavioral_risk_score: number
  access_impact_score: number
  regulatory_defensibility_score: number
  created_at?: string
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042']

export default function ScorecardsPage() {
  const [scorecards, setScorecards] = useState<Scorecard[]>([])
  const [policies, setPolicies] = useState<Policy[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedPeriod, setSelectedPeriod] = useState<string>('')
  const [selectedLob, setSelectedLob] = useState<string>('')
  const [selectedMarket, setSelectedMarket] = useState<string>('')
  const [selectedScorecard, setSelectedScorecard] = useState<Scorecard | null>(null)
  const [trends, setTrends] = useState<ScorecardTrend[]>([])
  const [trendsLoading, setTrendsLoading] = useState(false)
  const [detailDialogOpen, setDetailDialogOpen] = useState(false)
  const [generateDialogOpen, setGenerateDialogOpen] = useState(false)
  const [compareDialogOpen, setCompareDialogOpen] = useState(false)
  const [selectedPoliciesForCompare, setSelectedPoliciesForCompare] = useState<string[]>([])
  const [comparePeriod, setComparePeriod] = useState<string>('')
  const [comparisonData, setComparisonData] = useState<any>(null)
  const [comparing, setComparing] = useState(false)

  useEffect(() => {
    loadScorecards()
    loadPolicies()
  }, [selectedPeriod, selectedLob, selectedMarket])

  const loadScorecards = async () => {
    try {
      setLoading(true)
      setError(null)
      const params: any = {}
      if (selectedPeriod) params.period = selectedPeriod
      if (selectedLob) params.lob = selectedLob
      if (selectedMarket) params.market = selectedMarket
      
      const data = await apiClient.getScorecards(params)
      setScorecards(data)
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to load scorecards')
    } finally {
      setLoading(false)
    }
  }

  const loadPolicies = async () => {
    try {
      const data = await apiClient.getPolicies()
      const policiesList = Array.isArray(data) ? data : (data.items || [])
      setPolicies(policiesList)
    } catch (err) {
      console.error('Error loading policies:', err)
    }
  }

  const loadTrends = async (policyId: string) => {
    try {
      setTrendsLoading(true)
      const data = await apiClient.getPolicyScorecardTrends(policyId, 4)
      setTrends(data)
    } catch (err: any) {
      console.error('Error loading trends:', err)
      setError(err.detail || err.message || 'Failed to load trends')
    } finally {
      setTrendsLoading(false)
    }
  }

  const handleGenerateScorecards = async (period: string) => {
    try {
      setGenerating(true)
      setError(null)
      await apiClient.generateScorecards({ period })
      setGenerateDialogOpen(false)
      // Reload scorecards after a delay to allow generation to complete
      setTimeout(() => {
        loadScorecards()
      }, 5000)
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to generate scorecards')
    } finally {
      setGenerating(false)
    }
  }

  const handleScorecardClick = async (scorecard: Scorecard) => {
    setSelectedScorecard(scorecard)
    setDetailDialogOpen(true)
    await loadTrends(scorecard.policy_id)
  }

  const getPolicyName = (policyId: string): string => {
    const policy = policies.find(p => p.id === policyId)
    return policy?.name || policyId.substring(0, 8)
  }

  const chartData = scorecards.map((sc) => ({
    name: getPolicyName(sc.policy_id),
    'Cost Impact': sc.cost_impact_score,
    'Behavioral Risk': sc.behavioral_risk_score,
    'Access Impact': sc.access_impact_score,
    'Regulatory': sc.regulatory_defensibility_score,
  }))

  const getEffectivenessColor = (score: number): 'success' | 'warning' | 'error' => {
    if (score >= 70) return 'success'
    if (score >= 40) return 'warning'
    return 'error'
  }

  const handleCompareScorecards = async () => {
    if (selectedPoliciesForCompare.length < 2) {
      setError('Please select at least 2 policies to compare')
      return
    }

    try {
      setComparing(true)
      setError(null)
      const data = await apiClient.compareScorecards(
        selectedPoliciesForCompare,
        comparePeriod || undefined
      )
      setComparisonData(data)
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to compare scorecards')
    } finally {
      setComparing(false)
    }
  }

  if (loading && scorecards.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
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
          Scorecards
        </Typography>
        <Typography
          variant="body1"
          sx={{
            color: healthForesightColors.neutral.mid,
            lineHeight: 1.6,
            mb: 2,
          }}
        >
          Evaluate policy effectiveness across multiple dimensions. Compare policies and track trends over time.
        </Typography>
      </Box>
      {error && (
        <Alert 
          severity="error" 
          sx={{ mb: 2 }}
          onClose={() => setError(null)}
        >
          {error}
          {error.includes('predicted impact') && (
            <Box sx={{ mt: 1 }}>
              <Typography variant="body2">
                Go to the <strong>Policies</strong> page and click <strong>"Generate Predicted Impact (All)"</strong> to generate predicted impacts for your policies first.
              </Typography>
            </Box>
          )}
        </Alert>
      )}
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 3, gap: 2 }}>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<CompareIcon />}
            onClick={() => setCompareDialogOpen(true)}
          >
            Compare Policies
          </Button>
          <Button
            variant="contained"
            startIcon={generating ? <CircularProgress size={20} /> : <RunIcon />}
            onClick={() => setGenerateDialogOpen(true)}
            disabled={generating}
          >
            {generating ? 'Generating...' : 'Generate Scorecards'}
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Period</InputLabel>
          <Select
            value={selectedPeriod}
            label="Period"
            onChange={(e) => setSelectedPeriod(e.target.value)}
          >
            <MenuItem value="">All</MenuItem>
            <MenuItem value="2024-Q1">2024 Q1</MenuItem>
            <MenuItem value="2024-Q2">2024 Q2</MenuItem>
            <MenuItem value="2024-Q3">2024 Q3</MenuItem>
            <MenuItem value="2024-Q4">2024 Q4</MenuItem>
            <MenuItem value="2025-Q1">2025 Q1</MenuItem>
            <MenuItem value="2025-Q2">2025 Q2</MenuItem>
            <MenuItem value="2025-Q3">2025 Q3</MenuItem>
            <MenuItem value="2025-Q4">2025 Q4</MenuItem>
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>LOB</InputLabel>
          <Select
            value={selectedLob}
            label="LOB"
            onChange={(e) => setSelectedLob(e.target.value)}
          >
            <MenuItem value="">All</MenuItem>
            <MenuItem value="COMMERCIAL">Commercial</MenuItem>
            <MenuItem value="MA">Medicare Advantage</MenuItem>
            <MenuItem value="MEDICAID">Medicaid</MenuItem>
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Market</InputLabel>
          <Select
            value={selectedMarket}
            label="Market"
            onChange={(e) => setSelectedMarket(e.target.value)}
          >
            <MenuItem value="">All</MenuItem>
            <MenuItem value="NYC">NYC</MenuItem>
            <MenuItem value="DFW">DFW</MenuItem>
            <MenuItem value="BOS">BOS</MenuItem>
          </Select>
        </FormControl>
      </Box>


      {scorecards.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary">
            No scorecards found
          </Typography>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Effectiveness Scores by Dimension
                </Typography>
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="Cost Impact" fill={COLORS[0]} />
                    <Bar dataKey="Behavioral Risk" fill={COLORS[1]} />
                    <Bar dataKey="Access Impact" fill={COLORS[2]} />
                    <Bar dataKey="Regulatory" fill={COLORS[3]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Top Policies
                </Typography>
                {scorecards
                  .sort((a, b) => b.effectiveness_index - a.effectiveness_index)
                  .slice(0, 5)
                  .map((sc) => (
                    <Box 
                      key={sc.id} 
                      sx={{ mb: 2, cursor: 'pointer' }}
                      onClick={() => handleScorecardClick(sc)}
                    >
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body2" fontWeight="medium">
                          {getPolicyName(sc.policy_id)}
                        </Typography>
                        <Chip
                          label={`${sc.effectiveness_index.toFixed(1)}`}
                          color={getEffectivenessColor(sc.effectiveness_index)}
                          size="small"
                        />
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={sc.effectiveness_index}
                        color={getEffectivenessColor(sc.effectiveness_index)}
                      />
                    </Box>
                  ))}
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12}>
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Policy</TableCell>
                    <TableCell>Period</TableCell>
                    <TableCell>Effectiveness Index</TableCell>
                    <TableCell>Cost Impact</TableCell>
                    <TableCell>Behavioral Risk</TableCell>
                    <TableCell>Access Impact</TableCell>
                    <TableCell>Regulatory</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {scorecards.map((sc) => (
                    <TableRow 
                      key={sc.id} 
                      hover
                      onClick={() => handleScorecardClick(sc)}
                      sx={{ cursor: 'pointer' }}
                    >
                      <TableCell>{getPolicyName(sc.policy_id)}</TableCell>
                      <TableCell>{sc.period}</TableCell>
                      <TableCell>
                        <Chip
                          label={sc.effectiveness_index.toFixed(1)}
                          color={getEffectivenessColor(sc.effectiveness_index)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{sc.cost_impact_score.toFixed(1)}</TableCell>
                      <TableCell>{sc.behavioral_risk_score.toFixed(1)}</TableCell>
                      <TableCell>{sc.access_impact_score.toFixed(1)}</TableCell>
                      <TableCell>{sc.regulatory_defensibility_score.toFixed(1)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Grid>
        </Grid>
      )}

      {/* Scorecard Detail Dialog */}
      <Dialog 
        open={detailDialogOpen} 
        onClose={() => setDetailDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Scorecard Details: {selectedScorecard ? getPolicyName(selectedScorecard.policy_id) : ''}
        </DialogTitle>
        <DialogContent>
          {selectedScorecard && (
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                      Effectiveness Index
                    </Typography>
                    <Typography variant="h4" color={getEffectivenessColor(selectedScorecard.effectiveness_index) === 'success' ? 'success.main' : getEffectivenessColor(selectedScorecard.effectiveness_index) === 'warning' ? 'warning.main' : 'error.main'}>
                      {selectedScorecard.effectiveness_index.toFixed(1)}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                      Period
                    </Typography>
                    <Typography variant="h6">
                      {selectedScorecard.period}
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>

              {trendsLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                  <CircularProgress />
                </Box>
              ) : trends.length > 0 && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Trends (Last {trends.length} Periods)
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={trends}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="period" />
                      <YAxis domain={[0, 100]} />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="effectiveness_index" stroke="#8884d8" name="Effectiveness" strokeWidth={2} />
                      <Line type="monotone" dataKey="cost_impact_score" stroke="#82ca9d" name="Cost Impact" />
                      <Line type="monotone" dataKey="behavioral_risk_score" stroke="#ffc658" name="Behavioral Risk" />
                      <Line type="monotone" dataKey="access_impact_score" stroke="#ff8042" name="Access Impact" />
                    </LineChart>
                  </ResponsiveContainer>
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Generate Scorecards Dialog */}
      <Dialog open={generateDialogOpen} onClose={() => setGenerateDialogOpen(false)}>
        <DialogTitle>Generate Scorecards</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Period</InputLabel>
              <Select
                value={selectedPeriod || ''}
                label="Period"
                onChange={(e) => setSelectedPeriod(e.target.value)}
              >
                <MenuItem value="">Current Quarter</MenuItem>
                <MenuItem value="2024-Q1">2024 Q1</MenuItem>
                <MenuItem value="2024-Q2">2024 Q2</MenuItem>
                <MenuItem value="2024-Q3">2024 Q3</MenuItem>
                <MenuItem value="2024-Q4">2024 Q4</MenuItem>
                <MenuItem value="2025-Q1">2025 Q1</MenuItem>
                <MenuItem value="2025-Q2">2025 Q2</MenuItem>
                <MenuItem value="2025-Q3">2025 Q3</MenuItem>
                <MenuItem value="2025-Q4">2025 Q4</MenuItem>
              </Select>
            </FormControl>
            <Typography variant="body2" color="text.secondary">
              Generate scorecards for all active policies. This may take a few minutes.
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setGenerateDialogOpen(false)} disabled={generating}>Cancel</Button>
          <Button 
            onClick={() => handleGenerateScorecards(selectedPeriod || '')} 
            variant="contained"
            disabled={generating}
          >
            {generating ? 'Generating...' : 'Generate'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Compare Scorecards Dialog */}
      <Dialog open={compareDialogOpen} onClose={() => setCompareDialogOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle>Compare Scorecards</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, pt: 1 }}>
            <FormControl fullWidth>
              <InputLabel>Period (Optional)</InputLabel>
              <Select
                value={comparePeriod}
                label="Period (Optional)"
                onChange={(e) => setComparePeriod(e.target.value)}
              >
                <MenuItem value="">Latest for each policy</MenuItem>
                <MenuItem value="2024-Q1">2024 Q1</MenuItem>
                <MenuItem value="2024-Q2">2024 Q2</MenuItem>
                <MenuItem value="2024-Q3">2024 Q3</MenuItem>
                <MenuItem value="2024-Q4">2024 Q4</MenuItem>
                <MenuItem value="2025-Q1">2025 Q1</MenuItem>
                <MenuItem value="2025-Q2">2025 Q2</MenuItem>
                <MenuItem value="2025-Q3">2025 Q3</MenuItem>
                <MenuItem value="2025-Q4">2025 Q4</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel>Select Policies (2-10)</InputLabel>
              <Select
                multiple
                value={selectedPoliciesForCompare}
                label="Select Policies (2-10)"
                onChange={(e) => {
                  const value = e.target.value as string[]
                  if (value.length <= 10) {
                    setSelectedPoliciesForCompare(value)
                  }
                }}
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {selected.map((policyId) => {
                      const policy = policies.find(p => p.id === policyId)
                      return (
                        <Chip key={policyId} label={policy?.name || policyId.substring(0, 8)} size="small" />
                      )
                    })}
                  </Box>
                )}
              >
                {policies.map((policy) => (
                  <MenuItem key={policy.id} value={policy.id}>
                    {policy.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            {comparisonData && (
              <Box>
                <Typography variant="h6" gutterBottom>
                  Comparison Results - {comparisonData.period || 'Latest Period'}
                </Typography>
                <TableContainer component={Paper}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Policy</TableCell>
                        <TableCell align="right">Effectiveness</TableCell>
                        <TableCell align="right">Cost Impact</TableCell>
                        <TableCell align="right">Behavioral Risk</TableCell>
                        <TableCell align="right">Access Impact</TableCell>
                        <TableCell align="right">Regulatory</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {comparisonData.policies.map((policy: any) => (
                        <TableRow key={policy.policy_id}>
                          <TableCell>{policy.policy_name}</TableCell>
                          <TableCell align="right">
                            <Chip
                              label={policy.effectiveness_index.toFixed(1)}
                              color={getEffectivenessColor(policy.effectiveness_index)}
                              size="small"
                            />
                          </TableCell>
                          <TableCell align="right">{policy.cost_impact_score.toFixed(1)}</TableCell>
                          <TableCell align="right">{policy.behavioral_risk_score.toFixed(1)}</TableCell>
                          <TableCell align="right">{policy.access_impact_score.toFixed(1)}</TableCell>
                          <TableCell align="right">{policy.regulatory_defensibility_score.toFixed(1)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
                <Box sx={{ mt: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Comparison Chart
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={comparisonData.policies.map((p: any) => ({
                      name: p.policy_name,
                      Effectiveness: p.effectiveness_index,
                      'Cost Impact': p.cost_impact_score,
                      'Behavioral Risk': p.behavioral_risk_score,
                      'Access Impact': p.access_impact_score,
                      Regulatory: p.regulatory_defensibility_score,
                    }))}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="Effectiveness" fill={COLORS[0]} />
                      <Bar dataKey="Cost Impact" fill={COLORS[1]} />
                      <Bar dataKey="Behavioral Risk" fill={COLORS[2]} />
                      <Bar dataKey="Access Impact" fill={COLORS[3]} />
                      <Bar dataKey="Regulatory" fill="#8884d8" />
                    </BarChart>
                  </ResponsiveContainer>
                </Box>
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setCompareDialogOpen(false)
            setComparisonData(null)
            setSelectedPoliciesForCompare([])
            setComparePeriod('')
          }}>
            Close
          </Button>
          <Button
            onClick={handleCompareScorecards}
            variant="contained"
            disabled={selectedPoliciesForCompare.length < 2 || comparing}
            startIcon={comparing ? <CircularProgress size={20} /> : <CompareIcon />}
          >
            {comparing ? 'Comparing...' : 'Compare'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
