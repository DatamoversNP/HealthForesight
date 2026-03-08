/**
 * Audit Log – system and decision audit trail (placeholder)
 */
import { Box, Container, Typography, Button, Paper } from '@mui/material'
import { History as HistoryIcon } from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'

export default function AuditLogPage() {
  const navigate = useNavigate()

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <HistoryIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
        <Typography variant="h5" gutterBottom>
          Audit Log
        </Typography>
        <Typography color="text.secondary" sx={{ mb: 3 }}>
          View system and decision audit trail. Decision-level audit entries are available in Decisions.
        </Typography>
        <Button variant="contained" onClick={() => navigate('/decisions')}>
          Open Decisions
        </Button>
      </Paper>
    </Container>
  )
}
