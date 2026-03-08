/**
 * Pipeline Run History Dialog
 * Shows execution history for a pipeline
 */
import { useState, useEffect } from 'react'
import {
  Box,
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Typography,
  CircularProgress,
  Alert,
} from '@mui/material'
import {
  Close as CloseIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material'
import { apiClient } from '../../lib/api'
import { format } from 'date-fns'

interface Pipeline {
  pipeline_id: string
  pipeline_name: string
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
  errors?: any[]
}

interface PipelineRunHistoryDialogProps {
  open: boolean
  onClose: () => void
  pipeline: Pipeline
}

export default function PipelineRunHistoryDialog({
  open,
  onClose,
  pipeline,
}: PipelineRunHistoryDialogProps) {
  const [runs, setRuns] = useState<PipelineRun[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      loadRuns()
    }
  }, [open, pipeline.pipeline_id])

  const loadRuns = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.getPipelineRuns(pipeline.pipeline_id)
      setRuns(data)
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to load run history')
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, 'default' | 'primary' | 'success' | 'error'> = {
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

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">Run History: {pipeline.pipeline_name}</Typography>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>
      <DialogContent dividers>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : runs.length === 0 ? (
          <Box sx={{ textAlign: 'center', p: 4 }}>
            <Typography color="text.secondary">No runs found for this pipeline</Typography>
          </Box>
        ) : (
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Run ID</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Started</TableCell>
                  <TableCell>Completed</TableCell>
                  <TableCell>Processed</TableCell>
                  <TableCell>Succeeded</TableCell>
                  <TableCell>Failed</TableCell>
                  <TableCell>Duplicated</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {runs.map((run) => (
                  <TableRow key={run.run_id} hover>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                        {run.run_id.substring(0, 8)}...
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        icon={getStatusIcon(run.status)}
                        label={run.status}
                        color={getStatusColor(run.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {run.started_at
                        ? format(new Date(run.started_at), 'MMM d, yyyy HH:mm')
                        : '-'}
                    </TableCell>
                    <TableCell>
                      {run.completed_at
                        ? format(new Date(run.completed_at), 'MMM d, yyyy HH:mm')
                        : '-'}
                    </TableCell>
                    <TableCell>{run.records_processed.toLocaleString()}</TableCell>
                    <TableCell>
                      <Chip
                        label={run.records_succeeded.toLocaleString()}
                        size="small"
                        color="success"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      {run.records_failed > 0 ? (
                        <Chip
                          label={run.records_failed.toLocaleString()}
                          size="small"
                          color="error"
                          variant="outlined"
                        />
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell>
                      {run.records_duplicated > 0 ? (
                        <Chip
                          label={run.records_duplicated.toLocaleString()}
                          size="small"
                          color="warning"
                          variant="outlined"
                        />
                      ) : (
                        '-'
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </DialogContent>
    </Dialog>
  )
}

