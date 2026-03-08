/**
 * Policy Versions List Component
 * Epic 2: Policy Lifecycle Management
 * 
 * Displays policy version history and allows version comparison
 */
import { useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  List,
  ListItem,
  ListItemText,
  Chip,
  Alert,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material'
import {
  Compare as CompareIcon,
  History as HistoryIcon,
} from '@mui/icons-material'
import { format } from 'date-fns'
import { apiClient } from '../../lib/api'

interface PolicyVersionsListProps {
  policyId: string
  versions: any[]
  onRefresh: () => void
}

export default function PolicyVersionsList({
  policyId,
  versions,
  onRefresh,
}: PolicyVersionsListProps) {
  const [compareDialogOpen, setCompareDialogOpen] = useState(false)
  const [selectedVersions, setSelectedVersions] = useState<[any, any] | null>(null)

  const handleCompare = (v1: any, v2: any) => {
    setSelectedVersions([v1, v2])
    setCompareDialogOpen(true)
  }

  const getStateColor = (state: string) => {
    const colors: Record<string, 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'> = {
      DRAFT: 'default',
      PROPOSED: 'warning',
      APPROVED: 'info',
      ACTIVE: 'success',
      MONITORING: 'primary',
      ITERATING: 'warning',
      SUNSET: 'default',
    }
    return colors[state] || 'default'
  }

  if (versions.length === 0) {
    return (
      <Card variant="outlined">
        <CardContent>
          <Alert severity="info">
            No versions found. Versions are created automatically when policies are updated.
          </Alert>
        </CardContent>
      </Card>
    )
  }

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Version History
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {versions.length} version{versions.length !== 1 ? 's' : ''} total
        </Typography>
      </Box>

      <List>
        {versions.map((version: any, idx: number) => (
          <Card key={version.version_number} variant="outlined" sx={{ mb: 2 }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Box sx={{ flex: 1 }}>
                  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 1 }}>
                    <Typography variant="h6">
                      Version {version.version_number}
                    </Typography>
                    <Chip
                      label={version.state}
                      color={getStateColor(version.state)}
                      size="small"
                    />
                    {version.version_number === versions[0].version_number && (
                      <Chip label="Latest" color="primary" size="small" />
                    )}
                  </Box>
                  <Typography variant="body2" paragraph>
                    {version.change_summary || 'No summary provided'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" display="block">
                    Effective: {format(new Date(version.effective_start_date), 'MMM d, yyyy')}
                    {version.effective_end_date && ` - ${format(new Date(version.effective_end_date), 'MMM d, yyyy')}`}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" display="block">
                    Created: {format(new Date(version.created_at), 'MMM d, yyyy HH:mm')}
                  </Typography>
                  {version.approved_by && (
                    <Typography variant="caption" color="text.secondary" display="block">
                      Approved: {format(new Date(version.approved_at), 'MMM d, yyyy HH:mm')}
                    </Typography>
                  )}
                </Box>
                {idx > 0 && (
                  <Button
                    size="small"
                    startIcon={<CompareIcon />}
                    onClick={() => handleCompare(versions[0], version)}
                  >
                    Compare with Latest
                  </Button>
                )}
              </Box>
            </CardContent>
          </Card>
        ))}
      </List>

      {/* Comparison Dialog */}
      <Dialog
        open={compareDialogOpen}
        onClose={() => setCompareDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Version Comparison</DialogTitle>
        <DialogContent>
          {selectedVersions && (
            <TableContainer component={Paper}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Field</TableCell>
                    <TableCell>Version {selectedVersions[0].version_number} (Latest)</TableCell>
                    <TableCell>Version {selectedVersions[1].version_number}</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>State</TableCell>
                    <TableCell>
                      <Chip label={selectedVersions[0].state} color={getStateColor(selectedVersions[0].state)} size="small" />
                    </TableCell>
                    <TableCell>
                      <Chip label={selectedVersions[1].state} color={getStateColor(selectedVersions[1].state)} size="small" />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Effective Start</TableCell>
                    <TableCell>{format(new Date(selectedVersions[0].effective_start_date), 'MMM d, yyyy')}</TableCell>
                    <TableCell>{format(new Date(selectedVersions[1].effective_start_date), 'MMM d, yyyy')}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Change Summary</TableCell>
                    <TableCell>{selectedVersions[0].change_summary || 'N/A'}</TableCell>
                    <TableCell>{selectedVersions[1].change_summary || 'N/A'}</TableCell>
                  </TableRow>
                  {selectedVersions[0].change_details && Object.keys(selectedVersions[0].change_details).length > 0 && (
                    <TableRow>
                      <TableCell colSpan={3}>
                        <Typography variant="subtitle2" gutterBottom>
                          Change Details:
                        </Typography>
                        <pre style={{ fontSize: '0.875rem', margin: 0 }}>
                          {JSON.stringify(selectedVersions[0].change_details, null, 2)}
                        </pre>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCompareDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}


