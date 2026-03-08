/**
 * Admin – tenant and user administration (placeholder)
 */
import { Box, Container, Typography, Button, Paper } from '@mui/material'
import { AdminPanelSettings as AdminIcon } from '@mui/icons-material'

export default function AdminPage() {
  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <AdminIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
        <Typography variant="h5" gutterBottom>
          Admin
        </Typography>
        <Typography color="text.secondary">
          Tenant and user administration. Configure roles, permissions, and system settings here.
        </Typography>
      </Paper>
    </Container>
  )
}
