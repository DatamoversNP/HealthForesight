/**
 * Searchable policy picker — replaces plain MUI Select for 200+ policy catalogs.
 */
import Autocomplete from '@mui/material/Autocomplete'
import TextField from '@mui/material/TextField'

export type PolicyOption = {
  id: string
  name: string
  policy_type?: string
  status?: string
}

type Props = {
  policies: PolicyOption[]
  value: string
  onChange: (policyId: string) => void
  label?: string
  /** Allow clearing to empty string (All policies). Default true. */
  allowAll?: boolean
  allLabel?: string
  size?: 'small' | 'medium'
  disabled?: boolean
  sx?: object
  fullWidth?: boolean
}

export default function PolicyAutocomplete({
  policies,
  value,
  onChange,
  label = 'Policy',
  allowAll = true,
  allLabel = 'All policies',
  size = 'small',
  disabled = false,
  sx,
  fullWidth = true,
}: Props) {
  const sorted = [...policies].sort((a, b) =>
    String(a.name || '').localeCompare(String(b.name || ''))
  )
  const selected = value ? sorted.find((p) => p.id === value) || null : null

  return (
    <Autocomplete
      size={size}
      disabled={disabled}
      fullWidth={fullWidth}
      sx={sx}
      options={sorted}
      value={selected}
      onChange={(_e, next) => onChange(next?.id || '')}
      getOptionLabel={(p) => p.name || p.id}
      isOptionEqualToValue={(a, b) => a.id === b.id}
      clearOnEscape
      renderInput={(params) => (
        <TextField
          {...params}
          label={label}
          placeholder={allowAll ? allLabel : 'Search policies…'}
        />
      )}
    />
  )
}
