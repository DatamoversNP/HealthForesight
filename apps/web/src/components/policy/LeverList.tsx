/**
 * Lever List Component
 * Supports adding multiple levers for composite policies
 */
import { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Alert,
  Tooltip,
} from '@mui/material'
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Info as InfoIcon,
} from '@mui/icons-material'
import { apiClient } from '../../lib/api'
import { healthForesightColors } from '../../theme/healthForesightTheme'

interface LeverParameter {
  name: string
  value: any
}

interface PolicyLever {
  lever_id?: string
  lever_type: string
  name: string
  parameters: Record<string, any>
  conditions?: any
  exceptions?: any
  enabled?: boolean
  priority?: number
  notes?: string
}

interface LeverListProps {
  levers: PolicyLever[]
  onChange: (levers: PolicyLever[]) => void
}

export default function LeverList({ levers, onChange }: LeverListProps) {
  const [policyTypes, setPolicyTypes] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingIndex, setEditingIndex] = useState<number | null>(null)
  const [currentLever, setCurrentLever] = useState<Partial<PolicyLever>>({
    lever_type: '',
    name: '',
    parameters: {},
    enabled: true,
    priority: 0,
  })

  useEffect(() => {
    loadPolicyTypes()
  }, [])

  const loadPolicyTypes = async () => {
    try {
      setLoading(true)
      const types = await apiClient.getPolicyTypes()
      setPolicyTypes(types)
    } catch (err: any) {
      console.error('Error loading policy types:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleAddLever = () => {
    setEditingIndex(null)
    setCurrentLever({
      lever_type: '',
      name: '',
      parameters: {},
      enabled: true,
      priority: levers.length,
    })
    setDialogOpen(true)
  }

  const handleEditLever = (index: number) => {
    setEditingIndex(index)
    setCurrentLever({ ...levers[index] })
    setDialogOpen(true)
  }

  const handleDeleteLever = (index: number) => {
    const newLevers = levers.filter((_, i) => i !== index)
    // Reorder priorities
    newLevers.forEach((lever, i) => {
      lever.priority = i
    })
    onChange(newLevers)
  }

  const handleSaveLever = () => {
    if (!currentLever.lever_type || !currentLever.name) {
      return
    }

    // Get metadata for this lever type to validate parameters
    const metadata = policyTypes.find((t) => t.lever_type === currentLever.lever_type)
    if (metadata) {
      // Ensure required parameters are present
      for (const param of metadata.supported_parameters || []) {
        if (param.required && !(param.name in (currentLever.parameters || {}))) {
          // Set default value if available
          if (param.default_value !== undefined) {
            currentLever.parameters = {
              ...currentLever.parameters,
              [param.name]: param.default_value,
            }
          }
        }
      }
    }

    const newLever: PolicyLever = {
      lever_type: currentLever.lever_type!,
      name: currentLever.name!,
      parameters: currentLever.parameters || {},
      enabled: currentLever.enabled !== false,
      priority: currentLever.priority ?? levers.length,
      notes: currentLever.notes,
    }

    if (editingIndex !== null) {
      // Update existing lever
      const newLevers = [...levers]
      newLevers[editingIndex] = newLever
      onChange(newLevers)
    } else {
      // Add new lever
      onChange([...levers, newLever])
    }

    setDialogOpen(false)
    setCurrentLever({ lever_type: '', name: '', parameters: {} })
  }

  const handleParameterChange = (paramName: string, value: any) => {
    setCurrentLever({
      ...currentLever,
      parameters: {
        ...(currentLever.parameters || {}),
        [paramName]: value,
      },
    })
  }

  const getLeverMetadata = (leverType: string) => {
    return policyTypes.find((t) => t.lever_type === leverType)
  }

  const renderParameterField = (param: any) => {
    const value = currentLever.parameters?.[param.name] ?? param.default_value

    switch (param.type) {
      case 'string':
        return (
          <TextField
            key={param.name}
            label={param.name}
            value={value || ''}
            onChange={(e) => handleParameterChange(param.name, e.target.value)}
            fullWidth
            required={param.required}
            helperText={param.description}
            size="small"
          />
        )
      case 'number':
        return (
          <TextField
            key={param.name}
            label={param.name}
            type="number"
            value={value || ''}
            onChange={(e) => handleParameterChange(param.name, parseFloat(e.target.value) || 0)}
            fullWidth
            required={param.required}
            helperText={param.description}
            size="small"
          />
        )
      case 'boolean':
        return (
          <FormControl key={param.name} fullWidth size="small">
            <InputLabel>{param.name}</InputLabel>
            <Select
              value={value ?? param.default_value ?? false}
              onChange={(e) => handleParameterChange(param.name, e.target.value)}
              label={param.name}
            >
              <MenuItem value={true}>True</MenuItem>
              <MenuItem value={false}>False</MenuItem>
            </Select>
          </FormControl>
        )
      case 'array':
        return (
          <TextField
            key={param.name}
            label={param.name}
            value={Array.isArray(value) ? value.join(', ') : value || ''}
            onChange={(e) => {
              const arrayValue = e.target.value.split(',').map((v) => v.trim()).filter(Boolean)
              handleParameterChange(param.name, arrayValue)
            }}
            fullWidth
            required={param.required}
            helperText={`${param.description} (comma-separated)`}
            size="small"
          />
        )
      default:
        return (
          <TextField
            key={param.name}
            label={param.name}
            value={value || ''}
            onChange={(e) => handleParameterChange(param.name, e.target.value)}
            fullWidth
            required={param.required}
            helperText={param.description}
            size="small"
          />
        )
    }
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" sx={{ fontWeight: 600, color: healthForesightColors.neutral.dark }}>
          Policy Levers
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleAddLever}
          sx={{ bgcolor: healthForesightColors.primary.main }}
        >
          Add Lever
        </Button>
      </Box>

      {levers.length === 0 ? (
        <Alert severity="info" sx={{ mb: 2 }}>
          No levers defined. Add at least one lever to create a policy.
          <br />
          <strong>Standalone Policy:</strong> Add 1 lever
          <br />
          <strong>Composite Policy:</strong> Add multiple levers
        </Alert>
      ) : (
        <Grid container spacing={2}>
          {levers.map((lever, index) => {
            const metadata = getLeverMetadata(lever.lever_type)
            return (
              <Grid item xs={12} md={6} key={index}>
                <Card
                  sx={{
                    border: `1px solid ${healthForesightColors.neutral.light}`,
                    '&:hover': {
                      boxShadow: 2,
                    },
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 1 }}>
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 0.5 }}>
                          {lever.name}
                        </Typography>
                        <Chip
                          label={metadata?.display_name || lever.lever_type}
                          size="small"
                          color="primary"
                          sx={{ mr: 1 }}
                        />
                        {lever.enabled === false && (
                          <Chip label="Disabled" size="small" color="default" />
                        )}
                      </Box>
                      <Box>
                        <Tooltip title="Edit">
                          <IconButton size="small" onClick={() => handleEditLever(index)}>
                            <EditIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete">
                          <IconButton size="small" onClick={() => handleDeleteLever(index)} color="error">
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </Box>
                    {metadata?.help_text && (
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 1, fontStyle: 'italic' }}>
                        {metadata.help_text}
                      </Typography>
                    )}
                    {lever.notes && (
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        {lever.notes}
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            )
          })}
        </Grid>
      )}

      {/* Add/Edit Lever Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingIndex !== null ? 'Edit Lever' : 'Add Lever'}
        </DialogTitle>
        <DialogContent dividers>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
            <FormControl fullWidth required>
              <InputLabel>Lever Type</InputLabel>
              <Select
                value={currentLever.lever_type || ''}
                onChange={(e) => {
                  const selectedType = e.target.value
                  const metadata = policyTypes.find((t) => t.lever_type === selectedType)
                  setCurrentLever({
                    ...currentLever,
                    lever_type: selectedType,
                    name: metadata?.display_name || selectedType,
                    parameters: {},
                  })
                }}
                label="Lever Type"
              >
                {policyTypes.map((type) => (
                  <MenuItem key={type.lever_type} value={type.lever_type}>
                    {type.display_name} ({type.category})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <TextField
              label="Lever Name"
              value={currentLever.name || ''}
              onChange={(e) => setCurrentLever({ ...currentLever, name: e.target.value })}
              fullWidth
              required
              helperText="Descriptive name for this lever"
            />

            {currentLever.lever_type && (
              <>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mt: 1 }}>
                  Parameters
                </Typography>
                {(() => {
                  const metadata = getLeverMetadata(currentLever.lever_type)
                  if (metadata?.supported_parameters) {
                    return (
                      <Grid container spacing={2}>
                        {metadata.supported_parameters.map((param: any) => (
                          <Grid item xs={12} sm={6} key={param.name}>
                            {renderParameterField(param)}
                          </Grid>
                        ))}
                      </Grid>
                    )
                  }
                  return null
                })()}
              </>
            )}

            <TextField
              label="Notes (Optional)"
              value={currentLever.notes || ''}
              onChange={(e) => setCurrentLever({ ...currentLever, notes: e.target.value })}
              fullWidth
              multiline
              rows={2}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleSaveLever}
            variant="contained"
            disabled={!currentLever.lever_type || !currentLever.name}
          >
            {editingIndex !== null ? 'Update' : 'Add'} Lever
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
