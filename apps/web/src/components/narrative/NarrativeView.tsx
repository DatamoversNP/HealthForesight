/**
 * Narrative View Component - Epic 7
 * Displays executive narrative for a resource
 */
import { useState, useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  Button,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Divider,
} from '@mui/material'
import {
  Description as DescriptionIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Lightbulb as LightbulbIcon,
  Download as DownloadIcon,
} from '@mui/icons-material'
import { apiClient } from '../../lib/api'

interface Narrative {
  narrative_id: string
  resource_type: string
  resource_id: string
  executive_summary: string
  key_findings: string[]
  risks: Array<{ risk: string; mitigation: string }>
  recommended_action: string
  generated_at: string
  generated_by: string
}

interface NarrativeViewProps {
  resourceType: string
  resourceId: string
}

export default function NarrativeView({ resourceType, resourceId }: NarrativeViewProps) {
  const [narrative, setNarrative] = useState<Narrative | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadNarrative()
  }, [resourceType, resourceId])

  const loadNarrative = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.getNarratives({
        resource_type: resourceType,
        resource_id: resourceId,
      })
      const narratives = Array.isArray(data) ? data : []
      if (narratives.length > 0) {
        setNarrative(narratives[0]) // Get most recent
      }
    } catch (err: any) {
      console.error('Failed to load narrative:', err)
      setError(err.detail || err.message || 'Failed to load narrative')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateExport = async () => {
    try {
      // Create export pack
      await apiClient.createExportPack({
        template_type: 'board_pack',
        resource_type: resourceType,
        resource_id: resourceId,
      })
      alert('Export pack generated successfully!')
    } catch (err: any) {
      console.error('Failed to generate export:', err)
      alert('Failed to generate export pack')
    }
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    )
  }

  if (!narrative) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Executive Narrative
          </Typography>
          <Typography variant="body2" color="text.secondary">
            No narrative available. Generate one to see executive summary and key findings.
          </Typography>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">
            Executive Narrative
          </Typography>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleGenerateExport}
          >
            Export Pack
          </Button>
        </Box>

        <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: 'block' }}>
          Generated: {new Date(narrative.generated_at).toLocaleString()}
        </Typography>

        {/* Executive Summary */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle1" gutterBottom fontWeight="bold">
            Executive Summary
          </Typography>
          <Typography variant="body1" paragraph>
            {narrative.executive_summary}
          </Typography>
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Key Findings */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle1" gutterBottom fontWeight="bold">
            Key Findings
          </Typography>
          <List>
            {narrative.key_findings.map((finding, idx) => (
              <ListItem key={idx}>
                <ListItemIcon>
                  <CheckIcon color="success" />
                </ListItemIcon>
                <ListItemText primary={finding} />
              </ListItem>
            ))}
          </List>
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Risks */}
        {narrative.risks && narrative.risks.length > 0 && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle1" gutterBottom fontWeight="bold">
              Risks & Mitigations
            </Typography>
            <List>
              {narrative.risks.map((riskItem, idx) => (
                <ListItem key={idx} alignItems="flex-start">
                  <ListItemIcon>
                    <WarningIcon color="warning" />
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box>
                        <Typography variant="body2" fontWeight="medium" gutterBottom>
                          {riskItem.risk}
                        </Typography>
                        <Chip
                          icon={<LightbulbIcon />}
                          label={`Mitigation: ${riskItem.mitigation}`}
                          size="small"
                          color="info"
                          sx={{ mt: 0.5 }}
                        />
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        <Divider sx={{ my: 2 }} />

        {/* Recommended Action */}
        <Box>
          <Typography variant="subtitle1" gutterBottom fontWeight="bold">
            Recommended Action
          </Typography>
          <Typography variant="body1">
            {narrative.recommended_action}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  )
}

