/**
 * Guardrails Manager Component
 * Epic 2: Policy Lifecycle Management
 * 
 * Manages policy guardrails/rollback triggers
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
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material'
import { apiClient } from '../../lib/api'

interface GuardrailsManagerProps {
  policyId: string
  guardrails: any[]
  onRefresh: () => void
}

export default function GuardrailsManager({
  policyId,
  guardrails,
  onRefresh,
}: GuardrailsManagerProps) {
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingGuardrail, setEditingGuardrail] = useState<any>(null)
  const [formData, setFormData] = useState({
    metric_name: '',
    threshold_type: 'max',
    threshold_value: '',
    action: 'alert',
    description: '',
  })
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const handleOpenDialog = (guardrail?: any) => {
    if (guardrail) {
      setEditingGuardrail(guardrail)
      setFormData({
        metric_name: guardrail.metric_name || '',
        threshold_type: guardrail.threshold_type || 'max',
        threshold_value: guardrail.threshold_value?.toString() || '',
        action: guardrail.action || 'alert',
        description: guardrail.description || '',
      })
    } else {
      setEditingGuardrail(null)
      setFormData({
        metric_name: '',
        threshold_type: 'max',
        threshold_value: '',
        action: 'alert',
        description: '',
      })
    }
    setError(null)
    setDialogOpen(true)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
    setEditingGuardrail(null)
    setError(null)
  }

  const handleSave = async () => {
    if (!formData.metric_name || !formData.threshold_value || !formData.description) {
      setError('Metric name, threshold value, and description are required')
      return
    }

    setSaving(true)
    setError(null)

    try {
      const guardrailData = {
        metric_name: formData.metric_name,
        threshold_type: formData.threshold_type,
        threshold_value: parseFloat(formData.threshold_value),
        action: formData.action,
        description: formData.description,
      }

      if (editingGuardrail) {
        await apiClient.updateGuardrail(
          policyId,
          editingGuardrail.guardrail_id,
          guardrailData
        )
      } else {
        await apiClient.createGuardrail(policyId, guardrailData)
      }

      handleCloseDialog()
      onRefresh()
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to save guardrail')
      console.error('Failed to save guardrail:', err)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (guardrailId: string) => {
    if (!window.confirm('Are you sure you want to delete this guardrail?')) {
      return
    }

    try {
      await apiClient.deleteGuardrail(policyId, guardrailId)
      onRefresh()
    } catch (err: any) {
      alert('Failed to delete guardrail: ' + (err.detail || err.message))
      console.error('Failed to delete guardrail:', err)
    }
  }

  const getActionColor = (action: string) => {
    const colors: Record<string, 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'> = {
      alert: 'warning',
      suspend: 'error',
      rollback: 'error',
      default: 'default',
    }
    return colors[action.toLowerCase()] || 'default'
  }

  const triggeredCount = guardrails.filter((g: any) => g.triggered).length

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h6">Policy Guardrails</Typography>
          {triggeredCount > 0 && (
            <Alert severity="warning" sx={{ mt: 1 }}>
              {triggeredCount} guardrail{triggeredCount > 1 ? 's' : ''} currently triggered
            </Alert>
          )}
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          Add Guardrail
        </Button>
      </Box>

      {guardrails.length === 0 ? (
        <Card variant="outlined">
          <CardContent>
            <Alert severity="info">
              No guardrails defined. Add guardrails to set rollback triggers and monitoring thresholds.
            </Alert>
          </CardContent>
        </Card>
      ) : (
        <List>
          {guardrails.map((guardrail: any, idx: number) => (
            <Card
              key={guardrail.guardrail_id || idx}
              variant="outlined"
              sx={{
                mb: 2,
                borderLeft: guardrail.triggered ? '4px solid red' : '4px solid transparent',
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <Box sx={{ flex: 1 }}>
                    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 1 }}>
                      <Typography variant="subtitle1" fontWeight={600}>
                        {guardrail.metric_name}
                      </Typography>
                      <Chip
                        label={guardrail.threshold_type.toUpperCase()}
                        size="small"
                        variant="outlined"
                      />
                      <Chip
                        label={guardrail.action}
                        color={getActionColor(guardrail.action)}
                        size="small"
                      />
                      {guardrail.triggered && (
                        <Chip
                          icon={<WarningIcon />}
                          label="TRIGGERED"
                          color="error"
                          size="small"
                        />
                      )}
                    </Box>
                    <Typography variant="body2" paragraph>
                      {guardrail.description}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Threshold: {guardrail.threshold_type === 'max' ? 'Max' : guardrail.threshold_type === 'min' ? 'Min' : 'Change %'} = {guardrail.threshold_value}
                    </Typography>
                    {guardrail.triggered && guardrail.current_value !== undefined && (
                      <Typography variant="body2" color="error" sx={{ mt: 1 }}>
                        Current value: {guardrail.current_value} (exceeds threshold)
                      </Typography>
                    )}
                    {guardrail.last_checked_at && (
                      <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                        Last checked: {new Date(guardrail.last_checked_at).toLocaleString()}
                      </Typography>
                    )}
                  </Box>
                  <Box>
                    <IconButton
                      size="small"
                      onClick={() => handleOpenDialog(guardrail)}
                      sx={{ mr: 1 }}
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => handleDelete(guardrail.guardrail_id)}
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
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingGuardrail ? 'Edit Guardrail' : 'Add Guardrail'}
        </DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                required
                label="Metric Name"
                value={formData.metric_name}
                onChange={(e) => setFormData({ ...formData, metric_name: e.target.value })}
                placeholder="e.g., utilization_change_pct, cost_impact"
                helperText="The metric to monitor"
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <FormControl fullWidth required>
                <InputLabel>Threshold Type</InputLabel>
                <Select
                  value={formData.threshold_type}
                  onChange={(e) => setFormData({ ...formData, threshold_type: e.target.value })}
                  label="Threshold Type"
                >
                  <MenuItem value="max">Maximum</MenuItem>
                  <MenuItem value="min">Minimum</MenuItem>
                  <MenuItem value="change_pct">Change Percentage</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                required
                label="Threshold Value"
                type="number"
                value={formData.threshold_value}
                onChange={(e) => setFormData({ ...formData, threshold_value: e.target.value })}
              />
            </Grid>

            <Grid item xs={12}>
              <FormControl fullWidth required>
                <InputLabel>Action</InputLabel>
                <Select
                  value={formData.action}
                  onChange={(e) => setFormData({ ...formData, action: e.target.value })}
                  label="Action"
                >
                  <MenuItem value="alert">Alert</MenuItem>
                  <MenuItem value="suspend">Suspend Policy</MenuItem>
                  <MenuItem value="rollback">Rollback Policy</MenuItem>
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
                placeholder="Describe when this guardrail should trigger and why"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleSave}
            disabled={saving || !formData.metric_name || !formData.threshold_value || !formData.description}
          >
            {saving ? 'Saving...' : editingGuardrail ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}


