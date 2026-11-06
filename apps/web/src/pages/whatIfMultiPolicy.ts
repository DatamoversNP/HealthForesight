/**
 * Combine single-policy what-if results.
 * A missing allowed, paid, or utilization level stays unavailable.
 * A numeric zero is a real value and is included in the sum.
 */

export interface WhatIfPolicyRef {
  id: string
  name: string
}

export function presentNumber(value: unknown): number | null {
  if (value === null || value === undefined || value === '') return null
  if (typeof value === 'boolean') return null
  const n = typeof value === 'number' ? value : Number(value)
  return Number.isFinite(n) ? n : null
}

export function sumAllOrUnavailable(values: Array<number | null>): number | null {
  if (values.some((value) => value === null)) return null
  return values.reduce((sum, value) => sum + (value as number), 0)
}

function relativePercent(change: number | null, baseline: number | null): number | null {
  if (change === null || baseline === null || baseline <= 0) return null
  return (change / baseline) * 100
}

export function combineMultiPolicyResults(
  policyResults: Array<{ policy: WhatIfPolicyRef; scenario: any }>,
  scenarioName: string,
): any {
  if (policyResults.length === 0) {
    throw new Error('No policy results to combine')
  }

  const baselineMetrics = { ...policyResults[0].scenario.baseline_metrics }
  const baselineAllowed = presentNumber(baselineMetrics.allowed_pmpm)
  const baselinePaid = presentNumber(baselineMetrics.paid_pmpm)
  const baselineUtilization = presentNumber(baselineMetrics.utilization_per_1k)
  const baselineClaims = presentNumber(baselineMetrics.claim_count)
  const baselineMemberMonths = presentNumber(baselineMetrics.member_months)

  const allowedImpacts: Array<number | null> = []
  const paidImpacts: Array<number | null> = []
  const utilizationImpacts: Array<number | null> = []
  const utilizationPercents: Array<number | null> = []
  const claimCounts: Array<number | null> = []
  const confidenceScores: Array<number | null> = []

  for (const { scenario } of policyResults) {
    const impact = scenario.impact_metrics || {}
    const projected = scenario.projected_metrics || {}
    allowedImpacts.push(presentNumber(impact.allowed_pmpm))
    paidImpacts.push(presentNumber(impact.paid_pmpm))
    utilizationImpacts.push(presentNumber(impact.utilization_per_1k))
    utilizationPercents.push(presentNumber(impact.percent_changes?.utilization_per_1k))
    claimCounts.push(presentNumber(projected.claim_count))
    confidenceScores.push(presentNumber(scenario.confidence_score))
  }

  const totalAllowedChange = sumAllOrUnavailable(allowedImpacts)
  const totalPaidImpact = sumAllOrUnavailable(paidImpacts)
  const totalUtilizationChange = sumAllOrUnavailable(utilizationImpacts)
  const totalUtilizationPercent = sumAllOrUnavailable(utilizationPercents)
  const totalClaimCount = sumAllOrUnavailable(claimCounts)
  const totalConfidence = sumAllOrUnavailable(confidenceScores)

  const totalPaidAccumulator =
    baselinePaid === null || totalPaidImpact === null ? null : baselinePaid + totalPaidImpact
  const paidChange =
    totalPaidAccumulator === null || totalAllowedChange === null
      ? null
      : totalPaidAccumulator - totalAllowedChange

  const projectedMetrics = {
    utilization_per_1k:
      baselineUtilization === null || totalUtilizationChange === null
        ? null
        : baselineUtilization + totalUtilizationChange,
    allowed_pmpm:
      baselineAllowed === null || totalAllowedChange === null
        ? null
        : baselineAllowed + totalAllowedChange,
    paid_pmpm:
      baselinePaid === null || paidChange === null ? null : baselinePaid + paidChange,
    claim_count: totalClaimCount === null ? baselineClaims : totalClaimCount,
    member_months: baselineMemberMonths,
  }

  const impactMetrics = {
    utilization_per_1k: totalUtilizationChange,
    allowed_pmpm: totalAllowedChange,
    paid_pmpm: paidChange,
    claim_count:
      totalClaimCount === null || baselineClaims === null ? null : totalClaimCount - baselineClaims,
    member_months: baselineMemberMonths,
    percent_changes: {
      utilization_per_1k:
        totalUtilizationPercent === null ? null : totalUtilizationPercent / policyResults.length,
      allowed_pmpm: relativePercent(totalAllowedChange, baselineAllowed),
      paid_pmpm: relativePercent(paidChange, baselinePaid),
    },
  }

  return {
    scenario_id: `multi-policy-${Date.now()}`,
    scenario_name: scenarioName,
    baseline_metrics: {
      ...baselineMetrics,
      allowed_pmpm: baselineAllowed,
      paid_pmpm: baselinePaid,
      utilization_per_1k: baselineUtilization,
      member_months: baselineMemberMonths,
    },
    projected_metrics: projectedMetrics,
    impact_metrics: impactMetrics,
    confidence_intervals: policyResults[0].scenario.confidence_intervals || {},
    confidence_score:
      totalConfidence === null ? null : totalConfidence / policyResults.length,
    sensitivity_analysis: {
      policies_count: policyResults.length,
      individual_impacts: policyResults.map(({ policy, scenario }) => ({
        policy_id: policy.id,
        policy_name: policy.name,
        cost_impact: presentNumber(scenario.impact_metrics?.allowed_pmpm),
        utilization_impact: presentNumber(scenario.impact_metrics?.utilization_per_1k),
      })),
    },
  }
}
