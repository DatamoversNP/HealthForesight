/**
 * Enhanced Scope Selector Component - Step 2 of Policy Builder
 * Comprehensive scope configuration supporting all PolicyScope dimensions
 */
import { useState, useEffect } from 'react'
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Typography,
  Checkbox,
  FormControlLabel,
  TextField,
  Radio,
  RadioGroup,
  FormLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
} from '@mui/material'
import {
  ExpandMore as ExpandMoreIcon,
  Business as BusinessIcon,
  LocationOn as LocationIcon,
  AccountTree as NetworkIcon,
  People as PeopleIcon,
  LocalHospital as HospitalIcon,
} from '@mui/icons-material'
import { DatePicker } from '@mui/x-date-pickers'
import { LocalizationProvider } from '@mui/x-date-pickers'
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns'
import { apiClient } from '../../lib/api'

const LOB_OPTIONS = ['COMMERCIAL', 'MA', 'MEDICAID', 'EXCHANGE']
const MARKET_OPTIONS = ['NYC', 'DFW', 'BOS'] // Can be extended
const SITE_OF_CARE_OPTIONS = ['ER', 'HOPD', 'ASC', 'OFFICE', 'INPATIENT', 'HOME']
const PROVIDER_TYPE_OPTIONS = ['HOSPITAL', 'ASC', 'PHYSICIAN_GROUP', 'INDIVIDUAL_PHYSICIAN']
const GENDER_OPTIONS = ['M', 'F']

interface EnhancedScope {
  lob: string[]
  markets: string[]
  network: string[]
  plans?: string[]
  product_types?: string[]
  states?: string[]
  regions?: string[]
  network_tiers?: string[]
  member_age_min?: number | null
  member_age_max?: number | null
  exclude_pregnant?: boolean | null
  gender_filters?: string[]
  exclude_centers_of_excellence?: boolean | null
  include_provider_types?: string[]
  exclude_provider_types?: string[]
  provider_specialties?: string[]
  exclude_er?: boolean | null
  exclude_hospital_op?: boolean | null
  allowed_sites?: string[]
  applies_to_all?: boolean
  network_inclusion_mode?: 'include' | 'exclude'
}

interface ScopeSelectorEnhancedProps {
  scope: EnhancedScope
  effective_period: {
    start_date: string
    end_date: string | null
  }
  onChange: (updates: any) => void
}

export default function ScopeSelectorEnhanced({ scope, effective_period, onChange }: ScopeSelectorEnhancedProps) {
  const [networks, setNetworks] = useState<string[]>([])
  const [loadingNetworks, setLoadingNetworks] = useState(false)

  // Load networks from network master (placeholder for now)
  useEffect(() => {
    setLoadingNetworks(true)
    // TODO: Replace with actual API call: apiClient.getNetworks()
    // For now, use placeholder networks
    setTimeout(() => {
      setNetworks(['PPO Core', 'PPO Plus', 'Narrow Network', 'Tiered Network A', 'Tiered Network B', 'HMO'])
      setLoadingNetworks(false)
    }, 100)
  }, [])

  // Ensure network_inclusion_mode has a default
  const networkMode = scope.network_inclusion_mode || 'include'

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        <Typography variant="h6">Policy Scope</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Define who is eligible and where policy logic applies. This is NOT logic yet — just who is in-scope.
        </Typography>

        {/* A) Population Scope */}
        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <PeopleIcon fontSize="small" />
              <Typography variant="subtitle1">Population Scope (Member-Level)</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {/* Line of Business */}
              <FormControl fullWidth>
                <InputLabel>Line of Business</InputLabel>
                <Select
                  multiple
                  value={scope.lob || []}
                  onChange={(e) => onChange({ scope: { ...scope, lob: e.target.value as string[] } })}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {(selected as string[]).map((value) => (
                        <Chip key={value} label={value} size="small" />
                      ))}
                    </Box>
                  )}
                >
                  {LOB_OPTIONS.map((lob) => (
                    <MenuItem key={lob} value={lob}>
                      <Checkbox checked={(scope.lob || []).includes(lob)} />
                      {lob}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* Markets */}
              <FormControl fullWidth>
                <InputLabel>Markets / States / Regions</InputLabel>
                <Select
                  multiple
                  value={scope.markets || []}
                  onChange={(e) => onChange({ scope: { ...scope, markets: e.target.value as string[] } })}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {(selected as string[]).map((value) => (
                        <Chip key={value} label={value} size="small" />
                      ))}
                    </Box>
                  )}
                >
                  {MARKET_OPTIONS.map((market) => (
                    <MenuItem key={market} value={market}>
                      <Checkbox checked={(scope.markets || []).includes(market)} />
                      {market}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* Plans/Products */}
              <FormControl fullWidth>
                <InputLabel>Plans / Products (Optional)</InputLabel>
                <Select
                  multiple
                  value={scope.plans || []}
                  onChange={(e) => onChange({ scope: { ...scope, plans: e.target.value as string[] } })}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {(selected as string[]).length > 0 ? (
                        (selected as string[]).map((value) => <Chip key={value} label={value} size="small" />)
                      ) : (
                        <Typography variant="body2" color="text.secondary">All plans</Typography>
                      )}
                    </Box>
                  )}
                >
                  <MenuItem value="HMO">HMO</MenuItem>
                  <MenuItem value="PPO">PPO</MenuItem>
                  <MenuItem value="POS">POS</MenuItem>
                  <MenuItem value="EXCHANGE">Exchange</MenuItem>
                </Select>
              </FormControl>

              {/* Member Age Bands */}
              <Box sx={{ display: 'flex', gap: 2 }}>
                <TextField
                  label="Min Age (optional)"
                  type="number"
                  value={scope.member_age_min || ''}
                  onChange={(e) =>
                    onChange({
                      scope: {
                        ...scope,
                        member_age_min: e.target.value ? parseInt(e.target.value) : null,
                      },
                    })
                  }
                  sx={{ flex: 1 }}
                />
                <TextField
                  label="Max Age (optional)"
                  type="number"
                  value={scope.member_age_max || ''}
                  onChange={(e) =>
                    onChange({
                      scope: {
                        ...scope,
                        member_age_max: e.target.value ? parseInt(e.target.value) : null,
                      },
                    })
                  }
                  sx={{ flex: 1 }}
                />
              </Box>

              {/* Member Attributes */}
              <FormControlLabel
                control={
                  <Checkbox
                    checked={scope.exclude_pregnant || false}
                    onChange={(e) => onChange({ scope: { ...scope, exclude_pregnant: e.target.checked || null } })}
                  />
                }
                label="Exclude Pregnant Members"
              />

              <FormControl fullWidth>
                <InputLabel>Gender Filters (Optional)</InputLabel>
                <Select
                  multiple
                  value={scope.gender_filters || []}
                  onChange={(e) => onChange({ scope: { ...scope, gender_filters: e.target.value as string[] } })}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {(selected as string[]).length > 0 ? (
                        (selected as string[]).map((value) => <Chip key={value} label={value} size="small" />)
                      ) : (
                        <Typography variant="body2" color="text.secondary">All genders</Typography>
                      )}
                    </Box>
                  )}
                >
                  {GENDER_OPTIONS.map((gender) => (
                    <MenuItem key={gender} value={gender}>
                      <Checkbox checked={(scope.gender_filters || []).includes(gender)} />
                      {gender === 'M' ? 'Male' : 'Female'}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>
          </AccordionDetails>
        </Accordion>

        {/* B) Network Scope */}
        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <NetworkIcon fontSize="small" />
              <Typography variant="subtitle1">Network Scope</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {/* Network Inclusion Mode */}
              <FormControl component="fieldset">
                <FormLabel component="legend">Network Selection Mode</FormLabel>
                <RadioGroup
                  row
                  value={networkMode}
                  onChange={(e) =>
                    onChange({ scope: { ...scope, network_inclusion_mode: e.target.value as 'include' | 'exclude' } })
                  }
                >
                  <FormControlLabel value="include" control={<Radio />} label="Include selected networks" />
                  <FormControlLabel value="exclude" control={<Radio />} label="Exclude selected networks" />
                </RadioGroup>
              </FormControl>

              {/* Network Selection */}
              <FormControl fullWidth>
                <InputLabel>Network(s)</InputLabel>
                <Select
                  multiple
                  value={scope.network || []}
                  onChange={(e) => onChange({ scope: { ...scope, network: e.target.value as string[] } })}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {(selected as string[]).length > 0 ? (
                        (selected as string[]).map((value) => <Chip key={value} label={value} size="small" />)
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          {networkMode === 'include' ? 'All networks' : 'No exclusions'}
                        </Typography>
                      )}
                    </Box>
                  )}
                  disabled={loadingNetworks}
                >
                  {networks.map((network) => (
                    <MenuItem key={network} value={network}>
                      <Checkbox checked={(scope.network || []).includes(network)} />
                      {network}
                    </MenuItem>
                  ))}
                </Select>
                {loadingNetworks && <Typography variant="caption">Loading networks...</Typography>}
              </FormControl>
            </Box>
          </AccordionDetails>
        </Accordion>

        {/* C) Provider Scope (Optional) */}
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <BusinessIcon fontSize="small" />
              <Typography variant="subtitle1">Provider Scope (Optional)</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={scope.exclude_centers_of_excellence || false}
                    onChange={(e) =>
                      onChange({ scope: { ...scope, exclude_centers_of_excellence: e.target.checked || null } })
                    }
                  />
                }
                label="Exclude Centers of Excellence (COEs)"
              />

              <FormControl fullWidth>
                <InputLabel>Include Provider Types (Optional)</InputLabel>
                <Select
                  multiple
                  value={scope.include_provider_types || []}
                  onChange={(e) =>
                    onChange({ scope: { ...scope, include_provider_types: e.target.value as string[] } })
                  }
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {(selected as string[]).length > 0 ? (
                        (selected as string[]).map((value) => <Chip key={value} label={value} size="small" />)
                      ) : (
                        <Typography variant="body2" color="text.secondary">All provider types</Typography>
                      )}
                    </Box>
                  )}
                >
                  {PROVIDER_TYPE_OPTIONS.map((type) => (
                    <MenuItem key={type} value={type}>
                      <Checkbox checked={(scope.include_provider_types || []).includes(type)} />
                      {type.replace(/_/g, ' ')}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>
          </AccordionDetails>
        </Accordion>

        {/* D) Site of Care Scope (Optional) */}
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <HospitalIcon fontSize="small" />
              <Typography variant="subtitle1">Site of Care Scope (Optional)</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={scope.exclude_er || false}
                    onChange={(e) => onChange({ scope: { ...scope, exclude_er: e.target.checked || null } })}
                  />
                }
                label="Exclude Emergency Room (ER)"
              />

              <FormControlLabel
                control={
                  <Checkbox
                    checked={scope.exclude_hospital_op || false}
                    onChange={(e) =>
                      onChange({ scope: { ...scope, exclude_hospital_op: e.target.checked || null } })
                    }
                  />
                }
                label="Exclude Hospital Outpatient Department (HOPD)"
              />

              <FormControl fullWidth>
                <InputLabel>Allowed Sites (Optional)</InputLabel>
                <Select
                  multiple
                  value={scope.allowed_sites || []}
                  onChange={(e) => onChange({ scope: { ...scope, allowed_sites: e.target.value as string[] } })}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {(selected as string[]).length > 0 ? (
                        (selected as string[]).map((value) => <Chip key={value} label={value} size="small" />)
                      ) : (
                        <Typography variant="body2" color="text.secondary">All sites</Typography>
                      )}
                    </Box>
                  )}
                >
                  {SITE_OF_CARE_OPTIONS.map((site) => (
                    <MenuItem key={site} value={site}>
                      <Checkbox checked={(scope.allowed_sites || []).includes(site)} />
                      {site}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>
          </AccordionDetails>
        </Accordion>

        <Divider sx={{ my: 2 }} />

        {/* Effective Period */}
        <Box>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Effective Period
          </Typography>

          <DatePicker
            label="Effective Start Date"
            value={effective_period.start_date ? new Date(effective_period.start_date) : null}
            onChange={(date: Date | null) =>
              onChange({
                effective_period: {
                  ...effective_period,
                  start_date: date ? date.toISOString().split('T')[0] : '',
                },
              })
            }
            slotProps={{ textField: { fullWidth: true, required: true } }}
          />

          <FormControlLabel
            control={
              <Checkbox
                checked={!!effective_period.end_date}
                onChange={(e) =>
                  onChange({
                    effective_period: {
                      ...effective_period,
                      end_date: e.target.checked ? new Date().toISOString().split('T')[0] : null,
                    },
                  })
                }
                sx={{ mt: 2 }}
              />
            }
            label="Set end date (optional)"
          />

          {effective_period.end_date && (
            <DatePicker
              label="Effective End Date"
              value={effective_period.end_date ? new Date(effective_period.end_date) : null}
              onChange={(date: Date | null) =>
                onChange({
                  effective_period: {
                    ...effective_period,
                    end_date: date ? date.toISOString().split('T')[0] : null,
                  },
                })
              }
              minDate={effective_period.start_date ? new Date(effective_period.start_date) : undefined}
              slotProps={{ textField: { fullWidth: true } }}
            />
          )}
        </Box>
      </Box>
    </LocalizationProvider>
  )
}
