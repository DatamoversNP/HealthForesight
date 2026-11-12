# Lean Staging Lifecycle 2025/2026 Report

Generated: 2026-11-05T17:12:12.215186+00:00
PASS: **True**

## Verify

```json
{
  "baselines": 1,
  "predicted": 250,
  "observations": 3000,
  "obs_policies": 250,
  "claims_2025": 1260,
  "claims_2026": 3825
}
```

## Failures

_none_

## Recommendation — monthly process

1. **Monthly observation job** (registered): day-2 06:00 — create PERIODIC obs for prior month (synthetic demo path).
2. **Monthly claims top-up** (optional): mid-month tenant-wide seed only — do **not** policy-scope until CLAIMS_EXECUTABLE.
3. **Quarterly baseline refresh** of trailing FIXED/ROLLING window after authority-certified codes exist.
4. Keep remediation fail-closed: no unverified code-driven claims calc.
