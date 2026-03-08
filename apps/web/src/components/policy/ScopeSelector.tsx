/**
 * Scope Selector Component - Step 2 of Policy Builder
 * Configure policy scope (LOB, markets, network) and effective period
 */
import { Box, FormControl, InputLabel, Select, MenuItem, TextField, Chip, Typography, Checkbox, FormControlLabel } from '@mui/material'
import { DatePicker } from '@mui/x-date-pickers'
import { LocalizationProvider } from '@mui/x-date-pickers'
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns'

const LOB_OPTIONS = ['COMMERCIAL', 'MA', 'MEDICAID']
const MARKET_OPTIONS = ['NYC', 'DFW', 'BOS', 'ALL']
const NETWORK_OPTIONS = ['IN', 'OUT', 'ALL']

interface ScopeSelectorProps {
  scope: {
    lob: string[]
    markets: string[]
    network: string[]
  }
  effective_period: {
    start_date: string
    end_date: string | null
  }
  onChange: (updates: any) => void
}

export default function ScopeSelector({ scope, effective_period, onChange }: ScopeSelectorProps) {
  const handleLOBChange = (lob: string) => {
    const newLOBs = scope.lob.includes(lob)
      ? scope.lob.filter((l) => l !== lob)
      : [...scope.lob, lob]
    onChange({ scope: { ...scope, lob: newLOBs } })
  }

  const handleMarketChange = (market: string) => {
    if (market === 'ALL') {
      onChange({ scope: { ...scope, markets: ['ALL'] } })
    } else {
      const newMarkets = scope.markets.includes('ALL')
        ? [market]
        : scope.markets.includes(market)
        ? scope.markets.filter((m) => m !== market)
        : [...scope.markets, market]
      if (newMarkets.length === 0) {
        onChange({ scope: { ...scope, markets: ['ALL'] } })
      } else {
        onChange({ scope: { ...scope, markets: newMarkets } })
      }
    }
  }

  const handleNetworkChange = (network: string) => {
    if (network === 'ALL') {
      onChange({ scope: { ...scope, network: ['ALL'] } })
    } else {
      const newNetworks = scope.network.includes('ALL')
        ? [network]
        : scope.network.includes(network)
        ? scope.network.filter((n) => n !== network)
        : [...scope.network, network]
      if (newNetworks.length === 0) {
        onChange({ scope: { ...scope, network: ['ALL'] } })
      } else {
        onChange({ scope: { ...scope, network: newNetworks } })
      }
    }
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        <Typography variant="h6">Policy Scope</Typography>
        
        {/* Line of Business */}
        <FormControl fullWidth>
          <InputLabel>Line of Business</InputLabel>
          <Select
            multiple
            value={scope.lob}
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
                <Checkbox checked={scope.lob.includes(lob)} />
                {lob}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* Markets */}
        <FormControl fullWidth>
          <InputLabel>Markets</InputLabel>
          <Select
            multiple
            value={scope.markets}
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
                <Checkbox checked={scope.markets.includes(market)} />
                {market}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* Network */}
        <FormControl fullWidth>
          <InputLabel>Network</InputLabel>
          <Select
            multiple
            value={scope.network}
            onChange={(e) => onChange({ scope: { ...scope, network: e.target.value as string[] } })}
            renderValue={(selected) => (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {(selected as string[]).map((value) => (
                  <Chip key={value} label={value} size="small" />
                ))}
              </Box>
            )}
          >
            {NETWORK_OPTIONS.map((network) => (
              <MenuItem key={network} value={network}>
                <Checkbox checked={scope.network.includes(network)} />
                {network === 'IN' ? 'In-Network' : network === 'OUT' ? 'Out-of-Network' : 'All Networks'}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <Typography variant="h6" sx={{ mt: 2 }}>Effective Period</Typography>

        {/* Start Date */}
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

        {/* End Date (Optional) */}
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
    </LocalizationProvider>
  )
}

