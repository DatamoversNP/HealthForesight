import React, { useEffect, useState } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Alert,
} from '@mui/material'
import {
  TrendingUp as TrendingUpIcon,
  Assessment as AssessmentIcon,
  ShowChart as ShowChartIcon,
} from '@mui/icons-material'
import { apiClient } from '../../lib/api'

interface LearningMetricsDashboardProps {
  policyId: string
}

interface AccuracySummary {
  policy_id: string
  total_observations: number
  average_accuracy_pct: number | null
  average_mae: number | null
  average_rmse: number | null
  records: Array<{
    accuracy_id: string
    predicted_effect_size: number
    observed_effect_size: number
    prediction_accuracy_pct: number
    recorded_at: string
  }>
}

export const LearningMetricsDashboard: React.FC<LearningMetricsDashboardProps> = ({
  policyId,
}) => {
  const [accuracySummary, setAccuracySummary] = useState<AccuracySummary | null>(null)
  const [elasticityModels, setElasticityModels] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadMetrics()
  }, [policyId])

  const loadMetrics = async () => {
    try {
      setLoading(true)
      setError(null)

      // Load accuracy summary
      const accuracy = await apiClient.getPredictionAccuracy(policyId)
      setAccuracySummary(accuracy)

      // Load elasticity models (if policy type is known)
      try {
        const models = await apiClient.listElasticityModels()
        setElasticityModels(models)
      } catch (e) {
        console.warn('Failed to load elasticity models:', e)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load learning metrics')
      console.error('Error loading learning metrics:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Box>
        <LinearProgress />
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          Loading learning metrics...
        </Typography>
      </Box>
    )
  }

  if (error) {
    return (
      <Alert severity="error" onClose={() => setError(null)}>
        {error}
      </Alert>
    )
  }

  if (!accuracySummary) {
    return (
      <Alert severity="info">
        No learning metrics available yet. Metrics will appear after observations are recorded.
      </Alert>
    )
  }

  const accuracyColor = accuracySummary.average_accuracy_pct
    ? accuracySummary.average_accuracy_pct >= 80
      ? 'success'
      : accuracySummary.average_accuracy_pct >= 60
      ? 'warning'
      : 'error'
    : 'default'

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        <AssessmentIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
        Learning Metrics
      </Typography>

      <Grid container spacing={2} sx={{ mt: 1 }}>
        {/* Accuracy Summary Cards */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="body2">
                Average Accuracy
              </Typography>
              <Typography variant="h4" color={accuracyColor}>
                {accuracySummary.average_accuracy_pct
                  ? `${accuracySummary.average_accuracy_pct.toFixed(1)}%`
                  : 'N/A'}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Based on {accuracySummary.total_observations} observation(s)
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="body2">
                Mean Absolute Error
              </Typography>
              <Typography variant="h4">
                {accuracySummary.average_mae !== null
                  ? accuracySummary.average_mae.toFixed(2)
                  : 'N/A'}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Lower is better
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="body2">
                Root Mean Squared Error
              </Typography>
              <Typography variant="h4">
                {accuracySummary.average_rmse !== null
                  ? accuracySummary.average_rmse.toFixed(2)
                  : 'N/A'}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Lower is better
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Accuracy History Table */}
        {accuracySummary.records && accuracySummary.records.length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>
                  <ShowChartIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Accuracy History
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Date</TableCell>
                        <TableCell align="right">Predicted</TableCell>
                        <TableCell align="right">Observed</TableCell>
                        <TableCell align="right">Accuracy</TableCell>
                        <TableCell>Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {accuracySummary.records.map((record) => {
                        const accuracyColor =
                          record.prediction_accuracy_pct >= 80
                            ? 'success'
                            : record.prediction_accuracy_pct >= 60
                            ? 'warning'
                            : 'error'

                        return (
                          <TableRow key={record.accuracy_id}>
                            <TableCell>
                              {new Date(record.recorded_at).toLocaleDateString()}
                            </TableCell>
                            <TableCell align="right">
                              {record.predicted_effect_size.toFixed(2)}
                            </TableCell>
                            <TableCell align="right">
                              {record.observed_effect_size.toFixed(2)}
                            </TableCell>
                            <TableCell align="right">
                              <Chip
                                label={`${record.prediction_accuracy_pct.toFixed(1)}%`}
                                size="small"
                                color={accuracyColor}
                              />
                            </TableCell>
                            <TableCell>
                              <Chip
                                label={
                                  record.prediction_accuracy_pct >= 80
                                    ? 'Good'
                                    : record.prediction_accuracy_pct >= 60
                                    ? 'Fair'
                                    : 'Poor'
                                }
                                size="small"
                                variant="outlined"
                              />
                            </TableCell>
                          </TableRow>
                        )
                      })}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Elasticity Models */}
        {elasticityModels.length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>
                  <TrendingUpIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Elasticity Models
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Policy Type</TableCell>
                        <TableCell>Version</TableCell>
                        <TableCell align="right">Utilization Elasticity</TableCell>
                        <TableCell align="right">Cost Elasticity</TableCell>
                        <TableCell align="right">Confidence</TableCell>
                        <TableCell>Observations</TableCell>
                        <TableCell>Last Updated</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {elasticityModels.map((model) => (
                        <TableRow key={model.model_id}>
                          <TableCell>{model.policy_type}</TableCell>
                          <TableCell>
                            <Chip label={model.version} size="small" variant="outlined" />
                          </TableCell>
                          <TableCell align="right">
                            {model.elasticity_coefficients?.utilization_elasticity?.toFixed(3) ||
                              'N/A'}
                          </TableCell>
                          <TableCell align="right">
                            {model.elasticity_coefficients?.cost_elasticity?.toFixed(3) || 'N/A'}
                          </TableCell>
                          <TableCell align="right">
                            <Chip
                              label={`${(model.confidence * 100).toFixed(0)}%`}
                              size="small"
                              color={model.confidence >= 0.8 ? 'success' : 'warning'}
                            />
                          </TableCell>
                          <TableCell>
                            {model.training_metrics?.observation_count || 0}
                          </TableCell>
                          <TableCell>
                            {new Date(model.updated_at).toLocaleDateString()}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  )
}
