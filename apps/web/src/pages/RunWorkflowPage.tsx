/**
 * Run Workflow – execute data/workflow runs (placeholder; pipelines for run actions)
 */
import { Box, Container, Typography, Button, Paper } from '@mui/material'
import { PlayArrow as PlayIcon } from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'

export default function RunWorkflowPage() {
  const navigate = useNavigate()

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <PlayIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
        <Typography variant="h5" gutterBottom>
          Run Workflow
        </Typography>
        <Typography color="text.secondary" sx={{ mb: 3 }}>
          Execute pipelines and data workflows. Use Pipelines to configure and run workflows.
        </Typography>
        <Button variant="contained" onClick={() => navigate('/pipelines')}>
          Open Pipelines
        </Button>
      </Paper>
    </Container>
  )
}
