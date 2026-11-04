/**
 * Medicare Rules Explorer — NCD/LCD/articles/NCCI as first-class entities.
 * Coverage determinations ≠ coding edits ≠ payer medical policies.
 */
import { useEffect, useState } from 'react'
import {
  Alert,
  Box,
  Chip,
  CircularProgress,
  MenuItem,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'
import { apiClient } from '../lib/api'

export default function MedicareRulesExplorerPage() {
  const [data, setData] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [kind, setKind] = useState('')
  const [q, setQ] = useState('')

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setLoading(true)
      try {
        const d = await apiClient.listMedicareRules({
          kind: kind || undefined,
          q: q || undefined,
        })
        if (!cancelled) setData(d)
      } catch (e: any) {
        if (!cancelled) setError(e?.detail || e?.message || 'Failed to load Medicare rules')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [kind, q])

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" fontWeight={700} gutterBottom>
        Medicare Rules Explorer
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Independent public Medicare coverage determinations (NCD/LCD), supporting articles, and
        NCCI coding/payment edits. Not a complete CMS inventory. Analytical outcomes linked to
        Representative Payer demos remain synthetic.
      </Typography>
      {data?.honesty && (
        <Alert severity="info" sx={{ mb: 2 }}>
          NCD/LCD = coverage determinations · NCCI = coding/payment rules · Articles = supporting
          documents. Inventory completeness: not claimed.
        </Alert>
      )}
      <Paper variant="outlined" sx={{ p: 2, mb: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <TextField
          select
          size="small"
          label="Kind"
          value={kind}
          onChange={(e) => setKind(e.target.value)}
          sx={{ minWidth: 200 }}
        >
          <MenuItem value="">All</MenuItem>
          <MenuItem value="NCD">NCD</MenuItem>
          <MenuItem value="LCD">LCD</MenuItem>
          <MenuItem value="BILLING_CODING_ARTICLE">Article</MenuItem>
          <MenuItem value="NCCI_PTP">NCCI PTP</MenuItem>
          <MenuItem value="NCCI_MUE">NCCI MUE</MenuItem>
        </TextField>
        <TextField
          size="small"
          label="Search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          sx={{ minWidth: 240 }}
        />
      </Paper>
      {loading && <CircularProgress size={28} />}
      {error && <Alert severity="warning">{error}</Alert>}
      {data && !loading && (
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Kind</TableCell>
              <TableCell>Entity role</TableCell>
              <TableCell>ID</TableCell>
              <TableCell>Title</TableCell>
              <TableCell>Authority</TableCell>
              <TableCell>Program / jurisdiction</TableCell>
              <TableCell>Version</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {(data.rules || []).map((r: any) => (
              <TableRow key={`${r.family_id}-${r.source_document_id}-${r.source_version}`}>
                <TableCell>
                  <Chip size="small" label={r.kind} />
                </TableCell>
                <TableCell>{r.entity_role}</TableCell>
                <TableCell>{r.source_document_id}</TableCell>
                <TableCell>{r.title}</TableCell>
                <TableCell>{r.authority}</TableCell>
                <TableCell>
                  {r.program || '—'}
                  {r.jurisdiction ? ` · ${r.jurisdiction}` : ''}
                  {r.state ? ` · ${r.state}` : ''}
                </TableCell>
                <TableCell>{r.source_version || '—'}</TableCell>
              </TableRow>
            ))}
            {(data.rules || []).length === 0 && (
              <TableRow>
                <TableCell colSpan={7}>No Medicare source documents ingested yet.</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      )}
    </Box>
  )
}
