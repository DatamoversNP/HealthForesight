import React from 'react'
import {
  Box,
  Typography,
  Chip,
  Link,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material'
import {
  ExpandMore as ExpandMoreIcon,
  Link as LinkIcon,
  Timeline as TimelineIcon,
  Description as DescriptionIcon,
} from '@mui/icons-material'

interface TraceabilityLink {
  type: 'data_period' | 'policy_version' | 'baseline' | 'prediction' | 'observation'
  id: string
  label?: string
  timestamp?: string
}

interface TraceabilityDisplayProps {
  dataPeriodId?: string | null
  policyVersionId?: string | null
  baselineVersionId?: string | null
  predictionId?: string | null
  observationId?: string | null
  onNavigate?: (type: string, id: string) => void
  expanded?: boolean
}

export const TraceabilityDisplay: React.FC<TraceabilityDisplayProps> = ({
  dataPeriodId,
  policyVersionId,
  baselineVersionId,
  predictionId,
  observationId,
  onNavigate,
  expanded = false,
}) => {
  const links: TraceabilityLink[] = []

  if (dataPeriodId) {
    links.push({
      type: 'data_period',
      id: dataPeriodId,
      label: 'Data Period',
    })
  }

  if (policyVersionId) {
    links.push({
      type: 'policy_version',
      id: policyVersionId,
      label: 'Policy Version',
    })
  }

  if (baselineVersionId) {
    links.push({
      type: 'baseline',
      id: baselineVersionId,
      label: 'Baseline Version',
    })
  }

  if (predictionId) {
    links.push({
      type: 'prediction',
      id: predictionId,
      label: 'Predicted Impact',
    })
  }

  if (observationId) {
    links.push({
      type: 'observation',
      id: observationId,
      label: 'Observed Impact',
    })
  }

  if (links.length === 0) {
    return (
      <Box>
        <Typography variant="body2" color="text.secondary">
          No traceability information available
        </Typography>
      </Box>
    )
  }

  const handleClick = (link: TraceabilityLink) => {
    if (onNavigate) {
      onNavigate(link.type, link.id)
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'data_period':
        return <DescriptionIcon fontSize="small" />
      case 'policy_version':
        return <DescriptionIcon fontSize="small" />
      case 'baseline':
        return <TimelineIcon fontSize="small" />
      case 'prediction':
        return <TimelineIcon fontSize="small" />
      case 'observation':
        return <TimelineIcon fontSize="small" />
      default:
        return <LinkIcon fontSize="small" />
    }
  }

  const getTypeColor = (type: string): 'default' | 'primary' | 'secondary' | 'success' | 'warning' => {
    switch (type) {
      case 'data_period':
        return 'default'
      case 'policy_version':
        return 'primary'
      case 'baseline':
        return 'secondary'
      case 'prediction':
        return 'warning'
      case 'observation':
        return 'success'
      default:
        return 'default'
    }
  }

  return (
    <Accordion defaultExpanded={expanded}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Box display="flex" alignItems="center" gap={1}>
          <TimelineIcon fontSize="small" color="action" />
          <Typography variant="subtitle2">Traceability</Typography>
          <Chip label={links.length} size="small" variant="outlined" />
        </Box>
      </AccordionSummary>
      <AccordionDetails>
        <List dense>
          {links.map((link, index) => (
            <React.Fragment key={`${link.type}-${link.id}`}>
              <ListItem
                button={!!onNavigate}
                onClick={() => handleClick(link)}
                sx={{ cursor: onNavigate ? 'pointer' : 'default' }}
              >
                <Box display="flex" alignItems="center" gap={1} width="100%">
                  {getTypeIcon(link.type)}
                  <ListItemText
                    primary={link.label || link.type.replace('_', ' ')}
                    secondary={link.id.substring(0, 8) + '...'}
                  />
                  <Chip
                    label={link.type.replace('_', ' ')}
                    size="small"
                    color={getTypeColor(link.type)}
                    variant="outlined"
                    sx={{ ml: 'auto' }}
                  />
                </Box>
              </ListItem>
              {index < links.length - 1 && <Divider />}
            </React.Fragment>
          ))}
        </List>
      </AccordionDetails>
    </Accordion>
  )
}
