/**
 * Cohort Builder Component - Advanced Filter Builder
 */
import { useState } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Switch,
  TextField,
  Typography,
  Autocomplete,
  Alert,
  Paper,
  Divider,
} from '@mui/material'
import {
  Save as SaveIcon,
  Preview as PreviewIcon,
  Clear as ClearIcon,
} from '@mui/icons-material'

interface FilterSpec {
  lob?: string[]
  markets?: string[]
  date_range_start?: string
  date_range_end?: string
  pre_window_months?: number
  post_window_months?: number
  in_network_only?: boolean
  member_risk_bands?: string[]
  provider_specialties?: string[]
  facility_only?: boolean
  code_groups?: string[]
  cpt_codes?: string[]
  hcpcs_codes?: string[]
}

interface CohortBuilderProps {
  initialFilters?: FilterSpec
  onPreview?: (filters: FilterSpec) => Promise<{ memberCount?: number; claimCount?: number }>
  onSave?: (filters: FilterSpec, name: string, description?: string) => Promise<void>
  onApply?: (filters: FilterSpec) => void
  onCancel?: () => void
}

const LOB_OPTIONS = ['COMMERCIAL', 'MA', 'MEDICAID']
const MARKET_OPTIONS = ['NYC', 'DFW', 'BOS', 'CHI', 'LA', 'PHX']
const RISK_BANDS = ['Low (0-0.5)', 'Medium (0.5-1.5)', 'High (1.5-2.5)', 'Very High (2.5+)']
const PROVIDER_SPECIALTIES = [
  'Cardiology',
  'Oncology',
  'Orthopedics',
  'Radiology',
  'Primary Care',
  'Emergency Medicine',
  'Surgery',
  'Mental Health',
]
const CODE_GROUPS = [
  'MRI_LUMBAR',
  'ADV_IMAGING',
  'ER_IMAGING',
  'INFUSION',
  'PT',
  'SPECIALTY_VISIT',
  'URGENT_CARE',
]

export default function CohortBuilder({
  initialFilters = {},
  onPreview,
  onSave,
  onApply,
  onCancel,
}: CohortBuilderProps) {
  const [filters, setFilters] = useState<FilterSpec>(initialFilters)
  const [previewData, setPreviewData] = useState<{ memberCount?: number; claimCount?: number } | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [saveDialogOpen, setSaveDialogOpen] = useState(false)
  const [cohortName, setCohortName] = useState('')
  const [cohortDescription, setCohortDescription] = useState('')

  const handlePreview = async () => {
    if (!onPreview) return
    setPreviewLoading(true)
    try {
      const data = await onPreview(filters)
      setPreviewData(data)
    } catch (error) {
      console.error('Preview failed:', error)
    } finally {
      setPreviewLoading(false)
    }
  }

  const handleSave = async () => {
    if (!onSave || !cohortName.trim()) return
    try {
      await onSave(filters, cohortName, cohortDescription)
      setSaveDialogOpen(false)
      setCohortName('')
      setCohortDescription('')
    } catch (error) {
      console.error('Save failed:', error)
    }
  }

  const handleApply = () => {
    if (onApply) {
      onApply(filters)
    }
  }

  const handleClear = () => {
    setFilters({})
    setPreviewData(null)
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Cohort Builder
        </Typography>

        <Grid container spacing={2}>
          {/* LOB Selection */}
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Line of Business</InputLabel>
              <Select
                multiple
                value={filters.lob || []}
                label="Line of Business"
                onChange={(e) => setFilters({ ...filters, lob: e.target.value as string[] })}
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
                    {lob}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Markets Selection */}
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Markets</InputLabel>
              <Select
                multiple
                value={filters.markets || []}
                label="Markets"
                onChange={(e) => setFilters({ ...filters, markets: e.target.value as string[] })}
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
                    {market}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Date Range */}
          <Grid item xs={12} md={6}>
            <TextField
              label="Start Date"
              type="date"
              fullWidth
              value={filters.date_range_start || ''}
              onChange={(e) => setFilters({ ...filters, date_range_start: e.target.value })}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              label="End Date"
              type="date"
              fullWidth
              value={filters.date_range_end || ''}
              onChange={(e) => setFilters({ ...filters, date_range_end: e.target.value })}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>

          {/* Window Months */}
          <Grid item xs={12} md={6}>
            <TextField
              label="Pre Window (months)"
              type="number"
              fullWidth
              value={filters.pre_window_months || ''}
              onChange={(e) => setFilters({ ...filters, pre_window_months: parseInt(e.target.value) || undefined })}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              label="Post Window (months)"
              type="number"
              fullWidth
              value={filters.post_window_months || ''}
              onChange={(e) => setFilters({ ...filters, post_window_months: parseInt(e.target.value) || undefined })}
            />
          </Grid>

          {/* Network Filter */}
          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Switch
                  checked={filters.in_network_only || false}
                  onChange={(e) => setFilters({ ...filters, in_network_only: e.target.checked })}
                />
              }
              label="In-Network Only"
            />
          </Grid>

          {/* Member Risk Bands */}
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Member Risk Bands</InputLabel>
              <Select
                multiple
                value={filters.member_risk_bands || []}
                label="Member Risk Bands"
                onChange={(e) => setFilters({ ...filters, member_risk_bands: e.target.value as string[] })}
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {(selected as string[]).map((value) => (
                      <Chip key={value} label={value} size="small" />
                    ))}
                  </Box>
                )}
              >
                {RISK_BANDS.map((band) => (
                  <MenuItem key={band} value={band}>
                    {band}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Provider Specialties */}
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Provider Specialties</InputLabel>
              <Select
                multiple
                value={filters.provider_specialties || []}
                label="Provider Specialties"
                onChange={(e) => setFilters({ ...filters, provider_specialties: e.target.value as string[] })}
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {(selected as string[]).map((value) => (
                      <Chip key={value} label={value} size="small" />
                    ))}
                  </Box>
                )}
              >
                {PROVIDER_SPECIALTIES.map((specialty) => (
                  <MenuItem key={specialty} value={specialty}>
                    {specialty}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Facility Only */}
          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Switch
                  checked={filters.facility_only || false}
                  onChange={(e) => setFilters({ ...filters, facility_only: e.target.checked })}
                />
              }
              label="Facility Only"
            />
          </Grid>

          {/* Code Groups */}
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Code Groups</InputLabel>
              <Select
                multiple
                value={filters.code_groups || []}
                label="Code Groups"
                onChange={(e) => setFilters({ ...filters, code_groups: e.target.value as string[] })}
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {(selected as string[]).map((value) => (
                      <Chip key={value} label={value} size="small" />
                    ))}
                  </Box>
                )}
              >
                {CODE_GROUPS.map((group) => (
                  <MenuItem key={group} value={group}>
                    {group}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* CPT Codes */}
          <Grid item xs={12} md={6}>
            <Autocomplete
              multiple
              freeSolo
              options={[]}
              value={filters.cpt_codes || []}
              onChange={(_, newValue) => setFilters({ ...filters, cpt_codes: newValue })}
              renderInput={(params) => (
                <TextField {...params} label="CPT Codes" placeholder="Enter CPT codes" />
              )}
              renderTags={(value, getTagProps) =>
                value.map((option, index) => (
                  <Chip label={option} size="small" {...getTagProps({ index })} />
                ))
              }
            />
          </Grid>
        </Grid>

        <Divider sx={{ my: 2 }} />

        {/* Preview Section */}
        {previewData && (
          <Paper sx={{ p: 2, mb: 2, bgcolor: 'grey.50' }}>
            <Typography variant="subtitle2" gutterBottom>
              Preview Results:
            </Typography>
            <Box sx={{ display: 'flex', gap: 3 }}>
              {previewData.memberCount !== undefined && (
                <Typography variant="body2">
                  Members: <strong>{previewData.memberCount.toLocaleString()}</strong>
                </Typography>
              )}
              {previewData.claimCount !== undefined && (
                <Typography variant="body2">
                  Claims: <strong>{previewData.claimCount.toLocaleString()}</strong>
                </Typography>
              )}
            </Box>
          </Paper>
        )}

        {/* Actions */}
        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end', mt: 2 }}>
          <Button startIcon={<ClearIcon />} onClick={handleClear}>
            Clear
          </Button>
          {onPreview && (
            <Button
              variant="outlined"
              startIcon={<PreviewIcon />}
              onClick={handlePreview}
              disabled={previewLoading}
            >
              Preview
            </Button>
          )}
          {onSave && (
            <Button
              variant="outlined"
              startIcon={<SaveIcon />}
              onClick={() => setSaveDialogOpen(true)}
            >
              Save Cohort
            </Button>
          )}
          {onApply && (
            <Button variant="contained" onClick={handleApply}>
              Apply Filters
            </Button>
          )}
          {onCancel && (
            <Button onClick={onCancel}>Cancel</Button>
          )}
        </Box>

        {/* Save Dialog */}
        <Dialog open={saveDialogOpen} onClose={() => setSaveDialogOpen(false)}>
          <DialogTitle>Save Cohort</DialogTitle>
          <DialogContent>
            <TextField
              label="Cohort Name"
              fullWidth
              required
              value={cohortName}
              onChange={(e) => setCohortName(e.target.value)}
              sx={{ mt: 1, mb: 2 }}
            />
            <TextField
              label="Description"
              fullWidth
              multiline
              rows={3}
              value={cohortDescription}
              onChange={(e) => setCohortDescription(e.target.value)}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setSaveDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleSave} variant="contained" disabled={!cohortName.trim()}>
              Save
            </Button>
          </DialogActions>
        </Dialog>
      </CardContent>
    </Card>
  )
}

