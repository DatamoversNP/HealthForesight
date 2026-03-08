/**
 * Forecast Manager Component - Epic 4
 * Create and manage forecast distributions
 */
import { useState, useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
  Alert,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Chip,
} from '@mui/material'
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material'
import { apiClient } from '../../lib/api'
import FanChart from './FanChart'

interface ForecastData {
  forecast_id: string
  metric_name: string
  point_estimate: number
  uncertainty_range?: {
    p10: number
    p50: number
    p90: number
  }
  confidence_interval?: {
    lower_bound: number
    upper_bound: number
    confidence_level: number
  }
  created_at: string
}

interface ForecastManagerProps {
  policyId?: string
}

export default function ForecastManager({ policyId }: ForecastManagerProps) {
  const [forecasts, setForecasts] = useState<ForecastData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [viewingForecast, setViewingForecast] = useState<ForecastData | null>(null)
  const [formData, setFormData] = useState({
    metric_name: '',
    point_estimate: 0,
    p10: 0,
    p50: 0,
    p90: 0,
    lower_bound: 0,
    upper_bound: 0,
    confidence_level: 0.95,
  })

  useEffect(() => {
    loadForecasts()
  }, [])

  const loadForecasts = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.getForecasts()
      setForecasts(Array.isArray(data) ? data : [])
    } catch (err: any) {
      console.error('Failed to load forecasts:', err)
      setError(err.detail || err.message || 'Failed to load forecasts')
    } finally {
      setLoading(false)
    }
  }

  const handleOpenDialog = () => {
    setFormData({
      metric_name: '',
      point_estimate: 0,
      p10: 0,
      p50: 0,
      p90: 0,
      lower_bound: 0,
      upper_bound: 0,
      confidence_level: 0.95,
    })
    setDialogOpen(true)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
  }

  const handleSubmit = async () => {
    try {
      setError(null)

      // Validation
      if (!formData.metric_name.trim()) {
        setError('Metric name is required')
        return
      }

      if (formData.p10 >= formData.p50 || formData.p50 >= formData.p90) {
        setError('P10 < P50 < P90 must be true')
        return
      }

      const forecastData: any = {
        metric_name: formData.metric_name.trim(),
        point_estimate: Number(formData.point_estimate),
        uncertainty_range: {
          p10: Number(formData.p10),
          p50: Number(formData.p50),
          p90: Number(formData.p90),
        },
      }

      if (formData.lower_bound && formData.upper_bound && formData.confidence_level) {
        forecastData.confidence_interval = {
          lower_bound: Number(formData.lower_bound),
          upper_bound: Number(formData.upper_bound),
          confidence_level: Number(formData.confidence_level),
        }
      }

      await apiClient.createForecast(forecastData)
      handleCloseDialog()
      await loadForecasts()
    } catch (err: any) {
      console.error('Failed to create forecast:', err)
      setError(err.detail || err.message || 'Failed to create forecast')
    }
  }

  const handleView = (forecast: ForecastData) => {
    setViewingForecast(forecast)
  }

  const handleDelete = async (forecastId: string) => {
    if (!confirm('Are you sure you want to delete this forecast?')) {
      return
    }
    // Note: Delete endpoint not yet implemented in backend
    setError('Delete functionality not yet implemented')
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <>
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">
              Forecast Distributions
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleOpenDialog}
            >
              Create Forecast
            </Button>
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {forecasts.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No forecasts created yet. Click "Create Forecast" to add one.
            </Typography>
          ) : (
            <List>
              {forecasts.map((forecast) => (
                <ListItem
                  key={forecast.forecast_id}
                  secondaryAction={
                    <Box>
                      <IconButton
                        edge="end"
                        onClick={() => handleView(forecast)}
                        sx={{ mr: 1 }}
                      >
                        <ViewIcon />
                      </IconButton>
                      <IconButton
                        edge="end"
                        onClick={() => handleDelete(forecast.forecast_id)}
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Box>
                  }
                >
                  <ListItemText
                    primary={forecast.metric_name}
                    secondary={
                      <Box>
                        <Typography variant="caption" component="span" sx={{ mr: 2 }}>
                          Point Estimate: {forecast.point_estimate.toLocaleString(undefined, {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}
                        </Typography>
                        {forecast.uncertainty_range && (
                          <Chip
                            label={`P10/P50/P90: ${forecast.uncertainty_range.p10.toFixed(0)} / ${forecast.uncertainty_range.p50.toFixed(0)} / ${forecast.uncertainty_range.p90.toFixed(0)}`}
                            size="small"
                            sx={{ mr: 1 }}
                          />
                        )}
                        <Typography variant="caption" color="text.secondary">
                          {new Date(forecast.created_at).toLocaleString()}
                        </Typography>
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          )}
        </CardContent>
      </Card>

      {/* Create Forecast Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>Create Forecast Distribution</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Metric Name"
                value={formData.metric_name}
                onChange={(e) => setFormData({ ...formData, metric_name: e.target.value })}
                required
                placeholder="e.g., Total Cost, Utilization Rate"
              />
            </Grid>
            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom>
                Point Estimate
              </Typography>
              <TextField
                fullWidth
                type="number"
                label="Point Estimate"
                value={formData.point_estimate}
                onChange={(e) => setFormData({ ...formData, point_estimate: parseFloat(e.target.value) || 0 })}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom>
                Uncertainty Range (P10/P50/P90)
              </Typography>
            </Grid>
            <Grid item xs={4}>
              <TextField
                fullWidth
                type="number"
                label="P10 (Conservative)"
                value={formData.p10}
                onChange={(e) => setFormData({ ...formData, p10: parseFloat(e.target.value) || 0 })}
                required
                helperText="10th percentile"
              />
            </Grid>
            <Grid item xs={4}>
              <TextField
                fullWidth
                type="number"
                label="P50 (Median)"
                value={formData.p50}
                onChange={(e) => setFormData({ ...formData, p50: parseFloat(e.target.value) || 0 })}
                required
                helperText="50th percentile"
              />
            </Grid>
            <Grid item xs={4}>
              <TextField
                fullWidth
                type="number"
                label="P90 (Optimistic)"
                value={formData.p90}
                onChange={(e) => setFormData({ ...formData, p90: parseFloat(e.target.value) || 0 })}
                required
                helperText="90th percentile"
              />
            </Grid>
            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom>
                Confidence Interval (Optional)
              </Typography>
            </Grid>
            <Grid item xs={4}>
              <TextField
                fullWidth
                type="number"
                label="Lower Bound"
                value={formData.lower_bound}
                onChange={(e) => setFormData({ ...formData, lower_bound: parseFloat(e.target.value) || 0 })}
              />
            </Grid>
            <Grid item xs={4}>
              <TextField
                fullWidth
                type="number"
                label="Upper Bound"
                value={formData.upper_bound}
                onChange={(e) => setFormData({ ...formData, upper_bound: parseFloat(e.target.value) || 0 })}
              />
            </Grid>
            <Grid item xs={4}>
              <TextField
                fullWidth
                type="number"
                label="Confidence Level"
                value={formData.confidence_level}
                onChange={(e) => setFormData({ ...formData, confidence_level: parseFloat(e.target.value) || 0.95 })}
                inputProps={{ min: 0, max: 1, step: 0.01 }}
                helperText="0.0 to 1.0 (e.g., 0.95 = 95%)"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {/* View Forecast Dialog */}
      <Dialog
        open={!!viewingForecast}
        onClose={() => setViewingForecast(null)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          {viewingForecast?.metric_name}
        </DialogTitle>
        <DialogContent>
          {viewingForecast && <FanChart forecast={viewingForecast} height={400} />}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewingForecast(null)}>Close</Button>
        </DialogActions>
      </Dialog>
    </>
  )
}

