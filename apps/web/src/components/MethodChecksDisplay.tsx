/**
 * Method Checks Display Component - Shows pre-trends, control balance, seasonality diagnostics
 */
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
  Alert,
  LinearProgress,
} from '@mui/material'
import {
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material'

interface MethodChecksDisplayProps {
  methodChecks: {
    method_checks?: {
      pre_trends?: {
        parallel_trends?: 'PASS' | 'WARN' | 'FAIL'
        pre_trend_treatment?: number
        pre_trend_control?: number
        pre_trend_difference?: number
        p_value?: number
        warning?: string
      }
      control_balance?: {
        balanced?: boolean
        balance_score?: number
        imbalanced_covariates?: string[]
        standardized_mean_differences?: Record<string, number>
        warning?: string
      }
      seasonality?: {
        seasonal_pattern_detected?: boolean
        seasonality_risk?: 'LOW' | 'MEDIUM' | 'HIGH'
        seasonal_periods?: number[]
        adjustment_recommended?: boolean
        warning?: string
      }
      sample_size_ok?: boolean
      min_sample_size?: number
      actual_sample_size?: number
      warnings?: string[]
    }
  }
}

export default function MethodChecksDisplay({ methodChecks }: MethodChecksDisplayProps) {
  const checks = methodChecks?.method_checks || {}
  const preTrends = checks.pre_trends || {}
  const controlBalance = checks.control_balance
  const seasonality = checks.seasonality

  const getStatusColor = (status?: string): 'success' | 'warning' | 'error' => {
    if (!status) return 'warning'
    switch (status) {
      case 'PASS':
      case 'LOW':
        return 'success'
      case 'WARN':
      case 'MEDIUM':
        return 'warning'
      case 'FAIL':
      case 'HIGH':
        return 'error'
      default:
        return 'warning'
    }
  }

  const getStatusIcon = (status?: string) => {
    if (!status) return <InfoIcon />
    switch (status) {
      case 'PASS':
      case 'LOW':
        return <CheckIcon color="success" />
      case 'WARN':
      case 'MEDIUM':
        return <WarningIcon color="warning" />
      case 'FAIL':
      case 'HIGH':
        return <ErrorIcon color="error" />
      default:
        return <InfoIcon />
    }
  }

  return (
    <Box>
      {/* Pre-Trends Check */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <Typography variant="h6">Pre-Trends Diagnostic</Typography>
            {preTrends.parallel_trends && (
              <Chip
                icon={getStatusIcon(preTrends.parallel_trends)}
                label={`Parallel Trends: ${preTrends.parallel_trends}`}
                color={getStatusColor(preTrends.parallel_trends)}
                size="small"
              />
            )}
          </Box>

          {preTrends.warning && (
            <Alert severity={getStatusColor(preTrends.parallel_trends)} sx={{ mb: 2 }}>
              {preTrends.warning}
            </Alert>
          )}

          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableBody>
                {preTrends.pre_trend_treatment !== undefined && (
                  <TableRow>
                    <TableCell><strong>Treatment Group Trend (Slope)</strong></TableCell>
                    <TableCell>{preTrends.pre_trend_treatment.toFixed(4)}</TableCell>
                  </TableRow>
                )}
                {preTrends.pre_trend_control !== undefined && (
                  <TableRow>
                    <TableCell><strong>Control Group Trend (Slope)</strong></TableCell>
                    <TableCell>{preTrends.pre_trend_control.toFixed(4)}</TableCell>
                  </TableRow>
                )}
                {preTrends.pre_trend_difference !== undefined && (
                  <TableRow>
                    <TableCell><strong>Difference in Trends</strong></TableCell>
                    <TableCell>{preTrends.pre_trend_difference.toFixed(4)}</TableCell>
                  </TableRow>
                )}
                {preTrends.p_value !== undefined && preTrends.p_value !== null && (
                  <TableRow>
                    <TableCell><strong>P-Value</strong></TableCell>
                    <TableCell>
                      {preTrends.p_value.toFixed(4)}
                      {preTrends.p_value < 0.05 && (
                        <Chip label="Significant" color="error" size="small" sx={{ ml: 1 }} />
                      )}
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>

          {preTrends.parallel_trends === 'PASS' && (
            <Alert severity="success" sx={{ mt: 2 }}>
              Parallel trends assumption is satisfied. Difference-in-Differences method is appropriate.
            </Alert>
          )}
          {(preTrends.parallel_trends === 'WARN' || preTrends.parallel_trends === 'FAIL') && (
            <Alert severity={getStatusColor(preTrends.parallel_trends)} sx={{ mt: 2 }}>
              Parallel trends assumption may be violated. Results should be interpreted with caution.
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Control Balance Check */}
      {controlBalance && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <Typography variant="h6">Control Group Balance</Typography>
              <Chip
                icon={getStatusIcon(controlBalance.balanced ? 'PASS' : 'WARN')}
                label={controlBalance.balanced ? 'Balanced' : 'Imbalanced'}
                color={controlBalance.balanced ? 'success' : 'warning'}
                size="small"
              />
            </Box>

            {controlBalance.warning && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                {controlBalance.warning}
              </Alert>
            )}

            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Balance Score: {(controlBalance.balance_score || 0) * 100}%
              </Typography>
              <LinearProgress
                variant="determinate"
                value={(controlBalance.balance_score || 0) * 100}
                color={controlBalance.balanced ? 'success' : 'warning'}
                sx={{ height: 8, borderRadius: 1 }}
              />
            </Box>

            {controlBalance.imbalanced_covariates && controlBalance.imbalanced_covariates.length > 0 && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                Imbalanced Covariates: {controlBalance.imbalanced_covariates.join(', ')}
              </Alert>
            )}

            {controlBalance.standardized_mean_differences &&
              Object.keys(controlBalance.standardized_mean_differences).length > 0 && (
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell><strong>Covariate</strong></TableCell>
                        <TableCell align="right"><strong>Standardized Mean Difference</strong></TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {Object.entries(controlBalance.standardized_mean_differences).map(([covariate, smd]) => (
                        <TableRow key={covariate}>
                          <TableCell>{covariate}</TableCell>
                          <TableCell align="right">
                            {typeof smd === 'number' ? smd.toFixed(4) : smd}
                            {Math.abs(smd as number) > 0.25 && (
                              <Chip label="Imbalanced" color="warning" size="small" sx={{ ml: 1 }} />
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
          </CardContent>
        </Card>
      )}

      {/* Seasonality Check */}
      {seasonality && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <Typography variant="h6">Seasonality Diagnostic</Typography>
              <Chip
                icon={getStatusIcon(seasonality.seasonality_risk)}
                label={`Risk: ${seasonality.seasonality_risk || 'UNKNOWN'}`}
                color={getStatusColor(seasonality.seasonality_risk)}
                size="small"
              />
            </Box>

            {seasonality.warning && (
              <Alert severity={getStatusColor(seasonality.seasonality_risk)} sx={{ mb: 2 }}>
                {seasonality.warning}
              </Alert>
            )}

            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableBody>
                  <TableRow>
                    <TableCell><strong>Seasonal Pattern Detected</strong></TableCell>
                    <TableCell>
                      {seasonality.seasonal_pattern_detected ? (
                        <Chip label="Yes" color="warning" size="small" />
                      ) : (
                        <Chip label="No" color="success" size="small" />
                      )}
                    </TableCell>
                  </TableRow>
                  {seasonality.seasonal_periods && seasonality.seasonal_periods.length > 0 && (
                    <TableRow>
                      <TableCell><strong>Seasonal Periods (months)</strong></TableCell>
                      <TableCell>{seasonality.seasonal_periods.join(', ')}</TableCell>
                    </TableRow>
                  )}
                  <TableRow>
                    <TableCell><strong>Adjustment Recommended</strong></TableCell>
                    <TableCell>
                      {seasonality.adjustment_recommended ? (
                        <Chip label="Yes" color="warning" size="small" />
                      ) : (
                        <Chip label="No" color="success" size="small" />
                      )}
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* Sample Size Check */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <Typography variant="h6">Sample Size Adequacy</Typography>
            <Chip
              icon={getStatusIcon(checks.sample_size_ok ? 'PASS' : 'WARN')}
              label={checks.sample_size_ok ? 'Adequate' : 'Insufficient'}
              color={checks.sample_size_ok ? 'success' : 'warning'}
              size="small"
            />
          </Box>

          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableBody>
                <TableRow>
                  <TableCell><strong>Actual Sample Size</strong></TableCell>
                  <TableCell>
                    {checks.actual_sample_size?.toLocaleString() || 'N/A'}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><strong>Minimum Required</strong></TableCell>
                  <TableCell>
                    {checks.min_sample_size?.toLocaleString() || 'N/A'}
                  </TableCell>
                </TableRow>
                {checks.actual_sample_size !== undefined && checks.min_sample_size !== undefined && (
                  <TableRow>
                    <TableCell><strong>Ratio</strong></TableCell>
                    <TableCell>
                      {(checks.actual_sample_size / checks.min_sample_size).toFixed(2)}x
                      {checks.sample_size_ok ? (
                        <Chip label="OK" color="success" size="small" sx={{ ml: 1 }} />
                      ) : (
                        <Chip label="Low" color="warning" size="small" sx={{ ml: 1 }} />
                      )}
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Warnings Summary */}
      {checks.warnings && checks.warnings.length > 0 && (
        <Alert severity="warning" sx={{ mt: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            <strong>Method Checks Warnings:</strong>
          </Typography>
          <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
            {checks.warnings.map((warning: string, idx: number) => (
              <li key={idx}>{warning}</li>
            ))}
          </ul>
        </Alert>
      )}
    </Box>
  )
}

