/**
 * Scenario Manager Component - Epic 4
 * Create and manage scenario runs with sensitivity parameters
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
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material'
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  ExpandMore as ExpandMoreIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material'
import { apiClient } from '../../lib/api'
import SensitivityPanel from './SensitivityPanel'

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

interface ScenarioManagerProps {
  policyId?: string
}

export default function ScenarioManager({ policyId }: ScenarioManagerProps) {
  const [scenarios, setScenarios] = useState<ScenarioData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [viewingScenario, setViewingScenario] = useState<ScenarioData | null>(null)
  const [formData, setFormData] = useState({
    scenario_name: '',
    parameters: {} as Record<string, number>,
    sensitivity_parameters: [] as Array<{
      parameter_name: string
      base_value: number
      min_value: number
      max_value: number
      step_size?: number
    }>,
  })
  const [currentParam, setCurrentParam] = useState({
    parameter_name: '',
    base_value: 0,
    min_value: 0,
    max_value: 0,
    step_size: 0.1,
  })

  useEffect(() => {
    loadScenarios()
  }, [])

  const loadScenarios = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.getScenarios()
      setScenarios(Array.isArray(data) ? data : [])
    } catch (err: any) {
      console.error('Failed to load scenarios:', err)
      setError(err.detail || err.message || 'Failed to load scenarios')
    } finally {
      setLoading(false)
    }
  }

  const handleOpenDialog = () => {
    setFormData({
      scenario_name: '',
      parameters: {},
      sensitivity_parameters: [],
    })
    setCurrentParam({
      parameter_name: '',
      base_value: 0,
      min_value: 0,
      max_value: 0,
      step_size: 0.1,
    })
    setDialogOpen(true)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
  }

  const handleAddSensitivityParam = () => {
    if (!currentParam.parameter_name.trim()) {
      setError('Parameter name is required')
      return
    }
    if (currentParam.min_value >= currentParam.max_value) {
      setError('Min value must be less than max value')
      return
    }

    setFormData({
      ...formData,
      sensitivity_parameters: [
        ...formData.sensitivity_parameters,
        {
          parameter_name: currentParam.parameter_name.trim(),
          base_value: Number(currentParam.base_value),
          min_value: Number(currentParam.min_value),
          max_value: Number(currentParam.max_value),
          step_size: currentParam.step_size ? Number(currentParam.step_size) : undefined,
        },
      ],
    })
    setCurrentParam({
      parameter_name: '',
      base_value: 0,
      min_value: 0,
      max_value: 0,
      step_size: 0.1,
    })
    setError(null)
  }

  const handleRemoveSensitivityParam = (index: number) => {
    setFormData({
      ...formData,
      sensitivity_parameters: formData.sensitivity_parameters.filter((_, i) => i !== index),
    })
  }

  const handleSubmit = async () => {
    try {
      setError(null)

      if (!formData.scenario_name.trim()) {
        setError('Scenario name is required')
        return
      }

      if (formData.sensitivity_parameters.length === 0) {
        setError('At least one sensitivity parameter is required')
        return
      }

      const scenarioData: any = {
        scenario_name: formData.scenario_name.trim(),
        parameters: formData.parameters,
        sensitivity_parameters: formData.sensitivity_parameters,
        results: {}, // Will be populated by backend
      }

      await apiClient.createScenario(scenarioData)
      handleCloseDialog()
      await loadScenarios()
    } catch (err: any) {
      console.error('Failed to create scenario:', err)
      setError(err.detail || err.message || 'Failed to create scenario')
    }
  }

  const handleView = (scenario: ScenarioData) => {
    setViewingScenario(scenario)
  }

  const handleDelete = async (scenarioId: string) => {
    if (!confirm('Are you sure you want to delete this scenario?')) {
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
              Scenario Runs
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleOpenDialog}
            >
              Create Scenario
            </Button>
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {scenarios.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No scenarios created yet. Click "Create Scenario" to add one.
            </Typography>
          ) : (
            <List>
              {scenarios.map((scenario) => (
                <ListItem
                  key={scenario.scenario_id}
                  secondaryAction={
                    <Box>
                      <IconButton
                        edge="end"
                        onClick={() => handleView(scenario)}
                        sx={{ mr: 1 }}
                      >
                        <ViewIcon />
                      </IconButton>
                      <IconButton
                        edge="end"
                        onClick={() => handleDelete(scenario.scenario_id)}
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Box>
                  }
                >
                  <ListItemText
                    primary={scenario.scenario_name}
                    secondary={
                      <Box>
                        <Typography variant="caption" component="span" sx={{ mr: 2 }}>
                          {scenario.sensitivity_parameters?.length || 0} sensitivity parameters
                        </Typography>
                        <Chip
                          label={`${Object.keys(scenario.results || {}).length} results`}
                          size="small"
                          sx={{ mr: 1 }}
                        />
                        <Typography variant="caption" color="text.secondary">
                          {new Date(scenario.created_at).toLocaleString()}
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

      {/* Create Scenario Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>Create Scenario Run</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Scenario Name"
                value={formData.scenario_name}
                onChange={(e) => setFormData({ ...formData, scenario_name: e.target.value })}
                required
                placeholder="e.g., Base Case, Optimistic, Pessimistic"
              />
            </Grid>
            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom>
                Sensitivity Parameters
              </Typography>
            </Grid>
            <Grid item xs={12}>
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography>Add Sensitivity Parameter</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Parameter Name"
                        value={currentParam.parameter_name}
                        onChange={(e) => setCurrentParam({ ...currentParam, parameter_name: e.target.value })}
                        placeholder="e.g., Utilization Rate, Cost per Unit"
                      />
                    </Grid>
                    <Grid item xs={4}>
                      <TextField
                        fullWidth
                        type="number"
                        label="Base Value"
                        value={currentParam.base_value}
                        onChange={(e) => setCurrentParam({ ...currentParam, base_value: parseFloat(e.target.value) || 0 })}
                      />
                    </Grid>
                    <Grid item xs={4}>
                      <TextField
                        fullWidth
                        type="number"
                        label="Min Value"
                        value={currentParam.min_value}
                        onChange={(e) => setCurrentParam({ ...currentParam, min_value: parseFloat(e.target.value) || 0 })}
                      />
                    </Grid>
                    <Grid item xs={4}>
                      <TextField
                        fullWidth
                        type="number"
                        label="Max Value"
                        value={currentParam.max_value}
                        onChange={(e) => setCurrentParam({ ...currentParam, max_value: parseFloat(e.target.value) || 0 })}
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <Button
                        variant="outlined"
                        onClick={handleAddSensitivityParam}
                        disabled={!currentParam.parameter_name.trim()}
                      >
                        Add Parameter
                      </Button>
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>
            </Grid>
            {formData.sensitivity_parameters.length > 0 && (
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>
                  Added Parameters ({formData.sensitivity_parameters.length})
                </Typography>
                <List dense>
                  {formData.sensitivity_parameters.map((param, idx) => (
                    <ListItem
                      key={idx}
                      secondaryAction={
                        <IconButton
                          edge="end"
                          onClick={() => handleRemoveSensitivityParam(idx)}
                          size="small"
                        >
                          <DeleteIcon />
                        </IconButton>
                      }
                    >
                      <ListItemText
                        primary={param.parameter_name}
                        secondary={`Base: ${param.base_value}, Range: [${param.min_value}, ${param.max_value}]`}
                      />
                    </ListItem>
                  ))}
                </List>
              </Grid>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained" disabled={formData.sensitivity_parameters.length === 0}>
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {/* View Scenario Dialog */}
      <Dialog
        open={!!viewingScenario}
        onClose={() => setViewingScenario(null)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          {viewingScenario?.scenario_name}
        </DialogTitle>
        <DialogContent>
          {viewingScenario && (
            <SensitivityPanel scenario={viewingScenario} />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewingScenario(null)}>Close</Button>
        </DialogActions>
      </Dialog>
    </>
  )
}

