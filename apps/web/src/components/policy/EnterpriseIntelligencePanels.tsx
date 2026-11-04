/**
 * Dec 4 P0 panels — composition, causal, provider behavior, cold-start, applicability.
 * Demonstration catalog: Representative Payer Policies (Blue Cross NC-like).
 * Authoritative catalog: public CMS NCD/LCD/articles/NCCI when acquired.
 */
import { useEffect, useState } from 'react'
import {
  Alert,
  Box,
  Chip,
  CircularProgress,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { apiClient } from '../../lib/api'

export function PolicyCompositionPanel({ policyId }: { policyId: string }) {
  const [data, setData] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setLoading(true)
      try {
        const d = await apiClient.getEnterprisePolicyComposition(policyId)
        if (!cancelled) setData(d)
      } catch (e: any) {
        if (!cancelled) setError(e?.detail || e?.message || 'Failed to load composition')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [policyId])

  if (loading) return <CircularProgress size={28} />
  if (error) return <Alert severity="warning">{error}</Alert>
  if (!data) return null

  return (
    <Box>
      <Typography variant="h6" fontWeight={600} gutterBottom>
        Policy composition
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Domain + mechanisms + scope — one shared lifecycle, not a separate engine per policy shape.
      </Typography>
      <Grid container spacing={2}>
        <Grid item xs={12} md={4}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Primary domain
            </Typography>
            <Typography fontWeight={700}>{data.primary_domain}</Typography>
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
              Catalog type (compat): {data.catalog_policy_type || '—'}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={8}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Mechanisms (multi-select)
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75, mt: 1 }}>
              {(data.mechanisms || []).map((m: string) => (
                <Chip key={m} size="small" label={m.replace(/_/g, ' ')} />
              ))}
            </Box>
            <Typography variant="body2" sx={{ mt: 1.5 }}>
              Service scope: {(data.service_scope || []).join(', ') || '—'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Authority: {data.authority || '—'} · Jurisdiction: {data.jurisdiction || '—'}
            </Typography>
          </Paper>
        </Grid>
      </Grid>
      {data.notes && (
        <Alert severity="info" sx={{ mt: 2 }}>
          {data.notes}
        </Alert>
      )}
    </Box>
  )
}

export function CausalImpactPanel({ policyId }: { policyId: string }) {
  const [data, setData] = useState<any>(null)
  const [feasibility, setFeasibility] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setLoading(true)
      try {
        const [d, f] = await Promise.all([
          apiClient.getEnterpriseCausalImpact(policyId),
          apiClient.getEnterpriseCausalFeasibility(policyId).catch(() => null),
        ])
        if (!cancelled) {
          setData(d)
          setFeasibility(f)
        }
      } catch (e: any) {
        if (!cancelled) setError(e?.detail || e?.message || 'Failed to load causal impact')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [policyId])

  if (loading) return <CircularProgress size={28} />
  if (error) return <Alert severity="warning">{error}</Alert>
  if (!data) return null

  const cls = data.evidence_classification || 'INCONCLUSIVE'

  return (
    <Box>
      <Typography variant="h6" fontWeight={600} gutterBottom>
        Causal Impact Workbench
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Separates observed change, expected change without the policy, and estimated incremental effect.
        Naive pre/post is never labeled causal. Feasibility is assessed for every policy domain; estimates
        only when identifiable. Mechanical payment savings are never labeled causal.
      </Typography>
      {feasibility?.status && (
        <Alert
          severity={feasibility.status === 'CAUSAL_ESTIMATE_SUPPORTED' ? 'success' : 'info'}
          sx={{ mb: 2 }}
        >
          Causal feasibility: <strong>{feasibility.status}</strong>
          {feasibility.mechanism ? ` · mechanism ${feasibility.mechanism}` : ''}
          {feasibility.blockers?.length ? ` — ${feasibility.blockers[0]}` : ''}
        </Alert>
      )}
      {data.labeled_synthetic && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Labeled synthetic validation fixture ({data.fixture_id}). Not BCBS NC production claims.
          {data.recovered_within_tolerance != null && (
            <> DiD recovery check: {data.recovered_within_tolerance ? 'PASS' : 'FAIL'}.</>
          )}
        </Alert>
      )}
      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
        <Chip label={`Method: ${data.method}`} />
        <Chip
          label={`Evidence: ${cls}`}
          color={cls === 'CAUSAL' ? 'success' : cls === 'INCONCLUSIVE' ? 'default' : 'warning'}
        />
        {data.unit?.code && <Chip label={`Unit: ${data.unit.code}`} variant="outlined" />}
        {data.diagnostics?.parallel_trends_pre && (
          <Chip
            label={`Pre-trends: ${data.diagnostics.parallel_trends_pre}`}
            color={data.diagnostics.parallel_trends_pre === 'PASS' ? 'success' : 'error'}
            variant="outlined"
          />
        )}
      </Box>
      {data.unit?.description && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {data.unit.description}
        </Typography>
      )}
      {data.formula && (
        <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
          DiD: {data.formula}
          {data.calculation && (
            <>
              {' '}
              = ({data.calculation.Y_T_post} − {data.calculation.Y_T_pre}) − (
              {data.calculation.Y_C_post} − {data.calculation.Y_C_pre}) = {data.calculation.did}
            </>
          )}
        </Typography>
      )}
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={12} md={4}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Observed change (naive pre/post)
            </Typography>
            <Typography variant="h5" fontWeight={700}>
              {data.observed_change ?? '—'}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Expected without policy (control Δ)
            </Typography>
            <Typography variant="h5" fontWeight={700}>
              {data.expected_change_without_policy ?? '—'}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper variant="outlined" sx={{ p: 2, borderColor: 'primary.main' }}>
            <Typography variant="caption" color="text.secondary">
              Estimated incremental policy effect (DiD)
            </Typography>
            <Typography variant="h5" fontWeight={700} color="primary.main">
              {data.estimated_incremental_effect ?? '—'}
            </Typography>
          </Paper>
        </Grid>
      </Grid>
      {(data.treatment_definition || data.comparison_population) && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <div>
            Treatment:{' '}
            {typeof data.treatment_definition === 'string'
              ? data.treatment_definition
              : data.treatment_definition?.definition || '—'}
          </div>
          <div>
            Comparison:{' '}
            {typeof data.comparison_population === 'string'
              ? data.comparison_population
              : data.comparison_population?.definition || '—'}
          </div>
          {data.periods?.intervention_timing && (
            <div>Timing: {data.periods.intervention_timing}</div>
          )}
        </Alert>
      )}
      {data.diagnostics?.naive_pre_post_would_overstate && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Naive pre/post ({data.diagnostics.naive_pre_post_change}) would overstate the policy effect
          versus DiD incremental estimate ({data.estimated_incremental_effect}). Difference ≈ control
          change ({data.expected_change_without_policy}).
        </Alert>
      )}
      {data.uncertainty_interval?.lower != null && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Illustrative {Math.round((data.uncertainty_interval.level || 0.95) * 100)}% interval:{' '}
          [{data.uncertainty_interval.lower}, {data.uncertainty_interval.upper}]
          {data.uncertainty_interval.note ? ` — ${data.uncertainty_interval.note}` : ''}
        </Typography>
      )}
      {(data.series || []).length > 0 && (
        <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Policy vs comparison population (indexed)
          </Typography>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={data.series}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="policy_population" name="Policy population" stroke="#3B2F8F" />
              <Line
                type="monotone"
                dataKey="comparison_population"
                name="Comparison population"
                stroke="#64748B"
              />
            </LineChart>
          </ResponsiveContainer>
        </Paper>
      )}
      <Typography variant="subtitle2" gutterBottom>
        External factors considered
      </Typography>
      <Table size="small" sx={{ mb: 2 }}>
        <TableHead>
          <TableRow>
            <TableCell>Factor</TableCell>
            <TableCell>Category</TableCell>
            <TableCell>Timing</TableCell>
            <TableCell>Plausible direction</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {(data.external_factors || []).map((f: any) => (
            <TableRow key={f.factor_id}>
              <TableCell>{f.name}</TableCell>
              <TableCell>{f.category}</TableCell>
              <TableCell>{f.timing}</TableCell>
              <TableCell>{f.plausible_direction}</TableCell>
            </TableRow>
          ))}
          {(data.external_factors || []).length === 0 && (
            <TableRow>
              <TableCell colSpan={4}>No external-event register for this policy yet.</TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
      {(data.limitations || []).length > 0 && (
        <Alert severity="warning">
          {(data.limitations as string[]).map((l) => (
            <div key={l}>• {l}</div>
          ))}
        </Alert>
      )}
    </Box>
  )
}

export function ProviderBehaviorExplorerPanel({ policyId }: { policyId: string }) {
  const [data, setData] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setLoading(true)
      try {
        const d = await apiClient.getEnterpriseProviderBehavior(policyId)
        if (!cancelled) setData(d)
      } catch (e: any) {
        if (!cancelled) setError(e?.detail || e?.message || 'Failed to load provider behavior')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [policyId])

  if (loading) return <CircularProgress size={28} />
  if (error) return <Alert severity="warning">{error}</Alert>
  if (!data) return null

  return (
    <Box>
      <Typography variant="h6" fontWeight={600} gutterBottom>
        Provider Behavior Explorer
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Observable practice-pattern signals only — not inferred intent or “circumvention.”
      </Typography>
      {data.labeled_synthetic && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Demo fixture. Empiric panels require provider-grain aggregates. Small-cell suppression is
          applied in the API response (min n={data.minimum_n ?? 30}), not only in the UI.
        </Alert>
      )}
      {data.peer_selection && (
        <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Peer selection: {data.peer_selection.method}
          </Typography>
          <ul style={{ margin: 0, paddingLeft: 18 }}>
            {(data.peer_selection.criteria || []).map((c: string) => (
              <li key={c}>
                <Typography variant="body2">{c}</Typography>
              </li>
            ))}
          </ul>
          {data.peer_selection.not_used && (
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
              Not used: {data.peer_selection.not_used}
            </Typography>
          )}
        </Paper>
      )}
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Provider</TableCell>
            <TableCell>Signal</TableCell>
            <TableCell align="right">Baseline</TableCell>
            <TableCell align="right">Observed</TableCell>
            <TableCell align="right">Δ</TableCell>
            <TableCell align="right">Peer-adj Δ</TableCell>
            <TableCell>Denom</TableCell>
            <TableCell>n</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {(data.signals || []).map((s: any) => (
            <TableRow key={`${s.provider_id}-${s.signal}`} sx={{ opacity: s.suppressed ? 0.5 : 1 }}>
              <TableCell>
                <Typography variant="body2" fontWeight={600}>
                  {s.provider_name}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {s.interpretation}
                </Typography>
              </TableCell>
              <TableCell>{s.signal}</TableCell>
              <TableCell align="right">{s.suppressed ? '—' : s.baseline_value}</TableCell>
              <TableCell align="right">{s.suppressed ? '—' : s.observed_value}</TableCell>
              <TableCell align="right">{s.suppressed ? 'suppressed' : s.change}</TableCell>
              <TableCell align="right">
                {s.suppressed || s.peer_adjusted_change == null ? '—' : s.peer_adjusted_change}
              </TableCell>
              <TableCell>
                <Typography variant="caption">{s.denominator || '—'}</Typography>
              </TableCell>
              <TableCell>{s.n}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {(data.caveats || []).map((c: string) => (
        <Typography key={c} variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
          • {c}
        </Typography>
      ))}
    </Box>
  )
}

export function ColdStartPanel({ policyId }: { policyId: string }) {
  const [data, setData] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setLoading(true)
      try {
        const d = await apiClient.getEnterpriseColdStart(policyId)
        if (!cancelled) setData(d)
      } catch (e: any) {
        if (!cancelled) setError(e?.detail || e?.message || 'Failed to load cold-start')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [policyId])

  if (loading) return <CircularProgress size={28} />
  if (error) return <Alert severity="warning">{error}</Alert>
  if (!data) return null

  return (
    <Box>
      <Typography variant="h6" fontWeight={600} gutterBottom>
        Cold-start intelligence
      </Typography>
      <Chip label={`Evidence tier: ${data.evidence_tier}`} sx={{ mb: 2 }} color="warning" />
      <Alert severity="info" sx={{ mb: 2 }}>
        {data.uncertainty_note}
        {data.tier_selection_reason && (
          <Typography variant="body2" sx={{ mt: 1 }}>
            {data.tier_selection_reason}
          </Typography>
        )}
      </Alert>
      <Typography variant="body2" sx={{ mb: 1 }}>
        Baseline available: <strong>{data.baseline_available ? 'Yes' : 'No'}</strong> · Prior
        intervention history: <strong>{data.prior_intervention_history ? 'Yes' : 'No'}</strong>
      </Typography>
      <Typography variant="subtitle2">Assumptions (with provenance)</Typography>
      {(data.assumption_records || []).length > 0 ? (
        <Table size="small" sx={{ mb: 2 }}>
          <TableHead>
            <TableRow>
              <TableCell>Assumption</TableCell>
              <TableCell>Source</TableCell>
              <TableCell>Version</TableCell>
              <TableCell>As of</TableCell>
              <TableCell>Uncertainty</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {(data.assumption_records || []).map((a: any) => (
              <TableRow key={a.assumption_id || a.text}>
                <TableCell>{a.text}</TableCell>
                <TableCell>{a.source}</TableCell>
                <TableCell>{a.source_version}</TableCell>
                <TableCell>{a.as_of}</TableCell>
                <TableCell>
                  <Typography variant="caption">{a.uncertainty_rationale}</Typography>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : (
        <ul>
          {(data.assumptions || []).map((a: string) => (
            <li key={a}>
              <Typography variant="body2">{a}</Typography>
            </li>
          ))}
        </ul>
      )}
      <Typography variant="subtitle2">Analogs</Typography>
      <ul>
        {(data.analog_policies || []).map((a: any) => {
          const label = typeof a === 'string' ? a : `${a.name} (tier ${a.tier}) — ${a.why || ''}`
          return (
            <li key={label}>
              <Typography variant="body2">{label}</Typography>
            </li>
          )
        })}
      </ul>
      <Typography variant="body2" sx={{ mt: 1 }}>
        {data.directional_forecast}
      </Typography>
      {data.recalibration_rule && (
        <Alert severity="warning" sx={{ mt: 2 }}>
          {data.recalibration_rule}
        </Alert>
      )}
      {data.numeric_scenario && (
        <Paper variant="outlined" sx={{ p: 2, mt: 2 }}>
          <Typography variant="caption" color="text.secondary">
            Scenario range only (not a point estimate)
          </Typography>
          <Typography>
            {data.numeric_scenario.metric}: {data.numeric_scenario.scenario_low} –{' '}
            {data.numeric_scenario.scenario_high} (baseline {data.numeric_scenario.baseline})
          </Typography>
        </Paper>
      )}
    </Box>
  )
}

export function ApplicabilityExplorerPanel({ policyId }: { policyId?: string }) {
  const [data, setData] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setLoading(true)
      try {
        // Prefer policy-linked Medicare rules when a policy is in context; fall back to NC imaging query.
        if (policyId) {
          try {
            const linked = await apiClient.getApplicableMedicareRules(policyId)
            if (!cancelled && linked) {
              setData({
                disclaimer:
                  linked.disclaimer ||
                  'Applicability is policy-scoped. Commercial PA does not auto-inherit Medicare FFS rules.',
                program: linked.program || 'Policy-linked Medicare sources',
                program_family: linked.program_family || 'REFERENCE',
                state: linked.state || 'North Carolina',
                contractor: linked.contractor,
                jurisdiction: linked.jurisdiction,
                status: linked.status || 'POLICY_SCOPED',
                sources: linked.sources || linked.rules || linked.items || [],
                conflicts: linked.conflicts || [],
                unresolved_questions: linked.unresolved_questions || [
                  'Confirm commercial adoption before treating FFS sources as operative.',
                ],
                policy_id: policyId,
              })
              return
            }
          } catch {
            /* fall through */
          }
        }
        const d = await apiClient.resolveEnterpriseApplicability({
          program: 'Original Medicare FFS',
          state: 'North Carolina',
          service_category: 'Advanced imaging / MRI',
        })
        if (!cancelled) setData({ ...d, policy_id: policyId || null, query_mode: 'catalog_fallback' })
      } catch (e: any) {
        if (!cancelled) setError(e?.detail || e?.message || 'Failed to resolve applicability')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [policyId])

  if (loading) return <CircularProgress size={28} />
  if (error) return <Alert severity="warning">{error}</Alert>
  if (!data) return null

  return (
    <Box>
      <Typography variant="h6" fontWeight={600} gutterBottom>
        Medicare / reimbursement applicability
      </Typography>
      <Alert severity="warning" sx={{ mb: 2 }}>
        {data.disclaimer}
      </Alert>
      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 1 }}>
        {data.program_family && <Chip size="small" label={data.program_family} />}
        {data.status && <Chip size="small" label={data.status} variant="outlined" />}
      </Box>
      <Typography variant="body2" sx={{ mb: 1 }}>
        <strong>{data.program}</strong> · {data.state} · {data.contractor || '—'} ·{' '}
        {data.jurisdiction || '—'}
      </Typography>
      <Table size="small" sx={{ mb: 2 }}>
        <TableHead>
          <TableRow>
            <TableCell>Source</TableCell>
            <TableCell>ID</TableCell>
            <TableCell>Title</TableCell>
            <TableCell>Authority</TableCell>
            <TableCell>Effective</TableCell>
            <TableCell>Status</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {(data.sources || []).map((s: any) => (
            <TableRow key={s.identifier}>
              <TableCell>{s.source_type}</TableCell>
              <TableCell>{s.identifier}</TableCell>
              <TableCell>{s.title}</TableCell>
              <TableCell>{s.authority}</TableCell>
              <TableCell>{s.effective_date}</TableCell>
              <TableCell>{s.status || '—'}</TableCell>
            </TableRow>
          ))}
          {(data.sources || []).length === 0 && (
            <TableRow>
              <TableCell colSpan={6}>No matching sources for this program/jurisdiction query.</TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
      {(data.conflicts || []).length > 0 && (
        <>
          <Typography variant="subtitle2">Conflicts</Typography>
          <ul>
            {(data.conflicts || []).map((q: string) => (
              <li key={q}>
                <Typography variant="body2">{q}</Typography>
              </li>
            ))}
          </ul>
        </>
      )}
      <Typography variant="subtitle2">Unresolved questions</Typography>
      <ul>
        {(data.unresolved_questions || []).map((q: string) => (
          <li key={q}>
            <Typography variant="body2">{q}</Typography>
          </li>
        ))}
      </ul>
    </Box>
  )
}

export function UnifiedVerdictEvidencePanel({
  policyId,
  observationVerdict,
}: {
  policyId: string
  observationVerdict?: string
}) {
  const [data, setData] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setLoading(true)
      try {
        const d = await apiClient.getEnterpriseVerdictEvidence(policyId, observationVerdict)
        if (!cancelled) setData(d)
      } catch (e: any) {
        if (!cancelled) setError(e?.detail || e?.message || 'Failed to load verdict evidence')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [policyId, observationVerdict])

  if (loading) return <CircularProgress size={28} />
  if (error) return <Alert severity="warning">{error}</Alert>
  if (!data) return null

  const a = data.assessments || {}

  return (
    <Box>
      <Typography variant="h6" fontWeight={600} gutterBottom>
        Unified policy impact verdict
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {data.assessment_note ||
          'Three independent assessments — not collapsed into one success score.'}
      </Typography>
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={12} md={4}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Forecast performance
            </Typography>
            <Typography fontWeight={700}>{a.forecast_performance || '—'}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Causal evidence
            </Typography>
            <Typography fontWeight={700}>{a.causal_evidence || '—'}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Policy governance
            </Typography>
            <Typography fontWeight={700}>{a.policy_governance || '—'}</Typography>
          </Paper>
        </Grid>
      </Grid>
      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="subtitle2">Causal summary</Typography>
            <Typography variant="body2">
              Method: {data.causal_summary?.method || '—'} · Effect:{' '}
              {data.causal_summary?.estimated_incremental_effect ?? '—'} · Classification:{' '}
              {data.causal_summary?.evidence_classification || '—'}
            </Typography>
            {data.causal_summary?.labeled_synthetic && (
              <Typography variant="caption" color="warning.main" display="block">
                Synthetic causal fixture — not production claims.
              </Typography>
            )}
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="subtitle2">Provider behavior</Typography>
            <Typography variant="body2">
              Visible signals: {data.provider_behavior_summary?.signal_count ?? 0} · Suppressed:{' '}
              {data.provider_behavior_summary?.suppressed_count ?? 0}
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block">
              No intent inference. Peer method:{' '}
              {data.provider_behavior_summary?.peer_selection?.method || '—'}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="subtitle2">Applicability</Typography>
            <Typography variant="body2">
              {data.applicability_summary?.program_family || '—'} ·{' '}
              {data.applicability_summary?.status || '—'} · Sources:{' '}
              {data.applicability_summary?.source_count ?? 0}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="subtitle2">Composition</Typography>
            <Typography variant="body2">
              {data.composition?.primary_domain} · {(data.composition?.mechanisms || []).join(', ')}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Version: {data.policy_version || '—'}
            </Typography>
          </Paper>
        </Grid>
      </Grid>
      {data.cold_start && (
        <Alert severity="info" sx={{ mt: 2 }}>
          Cold-start tier {data.cold_start.evidence_tier}: scenario ranges only; assumptions are
          provenance-tracked and not auto-promoted to empirical forecasts.
        </Alert>
      )}
      <Typography variant="subtitle2" sx={{ mt: 2 }}>
        Decision options (advisory)
      </Typography>
      <ul>
        {(data.decision_options || []).map((o: string) => (
          <li key={o}>
            <Typography variant="body2">{o}</Typography>
          </li>
        ))}
      </ul>
    </Box>
  )
}

/** Linked NCD/LCD/articles/NCCI for this policy — not every rule applies to every service. */
export function ApplicableMedicareRulesPanel({ policyId }: { policyId: string }) {
  const [data, setData] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setLoading(true)
      try {
        const d = await apiClient.getApplicableMedicareRules(policyId)
        if (!cancelled) setData(d)
      } catch (e: any) {
        if (!cancelled) setError(e?.detail || e?.message || 'Failed to load applicable Medicare rules')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [policyId])

  if (loading) return <CircularProgress size={28} />
  if (error) return <Alert severity="warning">{error}</Alert>
  if (!data) return null

  const linked = data.linked_source_rules || []
  const appl = data.applicability_resolution || {}
  const clinical = data.clinical_applicability_bundle

  return (
    <Box sx={{ mb: 3 }}>
      <Typography variant="h6" fontWeight={600} gutterBottom>
        Applicable Medicare rules
      </Typography>
      <Alert severity="info" sx={{ mb: 2 }}>
        NCD/LCD are coverage determinations; NCCI edits are coding/payment rules; articles support
        documentation. Jurisdiction match is not clinical match. Synthetic analytics remain demo
        evidence — not Blue Cross NC outcomes.
        {data.rule_set?.rule_set_id ? (
          <>
            {' '}
            Rule-set: <code>{data.rule_set.rule_set_id}</code> ({data.rule_set.version}).
          </>
        ) : null}
      </Alert>
      {clinical?.honesty?.do_not_claim_L34425_as_general_mri_pa_lcd && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Clinical check: NCD 220.2 is the primary national MRI authority. L34425/A56729 are NC/JM
          documents but only cover orbit/face/neck MRI (CPT 70540/70542/70543) — not the full
          Outpatient MRI PA portfolio.
        </Alert>
      )}
      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 1 }}>
        <Chip size="small" label={appl.program_family || '—'} />
        <Chip size="small" label={appl.status || '—'} variant="outlined" />
        <Chip size="small" label={`${linked.length} linked source(s)`} variant="outlined" />
      </Box>
      {linked.length === 0 ? (
        <Typography variant="body2" color="text.secondary">
          No source documents linked to this policy yet. Open Medicare Rules Explorer to inspect
          public inventory, or seed MRI demo links for the imaging example.
        </Typography>
      ) : (
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Kind</TableCell>
              <TableCell>Role</TableCell>
              <TableCell>ID</TableCell>
              <TableCell>Clinical match</TableCell>
              <TableCell>Title</TableCell>
              <TableCell>Why applicable</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {linked.map((r: any) => (
              <TableRow key={`${r.link_role}-${r.source_document_id}`}>
                <TableCell>{r.kind}</TableCell>
                <TableCell>{r.link_role}</TableCell>
                <TableCell>{r.source_document_id}</TableCell>
                <TableCell>
                  {r.clinical_applicability?.clinical_match ||
                    (r.clinical_applicability?.present_as_mri_authority ? 'APPLICABLE' : '—')}
                </TableCell>
                <TableCell>{r.title}</TableCell>
                <TableCell>{r.clinical_caveat || r.why_applicable}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
      {(appl.unresolved_questions || []).length > 0 && (
        <Alert severity="warning" sx={{ mt: 2 }}>
          {(appl.unresolved_questions || []).join(' ')}
        </Alert>
      )}
    </Box>
  )
}

/** Surfaces docs/demo/.../policy_definitions/v1.2 packages that previously stayed invisible in workspace. */
export function PolicyDefinitionPackagePanel({ policyId }: { policyId: string }) {
  const [data, setData] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setLoading(true)
      try {
        const d = await apiClient.getEnterprisePolicyDefinitionPackage(policyId)
        if (!cancelled) setData(d)
      } catch (e: any) {
        if (!cancelled) setError(e?.detail || e?.message || 'Failed to load definition package')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [policyId])

  if (loading) return <CircularProgress size={28} />
  if (error) return <Alert severity="warning">{error}</Alert>
  if (!data) return null

  if (!data.available) {
    return (
      <Alert severity="info" data-testid="definition-package-absent">
        No v1.2 definition package is mapped for this catalog policy. Definition work for the
        Representative nine lives under <code>docs/demo/bcbs-nc/policy_definitions/v1.2/</code>.
        {data.reason ? ` (${data.reason})` : ''}
      </Alert>
    )
  }

  const blockers = Array.isArray(data.release_blockers) ? data.release_blockers : []
  const codes = data.codeset_summary?.candidate_codes
  const codeList = Array.isArray(codes)
    ? codes
        .map((c: any) => (typeof c === 'string' ? c : c?.code || c?.cpt || JSON.stringify(c)))
        .filter(Boolean)
    : []

  return (
    <Box data-testid="definition-package-panel">
      <Typography variant="h6" fontWeight={600} gutterBottom>
        Policy definition package (v1.2)
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Review-only package from the definition workstream — not operative activation and not a
        substitute for signed clinical/compliance criteria.
      </Typography>

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
        <Chip size="small" color="warning" label={data.definition_status || 'DEFINITION_REVIEW_REQUIRED'} />
        <Chip size="small" color="error" variant="outlined" label={`Activation: ${data.operational_activation}`} />
        <Chip size="small" variant="outlined" label={`Clinical approval: ${data.clinical_product_approval}`} />
        {data.package_version && <Chip size="small" variant="outlined" label={data.package_version} />}
        {data.structural_technical_closure && (
          <Chip size="small" color="info" variant="outlined" label={String(data.structural_technical_closure).slice(0, 48)} />
        )}
        {data.release_blocker_count != null && (
          <Chip size="small" color="warning" label={`${data.release_blocker_count} release blockers`} />
        )}
      </Box>

      {(data.ui_rules || []).map((r: string) => (
        <Alert key={r} severity="info" sx={{ mb: 1 }}>
          {r}
        </Alert>
      ))}

      <Grid container spacing={2} sx={{ mt: 0.5 }}>
        <Grid item xs={12} md={6}>
          <Paper variant="outlined" sx={{ p: 2 }} data-testid="definition-codeset-card">
            <Typography variant="subtitle2" gutterBottom>
              Codeset / applicability summary
            </Typography>
            {data.codeset_summary?.intended_scope && (
              <Typography variant="body2" sx={{ mb: 1 }}>
                Intended scope: {typeof data.codeset_summary.intended_scope === 'string'
                  ? data.codeset_summary.intended_scope
                  : JSON.stringify(data.codeset_summary.intended_scope)}
              </Typography>
            )}
            {codeList.length > 0 ? (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
                {codeList.slice(0, 24).map((c: string) => (
                  <Chip key={c} size="small" label={c} />
                ))}
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary">
                See package codeset JSON for schedule detail.
              </Typography>
            )}
            {data.codeset_summary?.notes && (
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                {(Array.isArray(data.codeset_summary.notes)
                  ? data.codeset_summary.notes.join(' ')
                  : String(data.codeset_summary.notes)
                ).slice(0, 280)}
              </Typography>
            )}
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
              Showing CANDIDATE/APPROVED include codes only (matches levers when aligned). Exclude /
              defect rows stay in the package JSON, not on this card.
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper variant="outlined" sx={{ p: 2 }} data-testid="definition-blockers-card">
            <Typography variant="subtitle2" gutterBottom>
              Release blockers (hard gates)
            </Typography>
            {blockers.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                No blocker rows loaded.
              </Typography>
            ) : (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                {blockers.slice(0, 12).map((b: any) => (
                  <Alert key={b.id || b.artifact} severity="warning" sx={{ py: 0.5 }}>
                    <strong>{b.id}</strong>
                    {b.artifact ? ` · ${b.artifact}` : ''}
                    {Array.isArray(b.blocks) ? ` — blocks ${b.blocks.join(', ')}` : ''}
                  </Alert>
                ))}
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>

      {data.scope_migration_excerpt && (
        <Paper variant="outlined" sx={{ p: 2, mt: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Scope migration
          </Typography>
          <Typography
            variant="body2"
            component="pre"
            sx={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit', m: 0, fontSize: 13 }}
          >
            {data.scope_migration_excerpt}
          </Typography>
        </Paper>
      )}

      {data.definition_excerpt && (
        <Paper variant="outlined" sx={{ p: 2, mt: 2 }} data-testid="definition-excerpt">
          <Typography variant="subtitle2" gutterBottom>
            Definition excerpt
          </Typography>
          <Typography
            variant="body2"
            component="pre"
            sx={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit', m: 0, fontSize: 13 }}
          >
            {data.definition_excerpt}
          </Typography>
        </Paper>
      )}

      {(data.artifacts || []).length > 0 && (
        <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 2 }}>
          Package artifacts: {(data.artifacts as string[]).join(' · ')}
        </Typography>
      )}
    </Box>
  )
}
