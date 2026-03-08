/**
 * Metric Tooltip Component - Shows formula and description for metrics
 */
import { Tooltip, IconButton, Box, Typography } from '@mui/material'
import { Info as InfoIcon } from '@mui/icons-material'

interface MetricTooltipProps {
  metricName: string
  formula?: string
  description?: string
}

// Metric definitions with formulas
const METRIC_FORMULAS: Record<string, { formula: string; description: string }> = {
  // Provider Archetype Metrics
  total_claims: {
    formula: 'Mean(total_claims for each provider in cluster)',
    description: 'Average number of claim lines per provider in this archetype. Each provider\'s total_claims = count of claim lines for that provider. Then averaged across all providers in the cluster.',
  },
  total_cost: {
    formula: 'Mean(total_cost for each provider in cluster)',
    description: 'Average total cost per provider in this archetype. Each provider\'s total_cost = sum of allowed_amount (or paid_amount) for their claim lines. Then averaged across all providers in the cluster.',
  },
  avg_cost_per_claim: {
    formula: 'Mean(avg_cost_per_claim for each provider in cluster) where avg_cost_per_claim = total_cost / total_claims',
    description: 'Average cost per claim line. For each provider: total_cost / total_claims, then averaged across all providers in the cluster.',
  },
  claims_per_member: {
    formula: 'Mean(claims_per_member for each provider in cluster) where claims_per_member = total_claims / unique_members',
    description: 'Average claims per unique member. For each provider: total_claims / unique_members, then averaged across all providers in the cluster.',
  },
  
  // Baseline Metrics
  util_rate_total_per_1000_mm: {
    formula: '(Total claim lines / Member-months) × 1,000',
    description: 'Utilization rate per 1,000 member-months. Total claim lines divided by total member-months, multiplied by 1,000.',
  },
  allowed_pmpm_total: {
    formula: 'Total allowed amount / Member-months',
    description: 'Cost per member per month (PMPM). Total allowed amount (or paid_amount) divided by total member-months.',
  },
  cost_pmpm: {
    formula: 'Total cost / Member-months',
    description: 'Cost per member per month (PMPM). Alternative name for allowed_pmpm_total.',
  },
  total_cost_per_1k: {
    formula: '(Total cost / Member-months) × 1,000',
    description: 'Cost per 1,000 member-months. Total cost divided by member-months, multiplied by 1,000.',
  },
  
  // Additional common metric names (normalized)
  'util rate total per 1000 mm': {
    formula: '(Total claim lines / Member-months) × 1,000',
    description: 'Utilization rate per 1,000 member-months.',
  },
  'allowed pmpm total': {
    formula: 'Total allowed amount / Member-months',
    description: 'Cost per member per month (PMPM).',
  },
  
  // Patient Segment Metrics
  avg_claims_per_member: {
    formula: 'Mean(total_claims) across members in segment',
    description: 'Average number of claim lines per member in this patient segment.',
  },
  avg_cost_per_member: {
    formula: 'Mean(total_cost) across members in segment',
    description: 'Average total cost per member in this patient segment.',
  },
  avg_cost_per_claim: {
    formula: 'Mean(avg_cost_per_claim) across members in segment',
    description: 'Average cost per claim line for members in this segment.',
  },
}

export default function MetricTooltip({ metricName, formula, description }: MetricTooltipProps) {
  const metricInfo = METRIC_FORMULAS[metricName] || { formula: formula || 'N/A', description: description || 'No description available' }
  
  // Create a simple string tooltip for Material-UI Tooltip
  const tooltipText = `${metricName.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}\n\nFormula: ${metricInfo.formula}\n\nDescription: ${metricInfo.description}`
  
  // For rich content, use a custom component with proper styling - make it compact
  const tooltipContent = (
    <Box sx={{ p: 0.75, maxWidth: 250 }}>
      <Typography variant="caption" sx={{ fontWeight: 600, mb: 0.5, display: 'block', fontSize: '0.7rem', lineHeight: 1.2 }}>
        {metricName.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
      </Typography>
      <Typography variant="caption" sx={{ mb: 0.25, fontWeight: 500, display: 'block', fontSize: '0.65rem', lineHeight: 1.2 }}>
        Formula:
      </Typography>
      <Typography variant="caption" sx={{ mb: 0.75, fontFamily: 'monospace', fontSize: '0.6rem', display: 'block', wordBreak: 'break-word', lineHeight: 1.3 }}>
        {metricInfo.formula}
      </Typography>
      <Typography variant="caption" sx={{ fontWeight: 500, mb: 0.25, display: 'block', fontSize: '0.65rem', lineHeight: 1.2 }}>
        Description:
      </Typography>
      <Typography variant="caption" sx={{ fontSize: '0.6rem', display: 'block', wordBreak: 'break-word', lineHeight: 1.3 }}>
        {metricInfo.description}
      </Typography>
    </Box>
  )

  return (
    <Tooltip 
      title={tooltipContent} 
      arrow 
      placement="top"
      componentsProps={{
        tooltip: {
          sx: {
            bgcolor: 'rgba(0, 0, 0, 0.87)',
            color: 'white',
            fontSize: '0.7rem',
            maxWidth: 260,
            padding: '6px 8px',
            boxShadow: '0px 2px 8px rgba(0,0,0,0.15)',
            '& .MuiTooltip-arrow': {
              color: 'rgba(0, 0, 0, 0.87)',
            },
          },
        },
        popper: {
          sx: {
            zIndex: 1300, // Ensure it's above other content but not blocking
          },
        },
      }}
      enterDelay={200}
      leaveDelay={50}
    >
      <IconButton 
        size="small" 
        sx={{ 
          p: 0.25, 
          ml: 0.5,
          minWidth: 'auto',
          width: '20px',
          height: '20px',
          '&:hover': {
            backgroundColor: 'rgba(0, 0, 0, 0.04)',
          },
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <InfoIcon sx={{ fontSize: '0.875rem', color: 'text.secondary' }} />
      </IconButton>
    </Tooltip>
  )
}

