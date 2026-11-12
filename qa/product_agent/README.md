# HealthForesight product QA agent

Frontend-first checks against the running staging application. The command evaluates every discovered policy through the API and the read-only database oracle, then runs authenticated browser journeys for each mechanism family and the edge cases. It does not claim one browser journey per policy.

## Run

```bash
export HF_QA_EMAIL=...
export HF_QA_PASSWORD=...
export HF_QA_WEB_URL=https://hfleanstg-web.whiteplant-64737337.eastus2.azurecontainerapps.io
export HF_QA_DV_URL=https://hfleanstg-web-datavoyager.whiteplant-64737337.eastus2.azurecontainerapps.io
export HF_QA_API_URL=https://hfleanstg-api.whiteplant-64737337.eastus2.azurecontainerapps.io/api/v1
python -m qa.product_agent
```

The process reads the staging database URL from `HF_QA_DATABASE_URL` or from Key Vault `hfleanstgkv` / `lean-staging-database-url`. It refuses any host other than `hfleanstg-pg.postgres.database.azure.com`. Credentials and the database URL are not written to the report.

Offline oracle regression, with no network:

```bash
python -m pytest -c pyproject.toml --rootdir=. qa/product_agent/test_oracle_arithmetic.py
```

Exit status is 1 when a data contract, calculation, dashboard, or browser journey fails. Legitimate blocked and review-only policies are recorded and do not by themselves fail the run.

Outputs:

- `docs/production/releases/HEALTHFORESIGHT_AUTONOMOUS_PRODUCT_QA_REPORT.md`
- `docs/production/releases/HEALTHFORESIGHT_QA_DEFECTS.csv`
- `docs/production/releases/HEALTHFORESIGHT_QA_POLICY_MATRIX.csv`
- `docs/production/releases/HEALTHFORESIGHT_QA_RESULTS.json`
- `docs/production/releases/HEALTHFORESIGHT_QA_REPORT.html`
- `docs/production/releases/qa_evidence/`
