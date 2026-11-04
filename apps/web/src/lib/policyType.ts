/**
 * Catalog / builder policy types.
 * Preserves original 16 for compatibility, then enterprise domain extensions.
 * Flat type remains a compatibility surface — multi-mechanism tagging is a later evolution.
 */
export const CATALOG_POLICY_TYPES = [
  // Original compatibility set
  'PRIOR_AUTH',
  'SITE_OF_CARE',
  'COVERAGE',
  'STEP_THERAPY',
  'BENEFIT',
  'CLINICAL_CRITERIA',
  'DURATION_FREQUENCY_LIMIT',
  'QUANTITY_LIMIT',
  'NETWORK_RESTRICTION',
  'PROVIDER_ELIGIBILITY',
  'REFERRAL_REQUIREMENT',
  'COST_SHARING',
  'PAYMENT_POLICY',
  'ADMINISTRATIVE_REQUIREMENT',
  'ACCESS_AVAILABILITY_RULE',
  'COMPOSITE',
  // Enterprise domain extensions
  'MEDICAL_NECESSITY',
  'UTILIZATION_MANAGEMENT',
  'DRUG_FORMULARY',
  'SPECIALTY_PHARMACY',
  'EXPERIMENTAL_INVESTIGATIONAL',
  'OUT_OF_NETWORK_COVERAGE',
  'REIMBURSEMENT_METHODOLOGY',
  'CODING_AND_BILLING',
  'CLINICAL_PATHWAY',
  'CONTINUITY_OF_CARE',
  'EPISODE_BUNDLED_PAYMENT',
  'VALUE_BASED_PAYMENT',
  'PREVENTIVE_SERVICES',
  'TELEHEALTH_VIRTUAL_CARE',
  'POST_ACUTE_CARE',
] as const

export type CatalogPolicyType = (typeof CATALOG_POLICY_TYPES)[number]

/** Canonicalize policy_type for dedupe / filter matching (spaces, case, slashes). */
export function normalizePolicyTypeKey(type: string | null | undefined): string {
  return String(type || '')
    .trim()
    .toUpperCase()
    .replace(/[/]+/g, ' ')
    .replace(/[\s-]+/g, '_')
    .replace(/_+/g, '_')
    .replace(/^_|_$/g, '')
}

/** Display label: PRIOR_AUTH → PRIOR AUTH */
export function formatPolicyTypeLabel(type: string | null | undefined): string {
  const key = normalizePolicyTypeKey(type)
  return key ? key.replace(/_/g, ' ') : ''
}

/**
 * Unique type options from raw values. Prefers catalog codes in `preferredOrder`.
 * Collapses PRIOR_AUTH / "PRIOR AUTH" / "prior auth " into one option.
 */
export function uniquePolicyTypeOptions(
  rawTypes: Array<string | null | undefined>,
  preferredOrder: string[] = []
): string[] {
  const fromDataKeys = new Set(
    rawTypes.map((t) => normalizePolicyTypeKey(t)).filter(Boolean)
  )

  const byKey = new Map<string, string>()
  // Always surface preferred catalog types in dropdowns (even before data loads).
  for (const preferred of preferredOrder) {
    const key = normalizePolicyTypeKey(preferred)
    if (!key) continue
    byKey.set(key, preferred)
  }
  for (const raw of rawTypes) {
    const key = normalizePolicyTypeKey(raw)
    if (!key || byKey.has(key)) continue
    byKey.set(key, key)
  }

  const preferredKeys = preferredOrder.map(normalizePolicyTypeKey).filter(Boolean)
  const preferredSet = new Set(preferredKeys)
  const known = preferredOrder.filter((t) => byKey.has(normalizePolicyTypeKey(t)))
  const extras = Array.from(byKey.entries())
    .filter(([key]) => !preferredSet.has(key))
    .map(([, value]) => value)
    .sort((a, b) => formatPolicyTypeLabel(a).localeCompare(formatPolicyTypeLabel(b)))

  const seen = new Set<string>()
  const ordered: string[] = []
  for (const t of [...known, ...extras]) {
    const key = normalizePolicyTypeKey(t)
    if (!key || seen.has(key)) continue
    seen.add(key)
    ordered.push(byKey.get(key) || t)
  }
  return ordered
}

export function policyTypesMatch(
  a: string | null | undefined,
  b: string | null | undefined
): boolean {
  const ka = normalizePolicyTypeKey(a)
  const kb = normalizePolicyTypeKey(b)
  return Boolean(ka && kb && ka === kb)
}
