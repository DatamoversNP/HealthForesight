/**
 * Decision Manager Component - Epic 3
 * Manages decisions linked to a policy
 */
import { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  List,
  ListItem,
  ListItemText,
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
  CircularProgress,
  IconButton,
  Divider,
} from '@mui/material'
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
  Visibility as VisibilityIcon,
  Download as DownloadIcon,
} from '@mui/icons-material'
import { format } from 'date-fns'
import { apiClient } from '../../lib/api'

interface Decision {
  id: string
  title: string
  recommendation: string
  rationale: string
  confidence_score: number
  status: string
  created_at: string
  created_by: string
  approvals: any[]
  evidence_links: any[]
}

interface DecisionManagerProps {
  policyId: string
  onDecisionCreated?: () => void
}

// Helper function to extract error message from API errors
const extractErrorMessage = (err: any): string => {
  if (err.response?.data?.detail) {
    const detail = err.response.data.detail
    if (Array.isArray(detail)) {
      // Pydantic validation errors: [{type, loc, msg, input}, ...]
      return detail.map((e: any) => {
        const field = e.loc?.slice(1).join('.') || 'field'
        return `${field}: ${e.msg}`
      }).join(', ')
    } else if (typeof detail === 'string') {
      return detail
    } else {
      return JSON.stringify(detail)
    }
  } else if (err.detail) {
    if (Array.isArray(err.detail)) {
      return err.detail.map((e: any) => {
        const field = e.loc?.slice(1).join('.') || 'field'
        return `${field}: ${e.msg}`
      }).join(', ')
    } else if (typeof err.detail === 'string') {
      return err.detail
    }
  } else if (err.message) {
    return err.message
  }
  return 'An error occurred'
}

export default function DecisionManager({ policyId, onDecisionCreated }: DecisionManagerProps) {
  const [decisions, setDecisions] = useState<Decision[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingDecision, setEditingDecision] = useState<Decision | null>(null)
  const [formData, setFormData] = useState({
    title: '',
    recommendation: '',
    rationale: '',
    confidence_score: 0.5,
    status: 'DRAFT',
  })

  useEffect(() => {
    loadDecisions()
  }, [policyId])

  const loadDecisions = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.getPolicyDecisions(policyId)
      setDecisions(Array.isArray(data) ? data : [])
    } catch (err: any) {
      console.error('Failed to load decisions:', err)
      setError(extractErrorMessage(err) || 'Failed to load decisions')
      setDecisions([])
    } finally {
      setLoading(false)
    }
  }

  const handleOpenDialog = (decision?: Decision) => {
    if (decision) {
      setEditingDecision(decision)
      setFormData({
        title: decision.title,
        recommendation: decision.recommendation,
        rationale: decision.rationale,
        confidence_score: decision.confidence_score,
        status: decision.status,
      })
    } else {
      setEditingDecision(null)
      setFormData({
        title: '',
        recommendation: '',
        rationale: '',
        confidence_score: 0.5,
        status: 'DRAFT',
      })
    }
    setDialogOpen(true)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
    setEditingDecision(null)
  }

  const handleSubmit = async () => {
    // Client-side validation
    const trimmedTitle = formData.title?.trim() || ''
    const trimmedRecommendation = formData.recommendation?.trim() || ''
    const trimmedRationale = formData.rationale?.trim() || ''
    
    if (!trimmedTitle) {
      setError('Title is required')
      return
    }
    if (!trimmedRecommendation) {
      setError('Recommendation is required')
      return
    }
    if (!trimmedRationale) {
      setError('Rationale is required')
      return
    }
    if (isNaN(formData.confidence_score) || formData.confidence_score < 0 || formData.confidence_score > 1) {
      setError('Confidence score must be between 0.0 and 1.0')
      return
    }

    try {
      setError(null)
      const decisionData: any = {
        title: trimmedTitle,
        recommendation: trimmedRecommendation,
        rationale: trimmedRationale,
        confidence_score: Number(formData.confidence_score),
      }
      
      // Only include optional fields if they have values
      if (policyId) {
        decisionData.policy_id = policyId
      }
      decisionData.assumptions_snapshot = {}
      
      console.log('Sending decision data:', decisionData)
      
      if (editingDecision) {
        await apiClient.updateDecisionWorkspace(editingDecision.id, decisionData)
      } else {
        await apiClient.createDecisionWorkspace(decisionData)
      }
      handleCloseDialog()
      await loadDecisions()
      if (onDecisionCreated) {
        onDecisionCreated()
      }
    } catch (err: any) {
      const errorMsg = extractErrorMessage(err)
      console.error('Error creating decision:', err, errorMsg)
      setError(errorMsg || 'Failed to save decision')
    }
  }

  const handleDelete = async (decisionId: string) => {
    if (!window.confirm('Are you sure you want to delete this decision?')) {
      return
    }
    try {
      // Note: Delete endpoint may not be implemented yet
      await loadDecisions()
    } catch (err: any) {
      setError(extractErrorMessage(err) || 'Failed to delete decision')
    }
  }

  const handleFinalize = async (decisionId: string) => {
    if (!window.confirm('Are you sure you want to finalize this decision? This cannot be undone.')) {
      return
    }
    try {
      await apiClient.finalizeDecision(decisionId)
      await loadDecisions()
    } catch (err: any) {
      setError(extractErrorMessage(err) || 'Failed to finalize decision')
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'FINAL':
        return 'success'
      case 'APPROVED':
        return 'success'
      case 'PENDING_APPROVAL':
        return 'warning'
      case 'DRAFT':
        return 'default'
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
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6">Decisions</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          Create Decision
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {decisions.length === 0 ? (
        <Card>
          <CardContent>
            <Typography color="text.secondary" align="center">
              No decisions linked to this policy yet.
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <List>
          {decisions.map((decision) => (
            <Card key={decision.id} sx={{ mb: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                  <Box>
                    <Typography variant="h6">{decision.title}</Typography>
                    <Box sx={{ display: 'flex', gap: 1, mt: 1, alignItems: 'center' }}>
                      <Chip
                        label={decision.status}
                        color={getStatusColor(decision.status) as any}
                        size="small"
                      />
                      <Chip
                        label={`${(decision.confidence_score * 100).toFixed(0)}% confidence`}
                        variant="outlined"
                        size="small"
                      />
                      <Typography variant="caption" color="text.secondary">
                        {format(new Date(decision.created_at), 'MMM d, yyyy')}
                      </Typography>
                    </Box>
                  </Box>
                  <Box>
                    <IconButton
                      size="small"
                      onClick={() => window.open(`/decisions/${decision.id}`, '_blank')}
                      title="View Decision"
                    >
                      <VisibilityIcon />
                    </IconButton>
                    {decision.status !== 'FINAL' && (
                      <>
                        <IconButton
                          size="small"
                          onClick={() => handleOpenDialog(decision)}
                          title="Edit Decision"
                        >
                          <EditIcon />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => handleFinalize(decision.id)}
                          title="Finalize Decision"
                        >
                          <CheckCircleIcon />
                        </IconButton>
                      </>
                    )}
                    <IconButton
                      size="small"
                      onClick={() => handleDelete(decision.id)}
                      title="Delete Decision"
                      color="error"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Box>
                </Box>

                <Typography variant="body2" color="text.secondary" paragraph>
                  <strong>Recommendation:</strong> {decision.recommendation}
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  <strong>Rationale:</strong> {decision.rationale}
                </Typography>

                {decision.approvals && decision.approvals.length > 0 && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Approvals ({decision.approvals.length})
                    </Typography>
                    {decision.approvals.map((approval: any, idx: number) => (
                      <Chip
                        key={idx}
                        label={`${approval.role} - ${format(new Date(approval.approved_at), 'MMM d, yyyy')}`}
                        size="small"
                        sx={{ mr: 1, mb: 1 }}
                      />
                    ))}
                  </Box>
                )}

                {decision.evidence_links && decision.evidence_links.length > 0 && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Evidence ({decision.evidence_links.length})
                    </Typography>
                    {decision.evidence_links.map((link: any, idx: number) => (
                      <Chip
                        key={idx}
                        label={`${link.evidence_type}: ${link.evidence_id.substring(0, 8)}...`}
                        size="small"
                        variant="outlined"
                        sx={{ mr: 1, mb: 1 }}
                      />
                    ))}
                  </Box>
                )}
              </CardContent>
            </Card>
          ))}
        </List>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>{editingDecision ? 'Edit Decision' : 'Create Decision'}</DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2, mt: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
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
                label="Recommendation"
                value={formData.recommendation}
                onChange={(e) => setFormData({ ...formData, recommendation: e.target.value })}
                multiline
                rows={3}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Rationale"
                value={formData.rationale}
                onChange={(e) => setFormData({ ...formData, rationale: e.target.value })}
                multiline
                rows={4}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Confidence Score"
                type="number"
                inputProps={{ min: 0, max: 1, step: 0.1 }}
                value={formData.confidence_score}
                onChange={(e) => setFormData({ ...formData, confidence_score: parseFloat(e.target.value) || 0 })}
                helperText="0.0 to 1.0 (0% to 100%)"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  label="Status"
                >
                  <MenuItem value="DRAFT">DRAFT</MenuItem>
                  <MenuItem value="PENDING_APPROVAL">PENDING_APPROVAL</MenuItem>
                  <MenuItem value="APPROVED">APPROVED</MenuItem>
                  <MenuItem value="FINAL">FINAL</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingDecision ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

