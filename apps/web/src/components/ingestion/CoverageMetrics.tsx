/**
 * Coverage Metrics Component
 * Displays data coverage status, completeness, and confidence penalties
 */
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  Grid,
  List,
  ListItem,
  ListItemText,
} from '@mui/material'
import {
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
} from '@mui/icons-material'
import { healthForesightColors } from '../../theme/healthForesightTheme'

interface CoverageMetricsProps {
  coverage: {
    coverage_status?: string
    completeness_score?: number
    confidence_penalty?: number
    available_fields?: string[]
    partial_fields?: string[]
    missing_fields?: string[]
  }
}

export default function CoverageMetrics({ coverage }: CoverageMetricsProps) {
  const status = coverage.coverage_status || 'UNKNOWN'
  const completeness = coverage.completeness_score || 0
  const confidencePenalty = coverage.confidence_penalty || 0
  const available = coverage.available_fields || []
  const partial = coverage.partial_fields || []
  const missing = coverage.missing_fields || []

  const getStatusColor = () => {
    switch (status) {
      case 'AVAILABLE':
        return 'success'
      case 'PARTIAL':
        return 'warning'
      case 'MISSING':
        return 'error'
      default:
        return 'default'
    }
  }

  const getStatusIcon = () => {
    switch (status) {
      case 'AVAILABLE':
        return <CheckCircleIcon fontSize="small" />
      case 'PARTIAL':
        return <WarningIcon fontSize="small" />
      case 'MISSING':
        return <ErrorIcon fontSize="small" />
      default:
        return null
    }
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Data Coverage Metrics
        </Typography>

        <Grid container spacing={2} sx={{ mb: 2 }}>
          <Grid item xs={12} sm={6}>
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Coverage Status
                </Typography>
                <Chip
                  icon={getStatusIcon()}
                  label={status}
                  color={getStatusColor()}
                  size="small"
                />
              </Box>
            </Box>
          </Grid>

          <Grid item xs={12} sm={6}>
            <Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Completeness Score
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <LinearProgress
                  variant="determinate"
                  value={completeness * 100}
                  sx={{ flexGrow: 1, height: 8, borderRadius: 4 }}
                  color={completeness >= 0.9 ? 'success' : completeness >= 0.7 ? 'warning' : 'error'}
                />
                <Typography variant="body2" fontWeight={600}>
                  {(completeness * 100).toFixed(1)}%
                </Typography>
              </Box>
            </Box>
          </Grid>

          {confidencePenalty > 0 && (
            <Grid item xs={12} sm={6}>
              <Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Confidence Penalty
                </Typography>
                <Typography variant="h6" color="warning.main">
                  {(confidencePenalty * 100).toFixed(1)}%
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Model confidence reduced due to missing data
                </Typography>
              </Box>
            </Grid>
          )}
        </Grid>

        {missing.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" color="error" gutterBottom>
              Missing Required Fields ({missing.length})
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {missing.map((field) => (
                <Chip key={field} label={field} size="small" color="error" variant="outlined" />
              ))}
            </Box>
          </Box>
        )}

        {partial.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" color="warning.main" gutterBottom>
              Partially Available Fields ({partial.length})
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {partial.map((field) => (
                <Chip key={field} label={field} size="small" color="warning" variant="outlined" />
              ))}
            </Box>
          </Box>
        )}

        {available.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" color="success.main" gutterBottom>
              Available Fields ({available.length})
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, maxHeight: 150, overflow: 'auto' }}>
              {available.map((field) => (
                <Chip key={field} label={field} size="small" color="success" variant="outlined" />
              ))}
            </Box>
          </Box>
        )}
      </CardContent>
    </Card>
  )
}

