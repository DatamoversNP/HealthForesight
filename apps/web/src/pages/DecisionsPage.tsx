/**
 * Decisions Page
 */
import { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
  MenuItem,
  Alert,
  CircularProgress,
  Select,
  FormControl,
  InputLabel,
} from '@mui/material'
import {
  Add as AddIcon,
  Edit as EditIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  AttachFile as AttachFileIcon,
  Download as DownloadIcon,
  Delete as DeleteIcon,
  CloudUpload as CloudUploadIcon,
} from '@mui/icons-material'
import { apiClient } from '../lib/api'
import { format } from 'date-fns'
import { healthForesightColors } from '../theme/healthForesightTheme'

interface Decision {
  id: string
  policy_id: string
  quarter: string
  lob?: string
  market?: string
  status: string
  recommended_action: string
  decided_action?: string
  owner_user_id?: string
  due_date?: string
  decision_rationale_md?: string
  created_at: string
  updated_at: string
}

const STATUSES = ['OPEN', 'IN_REVIEW', 'DECIDED', 'DEFERRED']
const ACTIONS = ['KEEP', 'MODIFY', 'RETIRE', 'REVIEW']

export default function DecisionsPage() {
  const [decisions, setDecisions] = useState<Decision[]>([])
  const [policies, setPolicies] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingDecision, setEditingDecision] = useState<Decision | null>(null)
  const [filters, setFilters] = useState({
    quarter: '',
    status: '',
    lob: '',
    market: '',
  })
  const [formData, setFormData] = useState({
    policy_id: '',
    quarter: '',
    lob: '',
    market: '',
    recommended_action: 'REVIEW',
    owner_user_id: '',
    due_date: '',
    decision_rationale_md: '',
  })
  const [attachmentsDialogOpen, setAttachmentsDialogOpen] = useState(false)
  const [selectedDecisionId, setSelectedDecisionId] = useState<string | null>(null)
  const [attachments, setAttachments] = useState<any[]>([])
  const [attachmentsLoading, setAttachmentsLoading] = useState(false)
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [uploadLabel, setUploadLabel] = useState('')
  const [uploading, setUploading] = useState(false)

  useEffect(() => {
    loadDecisions()
    loadPolicies()
  }, [filters])
  
  const loadPolicies = async () => {
    try {
      const data = await apiClient.getPolicies()
      const policiesList = Array.isArray(data) ? data : (data.items || [])
      setPolicies(policiesList)
    } catch (err) {
      console.error('Error loading policies:', err)
    }
  }
  
  const getPolicyName = (policyId: string): string => {
    const policy = policies.find(p => p.id === policyId)
    return policy?.name || policyId.substring(0, 8)
  }

  const handleOpenAttachmentsDialog = async (decisionId: string) => {
    setSelectedDecisionId(decisionId)
    setAttachmentsDialogOpen(true)
    await loadAttachments(decisionId)
  }

  const handleCloseAttachmentsDialog = () => {
    setAttachmentsDialogOpen(false)
    setSelectedDecisionId(null)
    setAttachments([])
    setUploadFile(null)
    setUploadLabel('')
  }

  const loadAttachments = async (decisionId: string) => {
    try {
      setAttachmentsLoading(true)
      const data = await apiClient.getDecisionAttachments(decisionId)
      setAttachments(Array.isArray(data) ? data : [])
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to load attachments')
    } finally {
      setAttachmentsLoading(false)
    }
  }

  const handleUploadFile = async () => {
    if (!selectedDecisionId || !uploadFile) {
      setError('Please select a file to upload')
      return
    }

    try {
      setUploading(true)
      setError(null)
      const label = uploadLabel || uploadFile.name
      await apiClient.uploadDecisionAttachment(selectedDecisionId, uploadFile, label)
      await loadAttachments(selectedDecisionId)
      setUploadFile(null)
      setUploadLabel('')
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to upload file')
    } finally {
      setUploading(false)
    }
  }

  const handleDownloadAttachment = async (attachment: any) => {
    if (!selectedDecisionId) return

    try {
      const blobUrl = await apiClient.downloadDecisionAttachment(selectedDecisionId, attachment.id)
      const link = document.createElement('a')
      link.href = blobUrl
      link.download = attachment.file_name || `attachment_${attachment.id}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(blobUrl)
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to download attachment')
    }
  }

  const handleDeleteAttachment = async (attachmentId: string) => {
    if (!selectedDecisionId) return

    if (!window.confirm('Are you sure you want to delete this attachment?')) {
      return
    }

    try {
      await apiClient.deleteDecisionAttachment(selectedDecisionId, attachmentId)
      await loadAttachments(selectedDecisionId)
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to delete attachment')
    }
  }

  const formatFileSize = (bytes: number | null | undefined): string => {
    if (!bytes) return '-'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const loadDecisions = async () => {
    try {
      setLoading(true)
      setError(null)
      const params: any = {}
      if (filters.quarter) params.quarter = filters.quarter
      if (filters.status) params.status = filters.status
      if (filters.lob) params.lob = filters.lob
      if (filters.market) params.market = filters.market
      
      const data = await apiClient.getDecisions(params)
      setDecisions(data)
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to load decisions')
    } finally {
      setLoading(false)
    }
  }

  const handleOpenDialog = (decision?: Decision) => {
    if (decision) {
      setEditingDecision(decision)
      setFormData({
        policy_id: decision.policy_id,
        quarter: decision.quarter,
        lob: decision.lob || '',
        market: decision.market || '',
        recommended_action: decision.recommended_action,
        owner_user_id: decision.owner_user_id || '',
        due_date: decision.due_date ? format(new Date(decision.due_date), 'yyyy-MM-dd') : '',
        decision_rationale_md: decision.decision_rationale_md || '',
      })
    } else {
      setEditingDecision(null)
      setFormData({
        policy_id: '',
        quarter: '',
        lob: '',
        market: '',
        recommended_action: 'REVIEW',
        owner_user_id: '',
        due_date: '',
        decision_rationale_md: '',
      })
    }
    setDialogOpen(true)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
    setEditingDecision(null)
  }

  const handleSubmit = async () => {
    try {
      setError(null)
      if (editingDecision) {
        await apiClient.updateDecision(editingDecision.id, formData)
      } else {
        await apiClient.createDecision(formData)
      }
      handleCloseDialog()
      loadDecisions()
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to save decision')
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'error'> = {
      OPEN: 'default',
      IN_REVIEW: 'primary',
      DECIDED: 'success',
      DEFERRED: 'warning',
    }
    return colors[status] || 'default'
  }

  const getActionColor = (action: string) => {
    const colors: Record<string, 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'error'> = {
      KEEP: 'success',
      MODIFY: 'warning',
      RETIRE: 'error',
      REVIEW: 'default',
    }
    return colors[action] || 'default'
  }

  if (loading && decisions.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography
          variant="h4"
          component="h1"
          sx={{
            fontFamily: 'IBM Plex Sans, Inter, sans-serif',
            fontWeight: 600,
            mb: 1,
            color: healthForesightColors.neutral.dark,
          }}
        >
          Decisions
        </Typography>
        <Typography
          variant="body1"
          sx={{
            color: healthForesightColors.neutral.mid,
            lineHeight: 1.6,
            mb: 2,
          }}
        >
          Track policy decisions, rationale, and outcomes. Document keep/modify/retire decisions with attachments and audit trails.
        </Typography>
      </Box>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 3 }}>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          New Decision
        </Button>
      </Box>

      <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Quarter</InputLabel>
          <Select
            value={filters.quarter}
            label="Quarter"
            onChange={(e) => setFilters({ ...filters, quarter: e.target.value })}
          >
            <MenuItem value="">All</MenuItem>
            <MenuItem value="2024-Q1">2024 Q1</MenuItem>
            <MenuItem value="2024-Q2">2024 Q2</MenuItem>
            <MenuItem value="2024-Q3">2024 Q3</MenuItem>
            <MenuItem value="2024-Q4">2024 Q4</MenuItem>
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Status</InputLabel>
          <Select
            value={filters.status}
            label="Status"
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          >
            <MenuItem value="">All</MenuItem>
            {STATUSES.map((status) => (
              <MenuItem key={status} value={status}>
                {status.replace(/_/g, ' ')}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>LOB</InputLabel>
          <Select
            value={filters.lob}
            label="LOB"
            onChange={(e) => setFilters({ ...filters, lob: e.target.value })}
          >
            <MenuItem value="">All</MenuItem>
            <MenuItem value="COMMERCIAL">Commercial</MenuItem>
            <MenuItem value="MA">Medicare Advantage</MenuItem>
            <MenuItem value="MEDICAID">Medicaid</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {decisions.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No decisions found
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Create your first decision to track policy actions
          </Typography>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => handleOpenDialog()}>
            Create Decision
          </Button>
        </Paper>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Policy ID</TableCell>
                <TableCell>Quarter</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Recommended</TableCell>
                <TableCell>Decided</TableCell>
                <TableCell>Due Date</TableCell>
                <TableCell>Updated</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {decisions.map((decision) => (
                <TableRow key={decision.id} hover>
                  <TableCell>{getPolicyName(decision.policy_id)}</TableCell>
                  <TableCell>{decision.quarter}</TableCell>
                  <TableCell>
                    <Chip
                      label={decision.status.replace(/_/g, ' ')}
                      color={getStatusColor(decision.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={decision.recommended_action}
                      color={getActionColor(decision.recommended_action)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {decision.decided_action ? (
                      <Chip
                        label={decision.decided_action}
                        color={getActionColor(decision.decided_action)}
                        size="small"
                      />
                    ) : (
                      '-'
                    )}
                  </TableCell>
                  <TableCell>
                    {decision.due_date
                      ? format(new Date(decision.due_date), 'MMM d, yyyy')
                      : '-'}
                  </TableCell>
                  <TableCell>
                    {format(new Date(decision.updated_at), 'MMM d, yyyy')}
                  </TableCell>
                  <TableCell align="right">
                    <IconButton
                      size="small"
                      onClick={() => handleOpenAttachmentsDialog(decision.id)}
                      title="Attachments"
                    >
                      <AttachFileIcon fontSize="small" />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handleOpenDialog(decision)}
                      title="Edit"
                    >
                      <EditIcon fontSize="small" />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingDecision ? 'Edit Decision' : 'Create New Decision'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <FormControl fullWidth required>
              <InputLabel>Policy</InputLabel>
              <Select
                value={formData.policy_id}
                label="Policy"
                onChange={(e) => setFormData({ ...formData, policy_id: e.target.value })}
              >
                {policies.map((policy) => (
                  <MenuItem key={policy.id} value={policy.id}>
                    {policy.name} ({policy.policy_type})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="Quarter"
              fullWidth
              required
              value={formData.quarter}
              onChange={(e) => setFormData({ ...formData, quarter: e.target.value })}
              placeholder="2024-Q1"
            />
            <TextField
              label="LOB"
              fullWidth
              value={formData.lob}
              onChange={(e) => setFormData({ ...formData, lob: e.target.value })}
            />
            <TextField
              label="Market"
              fullWidth
              value={formData.market}
              onChange={(e) => setFormData({ ...formData, market: e.target.value })}
            />
            <FormControl fullWidth>
              <InputLabel>Recommended Action</InputLabel>
              <Select
                value={formData.recommended_action}
                label="Recommended Action"
                onChange={(e) => setFormData({ ...formData, recommended_action: e.target.value })}
              >
                {ACTIONS.map((action) => (
                  <MenuItem key={action} value={action}>
                    {action}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="Due Date"
              type="date"
              fullWidth
              value={formData.due_date}
              onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
              InputLabelProps={{ shrink: true }}
            />
            <TextField
              label="Rationale"
              fullWidth
              multiline
              rows={4}
              value={formData.decision_rationale_md}
              onChange={(e) => setFormData({ ...formData, decision_rationale_md: e.target.value })}
              placeholder="Markdown supported"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingDecision ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Attachments Dialog */}
      <Dialog open={attachmentsDialogOpen} onClose={handleCloseAttachmentsDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          Attachments
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, pt: 1 }}>
            {/* Upload Section */}
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Upload File
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Button
                    variant="outlined"
                    component="label"
                    startIcon={<CloudUploadIcon />}
                    fullWidth
                  >
                    {uploadFile ? uploadFile.name : 'Select File'}
                    <input
                      type="file"
                      hidden
                      onChange={(e) => {
                        const file = e.target.files?.[0]
                        if (file) {
                          setUploadFile(file)
                          if (!uploadLabel) {
                            setUploadLabel(file.name)
                          }
                        }
                      }}
                    />
                  </Button>
                  <TextField
                    label="Label"
                    fullWidth
                    value={uploadLabel}
                    onChange={(e) => setUploadLabel(e.target.value)}
                    placeholder="Attachment label"
                  />
                  <Button
                    variant="contained"
                    onClick={handleUploadFile}
                    disabled={!uploadFile || uploading}
                    startIcon={uploading ? <CircularProgress size={20} /> : <CloudUploadIcon />}
                  >
                    {uploading ? 'Uploading...' : 'Upload'}
                  </Button>
                </Box>
              </CardContent>
            </Card>

            {/* Attachments List */}
            <Box>
              <Typography variant="h6" gutterBottom>
                Attached Files ({attachments.length})
              </Typography>
              {attachmentsLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                  <CircularProgress />
                </Box>
              ) : attachments.length === 0 ? (
                <Typography variant="body2" color="text.secondary" sx={{ p: 2, textAlign: 'center' }}>
                  No attachments yet. Upload a file to get started.
                </Typography>
              ) : (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Label</TableCell>
                        <TableCell>File Name</TableCell>
                        <TableCell>Size</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Created</TableCell>
                        <TableCell align="right">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {attachments.map((attachment) => (
                        <TableRow key={attachment.id}>
                          <TableCell>{attachment.label}</TableCell>
                          <TableCell>{attachment.file_name || '-'}</TableCell>
                          <TableCell>{formatFileSize(attachment.file_size_bytes)}</TableCell>
                          <TableCell>{attachment.content_type || '-'}</TableCell>
                          <TableCell>
                            {attachment.created_at
                              ? format(new Date(attachment.created_at), 'MMM d, yyyy')
                              : '-'}
                          </TableCell>
                          <TableCell align="right">
                            {attachment.download_url && (
                              <IconButton
                                size="small"
                                onClick={() => handleDownloadAttachment(attachment)}
                                title="Download"
                              >
                                <DownloadIcon fontSize="small" />
                              </IconButton>
                            )}
                            <IconButton
                              size="small"
                              onClick={() => handleDeleteAttachment(attachment.id)}
                              title="Delete"
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
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseAttachmentsDialog}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
