/**
 * Trust Panel Component - Shows confidence, methodology, and limitations
 */
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Alert,
} from '@mui/material'
import {
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material'
import { healthForesightColors } from '../theme/healthForesightTheme'
import ConfidenceBadge from './brand/ConfidenceBadge'

interface TrustPanelProps {
  confidenceScore?: number  // Legacy support
  confidence_score?: {  // New structure
    overall_score: number
    category: 'HIGH' | 'MEDIUM' | 'LOW'
    components?: {
      method_confidence?: number
      data_quality_score?: number
      sample_size_score?: number
      control_group_score?: number
      methodology_score?: number
    }
  }
  data_sufficiency?: {  // New structure
    sufficient: boolean
    min_sample_size: number
    actual_sample_size: number
    data_window_months: number
    coverage_score: number
    missing_data_flags?: string[]
  }
  dataCoverage?: {  // Legacy support
    claimMonths?: number
    claimLines?: number
    members?: number
    providers?: number
  }
  validation_checks?: Array<{  // New structure
    check_name: string
    passed: boolean
    message?: string
    severity: 'INFO' | 'WARNING' | 'ERROR'
  }>
  checks?: Array<{  // Legacy support
    name: string
    status: 'PASS' | 'WARN' | 'FAIL'
    message?: string
  }>
  methodology?: {
    method?: string
    pre_months?: number
    post_months?: number
    has_control_group?: boolean
    metric?: string
  }
  limitations?: string[]
  data_used?: {
    data_window_months?: number
    sample_size?: number
    treatment_filters?: any
    control_filters?: any
  }
  modelVersion?: string
  model_version?: string
  runTimestamp?: string
}

export default function TrustPanel({
  confidenceScore,
  confidence_score,
  data_sufficiency,
  dataCoverage,
  validation_checks,
  checks = [],
  methodology,
  limitations = [],
  data_used,
  modelVersion,
  model_version,
  runTimestamp,
}: TrustPanelProps) {
  // Support both new and legacy structures
  const overallScore = confidence_score?.overall_score ?? confidenceScore ?? 0
  const confidenceCategory = confidence_score?.category ?? (overallScore >= 70 ? 'HIGH' : overallScore >= 40 ? 'MEDIUM' : 'LOW')
  const method = methodology?.method ?? 'pre_post'
  
  const getConfidenceColor = (score: number): 'success' | 'warning' | 'error' => {
    if (score >= 70) return 'success'
    if (score >= 40) return 'warning'
    return 'error'
  }

  const getConfidenceLabel = (score: number): string => {
    if (score >= 70) return 'High'
    if (score >= 40) return 'Medium'
    return 'Low'
  }
  
  const getSeverityColor = (severity: string): 'success' | 'warning' | 'error' | 'info' => {
    switch (severity) {
      case 'ERROR':
        return 'error'
      case 'WARNING':
        return 'warning'
      case 'PASS':
      case 'INFO':
        return 'info'
      default:
        return 'info'
    }
  }

  const getCheckIcon = (status: string) => {
    switch (status) {
      case 'PASS':
        return <CheckIcon color="success" fontSize="small" />
      case 'WARN':
        return <WarningIcon color="warning" fontSize="small" />
      case 'FAIL':
        return <ErrorIcon color="error" fontSize="small" />
      default:
        return <InfoIcon fontSize="small" />
    }
  }

  return (
    <Card
      sx={{
        borderColor: healthForesightColors.neutral.light,
        backgroundColor: '#FFFFFF',
      }}
    >
      <CardContent>
        <Typography
          variant="h6"
          gutterBottom
          sx={{
            fontFamily: 'IBM Plex Sans, Inter, sans-serif',
            fontWeight: 600,
            color: healthForesightColors.neutral.dark,
          }}
        >
          Trust Panel
        </Typography>
        <Typography
          variant="caption"
          sx={{
            color: healthForesightColors.neutral.mid,
            display: 'block',
            mb: 2,
          }}
        >
          Confidence, methodology, and limitations for this analysis
        </Typography>

        {/* Confidence Score - HealthForesight Style */}
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
            <Typography
              variant="body2"
              sx={{
                fontWeight: 600,
                color: healthForesightColors.neutral.dark,
              }}
            >
              Confidence Score:
            </Typography>
            <ConfidenceBadge score={overallScore / 100} />
          </Box>
          {confidence_score?.components && (
            <Box sx={{ mt: 1.5, display: 'flex', flexDirection: 'column', gap: 1 }}>
              {confidence_score.components.method_confidence !== undefined && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="caption" sx={{ color: healthForesightColors.neutral.mid, minWidth: 100 }}>
                    Method:
                  </Typography>
                  <ConfidenceBadge score={confidence_score.components.method_confidence / 100} size="small" />
                </Box>
              )}
              {confidence_score.components.data_quality_score !== undefined && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="caption" sx={{ color: healthForesightColors.neutral.mid, minWidth: 100 }}>
                    Data Quality:
                  </Typography>
                  <ConfidenceBadge score={confidence_score.components.data_quality_score / 100} size="small" />
                </Box>
              )}
              {confidence_score.components.sample_size_score !== undefined && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="caption" sx={{ color: healthForesightColors.neutral.mid, minWidth: 100 }}>
                    Sample Size:
                  </Typography>
                  <ConfidenceBadge score={confidence_score.components.sample_size_score / 100} size="small" />
                </Box>
              )}
            </Box>
          )}
          {/* Subtle progress bar */}
          <Box
            sx={{
              width: '100%',
              height: 6,
              bgcolor: healthForesightColors.neutral.light,
              borderRadius: 1,
              overflow: 'hidden',
              mt: 1.5,
            }}
          >
            <Box
              sx={{
                width: `${Math.min(100, Math.max(0, overallScore))}%`,
                height: '100%',
                bgcolor:
                  getConfidenceColor(overallScore) === 'success'
                    ? healthForesightColors.semantic.positive
                    : getConfidenceColor(overallScore) === 'warning'
                    ? healthForesightColors.semantic.warning
                    : healthForesightColors.semantic.risk,
                transition: 'width 200ms cubic-bezier(0.4, 0, 0.2, 1)',
              }}
            />
          </Box>
        </Box>

        {/* Methodology */}
        {method && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" fontWeight="medium" gutterBottom>
              Method:
            </Typography>
            <Chip label={method} size="small" />
          </Box>
        )}

        {/* Data Sufficiency / Data Coverage */}
        {(data_sufficiency || dataCoverage || data_used) && (
          <Box sx={{ mb: 2 }}>
            <Typography
              variant="body2"
              sx={{
                fontWeight: 600,
                mb: 1,
                color: healthForesightColors.neutral.dark,
              }}
              gutterBottom
            >
              Data Coverage:
            </Typography>
            {data_sufficiency && (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, mb: 1 }}>
                <Chip
                  label={data_sufficiency.sufficient ? 'Sufficient' : 'Insufficient'}
                  color={data_sufficiency.sufficient ? 'success' : 'warning'}
                  size="small"
                  sx={{ alignSelf: 'flex-start' }}
                />
                <Typography variant="caption" sx={{ color: healthForesightColors.neutral.mid }}>
                  Sample Size: {data_sufficiency.actual_sample_size.toLocaleString()} / {data_sufficiency.min_sample_size.toLocaleString()} (required)
                </Typography>
                <Typography variant="caption" sx={{ color: healthForesightColors.neutral.mid }}>
                  Data Window: {data_sufficiency.data_window_months} months
                </Typography>
                <Typography variant="caption" sx={{ color: healthForesightColors.neutral.mid }}>
                  Coverage: {(data_sufficiency.coverage_score * 100).toFixed(0)}%
                </Typography>
                {data_sufficiency.missing_data_flags && data_sufficiency.missing_data_flags.length > 0 && (
                  <Alert severity="warning" sx={{ mt: 1 }}>
                    Missing Data: {data_sufficiency.missing_data_flags.join(', ')}
                  </Alert>
                )}
              </Box>
            )}
            {(dataCoverage || data_used) && (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {(data_used?.data_window_months || dataCoverage?.claimMonths) && (
                  <Chip label={`${(data_used?.data_window_months || dataCoverage?.claimMonths)} months`} size="small" variant="outlined" />
                )}
                {(data_used?.sample_size || dataCoverage?.claimLines) && (
                  <Chip label={`${(data_used?.sample_size || dataCoverage?.claimLines)?.toLocaleString()} claims`} size="small" variant="outlined" />
                )}
                {dataCoverage?.members && (
                  <Chip label={`${dataCoverage.members.toLocaleString()} members`} size="small" variant="outlined" />
                )}
                {dataCoverage?.providers && (
                  <Chip label={`${dataCoverage.providers.toLocaleString()} providers`} size="small" variant="outlined" />
                )}
              </Box>
            )}
          </Box>
        )}

        <Divider sx={{ my: 2 }} />

        {/* Validation Checks */}
        {((validation_checks && validation_checks.length > 0) || checks.length > 0) && (
          <Box sx={{ mb: 2 }}>
            <Typography
              variant="body2"
              sx={{
                fontWeight: 600,
                mb: 1,
                color: healthForesightColors.neutral.dark,
              }}
              gutterBottom
            >
              Validation Checks:
            </Typography>
            <List dense>
              {validation_checks && validation_checks.map((check, index) => (
                <ListItem key={index} sx={{ py: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 32 }}>
                    {check.passed ? (
                      <CheckIcon color="success" fontSize="small" />
                    ) : check.severity === 'ERROR' ? (
                      <ErrorIcon color="error" fontSize="small" />
                    ) : check.severity === 'WARNING' ? (
                      <WarningIcon color="warning" fontSize="small" />
                    ) : (
                      <InfoIcon fontSize="small" />
                    )}
                  </ListItemIcon>
                  <ListItemText
                    primary={check.check_name}
                    secondary={check.message}
                    primaryTypographyProps={{ variant: 'body2' }}
                    secondaryTypographyProps={{ variant: 'caption' }}
                  />
                </ListItem>
              ))}
              {!validation_checks && checks.map((check, index) => (
                <ListItem key={index} sx={{ py: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 32 }}>
                    {getCheckIcon(check.status)}
                  </ListItemIcon>
                  <ListItemText
                    primary={check.name}
                    secondary={check.message}
                    primaryTypographyProps={{ variant: 'body2' }}
                    secondaryTypographyProps={{ variant: 'caption' }}
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        {/* Limitations */}
        {limitations.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography
              variant="body2"
              sx={{
                fontWeight: 600,
                mb: 1,
                color: healthForesightColors.neutral.dark,
              }}
              gutterBottom
            >
              Limitations:
            </Typography>
            <List dense>
              {limitations.map((limitation, index) => (
                <ListItem key={index} sx={{ py: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 32 }}>
                    <InfoIcon fontSize="small" color="action" />
                  </ListItemIcon>
                  <ListItemText
                    primary={limitation}
                    primaryTypographyProps={{ variant: 'body2' }}
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        {/* Metadata */}
        {((modelVersion || model_version) || runTimestamp || methodology) && (
          <>
            <Divider sx={{ my: 2 }} />
            <Box>
              {(modelVersion || model_version) && (
                <Typography variant="caption" sx={{ color: healthForesightColors.neutral.mid }} display="block">
                  Model Version: {modelVersion || model_version}
                </Typography>
              )}
              {runTimestamp && (
                <Typography variant="caption" sx={{ color: healthForesightColors.neutral.mid }} display="block">
                  Run: {new Date(runTimestamp).toLocaleString()}
                </Typography>
              )}
              {methodology && (
                <Box sx={{ mt: 1 }}>
                  <Typography variant="caption" sx={{ color: healthForesightColors.neutral.mid }} display="block">
                    Pre Window: {methodology.pre_months || 6} months
                  </Typography>
                  <Typography variant="caption" sx={{ color: healthForesightColors.neutral.mid }} display="block">
                    Post Window: {methodology.post_months || 6} months
                  </Typography>
                  {methodology.has_control_group !== undefined && (
                    <Typography variant="caption" sx={{ color: healthForesightColors.neutral.mid }} display="block">
                      Control Group: {methodology.has_control_group ? 'Yes' : 'No'}
                    </Typography>
                  )}
                  {methodology.metric && (
                    <Typography variant="caption" sx={{ color: healthForesightColors.neutral.mid }} display="block">
                      Metric: {methodology.metric}
                    </Typography>
                  )}
                </Box>
              )}
            </Box>
          </>
        )}

        {/* Low Confidence Warning */}
        {overallScore < 40 && (
          <Alert severity="warning" sx={{ mt: 2 }}>
            Low confidence score. Results should be interpreted with caution.
          </Alert>
        )}
      </CardContent>
    </Card>
  )
}

