/**
 * Mock Data for Testing
 */

export const mockAnalysis = {
  id: 'analysis-123',
  policy_id: 'policy-456',
  analysis_type: 'IMPACT_ANALYSIS',
  status: 'COMPLETED',
  created_at: '2024-01-01T00:00:00Z',
  completed_at: '2024-01-01T01:00:00Z',
}

export const mockImpactResult = {
  effect_size: -15.5,
  confidence_interval: [-20.0, -11.0],
  percent_change: -12.5,
  methodology: 'DIFFERENCE_IN_DIFFERENCES',
  confidence_score: 85,
  data_coverage: {
    claimMonths: 24,
    claimLines: 1000000,
    members: 50000,
    providers: 5000,
  },
}

export const mockTrustPanel = {
  confidence_score: {
    overall_score: 85,
    category: 'HIGH' as const,
    components: {
      method_confidence: 90,
      data_quality_score: 85,
      sample_size_score: 80,
      control_group_score: 88,
      methodology_score: 92,
    },
  },
  data_sufficiency: {
    sufficient: true,
    min_sample_size: 1000,
    actual_sample_size: 50000,
    data_window_months: 24,
    coverage_score: 0.95,
    missing_data_flags: [],
  },
  validation_checks: [
    {
      check_name: 'Pre-trends parallel',
      passed: true,
      message: 'Parallel trends assumption satisfied',
      severity: 'INFO' as const,
    },
    {
      check_name: 'Control group balanced',
      passed: true,
      message: 'Control group is well-balanced',
      severity: 'INFO' as const,
    },
    {
      check_name: 'Sample size adequate',
      passed: true,
      message: 'Sample size exceeds minimum requirement',
      severity: 'INFO' as const,
    },
  ],
  limitations: [
    'Analysis limited to 24 months of data',
    'Results may not generalize to other markets',
  ],
  methodology: {
    method: 'DIFFERENCE_IN_DIFFERENCES',
    pre_months: 6,
    post_months: 6,
    has_control_group: true,
    metric: 'utilization_per_1k',
  },
  model_version: '1.0.0',
  run_timestamp: '2024-01-01T01:00:00Z',
}

export const mockMethodChecks = {
  method_checks: {
    pre_trends: {
      parallel_trends: 'PASS' as const,
      pre_trend_treatment: 0.5,
      pre_trend_control: 0.4,
      pre_trend_difference: 0.1,
      p_value: 0.25,
      warning: undefined,
    },
    control_balance: {
      balanced: true,
      balance_score: 0.92,
      imbalanced_covariates: [],
      standardized_mean_differences: {
        age: 0.05,
        risk_score: 0.08,
        gender: 0.02,
      },
      warning: undefined,
    },
    seasonality: {
      seasonal_pattern_detected: false,
      seasonality_risk: 'LOW' as const,
      seasonal_periods: [],
      adjustment_recommended: false,
      warning: undefined,
    },
    sample_size_ok: true,
    min_sample_size: 1000,
    actual_sample_size: 50000,
    warnings: [],
  },
}

export const mockSubstitutionResults = {
  substitutions: [
    {
      code: '70551',
      code_group: 'MRI Brain',
      classification: 'SITE_OF_CARE_SHIFT' as const,
      pre_allowed: 50000,
      post_allowed: 30000,
      allowed_delta: -20000,
      allowed_pct_change: -40.0,
      pre_claim_count: 100,
      post_claim_count: 80,
      claim_count_delta: -20,
      lag_effects: {
        '30_day': { claim_count: 85, total_allowed: 35000 },
        '60_day': { claim_count: 82, total_allowed: 32000 },
        '90_day': { claim_count: 80, total_allowed: 30000 },
      },
      confidence_score: 85,
      statistical_rank: 1,
      p_value: 0.001,
    },
    {
      code: '72141',
      code_group: 'MRI Spine',
      classification: 'SERVICE_SUBSTITUTION' as const,
      pre_allowed: 40000,
      post_allowed: 45000,
      allowed_delta: 5000,
      allowed_pct_change: 12.5,
      pre_claim_count: 80,
      post_claim_count: 90,
      claim_count_delta: 10,
      confidence_score: 75,
      statistical_rank: 2,
      p_value: 0.02,
    },
  ],
  total_substitutions_detected: 2,
  top_pathways: [
    {
      from_code: '70551',
      to_code: '70450',
      to_code_group: 'CT Head',
      count: 15,
      total_delta: -50000,
      avg_confidence: 82,
    },
  ],
  warnings: [],
}

export const mockSegmentationResults = {
  archetypes: [
    {
      archetype_id: 0,
      archetype_label: 'COMPLIERS',
      provider_count: 200,
      avg_allowed_delta: -5000,
      avg_claim_count_delta: -10,
      avg_allowed_pct_change: -15.0,
      pos_shift_rate: 0.2,
      top_features: [
        { feature: 'allowed_delta', mean_value: -5000, std_value: 1000, importance: 0.9 },
        { feature: 'claim_count_delta', mean_value: -10, std_value: 5, importance: 0.8 },
      ],
      stability_score: 0.85,
    },
    {
      archetype_id: 1,
      archetype_label: 'CIRCUMVENTERS',
      provider_count: 50,
      avg_allowed_delta: 10000,
      avg_claim_count_delta: 20,
      avg_allowed_pct_change: 25.0,
      pos_shift_rate: 0.8,
      top_features: [
        { feature: 'allowed_delta', mean_value: 10000, std_value: 2000, importance: 0.95 },
        { feature: 'pos_shift_rate', mean_value: 0.8, std_value: 0.2, importance: 0.85 },
      ],
      stability_score: 0.75,
    },
  ],
  provider_assignments: [
    {
      provider_id: 'PROV-001',
      archetype_id: 0,
      archetype_label: 'COMPLIERS',
      allowed_delta: -4500,
      claim_count_delta: -8,
      avg_allowed_pct_change: -12.0,
      pos_shift: false,
      confidence_score: 88,
    },
    {
      provider_id: 'PROV-002',
      archetype_id: 1,
      archetype_label: 'CIRCUMVENTERS',
      allowed_delta: 9500,
      claim_count_delta: 18,
      avg_allowed_pct_change: 22.0,
      pos_shift: true,
      confidence_score: 82,
    },
  ],
  total_providers: 250,
  clustering_quality: {
    silhouette_score: 0.65,
    quality: 'GOOD' as const,
    recommendation: 'Clustering quality is good. Results are reliable.',
  },
  warnings: [],
}

