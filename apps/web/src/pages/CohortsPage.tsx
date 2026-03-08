/**
 * Cohorts Page - View and manage saved cohorts
 * Accessible to all users, but most useful for analysts
 */
import { useState, useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  CircularProgress,
  Alert,
  Chip,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Tooltip,
} from '@mui/material'
import {
  DataObject as DataObjectIcon,
  Delete as DeleteIcon,
  Visibility as VisibilityIcon,
  Refresh as RefreshIcon,
  PlayArrow as PlayArrowIcon,
  Edit as EditIcon,
} from '@mui/icons-material'
import { format } from 'date-fns'
import { useNavigate } from 'react-router-dom'
import { apiClient } from '../lib/api'

export default function CohortsPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [cohorts, setCohorts] = useState<any[]>([])
  const [cohortMembersDialogOpen, setCohortMembersDialogOpen] = useState(false)
  const [selectedCohort, setSelectedCohort] = useState<any>(null)
  const [cohortMembers, setCohortMembers] = useState<any[]>([])
  const [loadingMembers, setLoadingMembers] = useState(false)

  useEffect(() => {
    loadCohorts()
  }, [])

  const loadCohorts = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.getCohorts()
      setCohorts(Array.isArray(data) ? data : [])
    } catch (err: any) {
      // Don't log timeout errors - they're expected when API is unavailable
      if (err.code !== 'ECONNABORTED' && !err.message?.includes('timeout')) {
        console.error('Failed to load cohorts:', err)
      }
      // Only set error for non-timeout errors
      if (err.code !== 'ECONNABORTED' && !err.message?.includes('timeout')) {
        setError(err.detail || err.message || 'Failed to load cohorts')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleViewMembers = async (cohort: any) => {
    try {
      setLoadingMembers(true)
      setSelectedCohort(cohort)
      const data = await apiClient.getCohortMembers(cohort.id, 0, 100)
      setCohortMembers(Array.isArray(data.members) ? data.members : [])
      setCohortMembersDialogOpen(true)
    } catch (err: any) {
      console.error('Failed to load cohort members:', err)
      setCohortMembers([])
      setCohortMembersDialogOpen(true)
    } finally {
      setLoadingMembers(false)
    }
  }

  const handleDelete = async (cohortId: string) => {
    if (!window.confirm('Are you sure you want to delete this cohort?')) {
      return
    }
    try {
      await apiClient.deleteCohort(cohortId)
      await loadCohorts()
    } catch (err: any) {
      alert('Failed to delete cohort: ' + (err.detail || err.message))
    }
  }

  const getFilterDescription = (criteria: any) => {
    if (!criteria) return 'No filters'
    
    if (criteria.utilization_change) {
      return `Utilization: ${criteria.utilization_change.min || 'any'}% to ${criteria.utilization_change.max || 'any'}%`
    }
    if (criteria.cost_impact) {
      const min = criteria.cost_impact.min !== undefined ? `$${criteria.cost_impact.min.toLocaleString()}` : 'any'
      const max = criteria.cost_impact.max !== undefined ? `$${criteria.cost_impact.max.toLocaleString()}` : 'any'
      return `Cost: ${min} to ${max}`
    }
    if (criteria.created_after) {
      return `Created after: ${new Date(criteria.created_after).toLocaleDateString()}`
    }
    if (criteria.status) {
      return `Status: ${criteria.status}`
    }
    return 'Custom filters'
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600 }}>
            Cohorts
          </Typography>
          <Typography variant="body2" color="text.secondary">
            View and manage saved policy cohorts
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadCohorts}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            onClick={() => navigate('/dashboard/analyst')}
          >
            Create Cohort
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {cohorts.length === 0 ? (
        <Card>
          <CardContent>
            <Alert severity="info">
              No cohorts found. Go to the Analyst Dashboard to create your first cohort.
            </Alert>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent>
            <List>
              {cohorts.map((cohort: any, idx: number) => (
                <Box key={cohort.id || idx}>
                  <ListItem>
                    <ListItemIcon>
                      <DataObjectIcon color="primary" />
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Typography variant="subtitle1" fontWeight={600}>
                            {cohort.name}
                          </Typography>
                          {cohort.member_count !== undefined && (
                            <Chip label={`${cohort.member_count} policies`} size="small" color="primary" />
                          )}
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                            {cohort.description || 'No description'}
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 1, mt: 1, flexWrap: 'wrap' }}>
                            <Chip
                              label={getFilterDescription(cohort.criteria)}
                              size="small"
                              variant="outlined"
                            />
                            {cohort.created_at && (
                              <Typography variant="caption" color="text.secondary">
                                Created: {format(new Date(cohort.created_at), 'MMM d, yyyy')}
                              </Typography>
                            )}
                            {cohort.last_used_at && (
                              <Typography variant="caption" color="text.secondary">
                                Last used: {format(new Date(cohort.last_used_at), 'MMM d, yyyy')}
                              </Typography>
                            )}
                          </Box>
                        </Box>
                      }
                    />
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Tooltip title="View Members">
                        <IconButton
                          size="small"
                          onClick={() => handleViewMembers(cohort)}
                        >
                          <VisibilityIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Use in Analysis">
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => {
                            // Navigate to analysis page with cohort filter
                            navigate(`/analyses?cohort=${cohort.id}`)
                          }}
                        >
                          <PlayArrowIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDelete(cohort.id)}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </ListItem>
                  {idx < cohorts.length - 1 && <Divider />}
                </Box>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* Cohort Members Dialog */}
      <Dialog
        open={cohortMembersDialogOpen}
        onClose={() => {
          setCohortMembersDialogOpen(false)
          setSelectedCohort(null)
          setCohortMembers([])
        }}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">
              {selectedCohort?.name || 'Cohort'} Members
            </Typography>
            <Button onClick={() => setCohortMembersDialogOpen(false)} size="small">
              Close
            </Button>
          </Box>
        </DialogTitle>
        <DialogContent>
          {loadingMembers ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : cohortMembers.length === 0 ? (
            <Alert severity="info">
              No policies match this cohort's criteria, or members haven't been calculated yet.
            </Alert>
          ) : (
            <List>
              {cohortMembers.map((member: any, idx: number) => (
                <Box key={idx}>
                  <ListItem>
                    <ListItemText
                      primary={
                        <Typography variant="subtitle2">
                          {member.name || member.policy_name || 'Unnamed Policy'}
                        </Typography>
                      }
                      secondary={
                        <Box>
                          {member.avg_utilization_change_pct !== undefined && (
                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                              Utilization: {member.avg_utilization_change_pct.toFixed(1)}%
                            </Typography>
                          )}
                          {member.avg_cost_impact !== undefined && (
                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                              Cost Impact: ${Math.abs(member.avg_cost_impact).toLocaleString()}
                            </Typography>
                          )}
                          {member.status && (
                            <Chip label={member.status} size="small" sx={{ mt: 0.5 }} />
                          )}
                        </Box>
                      }
                    />
                    <Button
                      size="small"
                      onClick={() => navigate(`/policies/builder/${member.policy_id || member.id}`)}
                    >
                      View Policy
                    </Button>
                  </ListItem>
                  {idx < cohortMembers.length - 1 && <Divider />}
                </Box>
              ))}
            </List>
          )}
        </DialogContent>
      </Dialog>
    </Box>
  )
}

