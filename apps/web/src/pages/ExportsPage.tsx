/**
 * Exports Page - Enhanced with download and status tracking
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
  LinearProgress,
  MenuItem,
  Paper,
  Select,
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
} from '@mui/material'
import {
  Download as DownloadIcon,
  FileDownload as FileDownloadIcon,
  Refresh as RefreshIcon,
  PictureAsPdf as PdfIcon,
  Description as DocIcon,
  Error as ErrorIcon,
  History as HistoryIcon,
  Add as AddIcon,
  CompareArrows as CompareIcon,
} from '@mui/icons-material'
import { apiClient } from '../lib/api'
import { format } from 'date-fns'
import { healthForesightColors } from '../theme/healthForesightTheme'

interface Export {
  id: string
  analysis_id?: string
  export_type: string
  status: string
  file_uri?: string
  file_size_bytes?: number
  download_count: number
  version_number?: number
  change_description?: string
  created_at: string
  completed_at?: string
  error_message?: string
}

const EXPORT_TYPES = ['PDF', 'PPTX', 'AUDIT_PACK']

export default function ExportsPage() {
  const [exports, setExports] = useState<Export[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [downloading, setDownloading] = useState<string | null>(null)
  const [analyses, setAnalyses] = useState<any[]>([])
  const [formData, setFormData] = useState({
    analysis_id: '',
    export_type: 'PDF',
  })

  const [trackingExportId, setTrackingExportId] = useState<string | null>(null)
  const [pollingInterval, setPollingInterval] = useState<number | null>(null)
  const [versionsDialogOpen, setVersionsDialogOpen] = useState(false)
  const [selectedExportId, setSelectedExportId] = useState<string | null>(null)
  const [versions, setVersions] = useState<any[]>([])
  const [versionsLoading, setVersionsLoading] = useState(false)
  const [createVersionDialogOpen, setCreateVersionDialogOpen] = useState(false)
  const [newVersionDescription, setNewVersionDescription] = useState('')
  const [creatingVersion, setCreatingVersion] = useState(false)

  useEffect(() => {
    loadExports()
    loadAnalyses()
    
    // Cleanup polling on unmount
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval)
      }
    }
  }, [])
  
  const loadAnalyses = async () => {
    try {
      const data = await apiClient.getAnalyses({ limit: 100 })
      const analysesList = Array.isArray(data) ? data : (data.items || [])
      setAnalyses(analysesList)
    } catch (err) {
      console.error('Error loading analyses:', err)
    }
  }

  // Poll for export status updates if tracking an export
  useEffect(() => {
    if (trackingExportId) {
      const interval = setInterval(async () => {
        try {
          const exportData = await apiClient.getExport(trackingExportId)
          setExports((prev) =>
            prev.map((exp) =>
              exp.id === trackingExportId ? { ...exp, ...exportData } : exp
            )
          )
          if (exportData.status === 'COMPLETED' || exportData.status === 'FAILED') {
            setTrackingExportId(null)
            if (pollingInterval) {
              clearInterval(pollingInterval)
            }
            loadExports() // Refresh full list
          }
        } catch (err) {
          console.error('Failed to poll export status:', err)
        }
      }, 2000) // Poll every 2 seconds
      
      setPollingInterval(interval)
      
      return () => {
        clearInterval(interval)
      }
    }
  }, [trackingExportId])

  const loadExports = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.listExports()
      setExports(data)
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to load exports')
      console.error('Failed to load exports:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleOpenDialog = () => {
    setFormData({
      analysis_id: '',
      export_type: 'PDF',
    })
    setDialogOpen(true)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
  }

  const handleCreateExport = async () => {
    try {
      setError(null)
      const exportResult = await apiClient.createExport({
        analysis_id: formData.analysis_id,
        export_type: formData.export_type,
      })
      handleCloseDialog()
      loadExports()
      // Start tracking this export for status updates
      if (exportResult?.id) {
        setTrackingExportId(exportResult.id)
      }
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to create export')
    }
  }

  const handleDownload = async (exportItem: Export) => {
    try {
      setDownloading(exportItem.id)
      setError(null)
      
      // Download file and get blob URL
      const blobUrl = await apiClient.downloadExport(exportItem.id)
      
      // Create download link and trigger download
      const link = document.createElement('a')
      link.href = blobUrl
      link.download = `export_${exportItem.id}.${exportItem.export_type === 'PPTX' ? 'pptx' : 'pdf'}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
      // Cleanup blob URL after a delay
      setTimeout(() => {
        window.URL.revokeObjectURL(blobUrl)
        loadExports() // Reload to update download count
      }, 1000)
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to download export')
      setDownloading(null)
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'error'> = {
      PENDING: 'default',
      PROCESSING: 'primary',
      COMPLETED: 'success',
      FAILED: 'error',
    }
    return colors[status] || 'default'
  }

  const getExportIcon = (type: string) => {
    switch (type) {
      case 'PDF':
        return <PdfIcon />
      case 'PPTX':
        return <DocIcon />
      default:
        return <FileDownloadIcon />
    }
  }

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '-'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const handleOpenVersionsDialog = async (exportId: string) => {
    setSelectedExportId(exportId)
    setVersionsDialogOpen(true)
    await loadVersions(exportId)
  }

  const loadVersions = async (exportId: string) => {
    try {
      setVersionsLoading(true)
      const data = await apiClient.getExportVersions(exportId)
      setVersions(Array.isArray(data) ? data : [])
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to load versions')
    } finally {
      setVersionsLoading(false)
    }
  }

  const handleCreateVersion = async () => {
    if (!selectedExportId) return

    try {
      setCreatingVersion(true)
      setError(null)
      await apiClient.createExportVersion(selectedExportId, newVersionDescription)
      setCreateVersionDialogOpen(false)
      setNewVersionDescription('')
      await loadVersions(selectedExportId)
      await loadExports() // Refresh exports list
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to create version')
    } finally {
      setCreatingVersion(false)
    }
  }

  if (loading && exports.length === 0) {
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
          Exports
        </Typography>
        <Button
          variant="contained"
          startIcon={<FileDownloadIcon />}
          onClick={handleOpenDialog}
        >
          New Export
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {exports.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No exports found
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Create your first export to download analysis reports
          </Typography>
          <Button variant="contained" startIcon={<FileDownloadIcon />} onClick={handleOpenDialog}>
            Create Export
          </Button>
        </Paper>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Type</TableCell>
                <TableCell>Analysis ID</TableCell>
                <TableCell>Version</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>File Size</TableCell>
                <TableCell>Downloads</TableCell>
                <TableCell>Created</TableCell>
                <TableCell>Completed</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {exports.map((exportItem) => (
                <TableRow key={exportItem.id} hover>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {getExportIcon(exportItem.export_type)}
                      <Chip label={exportItem.export_type} size="small" />
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" noWrap sx={{ maxWidth: 150 }}>
                      {exportItem.analysis_id || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={`v${exportItem.version_number || 1}`}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={exportItem.status}
                      color={getStatusColor(exportItem.status)}
                      size="small"
                    />
                    {exportItem.status === 'PROCESSING' && (
                      <LinearProgress sx={{ mt: 1, height: 2 }} />
                    )}
                  </TableCell>
                  <TableCell>{formatFileSize(exportItem.file_size_bytes)}</TableCell>
                  <TableCell>{exportItem.download_count}</TableCell>
                  <TableCell>
                    {format(new Date(exportItem.created_at), 'MMM d, yyyy HH:mm')}
                  </TableCell>
                  <TableCell>
                    {exportItem.completed_at
                      ? format(new Date(exportItem.completed_at), 'MMM d, yyyy HH:mm')
                      : '-'}
                  </TableCell>
                  <TableCell align="right">
                    {exportItem.status === 'COMPLETED' && (
                      <>
                        <Tooltip title="Version History">
                          <IconButton
                            size="small"
                            onClick={() => handleOpenVersionsDialog(exportItem.id)}
                          >
                            <HistoryIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Download">
                          <IconButton
                            size="small"
                            onClick={() => handleDownload(exportItem)}
                            disabled={downloading === exportItem.id}
                          >
                            {downloading === exportItem.id ? (
                              <CircularProgress size={20} />
                            ) : (
                              <DownloadIcon fontSize="small" />
                            )}
                          </IconButton>
                        </Tooltip>
                      </>
                    )}
                    {exportItem.status === 'PROCESSING' && (
                      <IconButton size="small" onClick={loadExports} title="Refresh">
                        <RefreshIcon fontSize="small" />
                      </IconButton>
                    )}
                    {exportItem.error_message && (
                      <Tooltip title={exportItem.error_message}>
                        <IconButton size="small" color="error">
                          <ErrorIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Export</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <FormControl fullWidth required>
              <InputLabel>Analysis</InputLabel>
              <Select
                value={formData.analysis_id}
                label="Analysis"
                onChange={(e) => setFormData({ ...formData, analysis_id: e.target.value })}
              >
                {analyses.map((analysis) => (
                  <MenuItem key={analysis.id} value={analysis.id}>
                    {analysis.analysis_type} - {analysis.id.substring(0, 8)} ({analysis.status})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel>Export Type</InputLabel>
              <Select
                value={formData.export_type}
                label="Export Type"
                onChange={(e) => setFormData({ ...formData, export_type: e.target.value })}
              >
                {EXPORT_TYPES.map((type) => (
                  <MenuItem key={type} value={type}>
                    {type.replace(/_/g, ' ')}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Alert severity="info">
              {formData.export_type === 'PDF' && 'Generates a comprehensive PDF report with analysis results, charts, and methodology.'}
              {formData.export_type === 'PPTX' && 'Generates a PowerPoint presentation for steering committee meetings.'}
              {formData.export_type === 'AUDIT_PACK' && 'Generates a complete audit pack with all supporting documentation.'}
            </Alert>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleCreateExport} variant="contained">
            Create Export
          </Button>
        </DialogActions>
      </Dialog>

      {/* Versions Dialog */}
      <Dialog open={versionsDialogOpen} onClose={() => setVersionsDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Export Versions
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            {versionsLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress />
              </Box>
            ) : versions.length === 0 ? (
              <Typography variant="body2" color="text.secondary" sx={{ p: 2, textAlign: 'center' }}>
                No versions found.
              </Typography>
            ) : (
              <>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="h6">
                    Version History ({versions.length})
                  </Typography>
                  <Button
                    variant="contained"
                    size="small"
                    startIcon={<AddIcon />}
                    onClick={() => {
                      setCreateVersionDialogOpen(true)
                    }}
                  >
                    Create New Version
                  </Button>
                </Box>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Version</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>File Size</TableCell>
                        <TableCell>Downloads</TableCell>
                        <TableCell>Change Description</TableCell>
                        <TableCell>Created</TableCell>
                        <TableCell align="right">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {versions.map((version) => (
                        <TableRow key={version.id}>
                          <TableCell>
                            <Chip label={`v${version.version_number}`} size="small" variant="outlined" />
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={version.status}
                              color={getStatusColor(version.status)}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>{formatFileSize(version.file_size_bytes)}</TableCell>
                          <TableCell>{version.download_count}</TableCell>
                          <TableCell>
                            <Typography variant="body2" sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                              {version.change_description || '-'}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            {version.created_at
                              ? format(new Date(version.created_at), 'MMM d, yyyy HH:mm')
                              : '-'}
                          </TableCell>
                          <TableCell align="right">
                            {version.status === 'COMPLETED' && (
                              <Tooltip title="Download">
                                <IconButton
                                  size="small"
                                  onClick={async () => {
                                    const exportItem = exports.find(e => e.id === version.id) || version
                                    await handleDownload(exportItem)
                                  }}
                                >
                                  <DownloadIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setVersionsDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Create Version Dialog */}
      <Dialog open={createVersionDialogOpen} onClose={() => setCreateVersionDialogOpen(false)}>
        <DialogTitle>Create New Version</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1, minWidth: 400 }}>
            <TextField
              label="Change Description"
              fullWidth
              multiline
              rows={4}
              value={newVersionDescription}
              onChange={(e) => setNewVersionDescription(e.target.value)}
              placeholder="Describe what changed in this version..."
              helperText="This description will help track changes across versions"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateVersionDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleCreateVersion}
            variant="contained"
            disabled={creatingVersion}
            startIcon={creatingVersion ? <CircularProgress size={20} /> : <AddIcon />}
          >
            {creatingVersion ? 'Creating...' : 'Create Version'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
