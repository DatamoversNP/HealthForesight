/**
 * Substitution Results Display Component - Shows substitution patterns, top pathways, lag effects
 */
import { useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Alert,
  LinearProgress,
} from '@mui/material'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts'

interface SubstitutionResultsDisplayProps {
  substitutionResults: {
    substitutions?: Array<{
      code: string
      code_group?: string
      classification: 'SITE_OF_CARE_SHIFT' | 'SERVICE_SUBSTITUTION' | 'UNKNOWN'
      pre_allowed: number
      post_allowed: number
      allowed_delta: number
      allowed_pct_change: number
      pre_claim_count: number
      post_claim_count: number
      claim_count_delta: number
      lag_effects?: Record<string, { claim_count: number; total_allowed: number }>
      confidence_score: number
      statistical_rank?: number
      p_value?: number
    }>
    total_substitutions_detected?: number
    top_pathways?: Array<{
      from_code: string
      to_code: string
      to_code_group: string
      count: number
      total_delta: number
      avg_confidence: number
    }>
    warnings?: string[]
  }
}

export default function SubstitutionResultsDisplay({ substitutionResults }: SubstitutionResultsDisplayProps) {
  const [filterClassification, setFilterClassification] = useState<string>('ALL')
  const [sortBy, setSortBy] = useState<'confidence' | 'rank' | 'magnitude'>('confidence')
  const [selectedSubstitution, setSelectedSubstitution] = useState<string | null>(null)

  const substitutions = substitutionResults?.substitutions || []
  const topPathways = substitutionResults?.top_pathways || []

  // Filter substitutions
  const filteredSubstitutions = substitutions.filter((sub) => {
    if (filterClassification === 'ALL') return true
    return sub.classification === filterClassification
  })

  // Sort substitutions
  const sortedSubstitutions = [...filteredSubstitutions].sort((a, b) => {
    switch (sortBy) {
      case 'confidence':
        return b.confidence_score - a.confidence_score
      case 'rank':
        return (a.statistical_rank || 999) - (b.statistical_rank || 999)
      case 'magnitude':
        return Math.abs(b.allowed_delta) - Math.abs(a.allowed_delta)
      default:
        return 0
    }
  })

  // Get selected substitution for lag effects chart
  const selectedSub = sortedSubstitutions.find((s) => s.code === selectedSubstitution)

  // Prepare lag effects data for chart
  const lagEffectsData = selectedSub?.lag_effects
    ? Object.entries(selectedSub.lag_effects).map(([window, data]) => ({
        window: window.replace('_day', ' days'),
        claim_count: data.claim_count,
        total_allowed: data.total_allowed,
      }))
    : []

  const getClassificationColor = (classification: string): 'success' | 'warning' | 'error' | 'default' => {
    switch (classification) {
      case 'SITE_OF_CARE_SHIFT':
        return 'warning'
      case 'SERVICE_SUBSTITUTION':
        return 'error'
      default:
        return 'default'
    }
  }

  const getConfidenceColor = (score: number): 'success' | 'warning' | 'error' => {
    if (score >= 70) return 'success'
    if (score >= 40) return 'warning'
    return 'error'
  }

  return (
    <Box>
      {substitutionResults?.warnings && substitutionResults.warnings.length > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            <strong>Warnings:</strong>
          </Typography>
          <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
            {substitutionResults.warnings.map((warning, idx) => (
              <li key={idx}>{warning}</li>
            ))}
          </ul>
        </Alert>
      )}

      {/* Summary Stats */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Total Substitutions Detected
              </Typography>
              <Typography variant="h4" color="primary">
                {substitutionResults?.total_substitutions_detected || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                High Confidence
              </Typography>
              <Typography variant="h4" color="success.main">
                {substitutions.filter((s) => s.confidence_score >= 70).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Site-of-Care Shifts
              </Typography>
              <Typography variant="h4" color="warning.main">
                {substitutions.filter((s) => s.classification === 'SITE_OF_CARE_SHIFT').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Top Pathways */}
      {topPathways.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Top Substitution Pathways
            </Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>From</strong></TableCell>
                    <TableCell><strong>To</strong></TableCell>
                    <TableCell><strong>Code Group</strong></TableCell>
                    <TableCell align="right"><strong>Occurrences</strong></TableCell>
                    <TableCell align="right"><strong>Total Delta ($)</strong></TableCell>
                    <TableCell align="right"><strong>Avg Confidence</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {topPathways.map((pathway, idx) => (
                    <TableRow key={idx} hover>
                      <TableCell>{pathway.from_code}</TableCell>
                      <TableCell>{pathway.to_code}</TableCell>
                      <TableCell>
                        <Chip label={pathway.to_code_group} size="small" />
                      </TableCell>
                      <TableCell align="right">{pathway.count}</TableCell>
                      <TableCell align="right">
                        ${pathway.total_delta.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </TableCell>
                      <TableCell align="right">
                        <Chip
                          label={`${pathway.avg_confidence.toFixed(0)}%`}
                          color={getConfidenceColor(pathway.avg_confidence)}
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* Filters and Sorting */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth size="small">
                <InputLabel>Filter by Classification</InputLabel>
                <Select
                  value={filterClassification}
                  onChange={(e) => setFilterClassification(e.target.value)}
                  label="Filter by Classification"
                >
                  <MenuItem value="ALL">All Classifications</MenuItem>
                  <MenuItem value="SITE_OF_CARE_SHIFT">Site-of-Care Shift</MenuItem>
                  <MenuItem value="SERVICE_SUBSTITUTION">Service Substitution</MenuItem>
                  <MenuItem value="UNKNOWN">Unknown</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth size="small">
                <InputLabel>Sort By</InputLabel>
                <Select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  label="Sort By"
                >
                  <MenuItem value="confidence">Confidence Score</MenuItem>
                  <MenuItem value="rank">Statistical Rank</MenuItem>
                  <MenuItem value="magnitude">Magnitude (Delta)</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>

          {/* Substitutions Table */}
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Rank</strong></TableCell>
                  <TableCell><strong>Code</strong></TableCell>
                  <TableCell><strong>Classification</strong></TableCell>
                  <TableCell align="right"><strong>Pre Allowed ($)</strong></TableCell>
                  <TableCell align="right"><strong>Post Allowed ($)</strong></TableCell>
                  <TableCell align="right"><strong>Delta ($)</strong></TableCell>
                  <TableCell align="right"><strong>% Change</strong></TableCell>
                  <TableCell align="right"><strong>Confidence</strong></TableCell>
                  <TableCell align="right"><strong>P-Value</strong></TableCell>
                  <TableCell><strong>Actions</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {sortedSubstitutions.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={10} align="center">
                      <Typography variant="body2" color="text.secondary" sx={{ py: 3 }}>
                        No substitutions detected
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  sortedSubstitutions.map((sub) => (
                    <TableRow
                      key={sub.code}
                      hover
                      selected={selectedSubstitution === sub.code}
                      onClick={() => setSelectedSubstitution(selectedSubstitution === sub.code ? null : sub.code)}
                      sx={{ cursor: 'pointer' }}
                    >
                      <TableCell>{sub.statistical_rank || '-'}</TableCell>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {sub.code}
                        </Typography>
                        {sub.code_group && (
                          <Typography variant="caption" color="text.secondary">
                            {sub.code_group}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={sub.classification.replace(/_/g, ' ')}
                          color={getClassificationColor(sub.classification)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="right">
                        ${sub.pre_allowed.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </TableCell>
                      <TableCell align="right">
                        ${sub.post_allowed.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </TableCell>
                      <TableCell align="right">
                        <Typography
                          variant="body2"
                          color={sub.allowed_delta > 0 ? 'error.main' : 'success.main'}
                          fontWeight="medium"
                        >
                          {sub.allowed_delta > 0 ? '+' : ''}
                          ${sub.allowed_delta.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography
                          variant="body2"
                          color={sub.allowed_pct_change > 0 ? 'error.main' : 'success.main'}
                          fontWeight="medium"
                        >
                          {sub.allowed_pct_change > 0 ? '+' : ''}
                          {sub.allowed_pct_change.toFixed(1)}%
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, justifyContent: 'flex-end' }}>
                          <LinearProgress
                            variant="determinate"
                            value={sub.confidence_score}
                            color={getConfidenceColor(sub.confidence_score)}
                            sx={{ width: 60, height: 6, borderRadius: 1 }}
                          />
                          <Typography variant="caption" fontWeight="medium">
                            {sub.confidence_score.toFixed(0)}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="right">
                        {sub.p_value !== undefined && sub.p_value !== null ? (
                          <Typography variant="body2">
                            {sub.p_value.toFixed(4)}
                            {sub.p_value < 0.05 && (
                              <Chip label="*" color="error" size="small" sx={{ ml: 0.5 }} />
                            )}
                          </Typography>
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            N/A
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption" color="primary">
                          {selectedSubstitution === sub.code ? 'Hide Details' : 'Show Details'}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Lag Effects Chart for Selected Substitution */}
      {selectedSub && lagEffectsData.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Lag Effects: {selectedSub.code}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Substitution patterns over time (30, 60, 90 day windows)
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={lagEffectsData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="window" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Legend />
                <Bar yAxisId="left" dataKey="claim_count" fill="#8884d8" name="Claim Count" />
                <Bar yAxisId="right" dataKey="total_allowed" fill="#82ca9d" name="Total Allowed ($)" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}
    </Box>
  )
}

