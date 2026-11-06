/**
 * Gate A labels. Mirrors packages/common/.../measurement_integrity.py.
 * A legacy number is not enrolled utilization or enrolled PMPM unless the
 * payload says denominator_basis ENROLLMENT and enrolled_rate_status MEASURED.
 */

export type RateMetrics = {
  denominator_basis?: string | null
  enrolled_rate_status?: string | null
  display_labels?: {
    utilization?: string
    cost?: string
    annualized?: string
  } | null
} | null | undefined

export function isEnrolledRate(metrics: RateMetrics): boolean {
  return metrics?.denominator_basis === 'ENROLLMENT' && metrics?.enrolled_rate_status === 'MEASURED'
}

export function utilizationLabel(metrics: RateMetrics): string {
  if (metrics?.display_labels?.utilization) return metrics.display_labels.utilization
  if (isEnrolledRate(metrics)) return 'Utilization per 1,000 eligible member-months'
  return 'Claim lines per 1,000 claimants (not enrolled utilization)'
}

export function costLabel(metrics: RateMetrics): string {
  if (metrics?.display_labels?.cost) return metrics.display_labels.cost
  if (isEnrolledRate(metrics)) return 'Dollars per enrolled member-month'
  return 'Dollars per claimant-month (not enrolled PMPM)'
}

export function annualizationLabel(metrics: RateMetrics): string {
  if (metrics?.display_labels?.annualized) return metrics.display_labels.annualized
  if (isEnrolledRate(metrics)) return 'Annualized enrolled-population total'
  return 'Claimant-based annualized total. Not enrolled-population spend.'
}

export function confidenceText(score: number | null | undefined): string {
  if (score == null || Number.isNaN(Number(score))) return 'Unavailable'
  return `${Number(score).toFixed(0)}%`
}

export function formatOptionalPercent(value: number | null | undefined): string {
  if (value == null || Number.isNaN(Number(value))) return '—'
  return `${Number(value).toFixed(1)}%`
}
