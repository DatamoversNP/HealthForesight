/**
 * Risk Register Component - Epic 4
 * Displays and manages risk drivers for a policy
 */
import { useState, useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  LinearProgress,
  Alert,
  CircularProgress,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
  IconButton,
  Tooltip,
} from '@mui/material'
import {
  Warning as WarningIcon,
  Edit as EditIcon,
  Add as AddIcon,
} from '@mui/icons-material'
import { apiClient } from '../../lib/api'

interface RiskDriver {
  driver_name: string
  impact_score: number // 0-1
  uncertainty_contribution: number
  mitigation_action?: string
  owner?: string
}

interface RiskRegisterData {
  policy_id: string
  top_drivers: RiskDriver[]
  overall_risk_score: number // 0-1
  last_updated: string
}

interface RiskRegisterProps {
  policyId: string
}

export default function RiskRegister({ policyId }: RiskRegisterProps) {
  const [riskRegister, setRiskRegister] = useState<RiskRegisterData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editingDriver, setEditingDriver] = useState<RiskDriver | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [formData, setFormData] = useState<Partial<RiskDriver>>({
    driver_name: '',
    impact_score: 0.5,
    uncertainty_contribution: 0.5,
    mitigation_action: '',
    owner: '',
  })

  useEffect(() => {
    loadRiskRegister()
  }, [policyId])

  const loadRiskRegister = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.getRiskRegisterForPolicy(policyId)
      setRiskRegister(data)
    } catch (err: any) {
      if (err.status === 404) {
        // No risk register exists yet - that's okay
        setRiskRegister(null)
      } else {
        console.error('Failed to load risk register:', err)
        setError(err.detail || err.message || 'Failed to load risk register')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleOpenDialog = (driver?: RiskDriver) => {
    if (driver) {
      setEditingDriver(driver)
      setFormData(driver)
    } else {
      setEditingDriver(null)
      setFormData({
        driver_name: '',
        impact_score: 0.5,
        uncertainty_contribution: 0.5,
        mitigation_action: '',
        owner: '',
      })
    }
    setDialogOpen(true)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
    setEditingDriver(null)
  }

  const handleSaveDriver = async () => {
    try {
      if (!editingDriver) {
        // Create new driver - would need to add to risk register
        setError('Adding new drivers not yet implemented. Please update existing drivers.')
        return
      }

      // Update existing driver
      await apiClient.updateRiskDriver(policyId, editingDriver.driver_name, {
        impact_score: formData.impact_score,
        uncertainty_contribution: formData.uncertainty_contribution,
        mitigation_action: formData.mitigation_action,
        owner: formData.owner,
      })

      handleCloseDialog()
      await loadRiskRegister()
    } catch (err: any) {
      console.error('Failed to save driver:', err)
      setError(err.detail || err.message || 'Failed to save driver')
    }
  }

  const getRiskColor = (score: number) => {
    if (score >= 0.7) return 'error'
    if (score >= 0.4) return 'warning'
    return 'info'
  }

  const getRiskLabel = (score: number) => {
    if (score >= 0.7) return 'High'
    if (score >= 0.4) return 'Medium'
    return 'Low'
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    )
  }

  if (error && !riskRegister) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    )
  }

  if (!riskRegister || !riskRegister.top_drivers || riskRegister.top_drivers.length === 0) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Risk Register
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            No risk register exists for this policy yet. Create one via the API or backend.
          </Typography>
        </CardContent>
      </Card>
    )
  }

  const sortedDrivers = [...riskRegister.top_drivers].sort(
    (a, b) => b.impact_score - a.impact_score
  )

  return (
    <>
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">
              Risk Register
            </Typography>
            <Chip
              icon={<WarningIcon />}
              label={`Overall Risk: ${getRiskLabel(riskRegister.overall_risk_score)} (${(riskRegister.overall_risk_score * 100).toFixed(0)}%)`}
              color={getRiskColor(riskRegister.overall_risk_score)}
              size="medium"
            />
          </Box>

          <Box sx={{ mb: 2 }}>
            <LinearProgress
              variant="determinate"
              value={riskRegister.overall_risk_score * 100}
              color={getRiskColor(riskRegister.overall_risk_score)}
              sx={{ height: 10, borderRadius: 1 }}
            />
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Risk Driver</strong></TableCell>
                  <TableCell align="right"><strong>Impact Score</strong></TableCell>
                  <TableCell align="right"><strong>Uncertainty Contribution</strong></TableCell>
                  <TableCell><strong>Mitigation Action</strong></TableCell>
                  <TableCell><strong>Owner</strong></TableCell>
                  <TableCell align="center"><strong>Actions</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {sortedDrivers.map((driver) => (
                  <TableRow key={driver.driver_name} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {driver.driver_name}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Box display="flex" alignItems="center" justifyContent="flex-end" gap={1}>
                        <Box sx={{ width: 80 }}>
                          <LinearProgress
                            variant="determinate"
                            value={driver.impact_score * 100}
                            color={getRiskColor(driver.impact_score)}
                            sx={{ height: 8, borderRadius: 1 }}
                          />
                        </Box>
                        <Typography variant="body2" sx={{ minWidth: 40 }}>
                          {(driver.impact_score * 100).toFixed(0)}%
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2">
                        {(driver.uncertainty_contribution * 100).toFixed(1)}%
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {driver.mitigation_action || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {driver.owner || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Tooltip title="Edit driver">
                        <IconButton
                          size="small"
                          onClick={() => handleOpenDialog(driver)}
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          <Box sx={{ mt: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Last updated: {new Date(riskRegister.last_updated).toLocaleString()}
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* Edit Driver Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingDriver ? 'Edit Risk Driver' : 'Add Risk Driver'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Driver Name"
                value={formData.driver_name || ''}
                onChange={(e) => setFormData({ ...formData, driver_name: e.target.value })}
                disabled={!!editingDriver}
                required
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                type="number"
                label="Impact Score"
                value={formData.impact_score}
                onChange={(e) => setFormData({ ...formData, impact_score: parseFloat(e.target.value) || 0 })}
                inputProps={{ min: 0, max: 1, step: 0.01 }}
                helperText="0.0 to 1.0"
                required
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                type="number"
                label="Uncertainty Contribution"
                value={formData.uncertainty_contribution}
                onChange={(e) => setFormData({ ...formData, uncertainty_contribution: parseFloat(e.target.value) || 0 })}
                inputProps={{ min: 0, max: 1, step: 0.01 }}
                helperText="0.0 to 1.0"
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Mitigation Action"
                value={formData.mitigation_action || ''}
                onChange={(e) => setFormData({ ...formData, mitigation_action: e.target.value })}
                placeholder="Describe the mitigation action for this risk driver..."
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Owner"
                value={formData.owner || ''}
                onChange={(e) => setFormData({ ...formData, owner: e.target.value })}
                placeholder="Person or team responsible"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSaveDriver} variant="contained" disabled={!formData.driver_name}>
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </>
  )
}
