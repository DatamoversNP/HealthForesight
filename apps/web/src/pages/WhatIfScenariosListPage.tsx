/**
 * List all what-if (SIMULATE) analysis runs for the tenant.
 */
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link as RouterLink } from 'react-router-dom'
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material'
import { Refresh as RefreshIcon, Psychology as WhatIfIcon } from '@mui/icons-material'
import { format, parseISO } from 'date-fns'
import { apiClient } from '../lib/api'
import { healthForesightColors } from '../theme/healthForesightTheme'

interface SimRow {
  id: string
  name?: string | null
  policy_id: string | null
  analysis_type: string
  status: string
  created_at: string | null
  updated_at?: string | null
}

export default function WhatIfScenariosListPage() {
  const [rows, setRows] = useState<SimRow[]>([])
  const [policies, setPolicies] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [analysesRaw, policiesRaw] = await Promise.all([
        apiClient.getAnalyses({ analysis_type: 'SIMULATE', limit: 500, skip: 0 }),
        apiClient.getPolicies(),
      ])
      const list = Array.isArray(analysesRaw) ? analysesRaw : []
      setRows(
        list.map((a: any) => ({
          id: String(a.id),
          name: a.name ?? null,
          policy_id: a.policy_id != null ? String(a.policy_id) : null,
          analysis_type: String(a.analysis_type || 'SIMULATE'),
          status: String(a.status || 'UNKNOWN'),
          created_at: a.created_at ?? null,
          updated_at: a.updated_at ?? null,
        }))
      )
      const plist = Array.isArray(policiesRaw) ? policiesRaw : (policiesRaw as any)?.items || []
      const map: Record<string, string> = {}
      for (const p of plist) {
        if (p?.id) map[String(p.id)] = p.name || String(p.id)
      }
      setPolicies(map)
    } catch (e: any) {
      setError(e?.message || 'Failed to load scenarios')
      setRows([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const sorted = useMemo(() => {
    return [...rows].sort((a, b) => {
      const ta = a.created_at ? new Date(a.created_at).getTime() : 0
      const tb = b.created_at ? new Date(b.created_at).getTime() : 0
      return tb - ta
    })
  }, [rows])

  const statusColor = (s: string) => {
    switch (s) {
      case 'COMPLETED':
        return 'success'
      case 'FAILED':
        return 'error'
      case 'RUNNING':
        return 'info'
      default:
        return 'default'
    }
  }

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', flexWrap: 'wrap', alignItems: 'flex-start', justifyContent: 'space-between', gap: 2 }}>
        <Box>
          <Typography
            variant="h4"
            component="h1"
            sx={{
              fontFamily: 'IBM Plex Sans, Inter, sans-serif',
              fontWeight: 600,
              mb: 1,
              color: healthForesightColors.neutral.dark,
              display: 'flex',
              alignItems: 'center',
              gap: 1,
            }}
          >
            <WhatIfIcon sx={{ color: healthForesightColors.primary.main }} />
            What-If scenario runs
          </Typography>
          <Typography variant="body1" sx={{ color: healthForesightColors.neutral.mid, maxWidth: 720 }}>
            All scenario simulations for your tenant (newest first). Open a run in the builder to view charts and
            compare with other scenarios.
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1, flexShrink: 0 }}>
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={load} disabled={loading}>
            Refresh
          </Button>
          <Button variant="contained" component={RouterLink} to="/whatif">
            New scenario
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Paper variant="outlined" sx={{ borderRadius: 0, borderColor: '#E2E8F0' }}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
            <CircularProgress />
          </Box>
        ) : sorted.length === 0 ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography color="text.secondary" sx={{ mb: 2 }}>
              No what-if runs yet. Create one from the What-If Scenarios page.
            </Typography>
            <Button variant="contained" component={RouterLink} to="/whatif">
              Go to What-If Scenarios
            </Button>
          </Box>
        ) : (
          <TableContainer>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>Started</TableCell>
                  <TableCell>Policy</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Name</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {sorted.map((r) => {
                  const policyName = r.policy_id ? policies[r.policy_id] || r.policy_id : '—'
                  const when = r.created_at
                    ? format(parseISO(r.created_at), 'MMM d, yyyy HH:mm')
                    : '—'
                  const openHref =
                    r.policy_id != null
                      ? `/whatif?policy=${encodeURIComponent(r.policy_id)}&scenario=${encodeURIComponent(r.id)}`
                      : `/whatif`
                  return (
                    <TableRow key={r.id} hover>
                      <TableCell sx={{ whiteSpace: 'nowrap' }}>{when}</TableCell>
                      <TableCell>{policyName}</TableCell>
                      <TableCell>
                        <Chip
                          size="small"
                          label={r.status}
                          color={statusColor(r.status) as 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'}
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell sx={{ maxWidth: 280 }}>{r.name?.trim() || '—'}</TableCell>
                      <TableCell align="right">
                        <Button size="small" component={RouterLink} to={openHref}>
                          Open
                        </Button>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
        Showing up to 500 runs. Failed or pending rows open in the builder with their current status.
      </Typography>
    </Box>
  )
}
