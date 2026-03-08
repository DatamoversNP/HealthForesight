/**
 * Scenario Comparison Component - Side-by-side comparison of multiple scenarios
 */
import { useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Button,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from '@mui/material'
import {
  Delete as DeleteIcon,
  CompareArrows as CompareIcon,
  Add as AddIcon,
} from '@mui/icons-material'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface ScenarioResult {
  scenario_id: string
  scenario_name?: string
  baseline_metrics: {
    utilization_per_1k: number
    allowed_pmpm: number
    paid_pmpm: number
  }
  projected_metrics: {
    utilization_per_1k: number
    allowed_pmpm: number
    paid_pmpm: number
  }
  impact_metrics: {
    utilization_per_1k: number
    allowed_pmpm: number
    paid_pmpm: number
    percent_changes: {
      utilization_per_1k: number
      allowed_pmpm: number
      paid_pmpm: number
    }
  }
  confidence_score: number
}

interface ScenarioComparisonProps {
  scenarios: ScenarioResult[]
  onRemoveScenario?: (scenarioId: string) => void
  onRenameScenario?: (scenarioId: string, name: string) => void
}

export default function ScenarioComparison({ 
  scenarios, 
  onRemoveScenario,
  onRenameScenario 
}: ScenarioComparisonProps) {
  const [renameDialogOpen, setRenameDialogOpen] = useState(false)
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null)
  const [newName, setNewName] = useState('')

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2 }).format(value)
  }

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
  }

  const handleRenameClick = (scenario: ScenarioResult) => {
    setSelectedScenario(scenario.scenario_id)
    setNewName(scenario.scenario_name || scenario.scenario_id)
    setRenameDialogOpen(true)
  }

  const handleRenameConfirm = () => {
    if (selectedScenario && newName.trim()) {
      onRenameScenario?.(selectedScenario, newName.trim())
      setRenameDialogOpen(false)
      setSelectedScenario(null)
      setNewName('')
    }
  }

  // Prepare data for comparison chart
  const comparisonData = scenarios.map((scenario) => ({
    name: scenario.scenario_name || scenario.scenario_id.substring(0, 8),
    'Utilization Change (%)': scenario.impact_metrics.percent_changes.utilization_per_1k,
    'Allowed PMPM Change (%)': scenario.impact_metrics.percent_changes.allowed_pmpm,
    'Paid PMPM Change (%)': scenario.impact_metrics.percent_changes.paid_pmpm,
  }))

  if (scenarios.length === 0) {
    return (
      <Card>
        <CardContent>
          <Typography variant="body1" color="text.secondary" align="center" sx={{ py: 4 }}>
            No scenarios to compare. Run multiple scenarios to enable comparison.
          </Typography>
        </CardContent>
      </Card>
    )
  }

  return (
    <Box>
      {/* Comparison Chart */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Scenario Comparison: Impact Summary
          </Typography>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={comparisonData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis label={{ value: 'Percent Change (%)', angle: -90, position: 'insideLeft' }} />
              <Tooltip formatter={(value: number) => formatPercent(value)} />
              <Legend />
              <Bar dataKey="Utilization Change (%)" fill="#8884d8" name="Utilization per 1k" />
              <Bar dataKey="Allowed PMPM Change (%)" fill="#82ca9d" name="Allowed PMPM" />
              <Bar dataKey="Paid PMPM Change (%)" fill="#ffc658" name="Paid PMPM" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Detailed Comparison Table */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Detailed Comparison
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {scenarios.length} scenario{scenarios.length !== 1 ? 's' : ''}
            </Typography>
          </Box>

          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Scenario</strong></TableCell>
                  <TableCell align="right"><strong>Utilization Change (%)</strong></TableCell>
                  <TableCell align="right"><strong>Allowed PMPM Change (%)</strong></TableCell>
                  <TableCell align="right"><strong>Paid PMPM Change (%)</strong></TableCell>
                  <TableCell align="right"><strong>Baseline Allowed PMPM</strong></TableCell>
                  <TableCell align="right"><strong>Projected Allowed PMPM</strong></TableCell>
                  <TableCell align="right"><strong>Confidence</strong></TableCell>
                  <TableCell><strong>Actions</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {scenarios.map((scenario) => (
                  <TableRow key={scenario.scenario_id} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {scenario.scenario_name || scenario.scenario_id.substring(0, 8)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography
                        variant="body2"
                        color={scenario.impact_metrics.percent_changes.utilization_per_1k < 0 ? 'success.main' : 'error.main'}
                        fontWeight="medium"
                      >
                        {formatPercent(scenario.impact_metrics.percent_changes.utilization_per_1k)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography
                        variant="body2"
                        color={scenario.impact_metrics.percent_changes.allowed_pmpm < 0 ? 'success.main' : 'error.main'}
                        fontWeight="medium"
                      >
                        {formatPercent(scenario.impact_metrics.percent_changes.allowed_pmpm)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography
                        variant="body2"
                        color={scenario.impact_metrics.percent_changes.paid_pmpm < 0 ? 'success.main' : 'error.main'}
                        fontWeight="medium"
                      >
                        {formatPercent(scenario.impact_metrics.percent_changes.paid_pmpm)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2">
                        {formatCurrency(scenario.baseline_metrics.allowed_pmpm)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" fontWeight="medium">
                        {formatCurrency(scenario.projected_metrics.allowed_pmpm)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Chip
                        label={`${scenario.confidence_score.toFixed(0)}%`}
                        color={scenario.confidence_score >= 70 ? 'success' : scenario.confidence_score >= 40 ? 'warning' : 'error'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 0.5 }}>
                        <IconButton
                          size="small"
                          onClick={() => handleRenameClick(scenario)}
                          title="Rename scenario"
                        >
                          <Typography variant="caption">✏️</Typography>
                        </IconButton>
                        {onRemoveScenario && (
                          <IconButton
                            size="small"
                            onClick={() => onRemoveScenario(scenario.scenario_id)}
                            color="error"
                            title="Remove scenario"
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        )}
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Rename Dialog */}
      <Dialog open={renameDialogOpen} onClose={() => setRenameDialogOpen(false)}>
        <DialogTitle>Rename Scenario</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Scenario Name"
            fullWidth
            variant="outlined"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRenameDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleRenameConfirm} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}


