/**
 * Dashboard Customization Page - Customize dashboard widgets and layout
 */
import { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  Grid,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Paper,
  Typography,
  Alert,
  Chip,
  Divider,
} from '@mui/material'
import {
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  DragIndicator as DragIcon,
  Add as AddIcon,
} from '@mui/icons-material'
import DashboardWidget from '../components/dashboard/DashboardWidget'
import { apiClient } from '../lib/api'

// Available widget types
const AVAILABLE_WIDGETS = [
  { id: 'metrics', name: 'Key Metrics', description: 'Executive-level metrics cards' },
  { id: 'policy_performance', name: 'Policy Performance', description: 'Policy performance table' },
  { id: 'cost_impact', name: 'Cost Impact', description: 'Cost impact visualization' },
  { id: 'utilization_trends', name: 'Utilization Trends', description: 'Utilization trends chart' },
  { id: 'risk_indicators', name: 'Risk Indicators', description: 'Risk indicators display' },
  { id: 'recent_activity', name: 'Recent Activity', description: 'Recent activity feed' },
]

interface WidgetConfig {
  id: string
  name: string
  enabled: boolean
  order: number
  size: 'small' | 'medium' | 'large'
}

export default function DashboardCustomizationPage() {
  const [widgets, setWidgets] = useState<WidgetConfig[]>([])
  const [draggedWidget, setDraggedWidget] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [previewMode, setPreviewMode] = useState(false)

  useEffect(() => {
    loadWidgetPreferences()
  }, [])

  const loadWidgetPreferences = () => {
    try {
      const saved = localStorage.getItem('dashboard_widgets')
      if (saved) {
        const parsed = JSON.parse(saved)
        setWidgets(parsed)
      } else {
        // Default configuration
        const defaultWidgets: WidgetConfig[] = AVAILABLE_WIDGETS.map((w, idx) => ({
          id: w.id,
          name: w.name,
          enabled: true,
          order: idx,
          size: idx < 4 ? 'medium' : 'small' as 'small' | 'medium' | 'large',
        }))
        setWidgets(defaultWidgets)
      }
    } catch (err) {
      console.error('Failed to load widget preferences:', err)
      setError('Failed to load dashboard preferences')
    }
  }

  const saveWidgetPreferences = async () => {
    try {
      setSaving(true)
      setError(null)
      localStorage.setItem('dashboard_widgets', JSON.stringify(widgets))
      setSuccess(true)
      setTimeout(() => setSuccess(false), 3000)
    } catch (err: any) {
      setError(err.message || 'Failed to save preferences')
    } finally {
      setSaving(false)
    }
  }

  const handleToggleWidget = (widgetId: string) => {
    setWidgets((prev) =>
      prev.map((w) =>
        w.id === widgetId ? { ...w, enabled: !w.enabled } : w
      )
    )
  }

  const handleDragStart = (e: React.DragEvent, widgetId: string) => {
    setDraggedWidget(widgetId)
    e.dataTransfer.effectAllowed = 'move'
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }

  const handleDrop = (e: React.DragEvent, targetWidgetId: string) => {
    e.preventDefault()
    if (!draggedWidget || draggedWidget === targetWidgetId) {
      setDraggedWidget(null)
      return
    }

    setWidgets((prev) => {
      const dragged = prev.find((w) => w.id === draggedWidget)
      const target = prev.find((w) => w.id === targetWidgetId)
      if (!dragged || !target) return prev

      const newWidgets = [...prev]
      const draggedIndex = newWidgets.indexOf(dragged)
      const targetIndex = newWidgets.indexOf(target)

      // Remove dragged widget
      newWidgets.splice(draggedIndex, 1)
      // Insert at target position
      newWidgets.splice(targetIndex, 0, dragged)

      // Update order
      return newWidgets.map((w, idx) => ({ ...w, order: idx }))
    })

    setDraggedWidget(null)
  }

  const handleAddWidget = (widgetId: string) => {
    const widget = AVAILABLE_WIDGETS.find((w) => w.id === widgetId)
    if (!widget) return

    const exists = widgets.find((w) => w.id === widgetId)
    if (exists) {
      // Enable if disabled
      handleToggleWidget(widgetId)
      return
    }

    // Add new widget
    const newWidget: WidgetConfig = {
      id: widgetId,
      name: widget.name,
      enabled: true,
      order: widgets.length,
      size: 'medium',
    }
    setWidgets([...widgets, newWidget])
  }

  const handleRemoveWidget = (widgetId: string) => {
    setWidgets((prev) => prev.filter((w) => w.id !== widgetId))
  }

  const handleSizeChange = (widgetId: string, size: 'small' | 'medium' | 'large') => {
    setWidgets((prev) =>
      prev.map((w) => (w.id === widgetId ? { ...w, size } : w))
    )
  }

  const enabledWidgets = widgets.filter((w) => w.enabled).sort((a, b) => a.order - b.order)
  const disabledWidgets = AVAILABLE_WIDGETS.filter(
    (w) => !widgets.find((widget) => widget.id === w.id && widget.enabled)
  )

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <SettingsIcon fontSize="large" />
          <Typography variant="h4" component="h1">
            Dashboard Customization
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadWidgetPreferences}
          >
            Reset
          </Button>
          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={saveWidgetPreferences}
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save Layout'}
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(false)}>
          Dashboard layout saved successfully!
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Widget Configuration Panel */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Available Widgets
              </Typography>
              <Divider sx={{ my: 2 }} />

              {/* Enabled Widgets */}
              <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
                Enabled Widgets
              </Typography>
              <List dense>
                {enabledWidgets.map((widget) => {
                  const widgetInfo = AVAILABLE_WIDGETS.find((w) => w.id === widget.id)
                  return (
                    <ListItem
                      key={widget.id}
                      sx={{
                        border: '1px solid',
                        borderColor: 'divider',
                        borderRadius: 1,
                        mb: 1,
                        bgcolor: 'background.paper',
                      }}
                      draggable
                      onDragStart={(e) => handleDragStart(e, widget.id)}
                      onDragOver={handleDragOver}
                      onDrop={(e) => handleDrop(e, widget.id)}
                    >
                      <DragIcon sx={{ mr: 1, color: 'text.secondary' }} />
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="body1" component="div">
                          {widgetInfo?.name || widget.name}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                          <Chip
                            label={widget.size}
                            size="small"
                            variant="outlined"
                            onClick={(e) => {
                              e.stopPropagation()
                              const sizes: ('small' | 'medium' | 'large')[] = ['small', 'medium', 'large']
                              const currentIdx = sizes.indexOf(widget.size)
                              const nextSize = sizes[(currentIdx + 1) % sizes.length]
                              handleSizeChange(widget.id, nextSize)
                            }}
                          />
                        </Box>
                      </Box>
                      <Checkbox
                        checked={widget.enabled}
                        onChange={() => handleToggleWidget(widget.id)}
                        onClick={(e) => e.stopPropagation()}
                      />
                    </ListItem>
                  )
                })}
              </List>

              {/* Disabled Widgets */}
              {disabledWidgets.length > 0 && (
                <>
                  <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
                    Add Widgets
                  </Typography>
                  <List dense>
                    {disabledWidgets.map((widget) => (
                      <ListItem
                        key={widget.id}
                        sx={{
                          border: '1px solid',
                          borderColor: 'divider',
                          borderRadius: 1,
                          mb: 1,
                        }}
                      >
                        <ListItemText
                          primary={widget.name}
                          secondary={widget.description}
                        />
                        <IconButton
                          size="small"
                          onClick={() => handleAddWidget(widget.id)}
                        >
                          <AddIcon />
                        </IconButton>
                      </ListItem>
                    ))}
                  </List>
                </>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Preview Panel */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6">Layout Preview</Typography>
                <Chip
                  label={previewMode ? 'Preview Mode' : 'Edit Mode'}
                  color={previewMode ? 'primary' : 'default'}
                  onClick={() => setPreviewMode(!previewMode)}
                />
              </Box>
              <Divider sx={{ mb: 2 }} />

              {enabledWidgets.length === 0 ? (
                <Paper sx={{ p: 4, textAlign: 'center' }}>
                  <Typography variant="h6" color="text.secondary" gutterBottom>
                    No widgets enabled
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Add widgets from the panel on the left to customize your dashboard
                  </Typography>
                </Paper>
              ) : (
                <Grid container spacing={2}>
                  {enabledWidgets.map((widget) => {
                    const cols = widget.size === 'large' ? 12 : widget.size === 'medium' ? 6 : 4
                    return (
                      <Grid item xs={12} sm={cols} key={widget.id}>
                        <DashboardWidget
                          id={widget.id}
                          title={widget.name}
                          draggable={!previewMode}
                          onDragStart={handleDragStart}
                          onDragOver={handleDragOver}
                          onDrop={handleDrop}
                          onRemove={!previewMode ? handleRemoveWidget : undefined}
                          isDragging={draggedWidget === widget.id}
                        >
                          <Box
                            sx={{
                              minHeight: widget.size === 'large' ? 300 : widget.size === 'medium' ? 200 : 150,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              bgcolor: 'action.hover',
                              borderRadius: 1,
                            }}
                          >
                            <Typography variant="body2" color="text.secondary">
                              {widget.name} Widget Preview
                            </Typography>
                          </Box>
                        </DashboardWidget>
                      </Grid>
                    )
                  })}
                </Grid>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
