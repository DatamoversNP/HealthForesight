export type RollupMetrics = {
  avg_utilization_change_pct?: number | null
  avg_utilization_change_status?: string | null
  avg_utilization_observation_count?: number | null
  total_cost_impact?: number | null
  total_cost_impact_annualized?: number | null
  total_cost_impact_status?: string | null
  total_cost_impact_unit?: string | null
  total_cost_impact_display_unit?: string | null
  total_cost_impact_label?: string | null
  total_cost_observation_count?: number | null
  cost_denominator_basis?: string | null
  portfolio_financials_available?: boolean
} | null | undefined

export type RollupPresentation = {
  valueText: string
  unit?: string
  subtitle: string
  trend?: 'up' | 'down'
  color?: 'success' | 'warning' | 'error'
}

function measuredCost(metrics: RollupMetrics): boolean {
  return (
    metrics?.total_cost_impact_status === 'MEASURED'
    && metrics.total_cost_impact != null
    && Number.isFinite(Number(metrics.total_cost_impact))
  )
}

export function costRollupPresentation(metrics: RollupMetrics): RollupPresentation {
  const unavailable: RollupPresentation = {
    valueText: 'Unavailable',
    subtitle: 'Cost rollup unavailable. Missing or mixed denominators are not shown as zero.',
  }
  if (!measuredCost(metrics)) return unavailable
  const unit = metrics?.total_cost_impact_display_unit || ''
  const enrolled = metrics?.cost_denominator_basis === 'ENROLLMENT'
  const claimant = metrics?.cost_denominator_basis === 'CLAIMANT_MONTHS'
  // Reject ambiguous ΔPMPM labels that claim enrollment without an enrollment basis.
  if (unit.includes('ΔPMPM') && !enrolled) return unavailable
  if (!unit && !claimant && !enrolled) return unavailable
  const value = Number(metrics?.total_cost_impact)
  const count = metrics?.total_cost_observation_count ?? 0
  const periodAbs = unit === 'period $' || metrics?.total_cost_impact_unit === 'claimant_period_dollar_sum'
  const displayUnit = unit || (claimant ? (periodAbs ? 'period $' : 'claimant-month $') : enrolled ? '$ / enrolled member-month' : '')
  const annualized = metrics?.total_cost_impact_annualized
  const annualizedBit =
    annualized != null && Number.isFinite(Number(annualized))
      ? ` ≈ $${Number(annualized).toLocaleString(undefined, { maximumFractionDigits: 0 })} annualized (×12).`
      : ''
  const subtitle = enrolled
    ? `${count} policies. Per enrolled member-month. Not a portfolio savings total.`
    : periodAbs
      ? `${count} policies. Period $ = Σ(Δ rate × member-months). Not attributed savings.${annualizedBit}`
      : `${count} policies. Observed vs baseline allowed $ (claimant-month). Not attributed policy savings.`
  const compact =
    Math.abs(value) >= 1_000_000
      ? value.toLocaleString(undefined, { maximumFractionDigits: 1, notation: 'compact' as Intl.NumberFormatOptions['notation'] })
      : value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  return {
    valueText: compact,
    unit: displayUnit,
    subtitle,
    trend: value < 0 ? 'down' : value > 0 ? 'up' : undefined,
    color: value < 0 ? 'success' : value > 0 ? 'warning' : undefined,
  }
}

export function utilizationRollupPresentation(metrics: RollupMetrics): RollupPresentation {
  const value = metrics?.avg_utilization_change_pct
  const measured = (
    metrics?.avg_utilization_change_status === 'MEASURED'
    && value != null
    && Number.isFinite(Number(value))
  )
  if (!measured) {
    return {
      valueText: 'Unavailable',
      subtitle: 'Unavailable. Missing utilization changes are excluded, not counted as zero.',
    }
  }
  const numeric = Number(value)
  const count = metrics?.avg_utilization_observation_count ?? 0
  const direction = numeric < 0 ? 'Reduction' : numeric > 0 ? 'Increase' : 'No change'
  return {
    valueText: Math.abs(numeric).toFixed(1),
    unit: '%',
    subtitle: `${direction} vs. pre-policy baseline. ${count} measured observation(s).`,
    trend: numeric < 0 ? 'down' : numeric > 0 ? 'up' : undefined,
    color: numeric < 0 ? 'success' : numeric > 0 ? 'error' : undefined,
  }
}
