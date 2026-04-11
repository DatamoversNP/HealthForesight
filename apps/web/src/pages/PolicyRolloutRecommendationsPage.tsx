/**
 * Enterprise policy rollout recommendations — explainable, deduplicated, impact-scored.
 */
import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Collapse,
  Divider,
  IconButton,
  LinearProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material'
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Refresh as RefreshIcon,
  Lightbulb as LightbulbIcon,
  Gavel as GavelIcon,
  TrendingFlat as TrendingIcon,
  OpenInNew as OpenInNewIcon,
  Block as BlockIcon,
} from '@mui/icons-material'
import { apiClient } from '../lib/api'

interface EvidenceItem {
  type?: string
  explanation?: string
  cpt_code?: string
  service_category?: string
  allowed_amount_window?: number
  claim_lines?: number
  distinct_members?: number
  rank_in_tenant_cpt?: number
}

interface RolloutRecommendation {
  recommendation_id: string
  priority: string
  archetype_id: string
  title: string
  policy_type: string
  summary: string
  suggested_scope?: {
    procedure_codes?: string[]
    service_categories?: string[]
    note?: string
  }
  estimated_impact: {
    methodology?: string
    lookback_start?: string
    lookback_end?: string
    months_lookback?: number
    utilization_change_pct_range?: [number, number]
    cost_pmpm_change_pct_range?: [number, number]
    baseline_util_per_1k_reference?: number | null
    baseline_allowed_pmpm_reference?: number | null
    projected_util_per_1k_range?: [number, number] | null
    projected_allowed_pmpm_range?: [number, number] | null
    confidence?: string
    confidence_explanation?: string
    elasticity_note?: string
  }
  explainability?: {
    why_recommended?: string[]
    evidence?: EvidenceItem[]
    implementation_guidance?: string
    governance?: string[]
  }
  data_signals?: {
    overlap_allowed_amount?: number
    overlap_claim_lines?: number
  }
}

interface SkippedDuplicate {
  archetype_id: string
  title: string
  reason: string
  matching_policy_ids: string[]
}

interface RolloutResponse {
  generated_at?: string
  parameters?: Record<string, unknown>
  baseline_reference?: Record<string, unknown>
  existing_policies_count?: number
  recommendations: RolloutRecommendation[]
  skipped_as_duplicates?: SkippedDuplicate[]
  methodology_footer?: string
}

export default function PolicyRolloutRecommendationsPage() {
  const navigate = useNavigate()
  const [data, setData] = useState<RolloutResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await apiClient.getPolicyRolloutRecommendations({
        months_lookback: 12,
        limit: 25,
        jaccard_threshold: 0.55,
      })
      setData(res as RolloutResponse)
    } catch (e: unknown) {
      const msg = e && typeof e === 'object' && 'message' in e ? String((e as Error).message) : 'Failed to load'
      setError(msg)
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const toggle = (id: string) => {
    setExpanded((prev) => ({ ...prev, [id]: !prev[id] }))
  }

  const priorityColor = (p: string) => {
    if (p === 'high') return 'error'
    if (p === 'medium') return 'warning'
    return 'default'
  }

  if (loading && !data) {
    return (
      <Box sx={{ p: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box sx={{ p: 3, maxWidth: 1400, mx: 'auto' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2, flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 700 }}>
            Policy rollout recommendations
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 720 }}>
            Net-new program ideas grounded in your claims history and baselines. Existing in-force policies are
            excluded when codes and type overlap materially. Every row includes reasoning, evidence, and impact bands
            for governance.
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<RefreshIcon />} onClick={() => load()} disabled={loading}>
          Refresh analysis
        </Button>
      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Alert severity="info" icon={<GavelIcon />} sx={{ mb: 3 }}>
        <Typography variant="subtitle2" fontWeight={600} gutterBottom>
          Governance and limitations
        </Typography>
        <Typography variant="body2">
          Projections are <strong>scenarios</strong> (not guarantees). They combine catalog benchmarks and optional
          tenant elasticity models with your latest tenant-wide baseline. Clinical, legal, and network review is required
          before any rollout. Parameters: lookback {String(data?.parameters?.months_lookback ?? 12)} months, duplicate
          similarity threshold {String(data?.parameters?.jaccard_duplicate_threshold ?? 0.55)} (Jaccard on CPT sets).
        </Typography>
      </Alert>

      {data && (
        <>
          <Paper variant="outlined" sx={{ p: 2, mb: 3, bgcolor: 'action.hover' }}>
            <Typography variant="body2" color="text.secondary">
              Generated {data.generated_at ? new Date(data.generated_at).toLocaleString() : '—'} · In-force policies
              indexed: <strong>{data.existing_policies_count ?? 0}</strong> · Recommendations returned:{' '}
              <strong>{data.recommendations?.length ?? 0}</strong>
            </Typography>
            {data.methodology_footer && (
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                {data.methodology_footer}
              </Typography>
            )}
          </Paper>

          {(data.recommendations?.length ?? 0) === 0 && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              No net-new archetypes passed deduplication. Add distinct target codes to existing policies or adjust
              threshold via API if appropriate.
            </Alert>
          )}

          {data.recommendations?.map((rec) => {
            const open = expanded[rec.recommendation_id] ?? false
            const ei = rec.estimated_impact || {}
            const ex = rec.explainability || {}
            return (
              <Card key={rec.recommendation_id} sx={{ mb: 2, borderRadius: 1 }}>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 2 }}>
                    <Box sx={{ flex: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap', mb: 1 }}>
                        <LightbulbIcon color="primary" fontSize="small" />
                        <Typography variant="h6" component="h2" sx={{ fontWeight: 600 }}>
                          {rec.title}
                        </Typography>
                        <Chip size="small" label={rec.policy_type} variant="outlined" />
                        <Chip size="small" label={rec.priority} color={priorityColor(rec.priority)} />
                        <Chip size="small" label={`Confidence: ${ei.confidence || '—'}`} variant="outlined" />
                      </Box>
                      <Typography variant="body2" color="text.secondary" paragraph sx={{ mb: 1 }}>
                        {rec.summary}
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 1 }}>
                        {(ei.utilization_change_pct_range || []).length === 2 && (
                          <Chip
                            icon={<TrendingIcon />}
                            size="small"
                            label={`Util Δ ${ei.utilization_change_pct_range![0]}% to ${ei.utilization_change_pct_range![1]}% (scenario)`}
                            variant="outlined"
                          />
                        )}
                        {(ei.cost_pmpm_change_pct_range || []).length === 2 && (
                          <Chip
                            size="small"
                            label={`Allowed PMPM Δ ${ei.cost_pmpm_change_pct_range![0]}% to ${ei.cost_pmpm_change_pct_range![1]}% (scenario)`}
                            variant="outlined"
                          />
                        )}
                      </Box>
                    </Box>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, alignItems: 'flex-end' }}>
                      <IconButton size="small" onClick={() => toggle(rec.recommendation_id)} aria-label="expand">
                        {open ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                      </IconButton>
                      <Button
                        size="small"
                        endIcon={<OpenInNewIcon />}
                        onClick={() => navigate('/policies/builder')}
                      >
                        Draft in builder
                      </Button>
                    </Box>
                  </Box>

                  <Collapse in={open}>
                    <Divider sx={{ my: 2 }} />
                    <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                      Why this recommendation
                    </Typography>
                    <Box component="ul" sx={{ pl: 2, mb: 2 }}>
                      {(ex.why_recommended || []).map((line, i) => (
                        <Typography component="li" variant="body2" key={i} sx={{ mb: 0.5 }}>
                          {line}
                        </Typography>
                      ))}
                    </Box>

                    <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                      Impact methodology
                    </Typography>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      {ei.methodology === 'hybrid_catalog_and_learned_elasticity'
                        ? 'Hybrid: archetype benchmarks adjusted using a tenant-specific elasticity model where available.'
                        : 'Catalog benchmarks applied to your baseline reference; no tenant elasticity model matched this policy type.'}{' '}
                      {ei.elasticity_note}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      {ei.confidence_explanation}
                    </Typography>

                    <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Reference</TableCell>
                            <TableCell align="right">Value</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          <TableRow>
                            <TableCell>Baseline util / 1K MM (tenant ref.)</TableCell>
                            <TableCell align="right">
                              {ei.baseline_util_per_1k_reference != null
                                ? ei.baseline_util_per_1k_reference.toFixed(2)
                                : '—'}
                            </TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>Baseline allowed PMPM (tenant ref.)</TableCell>
                            <TableCell align="right">
                              {ei.baseline_allowed_pmpm_reference != null
                                ? `$${ei.baseline_allowed_pmpm_reference.toFixed(2)}`
                                : '—'}
                            </TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>Scenario util / 1K range</TableCell>
                            <TableCell align="right">
                              {ei.projected_util_per_1k_range
                                ? `${ei.projected_util_per_1k_range[0].toFixed(2)} – ${ei.projected_util_per_1k_range[1].toFixed(2)}`
                                : '—'}
                            </TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>Scenario allowed PMPM range</TableCell>
                            <TableCell align="right">
                              {ei.projected_allowed_pmpm_range
                                ? `$${ei.projected_allowed_pmpm_range[0].toFixed(2)} – $${ei.projected_allowed_pmpm_range[1].toFixed(2)}`
                                : '—'}
                            </TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>Claims overlap (allowed $ in window)</TableCell>
                            <TableCell align="right">
                              {rec.data_signals?.overlap_allowed_amount != null
                                ? `$${rec.data_signals.overlap_allowed_amount.toLocaleString(undefined, { maximumFractionDigits: 0 })}`
                                : '—'}
                            </TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>Overlap claim lines</TableCell>
                            <TableCell align="right">
                              {rec.data_signals?.overlap_claim_lines?.toLocaleString() ?? '—'}
                            </TableCell>
                          </TableRow>
                        </TableBody>
                      </Table>
                    </TableContainer>

                    <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                      Evidence from your data (lookback window)
                    </Typography>
                    {(ex.evidence || []).length === 0 ? (
                      <Typography variant="body2" color="text.secondary" paragraph>
                        No CPT-level overlap in window — suggestion is exploratory against catalog archetype.
                      </Typography>
                    ) : (
                      <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell>Type</TableCell>
                              <TableCell>Detail</TableCell>
                              <TableCell align="right">Allowed $</TableCell>
                              <TableCell align="right">Lines</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {(ex.evidence || []).map((ev, idx) => (
                              <TableRow key={idx}>
                                <TableCell>{ev.type}</TableCell>
                                <TableCell>
                                  <Typography variant="body2">{ev.explanation}</Typography>
                                  {ev.cpt_code && (
                                    <Typography variant="caption" color="text.secondary" display="block">
                                      CPT {ev.cpt_code}
                                      {ev.rank_in_tenant_cpt != null ? ` · tenant rank ~${ev.rank_in_tenant_cpt + 1}` : ''}
                                    </Typography>
                                  )}
                                  {ev.service_category && (
                                    <Typography variant="caption" color="text.secondary" display="block">
                                      Category {ev.service_category}
                                    </Typography>
                                  )}
                                </TableCell>
                                <TableCell align="right">
                                  {ev.allowed_amount_window != null
                                    ? `$${ev.allowed_amount_window.toLocaleString(undefined, { maximumFractionDigits: 0 })}`
                                    : '—'}
                                </TableCell>
                                <TableCell align="right">{ev.claim_lines ?? '—'}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    )}

                    <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                      Suggested scope (starter)
                    </Typography>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      {rec.suggested_scope?.note}
                    </Typography>
                    <Typography variant="body2" component="pre" sx={{ fontFamily: 'inherit', whiteSpace: 'pre-wrap', bgcolor: 'action.hover', p: 1.5, borderRadius: 1 }}>
                      {JSON.stringify(
                        {
                          procedure_codes: rec.suggested_scope?.procedure_codes,
                          service_categories: rec.suggested_scope?.service_categories,
                        },
                        null,
                        2
                      )}
                    </Typography>

                    {ex.implementation_guidance && (
                      <>
                        <Typography variant="subtitle2" fontWeight={600} gutterBottom sx={{ mt: 2 }}>
                          Implementation guidance
                        </Typography>
                        <Typography variant="body2" paragraph>
                          {ex.implementation_guidance}
                        </Typography>
                      </>
                    )}

                    {(ex.governance || []).length > 0 && (
                      <>
                        <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                          Governance checklist
                        </Typography>
                        <Box component="ul" sx={{ pl: 2 }}>
                          {(ex.governance || []).map((g, i) => (
                            <Typography component="li" variant="body2" key={i}>
                              {g}
                            </Typography>
                          ))}
                        </Box>
                      </>
                    )}
                  </Collapse>
                </CardContent>
              </Card>
            )
          })}

          {(data.skipped_as_duplicates?.length ?? 0) > 0 && (
            <Card sx={{ mt: 3, borderRadius: 1 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <BlockIcon color="action" />
                  Not recommended (duplicate or equivalent in force)
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  These archetypes were suppressed because they match existing policies (code coverage or high Jaccard
                  similarity on CPT sets with aligned policy type).
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Archetype</TableCell>
                        <TableCell>Reason</TableCell>
                        <TableCell>Matching policy IDs</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {data.skipped_as_duplicates!.map((s) => (
                        <TableRow key={s.archetype_id}>
                          <TableCell>{s.title}</TableCell>
                          <TableCell>{s.reason}</TableCell>
                          <TableCell>{(s.matching_policy_ids || []).join(', ') || '—'}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </Box>
  )
}
