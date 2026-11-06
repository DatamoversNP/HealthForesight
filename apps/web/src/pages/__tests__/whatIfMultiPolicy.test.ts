import { describe, expect, it } from 'vitest'
import { combineMultiPolicyResults } from '../whatIfMultiPolicy'

function scenario(partial: {
  allowed?: number | null
  paid?: number | null
  utilization?: number | null
  confidence?: number | null
}) {
  return {
    baseline_metrics: {
      utilization_per_1k: 100,
      allowed_pmpm: 80,
      paid_pmpm: 60,
      claim_count: 10,
      member_months: 120,
    },
    projected_metrics: { claim_count: 10, member_months: 120 },
    impact_metrics: {
      allowed_pmpm: partial.allowed,
      paid_pmpm: partial.paid ?? 0,
      utilization_per_1k: partial.utilization ?? 0,
      percent_changes: { utilization_per_1k: 0, allowed_pmpm: 0, paid_pmpm: 0 },
    },
    confidence_score: partial.confidence,
    confidence_intervals: {},
  }
}

describe('combineMultiPolicyResults missing allowed_pmpm', () => {
  it('keeps a missing allowed impact unavailable instead of zero', () => {
    const combined = combineMultiPolicyResults(
      [
        { policy: { id: 'a', name: 'A' }, scenario: scenario({ allowed: null }) },
        { policy: { id: 'b', name: 'B' }, scenario: scenario({ allowed: 10 }) },
      ],
      'missing allowed',
    )

    expect(combined.impact_metrics.allowed_pmpm).toBeNull()
    expect(combined.projected_metrics.allowed_pmpm).toBeNull()
    expect(combined.impact_metrics.percent_changes.allowed_pmpm).toBeNull()
    expect(combined.sensitivity_analysis.individual_impacts[0].cost_impact).toBeNull()
    expect(combined.sensitivity_analysis.individual_impacts[1].cost_impact).toBe(10)
  })

  it('keeps an explicit zero and sums the other allowed impact', () => {
    const combined = combineMultiPolicyResults(
      [
        { policy: { id: 'a', name: 'A' }, scenario: scenario({ allowed: 0 }) },
        { policy: { id: 'b', name: 'B' }, scenario: scenario({ allowed: -5 }) },
      ],
      'zero allowed',
    )

    expect(combined.impact_metrics.allowed_pmpm).toBe(-5)
    expect(combined.projected_metrics.allowed_pmpm).toBe(75)
    expect(combined.impact_metrics.percent_changes.allowed_pmpm).toBeCloseTo(-6.25)
  })

  it('does not turn a missing confidence score into zero', () => {
    const combined = combineMultiPolicyResults(
      [
        { policy: { id: 'a', name: 'A' }, scenario: scenario({ allowed: 1, confidence: null }) },
        { policy: { id: 'b', name: 'B' }, scenario: scenario({ allowed: 1, confidence: 80 }) },
      ],
      'missing confidence',
    )
    expect(combined.confidence_score).toBeNull()
  })
})
