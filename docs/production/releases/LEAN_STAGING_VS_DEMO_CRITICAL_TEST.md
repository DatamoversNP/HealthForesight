# Lean staging vs demo — critical systems / integration / performance test

**Generated:** 2026-11-05T12:46:24.268309+00:00
**Verdict:** **PASS_WITH_CRITICAL_GAPS** (0 critical, 1 high)

## URLs
- Demo web: `https://healthforesight-web.azurewebsites.net`
- Demo API: `https://healthforesight-api.azurewebsites.net/api/v1`
- Staging web: `https://hfleanstg-web.whiteplant-64737337.eastus2.azurecontainerapps.io`
- Staging API: `https://hfleanstg-api.whiteplant-64737337.eastus2.azurecontainerapps.io/api/v1`

## Ruthless findings
- **HIGH** [integration] Staging policy catalog far thinner than demo (9 vs 289)
- **MEDIUM** [integration] Both envs fail monitoring_policies (route mismatch possible): demo=422 stg=422
- **MEDIUM** [integration] Both envs fail verdicts (route mismatch possible): demo=422 stg=422
- **INFO** [architecture] Staging is alembic 014 + SB Standard + synthetic seed; demo is frozen 012 App Service. Staging must not claim HA/Premium parity.

## Systems

| Check | Demo | Staging |
|---|---|---|
| api_docs | PASS 0.729s | PASS 0.614s |
| api_health | PASS 0.718s | PASS 0.679s |
| api_ready | PASS 0.775s | PASS 0.722s |
| login | PASS 1.045s | PASS 1.295s |
| web_root | PASS 1.339s | PASS 0.669s |

## Integration

| Check | Demo | Staging |
|---|---|---|
| executive | PASS http=200 | PASS http=200 |
| monitoring_policies | FAIL http=422 | FAIL http=422 |
| mri_policy_get | PASS http=200 | PASS http=200 |
| observations_latest | PASS http=200 | PASS http=200 |
| policies_list | PASS http=200 | PASS http=200 |
| verdicts | FAIL http=422 | FAIL http=422 |

## Performance (p50 / p95 seconds)

| Path | Demo p50/p95 | Staging p50/p95 |
|---|---|---|
| `/health` | 0.995/1.046 | 0.633/0.773 |
| `/observations?latest_only=true` | 1.957/1.962 | 0.867/0.869 |
| `/policies` | 1.948/2.042 | 0.877/0.882 |
| `/policies/d403f101-08dd-45c9-ab83-d42e37c62018` | 0.965/0.975 | 0.628/0.631 |

## Bottom line (post-elevation 2026-11-05)

- **Cold-start gap closed:** staging web now ~**0.6–0.8s** (was ~27s); often **faster** than demo web.  
- **Dec4-nine room path:** 9 policies, 9 predicted, 9 latest observations, login/executive/MRI GET PASS.  
- **Remaining HIGH:** catalog **9 vs 289** — by design for Dec4 focus, not a full catalog clone.  
- **Cutover:** staging is **rehearsal-ready** for the nine-policy demo; official primary URL flip is owner-gated (`ENV_ROLE_FLIP_STAGING_DEMO.md`). Current demo stays frozen until cutover.
