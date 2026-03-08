/**
 * PolicyClaimCounts - Shows claim counts breakdown for a policy (scope + levers)
 * Use on policy page to see if data supports policy criteria
 */
import { useState, useEffect } from 'react'
import { Box, Paper, Typography, CircularProgress, Alert, Table, TableBody, TableCell, TableRow } from '@mui/material'
import { apiClient } from '../../lib/api'

interface PolicyClaimCountsProps {
  policyId: string
  compact?: boolean
}

export default function PolicyClaimCounts({ policyId, compact = false }: PolicyClaimCountsProps) {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (policyId) {
      loadCounts()
    }
  }, [policyId])

  const loadCounts = async () => {
    try {
      setLoading(true)
      setError(null)
      const result = await apiClient.getPolicyClaimCountsBreakdown(policyId)
      setData(result)
    } catch (err: any) {
      setError(err.detail || err.message || 'Failed to load claim counts')
      setData(null)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Box display="flex" alignItems="center" gap={1} p={2}>
        <CircularProgress size={20} />
        <Typography variant="body2">Loading claim counts...</Typography>
      </Box>
    )
  }

  if (error) {
    return (
      <Alert severity="warning" sx={{ mb: 2 }}>
        {error}
      </Alert>
    )
  }

  if (!data?.counts) {
    return null
  }

  const { counts, filters, date_range, validation } = data

  if (compact) {
    return (
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Full scope: <strong>{counts.full_scope?.toLocaleString() ?? 0}</strong> claim lines
        </Typography>
        {counts.plus_lob_market !== counts.full_scope && (
          <Typography variant="caption" color="text.secondary">
            (tenant+date: {counts.tenant_and_date_only?.toLocaleString() ?? 0})
          </Typography>
        )}
      </Box>
    )
  }

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Typography variant="subtitle2" gutterBottom>
        Claim counts (scope + levers merged)
      </Typography>
      <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
        {date_range?.start} – {date_range?.end}
      </Typography>
      <Table size="small">
        <TableBody>
          <TableRow>
            <TableCell>Tenant + date only</TableCell>
            <TableCell align="right">{counts.tenant_and_date_only?.toLocaleString() ?? 0}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>+ LOB + market</TableCell>
            <TableCell align="right">{counts.plus_lob_market?.toLocaleString() ?? 0}</TableCell>
          </TableRow>
          <TableRow sx={{ bgcolor: 'action.hover' }}>
            <TableCell><strong>Full scope (procedure + service)</strong></TableCell>
            <TableCell align="right"><strong>{counts.full_scope?.toLocaleString() ?? 0}</strong></TableCell>
          </TableRow>
        </TableBody>
      </Table>
      {filters && (
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          Filters: LOB={filters.lob ?? 'all'}, Markets={Array.isArray(filters.markets) ? filters.markets.join(', ') : filters.markets ?? 'all'}, 
          {filters.procedure_codes_count ? ` ${filters.procedure_codes_count} procedure codes` : ''}
          {filters.service_categories_count ? `, ${filters.service_categories_count} service categories` : ''}
        </Typography>
      )}
      {validation && !validation.valid && validation.issues?.length > 0 && (
        <Alert severity="warning" sx={{ mt: 2 }}>
          Scope validation: {validation.issues.join('; ')}
        </Alert>
      )}
    </Paper>
  )
}
