# Nine Mock Policies — Financial Reconciliation (CY2025)

**Environment:** Azure lean staging (`hfleanstg`) only  
**Window:** 2025-01-01 … 2025-12-31  
**Mode:** Read-only. Existing FIXED baselines and canonical rows were not changed.  
**Machine evidence:** `NINE_POLICY_AUDIT_RESULTS.json`

## 1. What the stored “selected claims” count is

| Question | Answer |
|---|---|
| Grain | **Claim lines** (`claims_lines` rows), not claim headers |
| Numerators | `SUM(allowed_amount)`, `SUM(paid_amount)`, `COUNT(*)` on filtered lines |
| Filter | Configured procedure codes **AND** `service_category` tags from policy scope/levers |
| Source mix | **Combined** 500K longitudinal + 5K nine-policy book (no `preferred_source_system` filter) |

MPPR and PTP are multi-line claims (≈2 lines per header). Other policies are essentially 1 line per header in the selected set.

## 2. Denominator actually used

Every stored baseline used the **same** member-month total:

| Denominator | Value |
|---|---:|
| Script tenant-wide enrollment MM (stored) | **5,554,299.27** |
| Product enrollment-month formula (reference) | 5,374,450.41 |
| Distinct enrolled members overlapping CY2025 | 505,000 (500K + 5K) |

Formula used by the staging baseline script:

```
allowed_pmpm_target = SUM(selected line allowed_amount) / tenant_wide_enrollment_member_months
```

That is **book-level service allowed PMPM** (policy services ÷ whole enrolled book).  
It is **not** PMPM among only members who used the service, and not an MRI-eligible subpopulation PMPM from the lifecycle fixture.

## 3. Stored vs independent recomputation

All nine numerators and book-level PMPMs **reproduce exactly** (delta claims = 0, delta allowed = 0).

| Policy | Lines | Headers | Members | Total allowed | Avg $/line | Stored PMPM | Indep. book PMPM | Claimant-enroll PMPM |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| MRI Prior Auth | 14,396 | 14,396 | 9,411 | $13,747,869.50 | $954.98 | $2.4752 | $2.4752 | $138.39 |
| NCD 220.2 | 10,181 | 10,181 | 6,359 | $9,565,560.52 | $939.55 | $1.7222 | $1.7222 | $136.82 |
| LCD L34425 | 7,212 | 7,212 | 4,773 | $5,139,412.54 | $712.62 | $0.9253 | $0.9253 | $101.59 |
| Infusion SOC | 7,091 | 7,091 | 4,779 | $29,069,581.39 | $4,099.50 | $5.2337 | $5.2337 | $573.35 |
| Therapy | 9,782 | 9,782 | 6,037 | $2,281,618.20 | $233.25 | $0.4108 | $0.4108 | $34.74 |
| MUE | 6,467 | 6,467 | 4,576 | $2,009,833.24 | $310.78 | $0.3619 | $0.3619 | $41.42 |
| PTP | 14,720 | 7,360 | 4,847 | $13,578,791.19 | $922.47 | $2.4447 | $2.4447 | $263.51 |
| Imaging SOS | 11,255 | 11,255 | 6,710 | $13,051,195.57 | $1,159.59 | $2.3497 | $2.3497 | $177.19 |
| MPPR | 22,580 | 11,290 | 8,175 | $22,397,807.79 | $991.93 | $4.0325 | $4.0325 | $256.83 |

Identity check:

```
Allowed PMPM = Selected allowed / 5,554,299.27
```

holds for every policy within $0.01.

## 4. Why PMPMs look “low”

Example — MRI:

- 14,396 lines × ~$955 ≈ $13.7M allowed  
- ÷ 5.55M book member-months ≈ **$2.48 PMPM**  
- Annualized line rate ≈ \(14396 / 5554299 × 12 × 1000 ≈ 31\) per 1,000 member-years  

The MRI lifecycle illustrative fixture used **$2.40** allowed PMPM on a similar book-style exposure. The stored result is in that same magnitude. Low PMPM here is expected for a narrow imaging slice of a ~505K commercial synthetic book — not evidence of underpriced claims.

If the denominator is restricted to enrollment months of members who actually had a selected claim, MRI PMPM rises to **~$138**. That is a different metric (treated-claimant intensity), not a correction of the stored arithmetic.

## 5. Source population and exclusions

CY2025 operational claims:

| Source | Lines | Allowed |
|---|---:|---:|
| SYNTHETIC_LONGITUDINAL_V1 (500K) | 985,102 | $449.9M |
| SYNTHETIC_NINE_POLICY_5K_V1 | 28,835 | $30.4M |
| Combined | 1,013,937 | $480.3M |

Every policy’s selected set is **COMBINED**.

Service-category AND codeset removes same-code lines tagged to another mechanism (e.g. CPT 72148 in `sos` is excluded from `mri`). That is intentional synthetic partitioning, not a voids/adjustments issue. No negative or zero allowed amounts were found in CY2025 selected lines.

## 6. Reconciliation conclusion

| Check | Result |
|---|---|
| Numerators match stored baselines | **Yes (9/9)** |
| Book PMPM formula reproducible | **Yes (9/9)** |
| Grain established | Claim lines |
| Denominator known | Tenant-wide enrollment MM ≈ 5.55M |
| Product calculation arithmetic defect | **Not found** for the formula that was actually stored |
| Semantic risk | Labeling book-level PMPM as “eligible-cohort PMPM” would be wrong |

No baseline rows were overwritten during this review.
