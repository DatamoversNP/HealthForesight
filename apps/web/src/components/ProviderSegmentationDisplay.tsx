/**
 * Provider Segmentation Display Component - Shows archetypes, provider assignments, clustering quality
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
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress,
  Alert,
} from '@mui/material'
import {
  ExpandMore as ExpandMoreIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  SwapHoriz as SwapHorizIcon,
} from '@mui/icons-material'

interface ProviderSegmentationDisplayProps {
  segmentationResults: {
    archetypes?: Array<{
      archetype_id: number
      archetype_label: string
      provider_count: number
      avg_allowed_delta: number
      avg_claim_count_delta: number
      avg_allowed_pct_change: number
      pos_shift_rate: number
      top_features?: Array<{
        feature: string
        mean_value: number
        std_value: number
        importance: number
      }>
      stability_score: number
    }>
    provider_assignments?: Array<{
      provider_id: string
      archetype_id: number
      archetype_label: string
      allowed_delta: number
      claim_count_delta: number
      avg_allowed_pct_change: number
      pos_shift: boolean
      confidence_score: number
    }>
    total_providers?: number
    clustering_quality?: {
      silhouette_score?: number
      quality?: 'GOOD' | 'FAIR' | 'POOR' | 'UNKNOWN'
      recommendation?: string
    }
    warnings?: string[]
  }
}

export default function ProviderSegmentationDisplay({ segmentationResults }: ProviderSegmentationDisplayProps) {
  const [filterArchetype, setFilterArchetype] = useState<string>('ALL')
  const [expandedArchetype, setExpandedArchetype] = useState<number | null>(null)

  const archetypes = segmentationResults?.archetypes || []
  const providerAssignments = segmentationResults?.provider_assignments || []
  const clusteringQuality = segmentationResults?.clustering_quality

  // Filter provider assignments
  const filteredAssignments = providerAssignments.filter((assignment) => {
    if (filterArchetype === 'ALL') return true
    return assignment.archetype_label === filterArchetype
  })

  // Get archetype labels for filter
  const archetypeLabels = Array.from(new Set(archetypes.map((a) => a.archetype_label)))

  const getArchetypeColor = (label: string): 'success' | 'warning' | 'error' | 'info' | 'default' => {
    switch (label.toUpperCase()) {
      case 'COMPLIERS':
      case 'REDUCERS':
        return 'success'
      case 'CIRCUMVENTERS':
      case 'SUBSTITUTORS':
        return 'error'
      case 'INCREASERS':
        return 'warning'
      case 'NEUTRAL':
        return 'info'
      default:
        return 'default'
    }
  }

  const getQualityColor = (quality?: string): 'success' | 'warning' | 'error' => {
    if (!quality) return 'warning'
    switch (quality) {
      case 'GOOD':
        return 'success'
      case 'FAIR':
        return 'warning'
      case 'POOR':
      case 'UNKNOWN':
        return 'error'
      default:
        return 'warning'
    }
  }

  return (
    <Box>
      {segmentationResults?.warnings && segmentationResults.warnings.length > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            <strong>Warnings:</strong>
          </Typography>
          <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
            {segmentationResults.warnings.map((warning, idx) => (
              <li key={idx}>{warning}</li>
            ))}
          </ul>
        </Alert>
      )}

      {/* Clustering Quality Indicator */}
      {clusteringQuality && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <Typography variant="h6">Clustering Quality</Typography>
              <Chip
                label={clusteringQuality.quality || 'UNKNOWN'}
                color={getQualityColor(clusteringQuality.quality)}
                size="small"
              />
            </Box>
            {clusteringQuality.silhouette_score !== undefined && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Silhouette Score: {clusteringQuality.silhouette_score.toFixed(3)}
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={(clusteringQuality.silhouette_score + 1) * 50} // Normalize from [-1, 1] to [0, 100]
                  color={getQualityColor(clusteringQuality.quality)}
                  sx={{ height: 8, borderRadius: 1 }}
                />
              </Box>
            )}
            {clusteringQuality.recommendation && (
              <Alert severity={getQualityColor(clusteringQuality.quality)}>
                {clusteringQuality.recommendation}
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Summary Stats */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Total Providers
              </Typography>
              <Typography variant="h4" color="primary">
                {segmentationResults?.total_providers || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Archetypes Identified
              </Typography>
              <Typography variant="h4" color="primary">
                {archetypes.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Providers Analyzed
              </Typography>
              <Typography variant="h4" color="primary">
                {providerAssignments.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Archetypes Overview */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
            Provider Archetypes
          </Typography>
          <Grid container spacing={2}>
            {archetypes.map((archetype) => (
              <Grid item xs={12} md={6} key={archetype.archetype_id}>
                <Accordion
                  expanded={expandedArchetype === archetype.archetype_id}
                  onChange={() =>
                    setExpandedArchetype(expandedArchetype === archetype.archetype_id ? null : archetype.archetype_id)
                  }
                >
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Box sx={{ width: '100%', display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Chip
                        label={archetype.archetype_label}
                        color={getArchetypeColor(archetype.archetype_label)}
                        size="small"
                      />
                      <Typography variant="body2" color="text.secondary">
                        {archetype.provider_count} providers
                      </Typography>
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <TableContainer component={Paper} variant="outlined">
                      <Table size="small">
                        <TableBody>
                          <TableRow>
                            <TableCell><strong>Provider Count</strong></TableCell>
                            <TableCell>{archetype.provider_count}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell><strong>Avg Allowed Delta ($)</strong></TableCell>
                            <TableCell>
                              <Typography
                                variant="body2"
                                color={archetype.avg_allowed_delta > 0 ? 'error.main' : 'success.main'}
                                fontWeight="medium"
                              >
                                {archetype.avg_allowed_delta > 0 ? '+' : ''}
                                ${archetype.avg_allowed_delta.toLocaleString(undefined, {
                                  minimumFractionDigits: 2,
                                  maximumFractionDigits: 2,
                                })}
                              </Typography>
                            </TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell><strong>Avg Claim Count Delta</strong></TableCell>
                            <TableCell>
                              <Typography
                                variant="body2"
                                color={archetype.avg_claim_count_delta > 0 ? 'error.main' : 'success.main'}
                                fontWeight="medium"
                              >
                                {archetype.avg_claim_count_delta > 0 ? '+' : ''}
                                {archetype.avg_claim_count_delta.toFixed(1)}
                              </Typography>
                            </TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell><strong>Avg Allowed % Change</strong></TableCell>
                            <TableCell>
                              <Typography
                                variant="body2"
                                color={archetype.avg_allowed_pct_change > 0 ? 'error.main' : 'success.main'}
                                fontWeight="medium"
                              >
                                {archetype.avg_allowed_pct_change > 0 ? '+' : ''}
                                {archetype.avg_allowed_pct_change.toFixed(1)}%
                              </Typography>
                            </TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell><strong>POS Shift Rate</strong></TableCell>
                            <TableCell>
                              {(archetype.pos_shift_rate * 100).toFixed(1)}%
                              {archetype.pos_shift_rate > 0.5 && (
                                <Chip
                                  icon={<SwapHorizIcon />}
                                  label="High"
                                  color="warning"
                                  size="small"
                                  sx={{ ml: 1 }}
                                />
                              )}
                            </TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell><strong>Stability Score</strong></TableCell>
                            <TableCell>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <LinearProgress
                                  variant="determinate"
                                  value={archetype.stability_score * 100}
                                  color={archetype.stability_score > 0.7 ? 'success' : 'warning'}
                                  sx={{ width: 100, height: 6, borderRadius: 1 }}
                                />
                                <Typography variant="caption">
                                  {(archetype.stability_score * 100).toFixed(0)}%
                                </Typography>
                              </Box>
                            </TableCell>
                          </TableRow>
                        </TableBody>
                      </Table>
                    </TableContainer>

                    {/* Top Features */}
                    {archetype.top_features && archetype.top_features.length > 0 && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Top Contributing Features:
                        </Typography>
                        <TableContainer component={Paper} variant="outlined" sx={{ mt: 1 }}>
                          <Table size="small">
                            <TableHead>
                              <TableRow>
                                <TableCell><strong>Feature</strong></TableCell>
                                <TableCell align="right"><strong>Mean Value</strong></TableCell>
                                <TableCell align="right"><strong>Importance</strong></TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {archetype.top_features.map((feature, idx) => (
                                <TableRow key={idx}>
                                  <TableCell>{feature.feature.replace(/_/g, ' ')}</TableCell>
                                  <TableCell align="right">{feature.mean_value.toFixed(2)}</TableCell>
                                  <TableCell align="right">
                                    <Typography variant="body2" fontWeight="medium">
                                      {feature.importance.toFixed(2)}
                                    </Typography>
                                  </TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </TableContainer>
                      </Box>
                    )}
                  </AccordionDetails>
                </Accordion>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>

      {/* Provider Assignments Table */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">Provider Assignments</Typography>
            <FormControl size="small" sx={{ minWidth: 200 }}>
              <InputLabel>Filter by Archetype</InputLabel>
              <Select
                value={filterArchetype}
                onChange={(e) => setFilterArchetype(e.target.value)}
                label="Filter by Archetype"
              >
                <MenuItem value="ALL">All Archetypes</MenuItem>
                {archetypeLabels.map((label) => (
                  <MenuItem key={label} value={label}>
                    {label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>

          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Provider ID</strong></TableCell>
                  <TableCell><strong>Archetype</strong></TableCell>
                  <TableCell align="right"><strong>Allowed Delta ($)</strong></TableCell>
                  <TableCell align="right"><strong>Claim Count Delta</strong></TableCell>
                  <TableCell align="right"><strong>Avg Allowed % Change</strong></TableCell>
                  <TableCell><strong>POS Shift</strong></TableCell>
                  <TableCell align="right"><strong>Confidence</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredAssignments.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} align="center">
                      <Typography variant="body2" color="text.secondary" sx={{ py: 3 }}>
                        No provider assignments available
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredAssignments.map((assignment, idx) => (
                    <TableRow key={idx} hover>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {assignment.provider_id}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={assignment.archetype_label}
                          color={getArchetypeColor(assignment.archetype_label)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Typography
                          variant="body2"
                          color={assignment.allowed_delta > 0 ? 'error.main' : 'success.main'}
                          fontWeight="medium"
                        >
                          {assignment.allowed_delta > 0 ? '+' : ''}
                          ${assignment.allowed_delta.toLocaleString(undefined, {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography
                          variant="body2"
                          color={assignment.claim_count_delta > 0 ? 'error.main' : 'success.main'}
                          fontWeight="medium"
                        >
                          {assignment.claim_count_delta > 0 ? '+' : ''}
                          {assignment.claim_count_delta}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography
                          variant="body2"
                          color={assignment.avg_allowed_pct_change > 0 ? 'error.main' : 'success.main'}
                          fontWeight="medium"
                        >
                          {assignment.avg_allowed_pct_change > 0 ? '+' : ''}
                          {assignment.avg_allowed_pct_change.toFixed(1)}%
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {assignment.pos_shift ? (
                          <Chip icon={<SwapHorizIcon />} label="Yes" color="warning" size="small" />
                        ) : (
                          <Chip label="No" color="default" size="small" />
                        )}
                      </TableCell>
                      <TableCell align="right">
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, justifyContent: 'flex-end' }}>
                          <LinearProgress
                            variant="determinate"
                            value={assignment.confidence_score}
                            color={assignment.confidence_score >= 70 ? 'success' : assignment.confidence_score >= 40 ? 'warning' : 'error'}
                            sx={{ width: 60, height: 6, borderRadius: 1 }}
                          />
                          <Typography variant="caption" fontWeight="medium">
                            {assignment.confidence_score}
                          </Typography>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  )
}

