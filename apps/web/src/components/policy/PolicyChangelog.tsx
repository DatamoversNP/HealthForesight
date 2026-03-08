/**
 * Policy Changelog Component
 * Epic 2: Policy Lifecycle Management
 * 
 * Displays policy change history in a timeline format
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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
} from '@mui/material'
import { format } from 'date-fns'

interface PolicyChangelogProps {
  policyId: string
  changelog: any[]
  onRefresh: () => void
}

export default function PolicyChangelog({
  policyId,
  changelog,
  onRefresh,
}: PolicyChangelogProps) {
  const [filterType, setFilterType] = useState<string>('all')
  const [searchTerm, setSearchTerm] = useState('')

  const filteredChangelog = changelog.filter((entry: any) => {
    const matchesType = filterType === 'all' || entry.change_type === filterType
    const matchesSearch = !searchTerm || 
      entry.reason?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      entry.field_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      entry.change_type?.toLowerCase().includes(searchTerm.toLowerCase())
    return matchesType && matchesSearch
  })

  const getChangeTypeColor = (changeType: string) => {
    const colors: Record<string, 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'> = {
      created: 'success',
      updated: 'info',
      state_change: 'warning',
      assumption_added: 'primary',
      assumption_updated: 'primary',
      assumption_deleted: 'error',
      guardrail_added: 'primary',
      guardrail_updated: 'primary',
      guardrail_deleted: 'error',
      version_created: 'success',
      default: 'default',
    }
    return colors[changeType] || 'default'
  }

  const getChangeTypeIcon = (changeType: string) => {
    // Simplified - would use actual icons
    return '●'
  }

  const changeTypes = Array.from(new Set(changelog.map((e: any) => e.change_type)))

  if (changelog.length === 0) {
    return (
      <Card variant="outlined">
        <CardContent>
          <Alert severity="info">
            No changelog entries found. Changes will be logged automatically.
          </Alert>
        </CardContent>
      </Card>
    )
  }

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', gap: 2, alignItems: 'center' }}>
        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel>Filter by Type</InputLabel>
          <Select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            label="Filter by Type"
          >
            <MenuItem value="all">All Types</MenuItem>
            {changeTypes.map((type: string) => (
              <MenuItem key={type} value={type}>
                {type.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <TextField
          placeholder="Search changelog..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          size="small"
          sx={{ flex: 1 }}
        />
      </Box>

      <Card variant="outlined">
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Change History ({filteredChangelog.length} of {changelog.length})
          </Typography>
          <List>
            {filteredChangelog.map((entry: any, idx: number) => (
              <Card key={entry.change_id || idx} variant="outlined" sx={{ mb: 2 }}>
                <CardContent>
                  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 1 }}>
                    <Chip
                      label={entry.change_type.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                      size="small"
                      color={getChangeTypeColor(entry.change_type)}
                    />
                    <Typography variant="caption" color="text.secondary">
                      {format(new Date(entry.changed_at), 'MMM d, yyyy HH:mm')}
                    </Typography>
                  </Box>
                  {entry.field_name && (
                    <Typography variant="body2" color="text.secondary">
                      Field: <strong>{entry.field_name}</strong>
                    </Typography>
                  )}
                  {entry.reason && (
                    <Typography variant="body2" paragraph>
                      {entry.reason}
                    </Typography>
                  )}
                  {entry.old_value !== undefined && entry.new_value !== undefined && (
                    <Box sx={{ mt: 1, p: 1, bgcolor: 'grey.100', borderRadius: 1 }}>
                      <Typography variant="caption" color="text.secondary" display="block">
                        Changed from: <strong>{String(entry.old_value)}</strong>
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Changed to: <strong>{String(entry.new_value)}</strong>
                      </Typography>
                    </Box>
                  )}
                  {entry.version_number && (
                    <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
                      Version: {entry.version_number}
                    </Typography>
                  )}
                </CardContent>
              </Card>
            ))}
          </List>
        </CardContent>
      </Card>
    </Box>
  )
}

