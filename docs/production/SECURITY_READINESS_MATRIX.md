# Security Readiness Matrix

**ADR-005:** Both SaaS (HF subscription) and customer-subscription deploy are in scope; identity/KV/network controls must be validated **per mode**.

| Control | Implemented | Tested | Inherited Azure | Outstanding |
|---------|-------------|--------|-----------------|-------------|
| Dual-mode tenancy (ADR-005) | Documented + IaC `deployment_mode` | — | — | Entra/KV profiles per mode |
| TLS to PG | Yes (sslmode) | Partial | Flexible Server | Private Link |
| JWT auth | Yes | Demo | — | Entra enterprise federation (SaaS + customer) |
| Key Vault scripts | Partial | — | — | MI everywhere, no secrets in env long-term |
| Tenant isolation in cache keys | Contract defined | Unit | — | Enforce in all caches |
| PHI-safe logging | Partial | — | — | Redaction policy + review |
| Private networking | IaC module | No | — | Provision + Private DNS |
| Front Door + WAF | Not deployed | No | — | Wave 2 |
| Container image scan | CI partial | — | Defender optional | Gate on Critical |
| Encryption at rest | Azure defaults | — | Storage/PG | CMK decision |
| Audit evidence | Partial | — | — | Job/result access audit |
| HIPAA program | **Not asserted** | — | BAA with Microsoft ≠ product compliance | Customer BAA + controls |

**Do not claim HIPAA compliance from Azure SKUs alone.**
