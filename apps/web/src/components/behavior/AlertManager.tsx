/**
 * Alert Manager Component - Epic 5
 * Manages alert rules and displays alert events
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
  Chip,
  Switch,
  FormControlLabel,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material'
import {
  Add as AddIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material'
import { apiClient } from '../../lib/api'

interface AlertRule {
  rule_id: string
  rule_name: string
  signal_type: string
  threshold: number
  condition: string
  action: string
  enabled: boolean
  created_at: string
}

interface AlertEvent {
  alert_id: string
  rule_id: string
  policy_id?: string
  provider_id?: string
  signal_value: number
  threshold: number
  severity: string
  triggered_at: string
  acknowledged: boolean
}

interface AlertManagerProps {
  policyId?: string
}

export default function AlertManager({ policyId }: AlertManagerProps) {
  const [rules, setRules] = useState<AlertRule[]>([])
  const [events, setEvents] = useState<AlertEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [formData, setFormData] = useState({
    rule_name: '',
    signal_type: 'appeals_volume',
    threshold: 0,
    condition: 'greater_than',
    action: 'notify',
    enabled: true,
  })

  useEffect(() => {
    loadData()
  }, [policyId])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      const [rulesData, eventsData] = await Promise.all([
        apiClient.getAlertRules(),
        apiClient.getAlertEvents(policyId ? { policy_id: policyId } : undefined),
      ])
      setRules(Array.isArray(rulesData) ? rulesData : [])
      setEvents(Array.isArray(eventsData) ? eventsData : [])
    } catch (err: any) {
      console.error('Failed to load alert data:', err)
      setError(err.detail || err.message || 'Failed to load alert data')
    } finally {
      setLoading(false)
    }
  }

  const handleOpenDialog = () => {
    setFormData({
      rule_name: '',
      signal_type: 'appeals_volume',
      threshold: 0,
      condition: 'greater_than',
      action: 'notify',
      enabled: true,
    })
    setDialogOpen(true)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
  }

  const handleSubmit = async () => {
    try {
      setError(null)
      if (!formData.rule_name.trim()) {
        setError('Rule name is required')
        return
      }

      await apiClient.createAlertRule(formData)
      handleCloseDialog()
      await loadData()
    } catch (err: any) {
      console.error('Failed to create alert rule:', err)
      setError(err.detail || err.message || 'Failed to create alert rule')
    }
  }

  const handleToggleRule = async (ruleId: string, enabled: boolean) => {
    try {
      await apiClient.updateAlertRule(ruleId, { enabled })
      await loadData()
    } catch (err: any) {
      console.error('Failed to update alert rule:', err)
      setError(err.detail || err.message || 'Failed to update alert rule')
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'error'
      case 'high':
        return 'error'
      case 'medium':
        return 'warning'
      case 'low':
        return 'info'
      default:
        return 'default'
    }
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
              Alert Management
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleOpenDialog}
            >
              Create Alert Rule
            </Button>
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {/* Alert Rules */}
          <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
            Alert Rules
          </Typography>
          {rules.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No alert rules configured. Create one to start monitoring behavior signals.
            </Typography>
          ) : (
            <List>
              {rules.map((rule) => (
                <ListItem
                  key={rule.rule_id}
                  secondaryAction={
                    <FormControlLabel
                      control={
                        <Switch
                          checked={rule.enabled}
                          onChange={(e) => handleToggleRule(rule.rule_id, e.target.checked)}
                        />
                      }
                      label={rule.enabled ? 'Enabled' : 'Disabled'}
                    />
                  }
                >
                  <ListItemText
                    primary={rule.rule_name}
                    secondary={
                      <Box>
                        <Typography variant="caption" component="span" sx={{ mr: 2 }}>
                          Signal: {rule.signal_type}
                        </Typography>
                        <Typography variant="caption" component="span" sx={{ mr: 2 }}>
                          Threshold: {rule.threshold}
                        </Typography>
                        <Typography variant="caption" component="span">
                          Action: {rule.action}
                        </Typography>
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          )}

          {/* Alert Events */}
          <Typography variant="subtitle1" gutterBottom sx={{ mt: 3 }}>
            Recent Alert Events
          </Typography>
          {events.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No alert events triggered yet.
            </Typography>
          ) : (
            <List>
              {events.slice(0, 10).map((event) => (
                <ListItem key={event.alert_id}>
                  <ListItemText
                    primary={
                      <Box display="flex" alignItems="center" gap={1}>
                        <WarningIcon color={getSeverityColor(event.severity) as any} />
                        <Typography variant="body2" fontWeight="medium">
                          Alert Triggered
                        </Typography>
                        <Chip
                          label={event.severity}
                          color={getSeverityColor(event.severity) as any}
                          size="small"
                        />
                        {event.acknowledged && (
                          <Chip
                            icon={<CheckCircleIcon />}
                            label="Acknowledged"
                            color="success"
                            size="small"
                          />
                        )}
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography variant="caption" component="span" sx={{ mr: 2 }}>
                          Signal Value: {event.signal_value} (Threshold: {event.threshold})
                        </Typography>
                        {event.provider_id && (
                          <Typography variant="caption" component="span" sx={{ mr: 2 }}>
                            Provider: {event.provider_id}
                          </Typography>
                        )}
                        <Typography variant="caption" color="text.secondary">
                          {new Date(event.triggered_at).toLocaleString()}
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

      {/* Create Alert Rule Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>Create Alert Rule</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Rule Name"
                value={formData.rule_name}
                onChange={(e) => setFormData({ ...formData, rule_name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Signal Type</InputLabel>
                <Select
                  value={formData.signal_type}
                  onChange={(e) => setFormData({ ...formData, signal_type: e.target.value })}
                  label="Signal Type"
                >
                  <MenuItem value="appeals_volume">Appeals Volume</MenuItem>
                  <MenuItem value="denial_rate">Denial Rate</MenuItem>
                  <MenuItem value="site_shift">Site Shift</MenuItem>
                  <MenuItem value="coding_change">Coding Change</MenuItem>
                  <MenuItem value="lag_pattern">Lag Pattern</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                type="number"
                label="Threshold"
                value={formData.threshold}
                onChange={(e) => setFormData({ ...formData, threshold: parseFloat(e.target.value) || 0 })}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Condition</InputLabel>
                <Select
                  value={formData.condition}
                  onChange={(e) => setFormData({ ...formData, condition: e.target.value })}
                  label="Condition"
                >
                  <MenuItem value="greater_than">Greater Than</MenuItem>
                  <MenuItem value="less_than">Less Than</MenuItem>
                  <MenuItem value="change_pct">Change Percentage</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Action</InputLabel>
                <Select
                  value={formData.action}
                  onChange={(e) => setFormData({ ...formData, action: e.target.value })}
                  label="Action"
                >
                  <MenuItem value="notify">Notify</MenuItem>
                  <MenuItem value="escalate">Escalate</MenuItem>
                  <MenuItem value="suspend_policy">Suspend Policy</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </>
  )
}

