/**
 * Policy Monitoring — live observation / prediction / guardrail snapshot for a workspace policy.
 */
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Grid,
  LinearProgress,
  Paper,
  Typography,
} from '@mui/material'
import { format } from 'date-fns'
import { apiClient } from '../../lib/api'

interface PolicyMonitoringPanelProps {
  policyId: string
  policyName?: string
  guardrails?: any[]
  onObservationVerdict?: (verdict: string | undefined) => void
}

const MPPR_ID = 'd0eeb370-df14-4478-8755-dad6c3a35a47'
const SOS_ID = 'd7441dd9-3bfe-405e-ae6c-0377204bbb7e'
const EXPANSION_IDS = new Set([
  '58b839b5-b6e0-59e0-9406-d817877c3ce8', // ptp
  'e11b049d-fcce-55cc-bcd7-71329038383b', // mue
  'f2b8e7f3-1627-5dbe-8d7e-757ce21aa55b', // therapy
  '11218053-bdc0-569f-a415-fb61c5dcda37', // infusion
  '4f8c34e3-015b-509d-90ba-521261464258', // ncd
  '649b4ac8-ca82-5b84-aa87-84834490731a', // lcd
])

export default function PolicyMonitoringPanel({
  policyId,
  policyName,
  guardrails = [],
  onObservationVerdict,
}: PolicyMonitoringPanelProps) {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [observation, setObservation] = useState<any | null>(null)
  const [predictedImpact, setPredictedImpact] = useState<any | null>(null)
  const [recentScenarios, setRecentScenarios] = useState<any[]>([])
  const [mechanical, setMechanical] = useState<any | null>(null)

  useEffect(() => {
    let cancelled = false
    const withTimeout = <T,>(p: Promise<T>, ms: number, fallback: T): Promise<T> =>
      Promise.race([
        p,
        new Promise<T>((resolve) => setTimeout(() => resolve(fallback), ms)),
      ])

    ;(async () => {
      setLoading(true)
      setError(null)
      setObservation(null)
      setPredictedImpact(null)
      setRecentScenarios([])

      const isDemoKa =
        policyId === MPPR_ID || policyId === SOS_ID || EXPANSION_IDS.has(String(policyId))

      // Catalog policies: paint honest monitoring card immediately (don't block on slow lists).
      if (!isDemoKa) {
        setMechanical({
          demo_kind: 'catalog_monitoring',
          note:
            'Catalog policy monitoring: show live observation / predicted impact when present. No synthetic known-answer attached. Do not invent financial results.',
        })
        if (!cancelled) setLoading(false)
      }

      try {
        // Catalog policies: avoid unbounded getAnalyses fan-out (blocks other workspace tabs).
        const [obsList, impact, analyses] = await Promise.all([
          withTimeout(
            apiClient
              .listObservations({
                policy_id: policyId,
                latest_only: true,
                summary: true,
                limit: 5,
              })
              .catch(() => []),
            isDemoKa ? 12000 : 8000,
            []
          ),
          withTimeout(
            apiClient.getPolicyPredictedImpact(policyId).catch(() => null),
            isDemoKa ? 12000 : 8000,
            null
          ),
          isDemoKa
            ? withTimeout(
                apiClient.getAnalyses({ analysis_type: 'SIMULATE', limit: 20 }).catch(() => []),
                12000,
                []
              )
            : Promise.resolve([]),
        ])
        if (cancelled) return

        const observations = Array.isArray(obsList) ? obsList : []
        const forPolicy = observations.filter((o: any) => String(o.policy_id) === String(policyId))
        const obs = forPolicy[0] || null
        setObservation(obs)
        onObservationVerdict?.(obs?.verdict_status || undefined)
        setPredictedImpact(apiClient.hasUsablePredictedImpact(impact) ? impact : null)

        const sims = (Array.isArray(analyses) ? analyses : [])
          .filter(
            (a: any) =>
              String(a.policy_id) === String(policyId) && String(a.status).toUpperCase() === 'COMPLETED'
          )
          .slice(0, 5)
        setRecentScenarios(sims)

        // Mechanical / study cards from live APIs — never hardcode figures in JSX.
        let mech: any = null
        if (policyId === MPPR_ID) {
          mech = await apiClient.getMpprVertical().catch(() => null)
          if (mech) mech.demo_kind = 'mechanical'
        } else if (policyId === SOS_ID) {
          mech = await apiClient.getSosVertical().catch(() => null)
          if (mech) mech.demo_kind = 'mechanical'
        } else if (EXPANSION_IDS.has(String(policyId))) {
          const vert = await apiClient.getDemoExpansionVerticals().catch(() => null)
          const ids = vert?.policy_ids || {}
          const key = Object.entries(ids).find(([, id]) => String(id) === String(policyId))?.[0] as
            | string
            | undefined
          if (key && vert) {
            if (key === 'ncd' || key === 'lcd') {
              const study = vert.studies?.[key]
              mech = {
                demo_kind: 'provenance_study',
                expansion_key: key,
                study_class: study?.study_class || 'PROVENANCE_ONLY',
                composition: study?.composition,
                causal_feasibility: study?.causal_feasibility,
                talking_points: study?.demo_talking_points || [],
                financial_baseline: 'N/A',
                note:
                  key === 'lcd'
                    ? 'Orbit/face/neck only — never apply to lumbar MRI. No manufactured financial impact.'
                    : 'NCD study is provenance-only — no manufactured financial or causal estimate.',
              }
            } else {
              const wf = vert.what_ifs?.[key]
              mech = {
                demo_kind: 'mechanical',
                catalog_class: vert.catalog_class,
                expansion_key: key,
                known_answer: vert.known_answers?.[key],
                totals: vert.mechanical_totals?.[key],
                fully_validated_demo: Boolean(vert.known_answers?.[key]?.passed),
                what_if: wf,
                whatif_delta: wf?.delta_payer_savings ?? wf?.expected_delta_payer_savings,
                whatif_status: wf?.status,
                whatif_label: wf?.label,
                note:
                  key === 'therapy'
                    ? 'Coverage what-if is NOT_SUPPORTED_FOR_THIS_MECHANISM — mechanical $80 is the supported demo stage.'
                    : key === 'ptp' || key === 'mue'
                      ? 'SYNTHETIC_FIXTURE — not an authoritative CMS quarterly/confidential edit.'
                      : 'Synthetic mechanical fixture — not an observed causal effect.',
              }
            }
          }
        }
        if (!mech) {
          mech = {
            demo_kind: 'catalog_monitoring',
            note:
              'Catalog policy monitoring: show live observation / predicted impact when present. No synthetic known-answer attached. Do not invent financial results.',
          }
        }
        if (!cancelled) setMechanical(mech)
      } catch (e: any) {
        if (!cancelled) setError(e?.detail || e?.message || 'Failed to load monitoring data')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [policyId])

  if (loading) {
    return (
      <Box sx={{ py: 4 }}>
        <LinearProgress />
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          Loading monitoring snapshot for this policy…
        </Typography>
      </Box>
    )
  }

  const verdict = observation?.verdict_status
  const metrics = observation?.metrics || {}
  const vsBaseline = observation?.comparisons?.vs_baseline || {}
  const triggeredGuardrails = (guardrails || []).filter((g) => g?.triggered)

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2, gap: 2 }}>
        <Box>
          <Typography variant="h6" gutterBottom>
            Performance monitoring
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Latest observation, predicted impact, and guardrail status for{' '}
            <strong>{policyName || 'this policy'}</strong>.
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Button
            size="small"
            variant="outlined"
            onClick={() =>
              navigate(
                `/observation-analysis?policy=${encodeURIComponent(policyId)}${
                  observation?.observation_id
                    ? `&observation=${encodeURIComponent(observation.observation_id)}`
                    : ''
                }`
              )
            }
          >
            Observation analysis
          </Button>
          <Button size="small" variant="outlined" onClick={() => navigate('/policy-verdicts')}>
            Policy verdicts
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {!observation && !predictedImpact && !mechanical && (
        <Alert severity="info" sx={{ mb: 2 }}>
          No observation or predicted impact yet for this policy. Run observation analysis or generate Stage
          3.5 predicted impact to populate monitoring.
        </Alert>
      )}

      {mechanical?.demo_kind === 'catalog_monitoring' && (
        <Paper variant="outlined" sx={{ p: 2, mb: 2 }} data-testid="demo-catalog-monitoring-panel">
          <Typography variant="subtitle1" fontWeight={700} gutterBottom>
            Catalog policy monitoring
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 1 }}>
            <Chip size="small" label="CATALOG_POLICY" />
            <Chip size="small" variant="outlined" label="NO_SYNTHETIC_KA" />
            <Chip size="small" color="warning" label="OPERATIONAL_ACTIVATION_PROHIBITED" />
          </Box>
          <Alert severity="info" data-testid="demo-catalog-note">
            {mechanical.note}
          </Alert>
          <Typography variant="body2" sx={{ mt: 1 }}>
            Observation:{' '}
            <strong data-testid="demo-catalog-observation">
              {observation ? observation.verdict_status || 'PRESENT' : 'NONE'}
            </strong>
            {' · '}
            Predicted impact:{' '}
            <strong data-testid="demo-catalog-predicted">{predictedImpact ? 'PRESENT' : 'NONE'}</strong>
            {' · '}
            Completed what-if runs: <strong>{recentScenarios.length}</strong>
          </Typography>
          <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Button
              size="small"
              variant="outlined"
              onClick={() =>
                navigate(`/observation-analysis?policy=${encodeURIComponent(policyId)}`)
              }
            >
              Observations
            </Button>
            <Button size="small" variant="outlined" onClick={() => navigate('/predicted-impacts')}>
              Predicted impacts
            </Button>
            <Button
              size="small"
              variant="outlined"
              onClick={() => navigate(`/whatif?policy=${encodeURIComponent(policyId)}`)}
            >
              What-if
            </Button>
            <Button size="small" variant="outlined" onClick={() => navigate('/policy-verdicts')}>
              Verdicts
            </Button>
          </Box>
        </Paper>
      )}

      {mechanical?.demo_kind === 'provenance_study' && (
        <Paper variant="outlined" sx={{ p: 2, mb: 2 }} data-testid="demo-provenance-panel">
          <Typography variant="subtitle1" fontWeight={700} gutterBottom>
            Coverage study — provenance only
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 1 }}>
            <Chip size="small" color="info" label="PROVENANCE_ONLY" data-testid="demo-study-class" />
            <Chip size="small" variant="outlined" label="Financial baseline N/A" />
            <Chip size="small" variant="outlined" label="Causal estimate N/A" />
            <Chip size="small" color="warning" label="OPERATIONAL_ACTIVATION_PROHIBITED" />
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            {mechanical.composition?.notes ||
              'Source applicability and evidence traceability — not a payment lifecycle.'}
          </Typography>
          <Typography variant="body2" data-testid="demo-study-scope">
            Scope: {(mechanical.composition?.service_scope || []).join(', ') || '—'}
          </Typography>
          <Typography variant="body2">
            Authority: {mechanical.composition?.authority || '—'}
          </Typography>
          {(mechanical.talking_points || []).length > 0 && (
            <Box component="ul" sx={{ mt: 1, pl: 2 }}>
              {mechanical.talking_points.map((t: string) => (
                <li key={t}>
                  <Typography variant="body2">{t}</Typography>
                </li>
              ))}
            </Box>
          )}
          {mechanical.note && (
            <Alert severity="warning" sx={{ mt: 1 }} data-testid="demo-study-note">
              {mechanical.note}
            </Alert>
          )}
          <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Button size="small" variant="outlined" onClick={() => navigate(`/policies/workspace/${policyId}`)}>
              Composition / Applicability tabs
            </Button>
            <Button size="small" variant="outlined" onClick={() => navigate('/medicare-rules')}>
              Medicare Rules Explorer
            </Button>
          </Box>
        </Paper>
      )}

      {mechanical && mechanical.demo_kind !== 'provenance_study' && (
        <Paper variant="outlined" sx={{ p: 2, mb: 2 }} data-testid="demo-mechanical-panel">
          <Typography variant="subtitle1" fontWeight={700} gutterBottom>
            Mechanical / synthetic calculation
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            Deterministic payment or coding fixture for demo — not an observed causal effect. Payer
            perspective: savings reduce allowed/paid liability; provider payment moves opposite.
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 1 }}>
            {mechanical.catalog_class && <Chip size="small" label={mechanical.catalog_class} />}
            {mechanical.calculation_version && (
              <Chip size="small" variant="outlined" label={mechanical.calculation_version} />
            )}
            <Chip
              size="small"
              color={mechanical.fully_validated_demo || mechanical.known_answer?.passed ? 'success' : 'default'}
              label={
                mechanical.fully_validated_demo || mechanical.known_answer?.passed
                  ? 'FULLY_VALIDATED_DEMO'
                  : 'MECHANICAL'
              }
              data-testid="demo-validation-chip"
            />
          </Box>
          <Typography variant="body2" data-testid="demo-payer-savings">
            Payer savings:{' '}
            <strong>
              {mechanical.totals?.payer_savings != null
                ? `$${Number(mechanical.totals.payer_savings).toLocaleString()}`
                : mechanical.totals?.payment_impact != null
                  ? `$${Number(mechanical.totals.payment_impact).toLocaleString()}`
                  : '—'}
            </strong>
            {mechanical.totals?.baseline_paid != null && (
              <>
                {' '}
                · Baseline paid ${Number(mechanical.totals.baseline_paid).toLocaleString()} → post $
                {Number(mechanical.totals.post_policy_paid ?? mechanical.totals.post_paid ?? 0).toLocaleString()}
              </>
            )}
          </Typography>
          {(() => {
            const sosDelta =
              mechanical.what_if_80_to_70?.additional_payer_savings ??
              mechanical.what_if_80_to_70?.payer_savings_delta ??
              mechanical.what_if_80_to_70?.impact_metrics?.delta_payer_savings
            const mpprDelta =
              mechanical.what_if_50_to_40?.additional_payer_savings ??
              mechanical.what_if_50_to_40?.payer_savings_delta ??
              mechanical.what_if_50_to_40?.impact_metrics?.delta_payer_savings
            return (
              <>
                {sosDelta != null && (
                  <Typography variant="body2" sx={{ mt: 0.5 }} data-testid="demo-whatif-delta">
                    What-if (80%→70% hospital): additional payer savings{' '}
                    <strong>${Number(sosDelta).toLocaleString()}</strong>
                  </Typography>
                )}
                {mpprDelta != null && (
                  <Typography variant="body2" sx={{ mt: 0.5 }} data-testid="demo-whatif-delta">
                    What-if (50%→40% secondary): additional payer savings{' '}
                    <strong>${Number(mpprDelta).toLocaleString()}</strong>
                  </Typography>
                )}
              </>
            )
          })()}
          {mechanical.whatif_status === 'NOT_SUPPORTED_FOR_THIS_MECHANISM' && (
            <Alert severity="info" sx={{ mt: 1 }} data-testid="demo-whatif-unsupported">
              What-if: <strong>NOT_SUPPORTED_FOR_THIS_MECHANISM</strong>
              {mechanical.what_if?.message ? ` — ${mechanical.what_if.message}` : ''}
            </Alert>
          )}
          {mechanical.whatif_status === 'completed' && mechanical.whatif_delta != null && (
            <Typography variant="body2" sx={{ mt: 0.5 }} data-testid="demo-whatif-delta">
              What-if{mechanical.whatif_label ? ` (${mechanical.whatif_label})` : ''}: additional payer
              savings <strong>${Number(mechanical.whatif_delta).toLocaleString()}</strong>
            </Typography>
          )}
          {mechanical.note && (
            <Alert severity="info" sx={{ mt: 1 }} data-testid="demo-mechanical-note">
              {mechanical.note}
            </Alert>
          )}
          <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Button
              size="small"
              variant="outlined"
              onClick={() => navigate(`/whatif?policy=${encodeURIComponent(policyId)}`)}
              data-testid="demo-whatif-link"
            >
              What-if
            </Button>
            <Button
              size="small"
              variant="outlined"
              onClick={() => navigate(`/baseline-analysis?policy=${encodeURIComponent(policyId)}`)}
            >
              Baseline
            </Button>
            <Button size="small" variant="outlined" onClick={() => navigate('/policy-verdicts')}>
              Verdicts
            </Button>
          </Box>
        </Paper>
      )}

      <Grid container spacing={2}>
        <Grid item xs={12} md={4}>
          <Card variant="outlined" sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Current verdict
              </Typography>
              {verdict ? (
                <Chip
                  label={verdict.replace(/_/g, ' ')}
                  color={
                    verdict === 'BACKFIRE'
                      ? 'error'
                      : verdict === 'AT_RISK'
                        ? 'warning'
                        : verdict === 'ON_TRACK'
                          ? 'success'
                          : 'default'
                  }
                  sx={{ fontWeight: 700, mb: 1 }}
                />
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No verdict yet
                </Typography>
              )}
              {observation?.verdict_reason && (
                <Typography variant="body2" sx={{ mt: 1 }}>
                  {observation.verdict_reason}
                </Typography>
              )}
              {observation?.recommendation && (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  <strong>What to do:</strong> {observation.recommendation}
                </Typography>
              )}
              {observation?.observation_period_end && (
                <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1.5 }}>
                  Through{' '}
                  {format(new Date(observation.observation_period_end), 'MMM d, yyyy')}
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card variant="outlined" sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Observed vs baseline
              </Typography>
              <Typography variant="body2">
                Util / 1k:{' '}
                <strong>
                  {metrics.utilization_per_1k != null
                    ? Number(metrics.utilization_per_1k).toFixed(1)
                    : '—'}
                </strong>
              </Typography>
              <Typography variant="body2">
                Cost PMPM:{' '}
                <strong>
                  {metrics.cost_pmpm != null || metrics.cost_per_member != null
                    ? `$${Number(metrics.cost_pmpm ?? metrics.cost_per_member).toFixed(2)}`
                    : '—'}
                </strong>
              </Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                Cost change:{' '}
                <strong>
                  {vsBaseline.cost_change_pct != null
                    ? `${Number(vsBaseline.cost_change_pct).toFixed(1)}%`
                    : metrics.observed_percent_change != null
                      ? `${Number(metrics.observed_percent_change).toFixed(1)}%`
                      : '—'}
                </strong>
              </Typography>
              <Typography variant="body2">
                Claims:{' '}
                <strong>
                  {metrics.total_claims != null ? Number(metrics.total_claims).toLocaleString() : '—'}
                </strong>
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card variant="outlined" sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Predicted impact (Stage 3.5)
              </Typography>
              {predictedImpact ? (
                <>
                  <Typography variant="body2">
                    Util change:{' '}
                    <strong>
                      {predictedImpact.metrics?.utilization_change_pct != null
                        ? `${Number(predictedImpact.metrics.utilization_change_pct).toFixed(1)}%`
                        : '—'}
                    </strong>
                  </Typography>
                  <Typography variant="body2">
                    Cost PMPM change:{' '}
                    <strong>
                      {predictedImpact.metrics?.cost_change_pmpm != null
                        ? `$${Number(predictedImpact.metrics.cost_change_pmpm).toFixed(2)}`
                        : '—'}
                    </strong>
                  </Typography>
                  <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                    {predictedImpact.computed_at || predictedImpact.predicted_at
                      ? `Generated ${format(
                          new Date(predictedImpact.computed_at || predictedImpact.predicted_at),
                          'MMM d, yyyy'
                        )}`
                      : null}
                  </Typography>
                  <Button
                    size="small"
                    sx={{ mt: 1 }}
                    onClick={() => navigate('/predicted-impacts')}
                  >
                    Open predicted impacts
                  </Button>
                </>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No usable predicted impact stored for this policy.
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="subtitle2" fontWeight={700} gutterBottom>
              Guardrails
            </Typography>
            {guardrails.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                No guardrails configured.
              </Typography>
            ) : (
              <>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  {triggeredGuardrails.length > 0 ? (
                    <Chip
                      size="small"
                      color="error"
                      label={`${triggeredGuardrails.length} triggered`}
                      sx={{ mr: 1 }}
                    />
                  ) : (
                    <Chip size="small" color="success" label="None triggered" sx={{ mr: 1 }} />
                  )}
                  {guardrails.length} total
                </Typography>
                {(triggeredGuardrails.length ? triggeredGuardrails : guardrails.slice(0, 3)).map(
                  (g: any, idx: number) => (
                    <Typography key={g.id || idx} variant="body2" color="text.secondary">
                      • {g.metric_name || g.name || 'Guardrail'} ({g.threshold_type} {g.threshold_value}
                      ){g.triggered ? ' — TRIGGERED' : ''}
                    </Typography>
                  )
                )}
              </>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="subtitle2" fontWeight={700} gutterBottom>
              Recent what-if runs
            </Typography>
            {recentScenarios.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                No completed what-if scenarios for this policy yet.
              </Typography>
            ) : (
              recentScenarios.map((a) => (
                <Box
                  key={a.id}
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    py: 0.75,
                    borderBottom: '1px solid',
                    borderColor: 'divider',
                  }}
                >
                  <Typography variant="body2">
                    {a.name?.trim() || `Run ${String(a.id).slice(0, 8)}…`}
                    <Typography component="span" variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                      {a.created_at ? format(new Date(a.created_at), 'MMM d, yyyy HH:mm') : ''}
                    </Typography>
                  </Typography>
                  <Button
                    size="small"
                    onClick={() =>
                      navigate(
                        `/whatif?policy=${encodeURIComponent(policyId)}&scenario=${encodeURIComponent(a.id)}`
                      )
                    }
                  >
                    Open results
                  </Button>
                </Box>
              ))
            )}
            <Button
              size="small"
              sx={{ mt: 1 }}
              onClick={() => navigate('/whatif/scenarios')}
            >
              All what-if runs
            </Button>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}
