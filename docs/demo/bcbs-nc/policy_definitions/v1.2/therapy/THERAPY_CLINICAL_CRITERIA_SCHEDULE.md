# Outpatient Therapy Coverage and Payment — Clinical Criteria Schedule v1.2.1

**Status:** NOT APPROVED — rows are `PROPOSED_REPRESENTATIVE_NOT_APPROVED`.  
**Operative:** `false` until approval block signed.

## Non-operative lock

| Rule | Binding |
|---|---|
| May emit operative `APPROVED` / `ADVERSE_DETERMINATION_ISSUED` | **No** |
| `SYNTHETIC_SIMULATION` | Dry-run only; must not persist as member determination |
| Urgency | `DT-URGENCY` before routine incomplete-information (see decision tables) |

Linked LCD L34428 (OP Physical Therapy) is jurisdiction-relevant; indication rows still NOT_APPROVED until clinical owner signs.

Attach licensed/public guidance citations; do not invent payer approvals.  
Do **not** copy MRI lumbar clinical criteria into this schedule.

## Approval block (blank)

| Role | Name | Date | Signature |
|---|---|---|---|
| Clinical owner | | | |
| Compliance / legal | | | |
| Product owner | | | |
