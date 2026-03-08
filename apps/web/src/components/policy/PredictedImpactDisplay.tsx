/**
 * Predicted Impact Display Component - Shows Stage 3.5 predicted impact results
 */
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Divider,
  Grid,
  Alert,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material'
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Assessment as AssessmentIcon,
  Psychology as PsychologyIcon,
  LocalHospital as HospitalIcon,
  People as PeopleIcon,
} from '@mui/icons-material'
import { healthForesightColors } from '../../theme/healthForesightTheme'
import ConfidenceBadge from '../brand/ConfidenceBadge'
import PolicyScopeDisplay from './PolicyScopeDisplay'
import { format } from 'date-fns'

interface PredictedImpactMetrics {
  utilization_change_per_1k: number
  cost_change_pmpm: number
  cost_change_total: number
  utilization_change_pct: number
  cost_change_pct: number
  confidence_score: number
  prediction_method: string
}

interface PredictedSubstitutionEffect {
  service_category: string
  predicted_substitution_rate: number
  predicted_substitute_services: string[]
  confidence_score: number
}

interface PredictedProviderResponse {
  compliant_pct: number
  adaptive_pct: number
  resistant_pct: number
  circumvention_pct: number
  confidence_score: number
}

interface PredictedPatientResponse {
  defer_rate: number
  substitute_rate: number
  er_fallback_rate: number
  confidence_score: number
}

interface PredictedImpactData {
  policy_id: string
  predicted_at: string
  metrics: PredictedImpactMetrics
  substitution_effects?: PredictedSubstitutionEffect[]
  provider_response?: PredictedProviderResponse
  patient_response?: PredictedPatientResponse
  baseline_reference?: any
  model_versions?: Record<string, string>
  warnings?: string[]
  limitations?: string[]
  policy_scope?: any // Policy scope for display
}

interface PredictedImpactDisplayProps {
  predictedImpact: PredictedImpactData
}

function formatCurrency(value: number | undefined | null): string {
  if (value === undefined || value === null || isNaN(value)) {
    return 'N/A'
  }
  const sign = value >= 0 ? '+' : ''
  return `${sign}$${Math.abs(value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function formatPercent(value: number | undefined | null): string {
  if (value === undefined || value === null || isNaN(value)) {
    return 'N/A'
  }
  const sign = value >= 0 ? '+' : ''
  return `${sign}${value.toFixed(1)}%`
}

function getChangeColor(value: number): 'success' | 'error' | 'default' {
  if (value > 0) return 'error' // Increase is negative for cost/utilization
  if (value < 0) return 'success' // Decrease is positive
  return 'default'
}

export default function PredictedImpactDisplay({ predictedImpact }: PredictedImpactDisplayProps) {
  // Handle missing or invalid predicted impact data
  if (!predictedImpact || !predictedImpact.metrics) {
    return (
      <Alert severity="info">
        <Typography variant="body1">
          Predicted impact data is not available for this policy.
        </Typography>
        <Typography variant="body2" sx={{ mt: 1 }}>
          Click "Generate" to create predicted impact analysis.
        </Typography>
      </Alert>
    )
  }
  
  const { metrics, substitution_effects = [], provider_response, patient_response, warnings = [], limitations = [] } = predictedImpact

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'MMM d, yyyy h:mm a')
    } catch {
      return dateString
    }
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
          <PsychologyIcon sx={{ color: healthForesightColors.primary.main, fontSize: 32 }} />
          <Typography variant="h5" sx={{ fontFamily: 'IBM Plex Sans, sans-serif', fontWeight: 600 }}>
            Predicted Impact (Stage 3.5)
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary">
          Generated: {formatDate(predictedImpact.predicted_at)}
          {predictedImpact.prediction_method && ` • Method: ${predictedImpact.metrics.prediction_method}`}
        </Typography>
      </Box>

      {/* Warnings */}
      {warnings.length > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Warnings:
          </Typography>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {warnings.map((warning, idx) => (
              <li key={idx}>
                <Typography variant="body2">{warning}</Typography>
              </li>
            ))}
          </ul>
        </Alert>
      )}

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Utilization Change
                </Typography>
                {metrics.utilization_change_per_1k >= 0 ? (
                  <TrendingUpIcon color="error" fontSize="small" />
                ) : (
                  <TrendingDownIcon color="success" fontSize="small" />
                )}
              </Box>
              <Typography variant="h5" sx={{ fontWeight: 600, mb: 0.5 }}>
                {formatPercent(metrics.utilization_change_pct)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {metrics.utilization_change_per_1k !== undefined && metrics.utilization_change_per_1k !== null 
                  ? `${metrics.utilization_change_per_1k >= 0 ? '+' : ''}${metrics.utilization_change_per_1k.toFixed(1)} per 1K members`
                  : 'N/A'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Cost Change (PMPM)
                </Typography>
                {metrics.cost_change_pmpm >= 0 ? (
                  <TrendingUpIcon color="error" fontSize="small" />
                ) : (
                  <TrendingDownIcon color="success" fontSize="small" />
                )}
              </Box>
              <Typography variant="h5" sx={{ fontWeight: 600, mb: 0.5 }}>
                {formatCurrency(metrics.cost_change_pmpm)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {formatPercent(metrics.cost_change_pct)} change
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Total Cost Change
              </Typography>
              <Typography variant="h5" sx={{ fontWeight: 600, mb: 0.5 }}>
                {formatCurrency(metrics.cost_change_total)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Annual impact
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Prediction Confidence
              </Typography>
              <Box sx={{ mb: 1 }}>
                <ConfidenceBadge score={metrics.confidence_score / 100} />
              </Box>
              <LinearProgress
                variant="determinate"
                value={metrics.confidence_score}
                sx={{ height: 8, borderRadius: 1 }}
                color={metrics.confidence_score >= 70 ? 'success' : metrics.confidence_score >= 40 ? 'warning' : 'error'}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Provider Response */}
      {provider_response && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <PeopleIcon sx={{ color: healthForesightColors.primary.main }} />
              <Typography variant="h6" sx={{ fontFamily: 'IBM Plex Sans, sans-serif', fontWeight: 600 }}>
                Predicted Provider Response
              </Typography>
              <Chip
                label={`${provider_response.confidence_score.toFixed(0)}% confidence`}
                size="small"
                color={provider_response.confidence_score >= 70 ? 'success' : provider_response.confidence_score >= 40 ? 'warning' : 'error'}
              />
            </Box>
            <Grid container spacing={2}>
              <Grid item xs={6} md={3}>
                <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'success.light', borderRadius: 1 }}>
                  <Typography variant="h4" sx={{ fontWeight: 600, color: 'success.dark' }}>
                    {provider_response.compliant_pct.toFixed(0)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Compliant
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} md={3}>
                <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                  <Typography variant="h4" sx={{ fontWeight: 600, color: 'info.dark' }}>
                    {provider_response.adaptive_pct.toFixed(0)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Adaptive
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} md={3}>
                <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'warning.light', borderRadius: 1 }}>
                  <Typography variant="h4" sx={{ fontWeight: 600, color: 'warning.dark' }}>
                    {provider_response.resistant_pct.toFixed(0)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Resistant
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} md={3}>
                <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'error.light', borderRadius: 1 }}>
                  <Typography variant="h4" sx={{ fontWeight: 600, color: 'error.dark' }}>
                    {provider_response.circumvention_pct.toFixed(0)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Circumvention
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Patient Response */}
      {patient_response && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <HospitalIcon sx={{ color: healthForesightColors.primary.main }} />
              <Typography variant="h6" sx={{ fontFamily: 'IBM Plex Sans, sans-serif', fontWeight: 600 }}>
                Predicted Patient Response
              </Typography>
              <Chip
                label={`${patient_response.confidence_score.toFixed(0)}% confidence`}
                size="small"
                color={patient_response.confidence_score >= 70 ? 'success' : patient_response.confidence_score >= 40 ? 'warning' : 'error'}
              />
            </Box>
            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <Box sx={{ p: 2, border: 1, borderColor: 'divider', borderRadius: 1 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Care Deferral Rate
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: 600 }}>
                    {(patient_response.defer_rate * 100).toFixed(1)}%
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={4}>
                <Box sx={{ p: 2, border: 1, borderColor: 'divider', borderRadius: 1 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Service Substitution Rate
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: 600 }}>
                    {(patient_response.substitute_rate * 100).toFixed(1)}%
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={4}>
                <Box sx={{ p: 2, border: 1, borderColor: 'error.main', borderRadius: 1, bgcolor: 'error.light' }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    ER Fallback Rate
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: 600, color: 'error.dark' }}>
                    {(patient_response.er_fallback_rate * 100).toFixed(1)}%
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Substitution Effects */}
      {substitution_effects.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <AssessmentIcon sx={{ color: healthForesightColors.primary.main }} />
              <Typography variant="h6" sx={{ fontFamily: 'IBM Plex Sans, sans-serif', fontWeight: 600 }}>
                Predicted Substitution Effects
              </Typography>
            </Box>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Service Category</TableCell>
                    <TableCell align="right">Substitution Rate</TableCell>
                    <TableCell>Substitute Services</TableCell>
                    <TableCell align="right">Confidence</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {substitution_effects.map((effect, idx) => (
                    <TableRow key={idx}>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {effect.service_category}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2">
                          {(effect.predicted_substitution_rate * 100).toFixed(1)}%
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                          {effect.predicted_substitute_services.length > 0 ? (
                            effect.predicted_substitute_services.map((service, sidx) => (
                              <Chip key={sidx} label={service} size="small" variant="outlined" />
                            ))
                          ) : (
                            <Typography variant="body2" color="text.secondary">
                              None predicted
                            </Typography>
                          )}
                        </Box>
                      </TableCell>
                      <TableCell align="right">
                        <Chip
                          label={`${effect.confidence_score.toFixed(0)}%`}
                          size="small"
                          color={effect.confidence_score >= 70 ? 'success' : effect.confidence_score >= 40 ? 'warning' : 'error'}
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

      {/* Limitations */}
      {limitations.length > 0 && (
        <Alert severity="info">
          <Typography variant="subtitle2" gutterBottom>
            Limitations:
          </Typography>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {limitations.map((limitation, idx) => (
              <li key={idx}>
                <Typography variant="body2">{limitation}</Typography>
              </li>
            ))}
          </ul>
        </Alert>
      )}
    </Box>
  )
}
