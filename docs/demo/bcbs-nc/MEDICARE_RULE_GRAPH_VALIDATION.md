# Medicare Rule Graph Validation

## Layers

1. **Reference library** — `policy_source_documents`  
2. **Typed links** — `policy_source_links` (`REFERENCES_NCD`, `REFERENCES_LCD`, `HAS_RELATED_ARTICLE`, `USES_CODING_EDIT`, …)  
3. **Applicability resolution** — program / state / MAC / as-of → `rule_set_id`

## Validated relationships (MRI workspace)

| From | Relationship | To | Evidence |
|---|---|---|---|
| MRI PA policy | REFERENCES_NCD | NCD220.2 | CMS MCD NCDId=177 |
| MRI PA policy | REFERENCES_LCD | L34425 | Palmetto JM includes NC |
| L34425 | HAS_RELATED_ARTICLE | A56729 | CMS article text references L34425 |
| MRI PA policy | USES_CODING_EDIT | NCCI-PTP-PAIR-70553-70551 | Demo subset (synthetic pair) |

## Rejected / negative control

| Document | Why rejected for NC MRI |
|---|---|
| L35175 | Noridian J-F, not Palmetto JM |
| A54118 | Prior unverified stub on wrong LCD chain |

## Graph rules enforced

- No keyword-only binding relationships  
- Wrong-jurisdiction LCDs excluded in NC FFS applicable-rules response  
- Articles retain supporting-document role  
- NCCI edits are coding/payment rules, not medical-necessity policies  
- MA / commercial do not auto-inherit FFS LCD chains
