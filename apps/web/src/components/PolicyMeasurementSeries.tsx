import { useEffect, useState } from 'react'
import { Alert, Box, CircularProgress, Typography } from '@mui/material'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { apiClient } from '../lib/api'

type MonthPoint = { date?: string; observed?: number; line_count?: number }

type ChartRow = {
  month: string
  baseline_allowed: number | null
  observed_allowed: number | null
  baseline_lines: number | null
}

function seriesRows(points: MonthPoint[] | undefined): Map<string, { allowed: number | null; lines: number | null }> {
  const out = new Map<string, { allowed: number | null; lines: number | null }>()
  for (const point of points || []) {
    if (!point?.date) continue
    if (point.observed == null && point.line_count == null) continue
    out.set(String(point.date).slice(0, 10), {
      allowed: point.observed == null ? null : Number(point.observed),
      lines: point.line_count == null ? null : Number(point.line_count),
    })
  }
  return out
}

function money(value: number | null | undefined): string {
  if (value == null || Number.isNaN(Number(value))) return 'Unavailable'
  return `$${Number(value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

/**
 * Monthly allowed series are claim aggregates already reconciled to the stored
 * period totals. The frozen prediction is one number, so it is not drawn as a line.
 */
export default function PolicyMeasurementSeries({ policyId }: { policyId: string }) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [chart, setChart] = useState<ChartRow[]>([])
  const [seriesKind, setSeriesKind] = useState<'allowed' | 'lines' | 'none'>('none')
  const [baselineTotal, setBaselineTotal] = useState<number | null>(null)
  const [observedTotal, setObservedTotal] = useState<number | null>(null)
  const [predictedTotal, setPredictedTotal] = useState<number | null>(null)
  const [predictionNote, setPredictionNote] = useState<string | null>(null)
  const [verdict, setVerdict] = useState<string | null>(null)
  const [configNote, setConfigNote] = useState<string | null>(null)
  const [windowNote, setWindowNote] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const [baseline, observations, prediction, summary] = await Promise.all([
          apiClient.getBaselineForPolicy(policyId),
          apiClient.getObservations({ policy_id: policyId }),
          apiClient.getPolicyPredictedImpact(policyId),
          apiClient.getPolicyExecutionSummary(),
        ])
        if (cancelled) return
        const metrics = baseline?.baseline_metrics || {}
        const obsList = Array.isArray(observations) ? observations : []
        const observation = obsList[0]
        const obsMetrics = observation?.metrics || {}
        const baselineMap = seriesRows(metrics.time_series)
        const observedMap = seriesRows(obsMetrics.time_series)
        const months = Array.from(new Set([...baselineMap.keys(), ...observedMap.keys()])).sort()
        const rows = months.map((month) => ({
          month,
          baseline_allowed: baselineMap.get(month)?.allowed ?? null,
          observed_allowed: observedMap.get(month)?.allowed ?? null,
          baseline_lines: baselineMap.get(month)?.lines ?? null,
        }))
        const hasAllowed = rows.some((row) => row.baseline_allowed != null || row.observed_allowed != null)
        setSeriesKind(rows.length === 0 ? 'none' : hasAllowed ? 'allowed' : 'lines')
        setChart(rows)
        setBaselineTotal(metrics.total_allowed ?? null)
        const vsPredicted = observation?.comparisons?.vs_predicted || {}
        setObservedTotal(vsPredicted.observed_allowed ?? null)
        const predictedMetrics = prediction?.metrics || {}
        const baselineStart = baseline?.window_start_date
        const baselineEnd = baseline?.window_end_date
        const observedStart = observation?.observation_period_start
        const observedEnd = observation?.observation_period_end
        const monthCount = (start?: string, end?: string) => {
          if (!start || !end || start.length < 7 || end.length < 7) return null
          const months = (Number(end.slice(0, 4)) - Number(start.slice(0, 4))) * 12 + (Number(end.slice(5, 7)) - Number(start.slice(5, 7))) + 1
          return Number.isFinite(months) ? months : null
        }
        const baselineMonths = monthCount(baselineStart, baselineEnd)
        const observedMonths = monthCount(observedStart, observedEnd)
        if (baselineStart && observedStart && baselineMonths && observedMonths && baselineMonths !== observedMonths) {
          setWindowNote(
            `Baseline window ${String(baselineStart).slice(0, 10)} to ${String(baselineEnd).slice(0, 10)} (${baselineMonths} months). `
            + `Observation window ${String(observedStart).slice(0, 10)} to ${String(observedEnd).slice(0, 10)} (${observedMonths} months). `
            + 'These period totals cover different lengths. The frozen prediction is the exposure-scaled comparison.'
          )
        } else {
          setWindowNote(null)
        }
        setPredictedTotal(predictedMetrics.predicted_allowed ?? null)
        setPredictionNote(
          predictedMetrics.predicted_allowed == null
            ? null
            : 'The frozen prediction is one exposure-scaled total. No monthly prediction series was calculated, so it is not drawn as a line.'
        )
        setVerdict(observation?.verdict_status ? `${observation.verdict_status}: ${observation.verdict_reason || ''}` : null)
        const row = (summary?.policies || []).find((item: { policy_id?: string }) => item.policy_id === policyId)
        if (row?.configuration_state === 'AWAITING_CONFIGURATION' && row.required_parameter) {
          const engine = row.parameter_engine_implemented
            ? 'The quantity-limit engine can run after a client supplies this value. No value has been entered.'
            : 'Saving a number would not execute this policy. The mechanism engine for this parameter is not implemented.'
          setConfigNote(`Awaiting configuration: ${row.required_parameter}. ${engine} ${row.result_label || ''}`)
        } else if (row?.configuration_state === 'REVIEW_ONLY') {
          setConfigNote(row.result_label || 'Review required. This is not a clinical outcome.')
        } else if (row?.configuration_state === 'BLOCKED') {
          setConfigNote(row.result_label || row.blocked_reason || 'Blocked')
        } else if (row?.result_label) {
          setConfigNote(row.result_label)
        } else {
          setConfigNote(null)
        }
      } catch (err: any) {
        if (!cancelled) setError(err?.detail || err?.message || 'Measurement series could not be loaded')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void load()
    return () => {
      cancelled = true
    }
  }, [policyId])

  if (loading) return <CircularProgress size={24} />
  if (error) return <Alert severity="error">{error}</Alert>

  return (
    <Box>
      {configNote && <Alert severity="info" sx={{ mb: 2 }}>{configNote}</Alert>}
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        Baseline total {money(baselineTotal)}. Frozen prediction {money(predictedTotal)}. Observed allowed {money(observedTotal)}.
      </Typography>
      {windowNote && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {windowNote}
        </Typography>
      )}
      {verdict && (
        <Typography variant="body2" sx={{ mb: 1 }}>
          Verdict: {verdict}
        </Typography>
      )}
      {predictionNote && (
        <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
          {predictionNote}
        </Typography>
      )}
      {chart.length === 0 ? (
        <Typography color="text.secondary">
          No monthly claim series is stored for this policy. A chart line is not shown.
        </Typography>
      ) : (
        <Box sx={{ width: '100%', height: 280 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chart}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} interval={Math.max(0, Math.floor((chart.length - 1) / 8))} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip formatter={(value: number, name: string) => (String(name).includes('lines') ? Number(value).toLocaleString() : money(value))} />
              <Legend />
              {seriesKind === 'allowed' && (
                <Line type="monotone" dataKey="baseline_allowed" name="Baseline allowed" stroke="#15803d" strokeWidth={2} connectNulls={false} dot={false} />
              )}
              {seriesKind === 'allowed' && (
                <Line type="monotone" dataKey="observed_allowed" name="Observed allowed" stroke="#3B2F8F" strokeWidth={2} connectNulls={false} dot={false} />
              )}
              {seriesKind === 'lines' && (
                <Line type="monotone" dataKey="baseline_lines" name="Baseline claim lines" stroke="#15803d" strokeWidth={2} connectNulls={false} dot={false} />
              )}
            </LineChart>
          </ResponsiveContainer>
        </Box>
      )}
    </Box>
  )
}
