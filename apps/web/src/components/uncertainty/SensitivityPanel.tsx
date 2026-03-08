/**
 * Sensitivity Panel Component - Epic 4
 * Displays sensitivity analysis results showing which parameters drive uncertainty
 */
import { useState, useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  LinearProgress,
  Alert,
  CircularProgress,
} from '@mui/material'
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Remove as NeutralIcon,
} from '@mui/icons-material'
import { apiClient } from '../../lib/api'

interface SensitivityParameter {
  parameter_name: string
  base_value: number
  min_value: number
  max_value: number
  step_size?: number
}

interface ScenarioData {
  scenario_id: string
  scenario_name: string
  parameters: Record<string, number>
  sensitivity_parameters: SensitivityParameter[]
  results: Record<string, any>
  created_at: string
}

interface SensitivityPanelProps {
  policyId?: string
  scenarioId?: string
  scenario?: ScenarioData
}

export default function SensitivityPanel({ policyId, scenarioId, scenario: providedScenario }: SensitivityPanelProps) {
  const [scenario, setScenario] = useState<ScenarioData | null>(providedScenario || null)
  const [loading, setLoading] = useState(!providedScenario)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (scenarioId && !providedScenario) {
      loadScenario()
    }
  }, [scenarioId])

  const loadScenario = async () => {
    if (!scenarioId) return
    
    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.getScenario(scenarioId)
      setScenario(data)
    } catch (err: any) {
      console.error('Failed to load scenario:', err)
      setError(err.detail || err.message || 'Failed to load scenario')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    )
  }

  if (!scenario || !scenario.sensitivity_parameters || scenario.sensitivity_parameters.length === 0) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Sensitivity Analysis
          </Typography>
          <Typography variant="body2" color="text.secondary">
            No sensitivity analysis data available.
            {scenarioId && ' Create a scenario with sensitivity parameters to see results here.'}
          </Typography>
        </CardContent>
      </Card>
    )
  }

  // Calculate impact range for each parameter
  const sensitivityData = scenario.sensitivity_parameters.map((param) => {
    const range = param.max_value - param.min_value
    const rangePercent = param.base_value !== 0 
      ? (range / Math.abs(param.base_value)) * 100 
      : 0
    
    return {
      ...param,
      range,
      rangePercent: Math.abs(rangePercent),
      impact: rangePercent > 20 ? 'high' : rangePercent > 10 ? 'medium' : 'low',
    }
  }).sort((a, b) => b.rangePercent - a.rangePercent) // Sort by impact

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Sensitivity Analysis
        </Typography>
        {scenario.scenario_name && (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Scenario: {scenario.scenario_name}
          </Typography>
        )}

        <TableContainer component={Paper} variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell><strong>Parameter</strong></TableCell>
                <TableCell align="right"><strong>Base Value</strong></TableCell>
                <TableCell align="right"><strong>Range</strong></TableCell>
                <TableCell align="right"><strong>Impact</strong></TableCell>
                <TableCell align="center"><strong>Uncertainty Driver</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {sensitivityData.map((param, idx) => (
                <TableRow key={param.parameter_name} hover>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {param.parameter_name}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    {param.base_value.toLocaleString(undefined, {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </TableCell>
                  <TableCell align="right">
                    <Typography variant="body2">
                      [{param.min_value.toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}, {param.max_value.toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}]
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      ±{param.rangePercent.toFixed(1)}%
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Box sx={{ width: 100, display: 'inline-block' }}>
                      <LinearProgress
                        variant="determinate"
                        value={Math.min(param.rangePercent, 100)}
                        color={param.impact === 'high' ? 'error' : param.impact === 'medium' ? 'warning' : 'info'}
                        sx={{ height: 8, borderRadius: 1 }}
                      />
                    </Box>
                  </TableCell>
                  <TableCell align="center">
                    {idx < 3 ? (
                      <Chip
                        label={`Top ${idx + 1}`}
                        size="small"
                        color={idx === 0 ? 'error' : idx === 1 ? 'warning' : 'info'}
                        icon={idx === 0 ? <TrendingUpIcon /> : idx === 1 ? <TrendingDownIcon /> : <NeutralIcon />}
                      />
                    ) : (
                      <Typography variant="caption" color="text.secondary">
                        -
                      </Typography>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        <Box sx={{ mt: 2 }}>
          <Typography variant="caption" color="text.secondary">
            <strong>Top 3 uncertainty drivers</strong> are highlighted. Parameters with larger ranges relative to base values contribute more to overall uncertainty.
          </Typography>
        </Box>
      </CardContent>
    </Card>
  )
}

