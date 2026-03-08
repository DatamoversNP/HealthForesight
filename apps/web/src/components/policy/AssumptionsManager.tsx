/**
 * Assumptions Manager Component
 * Epic 2: Policy Lifecycle Management
 * 
 * Manages policy assumptions (elasticity, substitution, lag, etc.)
 */
import { useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Alert,
  Grid,
} from '@mui/material'
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material'
import { apiClient } from '../../lib/api'

interface AssumptionsManagerProps {
  policyId: string
  assumptions: any[]
  onRefresh: () => void
}

export default function AssumptionsManager({
  policyId,
  assumptions,
  onRefresh,
}: AssumptionsManagerProps) {
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingAssumption, setEditingAssumption] = useState<any>(null)
  const [formData, setFormData] = useState({
    assumption_type: '',
    description: '',
    value: '',
    source: '',
    confidence: 0.5,
    range_min: '',
    range_max: '',
    range_best: '',
  })
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const handleOpenDialog = (assumption?: any) => {
    if (assumption) {
      setEditingAssumption(assumption)
      setFormData({
        assumption_type: assumption.assumption_type || '',
        description: assumption.description || '',
        value: assumption.value?.toString() || '',
        source: assumption.source || '',
        confidence: assumption.confidence || 0.5,
        range_min: assumption.range?.min_value?.toString() || '',
        range_max: assumption.range?.max_value?.toString() || '',
        range_best: assumption.range?.best_estimate?.toString() || '',
      })
    } else {
      setEditingAssumption(null)
      setFormData({
        assumption_type: '',
        description: '',
        value: '',
        source: '',
        confidence: 0.5,
        range_min: '',
        range_max: '',
        range_best: '',
      })
    }
    setError(null)
    setDialogOpen(true)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
    setEditingAssumption(null)
    setError(null)
  }

  const handleSave = async () => {
    if (!formData.assumption_type || !formData.description) {
      setError('Assumption type and description are required')
      return
    }

    setSaving(true)
    setError(null)

    try {
      const assumptionData: any = {
        assumption_type: formData.assumption_type,
        description: formData.description,
        source: formData.source || undefined,
        confidence: parseFloat(formData.confidence.toString()) || 0.5,
      }

      // Add value or range
      if (formData.value) {
        assumptionData.value = parseFloat(formData.value)
      } else if (formData.range_min && formData.range_max && formData.range_best) {
        assumptionData.range = {
          min_value: parseFloat(formData.range_min),
          max_value: parseFloat(formData.range_max),
          best_estimate: parseFloat(formData.range_best),
          confidence_level: 0.95,
        }
      }

      if (editingAssumption) {
        await apiClient.updateAssumption(
          policyId,
          editingAssumption.assumption_id,
          assumptionData
        )
      } else {
        await apiClient.createAssumption(policyId, assumptionData)
      }

      handleCloseDialog()
      onRefresh()
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to save assumption')
      console.error('Failed to save assumption:', err)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (assumptionId: string) => {
    if (!window.confirm('Are you sure you want to delete this assumption?')) {
      return
    }

    try {
      await apiClient.deleteAssumption(policyId, assumptionId)
      onRefresh()
    } catch (err: any) {
      alert('Failed to delete assumption: ' + (err.detail || err.message))
      console.error('Failed to delete assumption:', err)
    }
  }

  const getAssumptionTypeColor = (type: string) => {
    const colors: Record<string, 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'> = {
      elasticity: 'primary',
      substitution: 'secondary',
      lag: 'info',
      default: 'default',
    }
    return colors[type.toLowerCase()] || 'default'
  }

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6">Policy Assumptions</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          Add Assumption
        </Button>
      </Box>

      {assumptions.length === 0 ? (
        <Card variant="outlined">
          <CardContent>
            <Alert severity="info">
              No assumptions defined. Add assumptions to document expected policy behavior.
            </Alert>
          </CardContent>
        </Card>
      ) : (
        <List>
          {assumptions.map((assumption: any, idx: number) => (
            <Card key={assumption.assumption_id || idx} variant="outlined" sx={{ mb: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <Box sx={{ flex: 1 }}>
                    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 1 }}>
                      <Chip
                        label={assumption.assumption_type}
                        color={getAssumptionTypeColor(assumption.assumption_type)}
                        size="small"
                      />
                      {assumption.confidence && (
                        <Chip
                          label={`${(assumption.confidence * 100).toFixed(0)}% confidence`}
                          size="small"
                          variant="outlined"
                        />
                      )}
                    </Box>
                    <Typography variant="body1" paragraph>
                      {assumption.description}
                    </Typography>
                    {assumption.range && (
                      <Typography variant="body2" color="text.secondary">
                        Range: {assumption.range.min_value} to {assumption.range.max_value} (best: {assumption.range.best_estimate})
                      </Typography>
                    )}
                    {assumption.value !== undefined && assumption.value !== null && (
                      <Typography variant="body2" color="text.secondary">
                        Value: {assumption.value}
                      </Typography>
                    )}
                    {assumption.source && (
                      <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                        Source: {assumption.source}
                      </Typography>
                    )}
                  </Box>
                  <Box>
                    <IconButton
                      size="small"
                      onClick={() => handleOpenDialog(assumption)}
                      sx={{ mr: 1 }}
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => handleDelete(assumption.assumption_id)}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          ))}
        </List>
      )}

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingAssumption ? 'Edit Assumption' : 'Add Assumption'}
        </DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <FormControl fullWidth required>
                <InputLabel>Assumption Type</InputLabel>
                <Select
                  value={formData.assumption_type}
                  onChange={(e) => setFormData({ ...formData, assumption_type: e.target.value })}
                  label="Assumption Type"
                >
                  <MenuItem value="elasticity">Elasticity</MenuItem>
                  <MenuItem value="substitution">Substitution</MenuItem>
                  <MenuItem value="lag">Lag</MenuItem>
                  <MenuItem value="adherence">Adherence</MenuItem>
                  <MenuItem value="other">Other</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                required
                label="Description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                multiline
                rows={3}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Value (if single value)"
                type="number"
                value={formData.value}
                onChange={(e) => setFormData({ ...formData, value: e.target.value })}
                helperText="Leave empty if using range"
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Confidence (0-1)"
                type="number"
                inputProps={{ min: 0, max: 1, step: 0.1 }}
                value={formData.confidence}
                onChange={(e) => setFormData({ ...formData, confidence: parseFloat(e.target.value) || 0.5 })}
              />
            </Grid>

            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom>
                Range (if using range instead of single value)
              </Typography>
            </Grid>

            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Min Value"
                type="number"
                value={formData.range_min}
                onChange={(e) => setFormData({ ...formData, range_min: e.target.value })}
              />
            </Grid>

            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Best Estimate"
                type="number"
                value={formData.range_best}
                onChange={(e) => setFormData({ ...formData, range_best: e.target.value })}
              />
            </Grid>

            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Max Value"
                type="number"
                value={formData.range_max}
                onChange={(e) => setFormData({ ...formData, range_max: e.target.value })}
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Source"
                value={formData.source}
                onChange={(e) => setFormData({ ...formData, source: e.target.value })}
                placeholder="e.g., Historical data, Literature, Expert opinion"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleSave}
            disabled={saving || !formData.assumption_type || !formData.description}
          >
            {saving ? 'Saving...' : editingAssumption ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}


