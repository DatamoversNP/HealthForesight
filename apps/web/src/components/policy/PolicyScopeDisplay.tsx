/**
 * Policy Scope Display Component - Shows policy scope in a readable format
 * Used across Policy Catalog, Baseline Analysis, Predicted Impact, and Observation pages
 */
import { Box, Chip, Typography, Accordion, AccordionSummary, AccordionDetails } from '@mui/material'
import {
  ExpandMore as ExpandMoreIcon,
  Business as BusinessIcon,
  LocationOn as LocationIcon,
  AccountTree as NetworkIcon,
  People as PeopleIcon,
  LocalHospital as HospitalIcon,
  Warning as WarningIcon,
} from '@mui/icons-material'

interface PolicyScope {
  lob?: string[] | null
  markets?: string[] | null
  network?: string[] | null
  plans?: string[] | null
  product_types?: string[] | null
  states?: string[] | null
  member_age_min?: number | null
  member_age_max?: number | null
  exclude_pregnant?: boolean | null
  gender_filters?: string[] | null
  exclude_centers_of_excellence?: boolean | null
  exclude_er?: boolean | null
  exclude_hospital_op?: boolean | null
  allowed_sites?: string[] | null
  applies_to_all?: boolean
}

interface PolicyScopeDisplayProps {
  scope: PolicyScope | null | undefined
  compact?: boolean
  showLabel?: boolean
}

export default function PolicyScopeDisplay({ scope, compact = false, showLabel = true }: PolicyScopeDisplayProps) {
  if (!scope) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <WarningIcon color="warning" fontSize="small" />
        <Typography variant="body2" color="text.secondary">
          No scope defined - defaults to all population
        </Typography>
      </Box>
    )
  }

  const hasDetailedScope =
    scope.member_age_min ||
    scope.member_age_max ||
    scope.exclude_pregnant ||
    scope.exclude_centers_of_excellence ||
    scope.exclude_er ||
    scope.exclude_hospital_op ||
    scope.allowed_sites?.length ||
    scope.plans?.length ||
    scope.product_types?.length

  // Build scope summary text
  const scopeParts: string[] = []

  // Population
  if (scope.lob && scope.lob.length > 0) {
    scopeParts.push(scope.lob.join(', '))
  } else if (!scope.applies_to_all) {
    scopeParts.push('All LOBs')
  }

  // Markets
  if (scope.markets && scope.markets.length > 0 && !scope.markets.includes('ALL')) {
    scopeParts.push(scope.markets.join(', '))
  } else if (!scope.applies_to_all && (!scope.markets || scope.markets.includes('ALL'))) {
    scopeParts.push('All Markets')
  }

  // Network
  if (scope.network && scope.network.length > 0) {
    if (scope.network.includes('IN') && !scope.network.includes('OUT')) {
      scopeParts.push('In-Network Only')
    } else if (scope.network.includes('OUT') && !scope.network.includes('IN')) {
      scopeParts.push('Out-of-Network')
    }
  }

  // Age filters
  if (scope.member_age_min || scope.member_age_max) {
    const ageRange: string[] = []
    if (scope.member_age_min) ageRange.push(`≥${scope.member_age_min}`)
    if (scope.member_age_max) ageRange.push(`≤${scope.member_age_max}`)
    scopeParts.push(`Age: ${ageRange.join(', ')}`)
  }

  // Site exclusions
  if (scope.exclude_er) scopeParts.push('Exclude ER')
  if (scope.exclude_hospital_op) scopeParts.push('Exclude HOPD')

  // COE exclusion
  if (scope.exclude_centers_of_excellence) scopeParts.push('Exclude COEs')

  const scopeSummary = scopeParts.length > 0 ? scopeParts.join(' • ') : 'All Population'

  if (compact) {
    return (
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, alignItems: 'center' }}>
        {showLabel && (
          <Typography variant="caption" color="text.secondary" sx={{ mr: 0.5 }}>
            Scope:
          </Typography>
        )}
        <Chip
          label={scope.applies_to_all ? 'All Population (Benefit Design)' : scopeSummary}
          size="small"
          variant="outlined"
          color={scope.applies_to_all ? 'default' : 'primary'}
        />
        {hasDetailedScope && (
          <Chip label="+" size="small" variant="outlined" color="secondary" />
        )}
      </Box>
    )
  }

  // Full display with accordion for details
  return (
    <Box>
      {showLabel && (
        <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <BusinessIcon fontSize="small" />
          Policy Scope
        </Typography>
      )}

      <Box sx={{ mb: 1 }}>
        <Typography variant="body2" color="text.secondary">
          {scope.applies_to_all ? (
            <Chip label="Applies to All Population (Benefit Design Policy)" size="small" color="default" />
          ) : (
            scopeSummary || 'All Population'
          )}
        </Typography>
      </Box>

      {hasDetailedScope && (
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="caption">Detailed Scope Filters</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {/* Plans/Products */}
              {(scope.plans?.length || scope.product_types?.length) && (
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Plans/Products:
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                    {scope.plans?.map((plan) => (
                      <Chip key={plan} label={plan} size="small" />
                    ))}
                    {scope.product_types?.map((pt) => (
                      <Chip key={pt} label={pt} size="small" />
                    ))}
                  </Box>
                </Box>
              )}

              {/* Member Attributes */}
              {(scope.member_age_min ||
                scope.member_age_max ||
                scope.exclude_pregnant ||
                scope.gender_filters?.length) && (
                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <PeopleIcon fontSize="small" />
                    Member Filters:
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                    {scope.member_age_min && <Chip label={`Age ≥ ${scope.member_age_min}`} size="small" />}
                    {scope.member_age_max && <Chip label={`Age ≤ ${scope.member_age_max}`} size="small" />}
                    {scope.exclude_pregnant && <Chip label="Exclude Pregnant" size="small" />}
                    {scope.gender_filters?.map((g) => (
                      <Chip key={g} label={`Gender: ${g}`} size="small" />
                    ))}
                  </Box>
                </Box>
              )}

              {/* Site of Care */}
              {(scope.exclude_er || scope.exclude_hospital_op || scope.allowed_sites?.length) && (
                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <HospitalIcon fontSize="small" />
                    Site of Care:
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                    {scope.exclude_er && <Chip label="Exclude ER" size="small" color="error" />}
                    {scope.exclude_hospital_op && <Chip label="Exclude HOPD" size="small" color="error" />}
                    {scope.allowed_sites?.map((site) => (
                      <Chip key={site} label={`Allow: ${site}`} size="small" color="success" />
                    ))}
                  </Box>
                </Box>
              )}

              {/* Provider Filters */}
              {scope.exclude_centers_of_excellence && (
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Provider Filters:
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                    <Chip label="Exclude Centers of Excellence" size="small" />
                  </Box>
                </Box>
              )}
            </Box>
          </AccordionDetails>
        </Accordion>
      )}
    </Box>
  )
}
