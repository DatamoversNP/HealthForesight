/**
 * Data Health Dashboard Page
 * Shows completeness, validation errors, lineage, and refresh status
 */
import { useState, useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
} from '@mui/material'
import {
  Refresh as RefreshIcon,
  Error as ErrorIcon,
  CheckCircle as CheckCircleIcon,
  Timeline as LineageIcon,
  Close as CloseIcon,
  Download as DownloadIcon,
} from '@mui/icons-material'
import { apiClient } from '../lib/api'
import { format } from 'date-fns'
import { healthForesightColors } from '../theme/healthForesightTheme'

interface CompletenessGrid {
  [lob: string]: {
    [market: string]: {
      [month: string]: number
    }
  }
}

interface CompletenessData {
  completeness_grid: CompletenessGrid
  summary: {
    total_records: number
    unique_months: number
    unique_lobs: number
    unique_markets: number
    total_datasets: number
  }
  last_updated: string | null
}

interface ValidationError {
  id: string
  ingestion_id: string
  error_type: string
  error_message: string
  row_number: number | null
  file_path: string | null
  created_at: string
}

interface ValidationErrorsData {
  errors: ValidationError[]
  summary: {
    total_errors: number
    by_type: { [type: string]: number }
  }
}

interface LineageData {
  ingestions: Array<{
    id: string
    ingestion_type: string
    status: string
    manifest_uri: string
    created_at: string
    started_at: string | null
    completed_at: string | null
  }>
  datasets: Array<{
    id: string
    dataset_type: string
    year: number
    month: number
    lob: string | null
    market: string | null
    record_count: number | null
    data_uri: string
    created_at: string
  }>
  analysis_runs: any[]
}

interface RefreshStatus {
  last_refresh: string | null
  last_refresh_status: string | null
  recent_runs: Array<{
    id: string
    ingestion_type: string
    status: string
    created_at: string
    completed_at: string | null
  }>
  statistics: {
    total_runs_30d: number
    successful_runs: number
    failed_runs: number
    success_rate: number
  }
}

export default function DataHealthPage() {
  const [tabValue, setTabValue] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Completeness
  const [completeness, setCompleteness] = useState<CompletenessData | null>(null)
  
  // Validation Errors
  const [validationErrors, setValidationErrors] = useState<ValidationErrorsData | null>(null)
  const [selectedError, setSelectedError] = useState<ValidationError | null>(null)
  const [errorDialogOpen, setErrorDialogOpen] = useState(false)
  
  // Lineage
  const [lineage, setLineage] = useState<LineageData | null>(null)
  
  // Refresh Status
  const [refreshStatus, setRefreshStatus] = useState<RefreshStatus | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    
    try {
      // Load all data in parallel
      const [completeness, errors, lineage, status] = await Promise.all([
        apiClient.getDataCompleteness(),
        apiClient.getValidationErrors(),
        apiClient.getDataLineage(),
        apiClient.getRefreshStatus(),
      ])
      
      setCompleteness(completeness)
      setValidationErrors(errors)
      setLineage(lineage)
      setRefreshStatus(status)
    } catch (err: any) {
      setError(err.message || 'Failed to load data health information')
      console.error('Error loading data health:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleErrorClick = (error: ValidationError) => {
    setSelectedError(error)
    setErrorDialogOpen(true)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return 'success'
      case 'FAILED':
        return 'error'
      case 'PROCESSING':
        return 'warning'
      default:
        return 'default'
    }
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box p={3}>
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
          Data Health
        </Typography>
        <Typography
          variant="body1"
          sx={{
            color: healthForesightColors.neutral.mid,
            lineHeight: 1.6,
            mb: 2,
          }}
        >
          Monitor data completeness, validation status, and lineage. View coverage heatmap and validation errors.
        </Typography>
      </Box>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 3 }}>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={loadData}
        >
          Refresh
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Refresh Status Widget */}
      {refreshStatus && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Refresh Status
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Last Refresh
                </Typography>
                <Typography variant="body1" fontWeight="bold">
                  {refreshStatus.last_refresh
                    ? format(new Date(refreshStatus.last_refresh), 'MMM d, yyyy HH:mm')
                    : 'Never'}
                </Typography>
                {refreshStatus.last_refresh_status && (
                  <Chip
                    label={refreshStatus.last_refresh_status}
                    color={getStatusColor(refreshStatus.last_refresh_status) as any}
                    size="small"
                    sx={{ mt: 1 }}
                  />
                )}
              </Grid>
              <Grid item xs={12} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Success Rate (30d)
                </Typography>
                <Typography variant="body1" fontWeight="bold">
                  {refreshStatus.statistics.success_rate.toFixed(1)}%
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {refreshStatus.statistics.successful_runs} / {refreshStatus.statistics.total_runs_30d} successful
                </Typography>
              </Grid>
              <Grid item xs={12} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Total Runs (30d)
                </Typography>
                <Typography variant="body1" fontWeight="bold">
                  {refreshStatus.statistics.total_runs_30d}
                </Typography>
              </Grid>
              <Grid item xs={12} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Failed Runs (30d)
                </Typography>
                <Typography variant="body1" fontWeight="bold" color="error">
                  {refreshStatus.statistics.failed_runs}
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
          <Tab label="Completeness" />
          <Tab label="Validation Errors" />
          <Tab label="Lineage" />
        </Tabs>
      </Paper>

      {/* Completeness Tab */}
      {tabValue === 0 && completeness && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Data Completeness
            </Typography>
            
            {/* Summary */}
            <Grid container spacing={2} sx={{ mb: 3 }}>
              <Grid item xs={12} md={3}>
                <Typography variant="body2" color="text.secondary">Total Records</Typography>
                <Typography variant="h5">{completeness.summary.total_records.toLocaleString()}</Typography>
              </Grid>
              <Grid item xs={12} md={3}>
                <Typography variant="body2" color="text.secondary">Unique Months</Typography>
                <Typography variant="h5">{completeness.summary.unique_months}</Typography>
              </Grid>
              <Grid item xs={12} md={3}>
                <Typography variant="body2" color="text.secondary">LOBs</Typography>
                <Typography variant="h5">{completeness.summary.unique_lobs}</Typography>
              </Grid>
              <Grid item xs={12} md={3}>
                <Typography variant="body2" color="text.secondary">Markets</Typography>
                <Typography variant="h5">{completeness.summary.unique_markets}</Typography>
              </Grid>
            </Grid>

            {/* Completeness Grid */}
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>LOB</TableCell>
                    <TableCell>Market</TableCell>
                    <TableCell>Months Covered</TableCell>
                    <TableCell>Record Count</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {Object.entries(completeness.completeness_grid).map(([lob, markets]) =>
                    Object.entries(markets).map(([market, months]) => {
                      const monthCount = Object.keys(months).length
                      const totalRecords = Object.values(months).reduce((a, b) => a + b, 0)
                      return (
                        <TableRow key={`${lob}-${market}`}>
                          <TableCell>{lob}</TableCell>
                          <TableCell>{market}</TableCell>
                          <TableCell>{monthCount} months</TableCell>
                          <TableCell>{totalRecords.toLocaleString()}</TableCell>
                        </TableRow>
                      )
                    })
                  )}
                  {Object.keys(completeness.completeness_grid).length === 0 && (
                    <TableRow>
                      <TableCell colSpan={4} align="center">
                        No data available
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* Validation Errors Tab */}
      {tabValue === 1 && validationErrors && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Validation Errors
            </Typography>
            
            {/* Error Summary */}
            {validationErrors.summary.total_errors > 0 && (
              <Box mb={3}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Error Summary by Type
                </Typography>
                <Box display="flex" gap={1} flexWrap="wrap">
                  {Object.entries(validationErrors.summary.by_type).map(([type, count]) => (
                    <Chip
                      key={type}
                      label={`${type}: ${count}`}
                      color="error"
                      variant="outlined"
                    />
                  ))}
                </Box>
              </Box>
            )}

            {/* Error Table */}
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Type</TableCell>
                    <TableCell>Message</TableCell>
                    <TableCell>Row</TableCell>
                    <TableCell>File</TableCell>
                    <TableCell>Date</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {validationErrors.errors.map((err) => (
                    <TableRow key={err.id} hover>
                      <TableCell>
                        <Chip label={err.error_type} size="small" color="error" />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" noWrap sx={{ maxWidth: 400 }}>
                          {err.error_message}
                        </Typography>
                      </TableCell>
                      <TableCell>{err.row_number || '-'}</TableCell>
                      <TableCell>
                        <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                          {err.file_path || '-'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {format(new Date(err.created_at), 'MMM d, yyyy')}
                      </TableCell>
                      <TableCell>
                        <Button
                          size="small"
                          onClick={() => handleErrorClick(err)}
                        >
                          Details
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                  {validationErrors.errors.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={6} align="center">
                        <CheckCircleIcon color="success" sx={{ fontSize: 48, opacity: 0.5, mb: 1 }} />
                        <Typography variant="body2" color="text.secondary">
                          No validation errors found
                        </Typography>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* Lineage Tab */}
      {tabValue === 2 && lineage && (
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Recent Ingestions
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Type</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Date</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {lineage.ingestions.slice(0, 10).map((ing) => (
                        <TableRow key={ing.id}>
                          <TableCell>{ing.ingestion_type}</TableCell>
                          <TableCell>
                            <Chip
                              label={ing.status}
                              size="small"
                              color={getStatusColor(ing.status) as any}
                            />
                          </TableCell>
                          <TableCell>
                            {format(new Date(ing.created_at), 'MMM d, yyyy')}
                          </TableCell>
                        </TableRow>
                      ))}
                      {lineage.ingestions.length === 0 && (
                        <TableRow>
                          <TableCell colSpan={3} align="center">
                            No ingestions found
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Recent Datasets
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Type</TableCell>
                        <TableCell>Period</TableCell>
                        <TableCell>Records</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {lineage.datasets.slice(0, 10).map((ds) => (
                        <TableRow key={ds.id}>
                          <TableCell>{ds.dataset_type}</TableCell>
                          <TableCell>
                            {ds.year}-{ds.month.toString().padStart(2, '0')}
                            {ds.lob && ` / ${ds.lob}`}
                            {ds.market && ` / ${ds.market}`}
                          </TableCell>
                          <TableCell>{ds.record_count?.toLocaleString() || '-'}</TableCell>
                        </TableRow>
                      ))}
                      {lineage.datasets.length === 0 && (
                        <TableRow>
                          <TableCell colSpan={3} align="center">
                            No datasets found
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Error Detail Dialog */}
      <Dialog open={errorDialogOpen} onClose={() => setErrorDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Error Details
          <IconButton
            onClick={() => setErrorDialogOpen(false)}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          {selectedError && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Error Type
              </Typography>
              <Chip label={selectedError.error_type} color="error" sx={{ mb: 2 }} />
              
              <Typography variant="subtitle2" gutterBottom>
                Message
              </Typography>
              <Typography variant="body2" sx={{ mb: 2, whiteSpace: 'pre-wrap' }}>
                {selectedError.error_message}
              </Typography>
              
              {selectedError.row_number && (
                <>
                  <Typography variant="subtitle2" gutterBottom>
                    Row Number
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 2 }}>
                    {selectedError.row_number}
                  </Typography>
                </>
              )}
              
              {selectedError.file_path && (
                <>
                  <Typography variant="subtitle2" gutterBottom>
                    File Path
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 2, fontFamily: 'monospace' }}>
                    {selectedError.file_path}
                  </Typography>
                </>
              )}
              
              <Typography variant="subtitle2" gutterBottom>
                Date
              </Typography>
              <Typography variant="body2">
                {format(new Date(selectedError.created_at), 'PPpp')}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setErrorDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

