/**
 * Tasks Panel Component - Epic 6
 * Displays and manages tasks
 */
import { useState, useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  List,
  ListItem,
  ListItemText,
  Chip,
  CircularProgress,
  Alert,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
} from '@mui/material'
import {
  Add as AddIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material'
import { apiClient } from '../../lib/api'

interface Task {
  task_id: string
  resource_type: string
  resource_id: string
  title: string
  description: string
  assigned_to: string
  assigned_by: string
  due_date?: string
  status: string
  created_at: string
  completed_at?: string
}

interface TasksPanelProps {
  resourceType?: string
  resourceId?: string
  assignedTo?: string
}

export default function TasksPanel({ resourceType, resourceId, assignedTo }: TasksPanelProps) {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    assigned_to: '',
    due_date: '',
  })

  useEffect(() => {
    loadTasks()
  }, [assignedTo])

  const loadTasks = async () => {
    try {
      setLoading(true)
      setError(null)
      const params: any = {}
      if (assignedTo) params.assigned_to = assignedTo
      const data = await apiClient.getTasks(params)
      setTasks(Array.isArray(data) ? data : [])
    } catch (err: any) {
      console.error('Failed to load tasks:', err)
      setError(err.detail || err.message || 'Failed to load tasks')
    } finally {
      setLoading(false)
    }
  }

  const handleOpenDialog = () => {
    setFormData({
      title: '',
      description: '',
      assigned_to: '',
      due_date: '',
    })
    setDialogOpen(true)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
  }

  const handleSubmit = async () => {
    try {
      setError(null)
      if (!formData.title.trim()) {
        setError('Title is required')
        return
      }

      await apiClient.createTask({
        resource_type: resourceType || 'POLICY',
        resource_id: resourceId || '00000000-0000-0000-0000-000000000000',
        title: formData.title.trim(),
        description: formData.description.trim(),
        assigned_to: formData.assigned_to || '00000000-0000-0000-0000-000000000001',
        due_date: formData.due_date || undefined,
      })
      handleCloseDialog()
      await loadTasks()
    } catch (err: any) {
      console.error('Failed to create task:', err)
      setError(err.detail || err.message || 'Failed to create task')
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return 'success'
      case 'IN_PROGRESS':
        return 'info'
      case 'PENDING':
        return 'warning'
      case 'CANCELLED':
        return 'default'
      default:
        return 'default'
    }
  }

  const pendingTasks = tasks.filter(t => t.status === 'PENDING' || t.status === 'IN_PROGRESS')
  const completedTasks = tasks.filter(t => t.status === 'COMPLETED')

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
              Tasks
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleOpenDialog}
            >
              Create Task
            </Button>
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {/* Pending Tasks */}
          {pendingTasks.length > 0 && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle1" gutterBottom>
                Pending ({pendingTasks.length})
              </Typography>
              <List>
                {pendingTasks.map((task) => (
                  <ListItem key={task.task_id}>
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="body2" fontWeight="medium">
                            {task.title}
                          </Typography>
                          <Chip
                            label={task.status}
                            color={getStatusColor(task.status) as any}
                            size="small"
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            {task.description}
                          </Typography>
                          {task.due_date && (
                            <Box display="flex" alignItems="center" gap={0.5} sx={{ mt: 0.5 }}>
                              <ScheduleIcon fontSize="small" />
                              <Typography variant="caption" color="text.secondary">
                                Due: {new Date(task.due_date).toLocaleDateString()}
                              </Typography>
                            </Box>
                          )}
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}

          {/* Completed Tasks */}
          {completedTasks.length > 0 && (
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                Completed ({completedTasks.length})
              </Typography>
              <List>
                {completedTasks.map((task) => (
                  <ListItem key={task.task_id}>
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <CheckCircleIcon color="success" fontSize="small" />
                          <Typography variant="body2" sx={{ textDecoration: 'line-through' }}>
                            {task.title}
                          </Typography>
                        </Box>
                      }
                      secondary={
                        <Typography variant="caption" color="text.secondary">
                          Completed: {task.completed_at ? new Date(task.completed_at).toLocaleString() : 'N/A'}
                        </Typography>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}

          {tasks.length === 0 && (
            <Typography variant="body2" color="text.secondary">
              No tasks found. Create a task to get started.
            </Typography>
          )}
        </CardContent>
      </Card>

      {/* Create Task Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>Create Task</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Title"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Assigned To (User ID)"
                value={formData.assigned_to}
                onChange={(e) => setFormData({ ...formData, assigned_to: e.target.value })}
                placeholder="UUID"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                type="date"
                label="Due Date"
                value={formData.due_date}
                onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                InputLabelProps={{ shrink: true }}
              />
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

