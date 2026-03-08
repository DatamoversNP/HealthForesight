/**
 * Ingestion Dashboard Page
 */
import { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
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
  Tabs,
  Tab,
} from '@mui/material'
import {
  CloudUpload as UploadIcon,
  Refresh as RefreshIcon,
  Error as ErrorIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  Visibility as ViewIcon,
  Close as CloseIcon,
} from '@mui/icons-material'
import DataViewer from '../components/DataViewer'
import SchemaMappingDialog from '../components/ingestion/SchemaMappingDialog'
import CoverageMetrics from '../components/ingestion/CoverageMetrics'
import { apiClient } from '../lib/api'
import { useIngestionUpdates } from '../hooks/useWebSocket'
import { format } from 'date-fns'
import { healthForesightColors } from '../theme/healthForesightTheme'

interface Ingestion {
  id: string
  ingestion_type: string
  status: string
  created_at: string
  started_at?: string
  completed_at?: string
  metadata?: any
  manifest_uri?: string
}

interface IngestionError {
  id: string
  error_type: string
  error_message: string
  row_number?: number
  file_path?: string
}

const INGESTION_TYPES = [
  'CLAIMS_LINES',
  'MEMBER_MASTER',
  'ELIGIBILITY_ENROLLMENT',
  'PROVIDER_MASTER',
  'PHARMACY_CLAIMS',
  'RISK_STRATIFICATION',
  'MARKET_EVENT', // Add MARKET_EVENT to supported ingestion types
  'CLAIMS',
  'ENROLLMENT',
  'PROVIDERS',
]

export default function IngestionDashboardPage() {
  const [ingestions, setIngestions] = useState<Ingestion[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [selectedIngestion, setSelectedIngestion] = useState<Ingestion | null>(null)
  const [ingestionErrors, setIngestionErrors] = useState<IngestionError[]>([])
  const [tabValue, setTabValue] = useState(0)
  const [datasets, setDatasets] = useState<any[]>([])
  const [selectedDataset, setSelectedDataset] = useState<any | null>(null)
  const [dataViewerOpen, setDataViewerOpen] = useState(false)
  const [lastExecuted, setLastExecuted] = useState<Ingestion | null>(null)
  const [sourceDataViewerOpen, setSourceDataViewerOpen] = useState(false)
  const [curatedDataViewerOpen, setCuratedDataViewerOpen] = useState(false)
  const [sourceData, setSourceData] = useState<any>(null)
  const [curatedData, setCuratedData] = useState<any>(null)
  const [formData, setFormData] = useState({
    ingestion_type: 'CLAIMS',
    manifest_uri: '',
  })
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploading, setUploading] = useState(false)
  const [schemaAnalysisDialogOpen, setSchemaAnalysisDialogOpen] = useState(false)
  const [schemaAnalysis, setSchemaAnalysis] = useState<any>(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [mappingConfig, setMappingConfig] = useState<any>(null)

  useEffect(() => {
    loadIngestions()
    loadDatasets()
    loadLastExecuted()
  }, [])

  const loadLastExecuted = async () => {
    try {
      const last = await apiClient.getLastExecutedIngestion()
      setLastExecuted(last)
    } catch (err: any) {
      // Ignore if no ingestions exist
      console.log('No last executed ingestion:', err)
    }
  }

  // Real-time updates for selected ingestion
  const [selectedIngestionId, setSelectedIngestionId] = useState<string | null>(null)
  useIngestionUpdates(selectedIngestionId, (data) => {
    // Update ingestion status in real-time
    setIngestions((prev) =>
      prev.map((ing) =>
        ing.id === data.ingestion_id
          ? { ...ing, status: data.status, ...data }
          : ing
      )
    )
    if (data.status === 'COMPLETED' || data.status === 'FAILED') {
      loadIngestions() // Refresh full list
    }
  })

  const loadIngestions = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.getIngestions()
      setIngestions(data)
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to load ingestions')
    } finally {
      setLoading(false)
    }
  }

  const loadDatasets = async () => {
    try {
      const data = await apiClient.getDatasets()
      setDatasets(data)
    } catch (err: any) {
      console.error('Error loading datasets:', err)
      // Don't show error - datasets may not exist yet
      setDatasets([])
    }
  }

  const handleViewData = async (dataset: any) => {
    setSelectedDataset(dataset)
    setDataViewerOpen(true)
  }

  const handleOpenDialog = () => {
    setFormData({
      ingestion_type: 'CLAIMS',
      manifest_uri: '',
    })
    setUploadFile(null)
    setMappingConfig(null)
    setSchemaAnalysis(null)
    setDialogOpen(true)
  }

  const handleFileSelect = async (file: File) => {
    setUploadFile(file)
    
    // Auto-analyze schema when file is selected
    if (file) {
      setAnalyzing(true)
      try {
        const analysis = await apiClient.analyzeSchema(file, formData.ingestion_type)
        setSchemaAnalysis(analysis)
        // Auto-open mapping dialog if there are unmapped columns
        if (analysis.coverage && analysis.coverage.unmapped_source?.length > 0) {
          setSchemaAnalysisDialogOpen(true)
        }
      } catch (err: any) {
        console.error('Failed to analyze schema:', err)
        setError(err.detail || err.message || 'Failed to analyze file schema')
      } finally {
        setAnalyzing(false)
      }
    }
  }

  const handleMappingConfirm = (mapping: any) => {
    setMappingConfig(mapping)
    setSchemaAnalysisDialogOpen(false)
  }

  const handleUploadAndIngest = async () => {
    if (!uploadFile) {
      setError('Please select a file to upload')
      return
    }

    try {
      setUploading(true)
      setError(null)
      
      const result = await apiClient.uploadAndIngest(
        uploadFile,
        formData.ingestion_type,
        !mappingConfig, // auto_detect if no manual mapping
        mappingConfig || undefined
      )
      
      // Refresh after successful ingestion
      await loadIngestions()
      await loadLastExecuted()
      await loadDatasets()

      handleCloseDialog()
      loadIngestions()
      loadLastExecuted()
      
      if (result.processing_result) {
        if (result.processing_result.success) {
          setError(null)
        } else {
          setError(
            `Ingestion completed with ${result.processing_result.records_invalid} invalid records. ` +
            `See ingestion details for error information.`
          )
        }
      }
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to upload and ingest file')
    } finally {
      setUploading(false)
    }
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
    setUploadFile(null)
    setMappingConfig(null)
    setSchemaAnalysis(null)
    setSchemaAnalysisDialogOpen(false)
  }

  const handleSubmit = async () => {
    try {
      setError(null)
      await apiClient.createIngestion(formData)
      handleCloseDialog()
      loadIngestions()
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to create ingestion')
    }
  }

  const handleViewErrors = async (ingestion: Ingestion) => {
    setSelectedIngestion(ingestion)
    setSelectedIngestionId(ingestion.id)
    setTabValue(2) // Errors tab is at index 2 (after Ingestions=0, Datasets=1)
    try {
      const errors = await apiClient.getIngestionErrors(ingestion.id)
      setIngestionErrors(errors)
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to load errors')
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

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <CheckCircleIcon fontSize="small" />
      case 'FAILED':
        return <ErrorIcon fontSize="small" />
      case 'PROCESSING':
        return <ScheduleIcon fontSize="small" />
      default:
        return undefined
    }
  }

  if (loading && ingestions.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Box sx={{ mb: 3 }} className="ingestion-header">
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
          Data & Ingestion
        </Typography>
        <Typography
          variant="body1"
          sx={{
            color: healthForesightColors.neutral.mid,
            lineHeight: 1.6,
            mb: 2,
          }}
        >
          Manage data ingestion pipelines and view ingested datasets. Upload files, monitor ingestion status, and validate data quality.
        </Typography>
      </Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        {lastExecuted && (
          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Last Executed
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Chip
                label={lastExecuted.ingestion_type}
                size="small"
                color="primary"
                variant="outlined"
              />
              <Typography variant="body2">
                {lastExecuted.completed_at
                  ? format(new Date(lastExecuted.completed_at), 'MMM d, yyyy HH:mm')
                  : format(new Date(lastExecuted.created_at), 'MMM d, yyyy HH:mm')}
              </Typography>
              {lastExecuted.metadata?.coverage && (
                <Chip
                  label={`${((lastExecuted.metadata.coverage.completeness_score || 0) * 100).toFixed(0)}% complete`}
                  size="small"
                  color={
                    (lastExecuted.metadata.coverage.completeness_score || 0) >= 0.9
                      ? 'success'
                      : (lastExecuted.metadata.coverage.completeness_score || 0) >= 0.7
                      ? 'warning'
                      : 'error'
                  }
                />
              )}
            </Box>
          </Box>
        )}
        <Button
          variant="contained"
          startIcon={<UploadIcon />}
          onClick={handleOpenDialog}
        >
          New Ingestion
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)} sx={{ mb: 3 }}>
        <Tab label="Ingestions" />
        <Tab label="Datasets" />
        {selectedIngestion && <Tab label="Errors" />}
      </Tabs>

      {tabValue === 0 && (
        <>
          {ingestions.length === 0 ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No ingestions found
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Create your first ingestion to upload data
              </Typography>
              <Button variant="contained" startIcon={<UploadIcon />} onClick={handleOpenDialog}>
                Create Ingestion
              </Button>
            </Paper>
          ) : (
            <TableContainer component={Paper} className="ingestion-list">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Type</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Created</TableCell>
                    <TableCell>Started</TableCell>
                    <TableCell>Completed</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {ingestions.map((ingestion) => (
                    <TableRow key={ingestion.id} hover>
                      <TableCell>
                        <Chip label={ingestion.ingestion_type} size="small" />
                      </TableCell>
                      <TableCell>
                        <Chip
                          icon={getStatusIcon(ingestion.status)}
                          label={ingestion.status}
                          color={getStatusColor(ingestion.status)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {format(new Date(ingestion.created_at), 'MMM d, yyyy HH:mm')}
                      </TableCell>
                      <TableCell>
                        {ingestion.started_at
                          ? format(new Date(ingestion.started_at), 'MMM d, yyyy HH:mm')
                          : '-'}
                      </TableCell>
                      <TableCell>
                        {ingestion.completed_at
                          ? format(new Date(ingestion.completed_at), 'MMM d, yyyy HH:mm')
                          : '-'}
                      </TableCell>
                      <TableCell align="right">
                        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                          {(ingestion.status === 'PENDING' || ingestion.status === 'FAILED') && (
                            <Button
                              size="small"
                              variant="outlined"
                              onClick={async () => {
                                try {
                                  await apiClient.runIngestion(ingestion.id)
                                  loadIngestions()
                                  loadLastExecuted()
                                } catch (err: any) {
                                  setError(err.detail || err.message || 'Failed to run ingestion')
                                }
                              }}
                              title="Run Ingestion"
                            >
                              Run
                            </Button>
                          )}
                          {ingestion.status === 'COMPLETED' && (
                            <>
                              <Button
                                size="small"
                                variant="outlined"
                                startIcon={<ViewIcon />}
                                onClick={async () => {
                                  try {
                                    const data = await apiClient.viewSourceData(ingestion.id)
                                    setSourceData(data)
                                    setSourceDataViewerOpen(true)
                                  } catch (err: any) {
                                    setError(err.detail || err.message || 'Failed to load source data')
                                  }
                                }}
                                title="View Source Data"
                              >
                                Source
                              </Button>
                              <Button
                                size="small"
                                variant="outlined"
                                startIcon={<ViewIcon />}
                                onClick={async () => {
                                  try {
                                    const data = await apiClient.viewCuratedData(ingestion.id)
                                    setCuratedData(data)
                                    setCuratedDataViewerOpen(true)
                                  } catch (err: any) {
                                    setError(err.detail || err.message || 'Failed to load curated data')
                                  }
                                }}
                                title="View Curated Data"
                              >
                                Curated
                              </Button>
                            </>
                          )}
                          {ingestion.status === 'FAILED' && (
                            <IconButton
                              size="small"
                              onClick={() => handleViewErrors(ingestion)}
                              title="View Errors"
                            >
                              <ErrorIcon fontSize="small" />
                            </IconButton>
                          )}
                          <IconButton
                            size="small"
                            onClick={() => {
                              loadIngestions()
                              loadLastExecuted()
                            }}
                            title="Refresh"
                          >
                            <RefreshIcon fontSize="small" />
                          </IconButton>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </>
      )}

      {tabValue === 1 && (
        <>
          {datasets.length === 0 ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No datasets found
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Datasets will appear here after successful ingestion
              </Typography>
            </Paper>
          ) : (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Type</TableCell>
                    <TableCell>Year</TableCell>
                    <TableCell>Month</TableCell>
                    <TableCell>LOB</TableCell>
                    <TableCell>Market</TableCell>
                    <TableCell>Records</TableCell>
                    <TableCell>Created</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {datasets.map((dataset) => (
                    <TableRow key={dataset.id} hover>
                      <TableCell>
                        <Chip label={dataset.dataset_type} size="small" color="primary" />
                      </TableCell>
                      <TableCell>{dataset.year}</TableCell>
                      <TableCell>{String(dataset.month).padStart(2, '0')}</TableCell>
                      <TableCell>{dataset.lob || '-'}</TableCell>
                      <TableCell>{dataset.market || '-'}</TableCell>
                      <TableCell>{dataset.record_count?.toLocaleString() || 0}</TableCell>
                      <TableCell>
                        {format(new Date(dataset.created_at), 'MMM d, yyyy')}
                      </TableCell>
                      <TableCell align="right">
                        <IconButton
                          size="small"
                          onClick={() => handleViewData(dataset)}
                          title="View Data"
                          color="primary"
                        >
                          <ViewIcon fontSize="small" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </>
      )}

      {tabValue === 2 && selectedIngestion && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Ingestion Errors: {selectedIngestion.id}
          </Typography>
          {ingestionErrors.length === 0 ? (
            <Typography color="text.secondary">No errors found</Typography>
          ) : (
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Type</TableCell>
                    <TableCell>Message</TableCell>
                    <TableCell>Row</TableCell>
                    <TableCell>File</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {ingestionErrors.map((err) => (
                    <TableRow key={err.id}>
                      <TableCell>
                        <Chip label={err.error_type} size="small" color="error" />
                      </TableCell>
                      <TableCell>{err.error_message}</TableCell>
                      <TableCell>{err.row_number || '-'}</TableCell>
                      <TableCell>{err.file_path || '-'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Paper>
      )}

      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth className="upload-section">
        <DialogTitle>Create New Ingestion</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField
              label="Ingestion Type"
              select
              fullWidth
              required
              value={formData.ingestion_type}
              onChange={(e) => setFormData({ ...formData, ingestion_type: e.target.value })}
            >
              {INGESTION_TYPES.map((type) => (
                <MenuItem key={type} value={type}>
                  {type}
                </MenuItem>
              ))}
            </TextField>
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Upload File
              </Typography>
              <input
                accept=".csv,.json,.parquet,.xlsx,.xls,.tsv"
                style={{ display: 'none' }}
                id="file-upload"
                type="file"
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  if (file) {
                    handleFileSelect(file)
                  }
                }}
              />
              <label htmlFor="file-upload">
                <Button variant="outlined" component="span" startIcon={<UploadIcon />} disabled={analyzing}>
                  {analyzing ? 'Analyzing...' : uploadFile ? uploadFile.name : 'Select File'}
                </Button>
              </label>
              {uploadFile && !analyzing && (
                <Box sx={{ mt: 1 }}>
                  <Button
                    size="small"
                    variant="text"
                    onClick={() => setSchemaAnalysisDialogOpen(true)}
                    disabled={!schemaAnalysis}
                  >
                    Configure Mapping
                  </Button>
                  {schemaAnalysis && schemaAnalysis.coverage && (
                    <Chip
                      label={`${schemaAnalysis.coverage.mapped}/${schemaAnalysis.coverage.total_canonical} fields mapped`}
                      size="small"
                      color={schemaAnalysis.coverage.mapped === schemaAnalysis.coverage.total_canonical ? 'success' : 'warning'}
                      sx={{ ml: 1 }}
                    />
                  )}
                </Box>
              )}
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button 
            onClick={handleUploadAndIngest} 
            variant="contained"
            disabled={!uploadFile || uploading || analyzing}
          >
            {uploading ? 'Uploading...' : 'Upload & Ingest'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Schema Mapping Dialog */}
      <SchemaMappingDialog
        open={schemaAnalysisDialogOpen}
        onClose={() => setSchemaAnalysisDialogOpen(false)}
        onConfirm={handleMappingConfirm}
        schemaAnalysis={schemaAnalysis}
        ingestionType={formData.ingestion_type}
      />

      {/* Data Viewer Dialog */}
      <Dialog
        open={dataViewerOpen}
        onClose={() => setDataViewerOpen(false)}
        maxWidth="xl"
        fullWidth
        PaperProps={{
          sx: { height: '90vh' },
        }}
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">Data Viewer</Typography>
            <IconButton onClick={() => setDataViewerOpen(false)} size="small">
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent dividers sx={{ overflow: 'auto' }}>
          {selectedDataset && <DataViewer dataset={selectedDataset} onClose={() => setDataViewerOpen(false)} />}
        </DialogContent>
      </Dialog>
    </Box>
  )
}
