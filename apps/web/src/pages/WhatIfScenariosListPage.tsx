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
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
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
import ListFilterBar from '../components/common/ListFilterBar'
import PolicyAutocomplete from '../components/common/PolicyAutocomplete'

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
  const [policyOptions, setPolicyOptions] = useState<Array<{ id: string; name: string }>>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [policyFilter, setPolicyFilter] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [analysesRaw, policiesRaw] = await Promise.all([
        apiClient.getAnalyses({ analysis_type: 'SIMULATE', limit: 500, skip: 0 }),
        apiClient.getPolicies({ limit: 1000 }),
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
      const opts: Array<{ id: string; name: string }> = []
      for (const p of plist) {
        if (p?.id) {
          const id = String(p.id)
          const name = p.name || id
          map[id] = name
          opts.push({ id, name })
        }
      }
      setPolicies(map)
      setPolicyOptions(opts)
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

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return sorted.filter((r) => {
      if (statusFilter && r.status !== statusFilter) return false
      if (policyFilter && r.policy_id !== policyFilter) return false
      if (!q) return true
      const policyName = r.policy_id ? policies[r.policy_id] || r.policy_id : ''
      const hay = `${r.name || ''} ${policyName} ${r.status} ${r.id}`.toLowerCase()
      return hay.includes(q)
    })
  }, [sorted, search, statusFilter, policyFilter, policies])

  const statusOptions = useMemo(
    () => Array.from(new Set(rows.map((r) => r.status).filter(Boolean))).sort(),
    [rows]
  )

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
            All scenario simulations for your tenant (newest first). Open a completed run to jump straight to its
            results charts (not a blank configuration form).
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

      <Paper variant="outlined" sx={{ borderRadius: 0, borderColor: '#E2E8F0', overflow: 'hidden' }}>
        <ListFilterBar
          search={search}
          onSearchChange={setSearch}
          searchLabel="Search runs"
          searchPlaceholder="Name, policy, status…"
          shown={filtered.length}
          total={rows.length}
          onClear={() => {
            setSearch('')
            setStatusFilter('')
            setPolicyFilter('')
          }}
          clearDisabled={!search && !statusFilter && !policyFilter}
        >
          <Box sx={{ minWidth: 220, flex: '1 1 200px', bgcolor: 'background.paper', borderRadius: 1 }}>
            <PolicyAutocomplete
              policies={policyOptions}
              value={policyFilter}
              label="Policy"
              onChange={setPolicyFilter}
            />
          </Box>
          <FormControl size="small" sx={{ minWidth: 140, bgcolor: 'background.paper' }}>
            <InputLabel>Status</InputLabel>
            <Select
              label="Status"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <MenuItem value="">All</MenuItem>
              {statusOptions.map((s) => (
                <MenuItem key={s} value={s}>
                  {s}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </ListFilterBar>

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
        ) : filtered.length === 0 ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography color="text.secondary">No runs match these filters.</Typography>
          </Box>
        ) : (
          <TableContainer sx={{ maxHeight: '70vh' }}>
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
                {filtered.map((r) => {
                  const policyName = r.policy_id ? policies[r.policy_id] || r.policy_id : '—'
                  const when = r.created_at
                    ? format(parseISO(r.created_at), 'MMM d, yyyy HH:mm')
                    : '—'
                  const openHref =
                    r.policy_id != null
                      ? `/whatif?policy=${encodeURIComponent(r.policy_id)}&scenario=${encodeURIComponent(r.id)}`
                      : `/whatif?scenario=${encodeURIComponent(r.id)}`
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
                          {r.status === 'COMPLETED' ? 'Open results' : 'Open'}
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
