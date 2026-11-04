# Engagement-Safe Policy Analytics — Required Report

Generated: 2026-11-04T13:23:06.581334+00:00

## Architecture
- Bulk HTTP lifecycle runner: **RETIRED**
- Preflight → pathway classification → isolated job runner / Celery
- Directional Representative Payer standard (not BCBS NC exact fidelity)

## Required counts
- Policies preflighted: **289**
- Nonzero eligible claim cohorts: **52**
- Mechanism inputs sufficient: **246**
- Eligible for empirical execution: **9**
- Validated synthetic execution path: **179**
- Provenance-only: **53**
- Blocked by missing evidence: **48**
- Successful worker jobs: **289**
- Timed-out / cancelled: **0**
- Duplicates prevented: **289**
- Reproducible persisted results: **289**
- Directional accuracy PASS: **267**

## Lane C — Platform
- API health: `OK_200`

## Dec4 MRI / MPPR / SOS
- **MRI** `d403f101-08dd-45c9-ab83-d42e37c62018` pathway=REPRESENTATIVE_SYNTHETIC_FIXTURE job=SYNTHETIC_VERIFY_ONLY frozen=True rewrite=False
- **MPPR** `d0eeb370-df14-4478-8755-dad6c3a35a47` pathway=REPRESENTATIVE_SYNTHETIC_FIXTURE job=SYNTHETIC_VERIFY_ONLY frozen=True rewrite=False
- **SOS** `d7441dd9-3bfe-405e-ae6c-0377204bbb7e` pathway=REPRESENTATIVE_SYNTHETIC_FIXTURE job=SYNTHETIC_VERIFY_ONLY frozen=True rewrite=False

## Blocked policy IDs
- `c922a9bd-0292-4df1-9bdd-f4bda3709fbf`
- `ce65ce76-ea5b-4a7d-8260-84c11ae54bb2`
- `38525bee-e8b4-483c-85e1-5abdc2747be9`
- `d3b25dd6-57d6-49e9-8e1f-5f45438caa06`
- `d1e25694-719d-428b-b5b5-329abb6147c0`
- `a45b26ab-305a-485a-8e29-17735584aaff`
- `9458bc86-990a-4a2e-9cec-facbc9e3fe27`
- `3e0b2ec4-217c-4d08-914d-015e9b8961d6`
- `8de16b8c-7bbb-49ca-850a-73b8e8f81908`
- `a196ff6f-047b-4809-b83d-5df4194e4820`
- `2b1a9c48-8352-4fd5-be6f-d12c7647de7d`
- `f0fb116f-2ef1-48d3-bbe1-3d4c7b5cf7d8`
- `90592b6e-95a3-4f83-aee5-ed17ddfa1d1b`
- `db345e39-73ba-4bde-9b04-0fdac8c4a7be`
- `17415dd5-1a1a-4e82-959e-a1924cc9c121`
- `e78ce5cf-a37b-4b8a-b66e-42fb44c15651`
- `c8c59559-b4b7-4cdc-9b48-9efed253be2b`
- `7e2ac9e6-7493-40c1-8bc3-7c4fe7347fdb`
- `7e9ec991-76a0-4da9-86f0-f0a940b063e7`
- `7ccbdad3-8688-4b4b-b21a-07c4877a9956`
- `46e3ebd7-3f65-43f2-9d3e-5bdeabdddacc`
- `258dc9fb-8530-4d18-9b49-5a42f46c3469`
- `cc1327fa-c66b-46dd-9271-03fb65a5bc73`
- `dacd8143-d53b-4ef8-ad40-65be55bd55d3`
- `2c14270f-aca3-4268-8562-235dce612e9f`
- `c5c9e942-0649-46b5-82e0-20e660ead31d`
- `fc8541ac-c246-40f2-afdc-9e1d8b50180c`
- `99dca188-8edd-4293-839f-29508666780d`
- `140fc121-b6b9-4166-bf5d-e2dfe2ea69db`
- `7a41ebf4-ce99-45da-9039-49a7bb262bc9`
- `e885e4fb-d001-4bc5-aa0d-91067b3e550b`
- `d8167a61-8d8a-4b7b-b1d8-889bfe5fedfd`
- `9fb617a1-2718-47dd-995d-b4fe2a77ca3a`
- `d1bffe1f-683f-4086-a873-7d1bcf4fa059`
- `b0d2714b-8bf5-40d4-a44e-8a9912ba6740`
- `cf421497-513a-4038-adcf-d5d6b176b940`
- `f54e4310-7f4b-4d6e-a6ab-c7b748722c8d`
- `914684fd-7480-4902-89fa-e7ae006f192e`
- `2c003e47-6137-4402-bbaa-67589ef2654b`
- `ef853bdb-40fb-4e68-8013-a4f8bf8d9b2c`
- `6c9cac8c-65f6-4214-8d9d-50dcf5f98bda`
- `b5895596-41cb-4f48-9f82-72d5ac388ea2`
- `d35e2fff-659c-4988-ab30-d55498631c2a`
- `2c1ed7ac-99f1-44c4-9d38-8c0bb77b79c4`
- `5e7a1a2b-5cbd-4a65-858f-a9b4f49fa7c4`
- `d9f83c02-fd70-41fa-b2c3-c93c103582eb`
- `b815e37b-98c9-40b4-8e17-b0821566fcaf`
- `51886386-a86a-4eb3-ae8e-b7f807464c96`

## Directional FAIL policy IDs
- `c922a9bd-0292-4df1-9bdd-f4bda3709fbf`
- `d3b25dd6-57d6-49e9-8e1f-5f45438caa06`
- `a196ff6f-047b-4809-b83d-5df4194e4820`
- `db345e39-73ba-4bde-9b04-0fdac8c4a7be`
- `e78ce5cf-a37b-4b8a-b66e-42fb44c15651`
- `c8c59559-b4b7-4cdc-9b48-9efed253be2b`
- `46e3ebd7-3f65-43f2-9d3e-5bdeabdddacc`
- `258dc9fb-8530-4d18-9b49-5a42f46c3469`
- `cc1327fa-c66b-46dd-9271-03fb65a5bc73`
- `dacd8143-d53b-4ef8-ad40-65be55bd55d3`
- `c5c9e942-0649-46b5-82e0-20e660ead31d`
- `99dca188-8edd-4293-839f-29508666780d`
- `140fc121-b6b9-4166-bf5d-e2dfe2ea69db`
- `7a41ebf4-ce99-45da-9039-49a7bb262bc9`
- `e885e4fb-d001-4bc5-aa0d-91067b3e550b`
- `cf421497-513a-4038-adcf-d5d6b176b940`
- `914684fd-7480-4902-89fa-e7ae006f192e`
- `b5895596-41cb-4f48-9f82-72d5ac388ea2`
- `d35e2fff-659c-4988-ab30-d55498631c2a`
- `2c1ed7ac-99f1-44c4-9d38-8c0bb77b79c4`
- `5e7a1a2b-5cbd-4a65-858f-a9b4f49fa7c4`
- `d9f83c02-fd70-41fa-b2c3-c93c103582eb`

