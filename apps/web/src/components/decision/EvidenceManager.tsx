/**
 * Evidence Manager Component - Epic 3
 * Manages evidence links for a policy
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
  Link,
} from '@mui/material'
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Link as LinkIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
} from '@mui/icons-material'
import { format } from 'date-fns'
import { apiClient } from '../../lib/api'

interface EvidenceLink {
  evidence_type: string
  evidence_id: string
  evidence_version?: string
  snapshot_hash?: string
  description?: string
}

interface EvidenceManagerProps {
  policyId: string
  onEvidenceLinked?: () => void
}

export default function EvidenceManager({ policyId, onEvidenceLinked }: EvidenceManagerProps) {
  const [evidence, setEvidence] = useState<any[]>([])
  const [decisions, setDecisions] = useState<any[]>([])
  const [availableEvidence, setAvailableEvidence] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingDecisions, setLoadingDecisions] = useState(false)
  const [loadingEvidence, setLoadingEvidence] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [showEvidenceBrowser, setShowEvidenceBrowser] = useState(false)
  const [formData, setFormData] = useState({
    decision_id: '',
    evidence_type: 'analysis',
    evidence_id: '',
    evidence_version: '',
    description: '',
  })

  useEffect(() => {
    loadEvidence()
    loadDecisions()
  }, [policyId])

  const loadDecisions = async () => {
    try {
      setLoadingDecisions(true)
      const decisionsData = await apiClient.getDecisionsWorkspace({ policy_id: policyId })
      setDecisions(Array.isArray(decisionsData) ? decisionsData : [])
    } catch (err: any) {
      console.error('Failed to load decisions:', err)
      setDecisions([])
    } finally {
      setLoadingDecisions(false)
    }
  }

  const loadAvailableEvidence = async (evidenceType: string) => {
    try {
      setLoadingEvidence(true)
      let evidenceList: any[] = []
      
      if (evidenceType === 'analysis') {
        const analyses = await apiClient.getAnalyses({ limit: 100 })
        evidenceList = (analyses || []).map((a: any) => ({
          id: a.id,
          name: `${a.analysis_type || 'Analysis'} - ${a.id?.substring(0, 8)}...`,
          type: a.analysis_type,
          status: a.status,
          created_at: a.created_at,
        }))
      } else if (evidenceType === 'dataset') {
        try {
          const datasets = await (apiClient as any).getDatasets?.() || []
          evidenceList = (datasets || []).map((d: any) => ({
            id: d.id,
            name: `${d.dataset_type || 'Dataset'} - ${d.year || ''}/${d.month || ''} (${d.record_count || 0} records)`,
            type: d.dataset_type,
            created_at: d.created_at,
          }))
        } catch (err) {
          console.warn('Datasets API not available:', err)
        }
      } else if (evidenceType === 'baseline') {
        try {
          const baselines = await (apiClient as any).getBaselines?.() || []
          evidenceList = (baselines || []).map((b: any) => ({
            id: b.id,
            name: `${b.baseline_type || 'Baseline'} - ${b.id?.substring(0, 8)}...`,
            type: b.baseline_type,
            created_at: b.created_at,
          }))
        } catch (err) {
          console.warn('Baselines API not available:', err)
        }
      }
      
      setAvailableEvidence(evidenceList)
    } catch (err: any) {
      console.error('Failed to load evidence:', err)
      setAvailableEvidence([])
    } finally {
      setLoadingEvidence(false)
    }
  }

  const loadEvidence = async () => {
    try {
      setLoading(true)
      setError(null)
      // Get decisions for this policy, then get evidence from each decision
      const decisions = await apiClient.getPolicyDecisions(policyId)
      const allEvidence: any[] = []
      
      for (const decision of decisions) {
        try {
          const decisionEvidence = await apiClient.getDecisionEvidence(decision.id)
          if (Array.isArray(decisionEvidence)) {
            decisionEvidence.forEach((ev: any) => {
              ev.decision_id = decision.id
              ev.decision_title = decision.title
            })
            allEvidence.push(...decisionEvidence)
          }
        } catch (err) {
          // Skip if evidence not available for this decision
        }
      }
      
      setEvidence(allEvidence)
    } catch (err: any) {
      console.error('Failed to load evidence:', err)
      setError(err.detail || err.message || 'Failed to load evidence')
      setEvidence([])
    } finally {
      setLoading(false)
    }
  }

  const handleOpenDialog = async () => {
    // Reload decisions when opening dialog
    await loadDecisions()
    setFormData({
      decision_id: '',
      evidence_type: 'analysis',
      evidence_id: '',
      evidence_version: '',
      description: '',
    })
    setError(null)
    setShowEvidenceBrowser(false)
    setAvailableEvidence([])
    setDialogOpen(true)
  }

  const handleEvidenceTypeChange = async (newType: string) => {
    setFormData({ ...formData, evidence_type: newType, evidence_id: '' })
    setShowEvidenceBrowser(false)
    setAvailableEvidence([])
    // Auto-load evidence when type changes
    await loadAvailableEvidence(newType)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
  }

  const handleLinkEvidence = async () => {
    if (!formData.decision_id) {
      setError('Please select a decision to link evidence to')
      return
    }
    if (!formData.evidence_id) {
      setError('Please provide an Evidence ID')
      return
    }
    
    try {
      setError(null)
      await apiClient.linkEvidence(formData.decision_id, {
        evidence_type: formData.evidence_type,
        evidence_id: formData.evidence_id,
        evidence_version: formData.evidence_version || undefined,
        description: formData.description || undefined,
      })
      handleCloseDialog()
      await loadEvidence()
      if (onEvidenceLinked) {
        onEvidenceLinked()
      }
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to link evidence')
    }
  }

  const getEvidenceTypeColor = (type: string) => {
    switch (type) {
      case 'analysis':
        return 'primary'
      case 'dataset':
        return 'secondary'
      case 'model':
        return 'success'
      case 'baseline':
        return 'warning'
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
        <Typography variant="h6">Evidence Links</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleOpenDialog}
        >
          Link Evidence
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {evidence.length === 0 ? (
        <Card>
          <CardContent>
            <Typography color="text.secondary" align="center">
              No evidence linked to this policy yet.
            </Typography>
            <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 1 }}>
              Link evidence from analyses, datasets, models, or baselines to support decisions.
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <List>
          {evidence.map((ev, idx) => (
            <Card key={idx} sx={{ mb: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                  <Box>
                    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 1 }}>
                      <Chip
                        label={ev.evidence_link?.evidence_type || 'unknown'}
                        color={getEvidenceTypeColor(ev.evidence_link?.evidence_type || 'unknown') as any}
                        size="small"
                      />
                      {ev.snapshot_verified === true && (
                        <Chip
                          icon={<CheckCircleIcon />}
                          label="Verified"
                          color="success"
                          size="small"
                        />
                      )}
                      {ev.snapshot_verified === false && (
                        <Chip
                          icon={<WarningIcon />}
                          label="Hash Mismatch"
                          color="warning"
                          size="small"
                        />
                      )}
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      <strong>Evidence ID:</strong> {ev.evidence_link?.evidence_id?.substring(0, 8)}...
                    </Typography>
                    {ev.evidence_link?.evidence_version && (
                      <Typography variant="body2" color="text.secondary">
                        <strong>Version:</strong> {ev.evidence_link.evidence_version}
                      </Typography>
                    )}
                    {ev.evidence_link?.description && (
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        {ev.evidence_link.description}
                      </Typography>
                    )}
                    {ev.decision_title && (
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                        Linked to decision: {ev.decision_title}
                      </Typography>
                    )}
                  </Box>
                </Box>
                {ev.snapshot && (
                  <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Snapshot Available
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Hash: {ev.snapshot_hash?.substring(0, 16)}...
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          ))}
        </List>
      )}

      {/* Link Evidence Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>Link Evidence</DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
          
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <FormControl fullWidth required>
                <InputLabel>Decision *</InputLabel>
                <Select
                  value={formData.decision_id}
                  onChange={(e) => setFormData({ ...formData, decision_id: e.target.value })}
                  label="Decision *"
                  disabled={loadingDecisions}
                >
                  {decisions.length === 0 ? (
                    <MenuItem value="" disabled>
                      {loadingDecisions ? 'Loading decisions...' : 'No decisions found. Create a decision first.'}
                    </MenuItem>
                  ) : (
                    decisions.map((decision) => (
                      <MenuItem key={decision.id} value={decision.id}>
                        {decision.title || `Decision ${decision.id.substring(0, 8)}...`}
                        {decision.status && (
                          <Chip 
                            label={decision.status} 
                            size="small" 
                            sx={{ ml: 1 }}
                            color={decision.status === 'FINAL' ? 'success' : 'default'}
                          />
                        )}
                      </MenuItem>
                    ))
                  )}
                </Select>
              </FormControl>
              {decisions.length === 0 && !loadingDecisions && (
                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                  Go to the "Decisions" tab to create a decision first.
                </Typography>
              )}
            </Grid>
            
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Evidence Type</InputLabel>
                <Select
                  value={formData.evidence_type}
                  onChange={(e) => handleEvidenceTypeChange(e.target.value)}
                  label="Evidence Type"
                >
                  <MenuItem value="analysis">Analysis</MenuItem>
                  <MenuItem value="dataset">Dataset</MenuItem>
                  <MenuItem value="model">Model</MenuItem>
                  <MenuItem value="baseline">Baseline</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-start' }}>
                <TextField
                  fullWidth
                  label="Evidence ID *"
                  value={formData.evidence_id}
                  onChange={(e) => setFormData({ ...formData, evidence_id: e.target.value.trim() })}
                  required
                  helperText={
                    showEvidenceBrowser 
                      ? "Select from the list below, or enter a UUID manually"
                      : "Click 'Browse' to select from available evidence, or enter a UUID manually"
                  }
                  placeholder="e.g., 12345678-1234-1234-1234-123456789abc"
                  error={formData.evidence_id ? !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(formData.evidence_id) : false}
                />
                <Button
                  variant="outlined"
                  onClick={async () => {
                    if (!showEvidenceBrowser) {
                      await loadAvailableEvidence(formData.evidence_type)
                    }
                    setShowEvidenceBrowser(!showEvidenceBrowser)
                  }}
                  sx={{ mt: 1, minWidth: 100 }}
                >
                  {showEvidenceBrowser ? 'Hide' : 'Browse'}
                </Button>
              </Box>
              
              {showEvidenceBrowser && (
                <Box sx={{ mt: 2, maxHeight: 200, overflow: 'auto', border: '1px solid #e0e0e0', borderRadius: 1, p: 1 }}>
                  {loadingEvidence ? (
                    <Box display="flex" justifyContent="center" p={2}>
                      <CircularProgress size={24} />
                    </Box>
                  ) : availableEvidence.length === 0 ? (
                    <Typography variant="body2" color="text.secondary" sx={{ p: 2, textAlign: 'center' }}>
                      No {formData.evidence_type} evidence available. 
                      {formData.evidence_type === 'analysis' && ' Run an analysis first in the Analyses section.'}
                      {formData.evidence_type === 'dataset' && ' Ingest a dataset first in the Data & Ingestion section.'}
                      {formData.evidence_type === 'baseline' && ' Create a baseline first.'}
                    </Typography>
                  ) : (
                    <List dense>
                      {availableEvidence.map((ev) => (
                        <ListItem
                          key={ev.id}
                          button
                          onClick={() => {
                            setFormData({ ...formData, evidence_id: ev.id })
                            setShowEvidenceBrowser(false)
                          }}
                          selected={formData.evidence_id === ev.id}
                          sx={{ borderRadius: 1, mb: 0.5 }}
                        >
                          <ListItemText
                            primary={ev.name}
                            secondary={
                              <Box component="span">
                                {ev.type && <Chip label={ev.type} size="small" sx={{ mr: 1 }} />}
                                {ev.status && <Chip label={ev.status} size="small" color={ev.status === 'COMPLETED' ? 'success' : 'default'} />}
                                {ev.id && <Typography variant="caption" sx={{ ml: 1, fontFamily: 'monospace' }}>{ev.id.substring(0, 8)}...</Typography>}
                              </Box>
                            }
                          />
                        </ListItem>
                      ))}
                    </List>
                  )}
                </Box>
              )}
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Version (optional)"
                value={formData.evidence_version}
                onChange={(e) => setFormData({ ...formData, evidence_version: e.target.value })}
                helperText="Version identifier for the evidence"
                placeholder="e.g., v1.0, 2024-01-15"
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description (optional)"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                multiline
                rows={3}
                placeholder="Brief description of this evidence..."
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleLinkEvidence}
            variant="contained"
            disabled={!formData.decision_id || !formData.evidence_id || loadingDecisions}
          >
            Link Evidence
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

