/**
 * Schedules Management Page - Manage automated report generation schedules
 */
import { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
  Alert,
  Tooltip,
  FormControlLabel,
} from '@mui/material'
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  PlayArrow as RunIcon,
  Pause as PauseIcon,
  Schedule as ScheduleIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material'
import { apiClient } from '../lib/api'
import { format } from 'date-fns'
import { healthForesightColors } from '../theme/healthForesightTheme'

interface Schedule {
  id: string
  name: string
  schedule_type: string
  frequency: string
  time: string
  day_of_week?: number
  day_of_month?: number
  enabled: boolean
  last_run?: string
  next_run?: string
  config?: any
  created_at: string
  updated_at: string
}

const SCHEDULE_TYPES = ['EXPORT', 'ANALYSIS', 'OBSERVATION']
const FREQUENCIES = ['DAILY', 'WEEKLY', 'MONTHLY']
const DAYS_OF_WEEK = [
  { value: 0, label: 'Monday' },
  { value: 1, label: 'Tuesday' },
  { value: 2, label: 'Wednesday' },
  { value: 3, label: 'Thursday' },
  { value: 4, label: 'Friday' },
  { value: 5, label: 'Saturday' },
  { value: 6, label: 'Sunday' },
]

export default function SchedulesPage() {
  const [schedules, setSchedules] = useState<Schedule[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingSchedule, setEditingSchedule] = useState<Schedule | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    schedule_type: 'EXPORT',
    frequency: 'DAILY',
    time: '09:00',
    day_of_week: 0,
    day_of_month: 1,
    enabled: true,
    config: {},
  })

  useEffect(() => {
    loadSchedules()
  }, [])

  const loadSchedules = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.getSchedules()
      setSchedules(Array.isArray(data) ? data : [])
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to load schedules')
      console.error('Failed to load schedules:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleOpenDialog = (schedule?: Schedule) => {
    if (schedule) {
      setEditingSchedule(schedule)
      setFormData({
        name: schedule.name,
        schedule_type: schedule.schedule_type,
        frequency: schedule.frequency,
        time: schedule.time,
        day_of_week: schedule.day_of_week ?? 0,
        day_of_month: schedule.day_of_month ?? 1,
        enabled: schedule.enabled,
        config: schedule.config || {},
      })
    } else {
      setEditingSchedule(null)
      setFormData({
        name: '',
        schedule_type: 'EXPORT',
        frequency: 'DAILY',
        time: '09:00',
        day_of_week: 0,
        day_of_month: 1,
        enabled: true,
        config: {},
      })
    }
    setDialogOpen(true)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
    setEditingSchedule(null)
  }

  const handleSaveSchedule = async () => {
    try {
      setError(null)
      
      const scheduleData: any = {
        name: formData.name,
        schedule_type: formData.schedule_type,
        frequency: formData.frequency,
        time: formData.time,
        enabled: formData.enabled,
        config: formData.config,
      }
      
      if (formData.frequency === 'WEEKLY') {
        scheduleData.day_of_week = formData.day_of_week
      }
      if (formData.frequency === 'MONTHLY') {
        scheduleData.day_of_month = formData.day_of_month
      }
      
      if (editingSchedule) {
        await apiClient.updateSchedule(editingSchedule.id, scheduleData)
      } else {
        await apiClient.createSchedule(scheduleData)
      }
      
      handleCloseDialog()
      loadSchedules()
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to save schedule')
    }
  }

  const handleDeleteSchedule = async (scheduleId: string) => {
    if (!window.confirm('Are you sure you want to delete this schedule?')) {
      return
    }
    
    try {
      setError(null)
      await apiClient.deleteSchedule(scheduleId)
      loadSchedules()
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to delete schedule')
    }
  }

  const handleToggleEnabled = async (schedule: Schedule) => {
    try {
      setError(null)
      await apiClient.updateSchedule(schedule.id, { enabled: !schedule.enabled })
      loadSchedules()
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to update schedule')
    }
  }

  const formatNextRun = (nextRun?: string) => {
    if (!nextRun) return 'Not scheduled'
    try {
      return format(new Date(nextRun), 'MMM d, yyyy HH:mm')
    } catch {
      return nextRun
    }
  }

  const formatLastRun = (lastRun?: string) => {
    if (!lastRun) return 'Never'
    try {
      return format(new Date(lastRun), 'MMM d, yyyy HH:mm')
    } catch {
      return lastRun
    }
  }

  if (loading && schedules.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Scheduled Jobs
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          New Schedule
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {schedules.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No schedules found
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Create your first schedule to automate report generation and analyses
          </Typography>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => handleOpenDialog()}>
            Create Schedule
          </Button>
        </Paper>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Frequency</TableCell>
                <TableCell>Time</TableCell>
                <TableCell>Next Run</TableCell>
                <TableCell>Last Run</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {schedules.map((schedule) => (
                <TableRow key={schedule.id} hover>
                  <TableCell>
                    <Typography variant="body2" fontWeight={500}>
                      {schedule.name}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip label={schedule.schedule_type} size="small" />
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <ScheduleIcon fontSize="small" color="action" />
                      <Typography variant="body2">
                        {schedule.frequency}
                        {schedule.frequency === 'WEEKLY' && schedule.day_of_week !== undefined && (
                          <span> ({DAYS_OF_WEEK[schedule.day_of_week]?.label})</span>
                        )}
                        {schedule.frequency === 'MONTHLY' && schedule.day_of_month !== undefined && (
                          <span> (Day {schedule.day_of_month})</span>
                        )}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>{schedule.time}</TableCell>
                  <TableCell>{formatNextRun(schedule.next_run)}</TableCell>
                  <TableCell>{formatLastRun(schedule.last_run)}</TableCell>
                  <TableCell>
                    <Chip
                      label={schedule.enabled ? 'Enabled' : 'Disabled'}
                      color={schedule.enabled ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title={schedule.enabled ? 'Disable' : 'Enable'}>
                      <IconButton
                        size="small"
                        onClick={() => handleToggleEnabled(schedule)}
                      >
                        {schedule.enabled ? <PauseIcon fontSize="small" /> : <RunIcon fontSize="small" />}
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Edit">
                      <IconButton
                        size="small"
                        onClick={() => handleOpenDialog(schedule)}
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDeleteSchedule(schedule.id)}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingSchedule ? 'Edit Schedule' : 'Create New Schedule'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField
              label="Schedule Name"
              fullWidth
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Weekly Executive Report"
            />
            
            <FormControl fullWidth required>
              <InputLabel>Schedule Type</InputLabel>
              <Select
                value={formData.schedule_type}
                label="Schedule Type"
                onChange={(e) => setFormData({ ...formData, schedule_type: e.target.value })}
              >
                {SCHEDULE_TYPES.map((type) => (
                  <MenuItem key={type} value={type}>
                    {type.replace(/_/g, ' ')}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl fullWidth required>
              <InputLabel>Frequency</InputLabel>
              <Select
                value={formData.frequency}
                label="Frequency"
                onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
              >
                {FREQUENCIES.map((freq) => (
                  <MenuItem key={freq} value={freq}>
                    {freq}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {formData.frequency === 'WEEKLY' && (
              <FormControl fullWidth required>
                <InputLabel>Day of Week</InputLabel>
                <Select
                  value={formData.day_of_week}
                  label="Day of Week"
                  onChange={(e) => setFormData({ ...formData, day_of_week: e.target.value as number })}
                >
                  {DAYS_OF_WEEK.map((day) => (
                    <MenuItem key={day.value} value={day.value}>
                      {day.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}

            {formData.frequency === 'MONTHLY' && (
              <TextField
                label="Day of Month"
                type="number"
                fullWidth
                required
                inputProps={{ min: 1, max: 31 }}
                value={formData.day_of_month}
                onChange={(e) => setFormData({ ...formData, day_of_month: parseInt(e.target.value) || 1 })}
              />
            )}

            <TextField
              label="Time"
              type="time"
              fullWidth
              required
              value={formData.time}
              onChange={(e) => setFormData({ ...formData, time: e.target.value })}
              InputLabelProps={{ shrink: true }}
            />

            <FormControlLabel
              control={
                <Switch
                  checked={formData.enabled}
                  onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                />
              }
              label="Enabled"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSaveSchedule} variant="contained" disabled={!formData.name}>
            {editingSchedule ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
