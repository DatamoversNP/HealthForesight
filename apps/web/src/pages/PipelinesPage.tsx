/**
 * Pipelines Management Page
 * Lists all pipelines (preconfigured and custom), with ability to run, edit, activate/deactivate
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
  Typography,
  Alert,
  CircularProgress,
  Switch,
  FormControlLabel,
  Tabs,
  Tab,
} from '@mui/material'
import {
  PlayArrow as PlayIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Add as AddIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material'
import PipelineConfigurationDialog from '../components/pipelines/PipelineConfigurationDialog'
import PipelineRunHistoryDialog from '../components/pipelines/PipelineRunHistoryDialog'
import { apiClient } from '../lib/api'
import { format } from 'date-fns'
import { healthForesightColors } from '../theme/healthForesightTheme'

interface Pipeline {
  pipeline_id: string
  pipeline_name: string
  pipeline_description?: string
  source_type: string
  target_dataset_type: string
  target_model: string
  mode: string
  active: boolean
  created_at: string
  updated_at: string
  tags?: string[]
}

interface PipelineRun {
  run_id: string
  pipeline_id: string
  status: string
  started_at?: string
  completed_at?: string
  records_processed: number
  records_succeeded: number
  records_failed: number
  records_duplicated: number
}

export default function PipelinesPage() {
  const [pipelines, setPipelines] = useState<Pipeline[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [configDialogOpen, setConfigDialogOpen] = useState(false)
  const [runHistoryDialogOpen, setRunHistoryDialogOpen] = useState(false)
  const [selectedPipeline, setSelectedPipeline] = useState<Pipeline | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [tabValue, setTabValue] = useState(0)
  const [activeOnly, setActiveOnly] = useState(false)

  useEffect(() => {
    loadPipelines()
  }, [activeOnly])

  const loadPipelines = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.getPipelines({ active_only: activeOnly })
      setPipelines(data)
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to load pipelines')
    } finally {
      setLoading(false)
    }
  }

  const handleCreatePipeline = () => {
    setSelectedPipeline(null)
    setIsEditing(false)
    setConfigDialogOpen(true)
  }

  const handleEditPipeline = (pipeline: Pipeline) => {
    setSelectedPipeline(pipeline)
    setIsEditing(true)
    setConfigDialogOpen(true)
  }

  const handleDeletePipeline = async (pipelineId: string) => {
    if (!window.confirm('Are you sure you want to delete this pipeline?')) {
      return
    }

    try {
      await apiClient.deletePipeline(pipelineId)
      loadPipelines()
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to delete pipeline')
    }
  }

  const handleToggleActive = async (pipeline: Pipeline) => {
    try {
      await apiClient.activatePipeline(pipeline.pipeline_id, !pipeline.active)
      loadPipelines()
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to toggle pipeline status')
    }
  }

  const handleRunPipeline = async (pipeline: Pipeline) => {
    if (!pipeline.active) {
      setError('Cannot run inactive pipeline. Please activate it first.')
      return
    }

    try {
      setError(null)
      // Open file upload dialog or use source URI
      const fileInput = document.createElement('input')
      fileInput.type = 'file'
      fileInput.accept = '.csv,.parquet,.json,.xlsx,.xls'
      fileInput.onchange = async (e: any) => {
        const file = e.target.files?.[0]
        if (file) {
          try {
            await apiClient.runPipeline(pipeline.pipeline_id, file)
            setError(null)
            loadPipelines()
            // Show success message
            alert(`Pipeline "${pipeline.pipeline_name}" executed successfully!`)
          } catch (err: any) {
            setError(err.detail || err.message || 'Failed to run pipeline')
          }
        }
      }
      fileInput.click()
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to run pipeline')
    }
  }

  const handleViewRunHistory = (pipeline: Pipeline) => {
    setSelectedPipeline(pipeline)
    setRunHistoryDialogOpen(true)
  }

  const getStatusColor = (active: boolean) => {
    return active ? 'success' : 'default'
  }

  const getModeColor = (mode: string) => {
    const colors: Record<string, 'default' | 'primary' | 'secondary'> = {
      APPEND: 'primary',
      REPLACE: 'secondary',
      UPSERT: 'default',
    }
    return colors[mode] || 'default'
  }

  if (loading && pipelines.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    )
  }

  // Separate preconfigured and custom pipelines
  const preconfiguredPipelines = pipelines.filter((p) => p.tags?.includes('preconfigured'))
  const customPipelines = pipelines.filter((p) => !p.tags?.includes('preconfigured'))

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
          Ingestion Pipelines
        </Typography>
        <Typography
          variant="body1"
          sx={{
            color: healthForesightColors.neutral.mid,
            lineHeight: 1.6,
            mb: 2,
          }}
        >
          Manage metadata-driven ingestion pipelines. Configure field mappings, deduplication, and ingestion modes.
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <FormControlLabel
          control={
            <Switch
              checked={activeOnly}
              onChange={(e) => setActiveOnly(e.target.checked)}
              size="small"
            />
          }
          label="Show active only"
        />
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleCreatePipeline}
        >
          New Pipeline
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)} sx={{ mb: 3 }}>
        <Tab label={`Preconfigured (${preconfiguredPipelines.length})`} />
        <Tab label={`Custom (${customPipelines.length})`} />
      </Tabs>

      {tabValue === 0 && (
        <>
          {preconfiguredPipelines.length === 0 ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No preconfigured pipelines found
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Run the seed script to create preconfigured pipelines
              </Typography>
            </Paper>
          ) : (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Name</TableCell>
                    <TableCell>Source Type</TableCell>
                    <TableCell>Target Model</TableCell>
                    <TableCell>Mode</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Created</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {preconfiguredPipelines.map((pipeline) => (
                    <TableRow key={pipeline.pipeline_id} hover>
                      <TableCell>
                        <Box>
                          <Typography variant="body2" fontWeight={600}>
                            {pipeline.pipeline_name}
                          </Typography>
                          {pipeline.pipeline_description && (
                            <Typography variant="caption" color="text.secondary">
                              {pipeline.pipeline_description}
                            </Typography>
                          )}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip label={pipeline.source_type} size="small" />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                          {pipeline.target_model}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={pipeline.mode}
                          size="small"
                          color={getModeColor(pipeline.mode)}
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          icon={pipeline.active ? <CheckCircleIcon /> : <CancelIcon />}
                          label={pipeline.active ? 'Active' : 'Inactive'}
                          color={getStatusColor(pipeline.active)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {format(new Date(pipeline.created_at), 'MMM d, yyyy')}
                      </TableCell>
                      <TableCell align="right">
                        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                          <IconButton
                            size="small"
                            onClick={() => handleRunPipeline(pipeline)}
                            title="Run Pipeline"
                            color="primary"
                            disabled={!pipeline.active}
                          >
                            <PlayIcon fontSize="small" />
                          </IconButton>
                          <IconButton
                            size="small"
                            onClick={() => handleViewRunHistory(pipeline)}
                            title="View Run History"
                          >
                            <ViewIcon fontSize="small" />
                          </IconButton>
                          <IconButton
                            size="small"
                            onClick={() => handleEditPipeline(pipeline)}
                            title="Edit Pipeline"
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                          <Switch
                            size="small"
                            checked={pipeline.active}
                            onChange={() => handleToggleActive(pipeline)}
                            title={pipeline.active ? 'Deactivate' : 'Activate'}
                          />
                          <IconButton
                            size="small"
                            onClick={() => handleDeletePipeline(pipeline.pipeline_id)}
                            title="Delete Pipeline"
                            color="error"
                          >
                            <DeleteIcon fontSize="small" />
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
          {customPipelines.length === 0 ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No custom pipelines found
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Create your first custom pipeline
              </Typography>
              <Button variant="contained" startIcon={<AddIcon />} onClick={handleCreatePipeline}>
                Create Pipeline
              </Button>
            </Paper>
          ) : (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Name</TableCell>
                    <TableCell>Source Type</TableCell>
                    <TableCell>Target Model</TableCell>
                    <TableCell>Mode</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Created</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {customPipelines.map((pipeline) => (
                    <TableRow key={pipeline.pipeline_id} hover>
                      <TableCell>
                        <Box>
                          <Typography variant="body2" fontWeight={600}>
                            {pipeline.pipeline_name}
                          </Typography>
                          {pipeline.pipeline_description && (
                            <Typography variant="caption" color="text.secondary">
                              {pipeline.pipeline_description}
                            </Typography>
                          )}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip label={pipeline.source_type} size="small" />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                          {pipeline.target_model}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={pipeline.mode}
                          size="small"
                          color={getModeColor(pipeline.mode)}
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          icon={pipeline.active ? <CheckCircleIcon /> : <CancelIcon />}
                          label={pipeline.active ? 'Active' : 'Inactive'}
                          color={getStatusColor(pipeline.active)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {format(new Date(pipeline.created_at), 'MMM d, yyyy')}
                      </TableCell>
                      <TableCell align="right">
                        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                          <IconButton
                            size="small"
                            onClick={() => handleRunPipeline(pipeline)}
                            title="Run Pipeline"
                            color="primary"
                            disabled={!pipeline.active}
                          >
                            <PlayIcon fontSize="small" />
                          </IconButton>
                          <IconButton
                            size="small"
                            onClick={() => handleViewRunHistory(pipeline)}
                            title="View Run History"
                          >
                            <ViewIcon fontSize="small" />
                          </IconButton>
                          <IconButton
                            size="small"
                            onClick={() => handleEditPipeline(pipeline)}
                            title="Edit Pipeline"
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                          <Switch
                            size="small"
                            checked={pipeline.active}
                            onChange={() => handleToggleActive(pipeline)}
                            title={pipeline.active ? 'Deactivate' : 'Activate'}
                          />
                          <IconButton
                            size="small"
                            onClick={() => handleDeletePipeline(pipeline.pipeline_id)}
                            title="Delete Pipeline"
                            color="error"
                          >
                            <DeleteIcon fontSize="small" />
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

      {/* Pipeline Configuration Dialog */}
      <PipelineConfigurationDialog
        open={configDialogOpen}
        onClose={() => {
          setConfigDialogOpen(false)
          setSelectedPipeline(null)
          setIsEditing(false)
        }}
        onSave={() => {
          setConfigDialogOpen(false)
          setSelectedPipeline(null)
          setIsEditing(false)
          loadPipelines()
        }}
        pipeline={selectedPipeline}
        isEditing={isEditing}
      />

      {/* Pipeline Run History Dialog */}
      {selectedPipeline && (
        <PipelineRunHistoryDialog
          open={runHistoryDialogOpen}
          onClose={() => {
            setRunHistoryDialogOpen(false)
            setSelectedPipeline(null)
          }}
          pipeline={selectedPipeline}
        />
      )}
    </Box>
  )
}

