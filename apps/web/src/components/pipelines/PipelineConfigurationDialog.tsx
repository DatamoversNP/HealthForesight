/**
 * Pipeline Configuration Dialog
 * UI for configuring pipeline metadata, field mappings, and ingestion settings
 */
import { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  TextField,
  Typography,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Switch,
  FormControlLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
} from '@mui/material'
import {
  ExpandMore as ExpandMoreIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
} from '@mui/icons-material'
import { apiClient } from '../../lib/api'

interface Pipeline {
  pipeline_id?: string
  pipeline_name: string
  pipeline_description?: string
  source_type: string
  target_dataset_type: string
  target_model: string
  field_mappings: FieldMapping[]
  mode: string
  deduplication: DeduplicationConfig
  control_fields: ControlFields
  required_fields: string[]
  active?: boolean
}

interface FieldMapping {
  source_field: string
  target_field: string
  transform_function?: string
  default_value?: any
  required: boolean
}

interface DeduplicationConfig {
  strategy: string
  key_fields?: string[]
  source_id_field?: string
}

interface ControlFields {
  created_at?: string
  updated_at?: string
  active_flag?: boolean
  effective_date?: string
  expiration_date?: string
}

interface PipelineConfigurationDialogProps {
  open: boolean
  onClose: () => void
  onSave: () => void
  pipeline?: Pipeline | null
  isEditing?: boolean
}

const SOURCE_TYPES = ['CSV', 'PARQUET', 'JSON', 'EXCEL', 'API']
const TARGET_DATASET_TYPES = [
  'CLAIMS_LINES',
  'MEMBER_MASTER',
  'ELIGIBILITY_ENROLLMENT',
  'PROVIDER_MASTER',
  'PHARMACY_CLAIMS',
  'RISK_STRATIFICATION',
  'MARKET_EVENT', // Add MARKET_EVENT to supported types
]
const TARGET_MODELS = [
  'ClaimLine',
  'MemberMaster',
  'EligibilityEnrollment',
  'ProviderMaster',
  'PharmacyClaim',
  'MemberRiskStratification',
  'MarketEvent', // Add MarketEvent to supported models
]
const PIPELINE_MODES = ['APPEND', 'REPLACE', 'UPSERT']
const DEDUP_STRATEGIES = ['NONE', 'HASH', 'KEY_FIELDS', 'SOURCE_ID']
const TRANSFORM_FUNCTIONS = [
  '',
  'to_date',
  'to_datetime',
  'to_float',
  'to_int',
  'to_bool',
  'normalize_string',
  'lowercase',
  'uppercase',
]

export default function PipelineConfigurationDialog({
  open,
  onClose,
  onSave,
  pipeline,
  isEditing = false,
}: PipelineConfigurationDialogProps) {
  const [formData, setFormData] = useState<Pipeline>({
    pipeline_name: '',
    pipeline_description: '',
    source_type: 'CSV',
    target_dataset_type: 'CLAIMS_LINES',
    target_model: 'ClaimLine',
    field_mappings: [],
    mode: 'APPEND',
    deduplication: { strategy: 'HASH' },
    control_fields: {
      created_at: 'CURRENT_TIMESTAMP',
      updated_at: 'CURRENT_TIMESTAMP',
      active_flag: true,
    },
    required_fields: [],
    active: true,
  })

  const [newMapping, setNewMapping] = useState<FieldMapping>({
    source_field: '',
    target_field: '',
    transform_function: '',
    default_value: '',
    required: false,
  })

  const [editingMappingIndex, setEditingMappingIndex] = useState<number | null>(null)

  useEffect(() => {
    if (pipeline) {
      setFormData(pipeline)
    } else {
      // Reset form
      setFormData({
        pipeline_name: '',
        pipeline_description: '',
        source_type: 'CSV',
        target_dataset_type: 'CLAIMS_LINES',
        target_model: 'ClaimLine',
        field_mappings: [],
        mode: 'APPEND',
        deduplication: { strategy: 'HASH' },
        control_fields: {
          created_at: 'CURRENT_TIMESTAMP',
          updated_at: 'CURRENT_TIMESTAMP',
          active_flag: true,
        },
        required_fields: [],
        active: true,
      })
    }
  }, [pipeline, open])

  const handleAddMapping = () => {
    if (!newMapping.source_field || !newMapping.target_field) {
      return
    }

    if (editingMappingIndex !== null) {
      // Update existing mapping
      const updated = [...formData.field_mappings]
      updated[editingMappingIndex] = newMapping
      setFormData({ ...formData, field_mappings: updated })
      setEditingMappingIndex(null)
    } else {
      // Add new mapping
      setFormData({
        ...formData,
        field_mappings: [...formData.field_mappings, newMapping],
      })
    }

    setNewMapping({
      source_field: '',
      target_field: '',
      transform_function: '',
      default_value: '',
      required: false,
    })
  }

  const handleDeleteMapping = (index: number) => {
    const updated = formData.field_mappings.filter((_, i) => i !== index)
    setFormData({ ...formData, field_mappings: updated })
  }

  const handleEditMapping = (index: number) => {
    setNewMapping(formData.field_mappings[index])
    setEditingMappingIndex(index)
  }

  const handleSave = async () => {
    try {
      if (isEditing && pipeline?.pipeline_id) {
        await apiClient.updatePipeline(pipeline.pipeline_id, formData)
      } else {
        await apiClient.createPipeline(formData)
      }
      onSave()
    } catch (err: any) {
      console.error('Failed to save pipeline:', err)
      alert(err.detail || err.message || 'Failed to save pipeline')
    }
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        {isEditing ? 'Edit Pipeline' : 'Create New Pipeline'}
      </DialogTitle>
      <DialogContent dividers>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, pt: 2 }}>
          {/* Basic Information */}
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Basic Information</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    label="Pipeline Name"
                    fullWidth
                    required
                    value={formData.pipeline_name}
                    onChange={(e) =>
                      setFormData({ ...formData, pipeline_name: e.target.value })
                    }
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    label="Description"
                    fullWidth
                    multiline
                    rows={2}
                    value={formData.pipeline_description}
                    onChange={(e) =>
                      setFormData({ ...formData, pipeline_description: e.target.value })
                    }
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Source Type</InputLabel>
                    <Select
                      value={formData.source_type}
                      onChange={(e) =>
                        setFormData({ ...formData, source_type: e.target.value })
                      }
                    >
                      {SOURCE_TYPES.map((type) => (
                        <MenuItem key={type} value={type}>
                          {type}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Target Dataset Type</InputLabel>
                    <Select
                      value={TARGET_DATASET_TYPES.includes(formData.target_dataset_type) ? formData.target_dataset_type : ''}
                      onChange={(e) =>
                        setFormData({ ...formData, target_dataset_type: e.target.value })
                      }
                    >
                      {TARGET_DATASET_TYPES.map((type) => (
                        <MenuItem key={type} value={type}>
                          {type}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Target Model</InputLabel>
                    <Select
                      value={TARGET_MODELS.includes(formData.target_model) ? formData.target_model : ''}
                      onChange={(e) =>
                        setFormData({ ...formData, target_model: e.target.value })
                      }
                    >
                      {TARGET_MODELS.map((model) => (
                        <MenuItem key={model} value={model}>
                          {model}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Ingestion Mode</InputLabel>
                    <Select
                      value={formData.mode}
                      onChange={(e) =>
                        setFormData({ ...formData, mode: e.target.value })
                      }
                    >
                      {PIPELINE_MODES.map((mode) => (
                        <MenuItem key={mode} value={mode}>
                          {mode}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>

          {/* Field Mappings */}
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">
                Field Mappings ({formData.field_mappings.length})
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Add Field Mapping
                </Typography>
                <Grid container spacing={2} sx={{ mb: 2 }}>
                  <Grid item xs={12} sm={3}>
                    <TextField
                      label="Source Field"
                      fullWidth
                      size="small"
                      value={newMapping.source_field}
                      onChange={(e) =>
                        setNewMapping({ ...newMapping, source_field: e.target.value })
                      }
                    />
                  </Grid>
                  <Grid item xs={12} sm={3}>
                    <TextField
                      label="Target Field"
                      fullWidth
                      size="small"
                      value={newMapping.target_field}
                      onChange={(e) =>
                        setNewMapping({ ...newMapping, target_field: e.target.value })
                      }
                    />
                  </Grid>
                  <Grid item xs={12} sm={2}>
                    <FormControl fullWidth size="small">
                      <InputLabel>Transform</InputLabel>
                      <Select
                        value={newMapping.transform_function || ''}
                        onChange={(e) =>
                          setNewMapping({
                            ...newMapping,
                            transform_function: e.target.value || undefined,
                          })
                        }
                      >
                        {TRANSFORM_FUNCTIONS.map((func) => (
                          <MenuItem key={func || 'none'} value={func || ''}>
                            {func || 'None'}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} sm={2}>
                    <TextField
                      label="Default Value"
                      fullWidth
                      size="small"
                      value={newMapping.default_value || ''}
                      onChange={(e) =>
                        setNewMapping({ ...newMapping, default_value: e.target.value })
                      }
                    />
                  </Grid>
                  <Grid item xs={12} sm={2}>
                    <Box sx={{ display: 'flex', alignItems: 'center', height: '100%', gap: 1 }}>
                      <FormControlLabel
                        control={
                          <Switch
                            size="small"
                            checked={newMapping.required}
                            onChange={(e) =>
                              setNewMapping({
                                ...newMapping,
                                required: e.target.checked,
                              })
                            }
                          />
                        }
                        label="Required"
                      />
                      <IconButton
                        size="small"
                        color="primary"
                        onClick={handleAddMapping}
                        disabled={!newMapping.source_field || !newMapping.target_field}
                      >
                        {editingMappingIndex !== null ? <EditIcon /> : <AddIcon />}
                      </IconButton>
                    </Box>
                  </Grid>
                </Grid>
              </Box>

              {formData.field_mappings.length > 0 && (
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Source Field</TableCell>
                        <TableCell>Target Field</TableCell>
                        <TableCell>Transform</TableCell>
                        <TableCell>Default</TableCell>
                        <TableCell>Required</TableCell>
                        <TableCell align="right">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {formData.field_mappings.map((mapping, index) => (
                        <TableRow key={index}>
                          <TableCell>{mapping.source_field}</TableCell>
                          <TableCell>
                            <Chip label={mapping.target_field} size="small" />
                          </TableCell>
                          <TableCell>
                            {mapping.transform_function || '-'}
                          </TableCell>
                          <TableCell>
                            {mapping.default_value !== undefined && mapping.default_value !== null
                              ? String(mapping.default_value)
                              : '-'}
                          </TableCell>
                          <TableCell>
                            {mapping.required ? (
                              <Chip label="Required" size="small" color="error" />
                            ) : (
                              <Chip label="Optional" size="small" />
                            )}
                          </TableCell>
                          <TableCell align="right">
                            <IconButton
                              size="small"
                              onClick={() => handleEditMapping(index)}
                            >
                              <EditIcon fontSize="small" />
                            </IconButton>
                            <IconButton
                              size="small"
                              onClick={() => handleDeleteMapping(index)}
                              color="error"
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </AccordionDetails>
          </Accordion>

          {/* Deduplication */}
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Deduplication</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Strategy</InputLabel>
                    <Select
                      value={formData.deduplication.strategy}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          deduplication: {
                            ...formData.deduplication,
                            strategy: e.target.value,
                          },
                        })
                      }
                    >
                      {DEDUP_STRATEGIES.map((strategy) => (
                        <MenuItem key={strategy} value={strategy}>
                          {strategy}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                {formData.deduplication.strategy === 'KEY_FIELDS' && (
                  <Grid item xs={12} sm={6}>
                    <TextField
                      label="Key Fields (comma-separated)"
                      fullWidth
                      value={formData.deduplication.key_fields?.join(',') || ''}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          deduplication: {
                            ...formData.deduplication,
                            key_fields: e.target.value
                              .split(',')
                              .map((f) => f.trim())
                              .filter((f) => f),
                          },
                        })
                      }
                    />
                  </Grid>
                )}
                {formData.deduplication.strategy === 'SOURCE_ID' && (
                  <Grid item xs={12} sm={6}>
                    <TextField
                      label="Source ID Field"
                      fullWidth
                      value={formData.deduplication.source_id_field || ''}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          deduplication: {
                            ...formData.deduplication,
                            source_id_field: e.target.value,
                          },
                        })
                      }
                    />
                  </Grid>
                )}
              </Grid>
            </AccordionDetails>
          </Accordion>

          {/* Control Fields */}
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Control Fields</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={formData.control_fields.active_flag ?? true}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            control_fields: {
                              ...formData.control_fields,
                              active_flag: e.target.checked,
                            },
                          })
                        }
                      />
                    }
                    label="Active Flag"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Effective Date"
                    type="date"
                    fullWidth
                    InputLabelProps={{ shrink: true }}
                    value={formData.control_fields.effective_date || ''}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        control_fields: {
                          ...formData.control_fields,
                          effective_date: e.target.value || undefined,
                        },
                      })
                    }
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Expiration Date"
                    type="date"
                    fullWidth
                    InputLabelProps={{ shrink: true }}
                    value={formData.control_fields.expiration_date || ''}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        control_fields: {
                          ...formData.control_fields,
                          expiration_date: e.target.value || undefined,
                        },
                      })
                    }
                  />
                </Grid>
              </Grid>
              <Alert severity="info" sx={{ mt: 2 }}>
                created_at and updated_at are automatically set to CURRENT_TIMESTAMP
              </Alert>
            </AccordionDetails>
          </Accordion>

          {/* Advanced Settings */}
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Advanced Settings</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Batch Size"
                    type="number"
                    fullWidth
                    value={formData.batch_size || 10000}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        batch_size: parseInt(e.target.value) || 10000,
                      })
                    }
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Error Threshold (0-1)"
                    type="number"
                    fullWidth
                    inputProps={{ step: 0.01, min: 0, max: 1 }}
                    value={formData.error_threshold || 0.05}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        error_threshold: parseFloat(e.target.value) || 0.05,
                      })
                    }
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={formData.continue_on_error ?? true}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            continue_on_error: e.target.checked,
                          })
                        }
                      />
                    }
                    label="Continue on Error"
                  />
                </Grid>
                {isEditing && (
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={formData.active ?? true}
                          onChange={(e) =>
                            setFormData({ ...formData, active: e.target.checked })
                          }
                        />
                      }
                      label="Active"
                    />
                  </Grid>
                )}
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleSave}
          variant="contained"
          disabled={!formData.pipeline_name || formData.field_mappings.length === 0}
        >
          {isEditing ? 'Update' : 'Create'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

