#!/usr/bin/env python3
"""
Build an industry / Blues-aligned payer policy catalog for Data Voyager demos.

ACCURACY CONTRACT
-----------------
- Definitions follow common U.S. payer UM / medical-policy / pharmacy-UM practice
  (prior auth, concurrent review, site of care, step therapy, QL, bundles, etc.)
  and how Blues plans in NC typically organize programs by LOB.
- This is NOT a verbatim copy of Blue Cross NC proprietary medical policies,
  CUMG text, formulary files, or NCD/LCD language. Claiming otherwise would be
  inaccurate. Every record is tagged illustrative_standards_aligned=true.
- Code/NDC appendices are intentionally omitted here; those belong in code-sets.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "scripts" / "demo" / "catalog" / "bcbs_nc_aligned_policy_catalog.json"

DISCLAIMER = (
    "Illustrative industry-standard program definition aligned with typical "
    "Blues / North Carolina payer UM structures. Not a verbatim Blue Cross NC "
    "medical policy, clinical guideline, or formulary row."
)

# (domain, subdomain, name, policy_type, owner_role, lobs, definition)
# policy_type must match uepi_common.models.PolicyType values.
RAW: list[tuple] = []


def add(domain, subdomain, name, ptype, owner, lobs, definition):
    RAW.append((domain, subdomain, name, ptype, owner, lobs, definition))


# ─── B. Medical PA ───────────────────────────────────────────────────────────
for name, definition in [
    ("Outpatient MRI Prior Authorization", "Requires PA for outpatient MRI to confirm medical necessity and preferred freestanding site when clinically appropriate."),
    ("Outpatient CT / CTA Prior Authorization", "Requires PA for outpatient CT/CTA studies against clinical criteria and frequency standards."),
    ("PET / PET-CT Prior Authorization", "Requires PA for PET/PET-CT, typically oncology, cardiac, or selected neurologic indications."),
    ("Nuclear Cardiology Prior Authorization", "Requires PA for SPECT/PET myocardial perfusion and related nuclear cardiology studies."),
    ("Cardiac CT Angiography Prior Authorization", "Requires PA for coronary CTA based on pre-test probability and alternative testing pathways."),
    ("Coronary Calcium Scoring Coverage Criteria", "Defines when coronary artery calcium scoring is covered vs investigational/not covered by LOB."),
    ("Low-Dose CT Lung Cancer Screening Criteria", "Aligns LDCT lung screening with USPSTF/CMS-style eligibility (age, pack-years, cessation window)."),
    ("Breast MRI Medical Necessity Criteria", "PA/criteria for breast MRI beyond screening mammography (high risk, staging, implant evaluation)."),
    ("Bone Densitometry Frequency Limits", "Limits DXA frequency to clinically accepted intervals unless high-risk exceptions apply."),
    ("Interventional Radiology Procedure Prior Authorization", "PA for selected IR procedures (e.g., embolization, ablation) against medical necessity criteria."),
]:
    add("Medical PA", "Imaging & radiology", name, "PRIOR_AUTH", "UM_LEADER", ["COMMERCIAL", "MA", "MEDICAID"], definition)

for name, definition in [
    ("Cardiac Stress Testing Prior Authorization", "PA for imaging stress tests when resting ECG or alternatives may suffice; promotes stepwise testing."),
    ("Diagnostic Cardiac Catheterization Appropriateness", "Reviews elective diagnostic cath against appropriateness criteria and noninvasive testing history."),
    ("PCI Elective Appropriateness Review", "Elective PCI reviewed for ischemia documentation and guideline-directed medical therapy trial where required."),
    ("Cardiac Implantable Device Prior Authorization", "PA for pacemaker/ICD/CRT based on indication class and electrophysiology criteria."),
    ("Structural Heart Procedure Prior Authorization", "PA for Watchman, TAVR pathway steps, and related structural interventions where plan-covered."),
    ("Peripheral Vascular Intervention Prior Authorization", "PA for peripheral endovascular interventions after conservative therapy and imaging documentation."),
    ("Cardiac Rehabilitation Authorization", "Authorizes cardiac rehab sessions within covered episode limits and qualifying diagnoses."),
    ("Insertable Cardiac Monitor Prior Authorization", "PA for ILR/ICM when syncope/AF monitoring criteria are met."),
]:
    add("Medical PA", "Cardiology", name, "PRIOR_AUTH", "UM_LEADER", ["COMMERCIAL", "MA"], definition)

for name, definition in [
    ("Elective Joint Arthroplasty Prior Authorization", "PA for elective hip/knee/shoulder arthroplasty with osteoarthritis staging, BMI, smoking, and PT trial criteria."),
    ("Spine Fusion Prior Authorization", "PA for elective lumbar/cervical fusion with imaging correlation, conservative care, and second-opinion rules where used."),
    ("Spinal Decompression Without Fusion Prior Authorization", "PA for laminectomy/discectomy pathways distinct from fusion criteria."),
    ("Vertebral Augmentation Prior Authorization", "PA for vertebroplasty/kyphoplasty limited to acute osteoporotic fracture criteria."),
    ("Orthobiologics and PRP Noncoverage", "Defines PRP/stem-cell injections as investigational/not covered unless LOB exception."),
    ("ACL Reconstruction Prior Authorization", "PA for elective ACL reconstruction with instability and rehab documentation."),
    ("Bunion and Forefoot Elective Surgery Prior Authorization", "PA for elective forefoot surgery after conservative care."),
    ("Bone Growth Stimulator Prior Authorization", "PA for invasive/noninvasive bone growth stimulators under fracture nonunion criteria."),
    ("Custom Orthotic and Brace Prior Authorization", "PA for custom orthoses when off-the-shelf options are insufficient."),
]:
    add("Medical PA", "Orthopedics & spine", name, "PRIOR_AUTH", "UM_LEADER", ["COMMERCIAL", "MA", "MEDICAID"], definition)

for name, definition in [
    ("Epidural Steroid Injection Prior Authorization", "PA/frequency limits for ESI with radiculopathy documentation and failed conservative care."),
    ("Facet Joint Intervention Prior Authorization", "PA for facet injections/RFA with diagnostic block algorithms."),
    ("Spinal Cord Stimulator Trial and Implant Prior Authorization", "Two-step PA for SCS trial then permanent implant after psych eval and pain criteria."),
    ("Intrathecal Drug Pump Prior Authorization", "PA for IT pump trial/implant for refractory pain or spasticity indications."),
    ("Interventional Pain Regenerative Injection Noncoverage", "Noncoverage of regenerative pain injections lacking evidence standards."),
]:
    add("Medical PA", "Pain & neuromodulation", name, "PRIOR_AUTH", "UM_LEADER", ["COMMERCIAL", "MA"], definition)

for name, definition in [
    ("Bariatric Surgery Prior Authorization", "PA for bariatric procedures with BMI, comorbidity, nutritional, and behavioral criteria."),
    ("Bariatric Revisional Surgery Prior Authorization", "Stricter PA for revisional bariatric surgery (complication vs insufficient weight loss)."),
    ("Complex Hernia Repair Prior Authorization", "PA for complex/recurrent hernia with mesh and site-of-service considerations."),
    ("Breast Reduction Medical Necessity", "PA for reduction mammoplasty using symptom and resection criteria; excludes cosmetic."),
    ("Panniculectomy Medical Necessity", "PA distinguishing panniculectomy after weight loss from cosmetic abdominoplasty."),
    ("Varicose Vein Ablation Prior Authorization", "PA for endovenous ablation after conservative therapy and CEAP/ultrasound criteria."),
    ("Sinus Surgery Prior Authorization", "PA for functional endoscopic sinus surgery after medical management."),
    ("Tonsillectomy and Adenoidectomy Criteria", "Coverage criteria for T&A by indication (OSA, recurrent infection) and age."),
    ("Sleep Surgery Prior Authorization", "PA for hypoglossal nerve stim and selected OSA surgeries after PAP failure."),
    ("Cataract Surgery Second-Eye and Specialty Lens Rules", "Defines medically necessary cataract surgery vs noncovered refractive upgrades."),
    ("Eyelid Surgery Medical Necessity", "PA for blepharoplasty when visual field impairment criteria are met."),
    ("Prostate Procedure Prior Authorization", "PA for selected BPH and prostate interventions when first-line therapies fail."),
    ("Hysterectomy Route Medical Necessity", "Reviews hysterectomy indication and preferred least-invasive clinically appropriate route."),
    ("Transplant Evaluation and Listing Authorization", "Authorizes transplant center evaluation/listing within Centers of Excellence networks."),
    ("Retransplant Prior Authorization", "Separate criteria and network rules for retransplant episodes."),
]:
    add("Medical PA", "Surgery", name, "PRIOR_AUTH", "UM_LEADER", ["COMMERCIAL", "MA", "MEDICAID"], definition)

for name, definition in [
    ("Radiation Therapy Modality Prior Authorization", "PA for IMRT/SBRT/proton/brachytherapy based on diagnosis and comparative modality criteria."),
    ("Proton Beam Therapy Coverage Criteria", "Limits proton therapy to indications with accepted comparative evidence by LOB."),
    ("Medical Oncology Regimen Prior Authorization", "PA for selected high-cost infused oncology regimens on the medical benefit."),
    ("CAR-T and Cellular Therapy Prior Authorization", "PA for CAR-T/cellular therapies at designated centers with indication and REMS-aligned criteria."),
    ("Oncology Genomic Profiling Prior Authorization", "PA for comprehensive genomic profiling panels when results will alter management."),
    ("Fertility Preservation with Oncology Coverage", "Coverage criteria for gamete preservation when gonadotoxic therapy is planned."),
    ("Cancer Clinical Trial Routine Cost Coverage", "Covers routine costs of qualifying clinical trials per ACA/Medicare-style rules by LOB."),
]:
    add("Medical PA", "Oncology", name, "PRIOR_AUTH", "UM_LEADER", ["COMMERCIAL", "MA"], definition)

for name, definition in [
    ("Facility Polysomnography Prior Authorization", "Prefers HSAT when appropriate; PA for facility PSG when HSAT contraindicated."),
    ("Home Sleep Apnea Testing Preference", "Steers qualifying members to HSAT before facility PSG."),
    ("PAP Therapy Initiation and Compliance", "Initiation criteria plus compliance thresholds for ongoing PAP coverage."),
    ("Noninvasive Ventilation Prior Authorization", "PA for BiPAP/NIV devices under COPD/neuromuscular criteria."),
    ("Pulmonary Rehabilitation Authorization", "Authorizes pulmonary rehab within qualifying diagnosis and session limits."),
]:
    add("Medical PA", "Pulmonary & sleep", name, "PRIOR_AUTH", "UM_LEADER", ["COMMERCIAL", "MA", "MEDICAID"], definition)

for name, definition in [
    ("Upper Endoscopy Frequency Criteria", "Limits EGD frequency to guideline intervals unless alarm features present."),
    ("Colonoscopy Screening and Surveillance Intervals", "Aligns screening/surveillance intervals with USPSTF/specialty guidelines."),
    ("Capsule Endoscopy Prior Authorization", "PA for capsule endoscopy after nondiagnostic standard evaluation."),
    ("Anti-Reflux Procedure Prior Authorization", "PA for fundoplication/LINX-type procedures after failed medical therapy."),
]:
    add("Medical PA", "Gastroenterology", name, "PRIOR_AUTH", "UM_LEADER", ["COMMERCIAL", "MA"], definition)

for name, definition in [
    ("Elective Delivery Before 39 Weeks Restriction", "Restricts elective delivery <39 weeks without medical indication."),
    ("High-Risk Obstetrics Case Management Referral", "Requires/triggers CM referral for defined high-risk OB conditions."),
    ("NICU Level-of-Care Authorization", "Authorizes NICU days by level of care with concurrent review."),
    ("Infertility Diagnostic Coverage Criteria", "Separates covered infertility diagnostics from treatment benefits by product."),
    ("Infertility Treatment Prior Authorization", "PA for ART/IUI where benefit exists; excludes where rider absent."),
]:
    add("Medical PA", "Maternity & neonatal", name, "PRIOR_AUTH", "UM_LEADER", ["COMMERCIAL", "MEDICAID"], definition)

for name, definition in [
    ("Skilled Nursing Facility Authorization", "PA/concurrent review for SNF admissions and continued stay."),
    ("Inpatient Rehabilitation Facility Authorization", "PA for IRF based on intensity and medical necessity criteria."),
    ("Long-Term Acute Care Hospital Authorization", "PA for LTACH when acute hospital level still required."),
    ("Home Health Episode Authorization", "Authorizes skilled home health episodes with goal-oriented plans of care."),
    ("Private Duty Nursing Prior Authorization", "PA for PDN hours under skilled need criteria; excludes custodial."),
    ("Hospice Election and Concurrent Care Rules", "Defines hospice election, covered services, and concurrent care by LOB."),
]:
    add("Medical PA", "Post-acute & home", name, "PRIOR_AUTH", "UM_LEADER", ["COMMERCIAL", "MA", "MEDICAID"], definition)

for name, definition in [
    ("Power Mobility Device Prior Authorization", "PA for power WC/scooters with face-to-face and functional criteria."),
    ("Manual Wheelchair Medical Necessity", "Coverage criteria for manual mobility devices."),
    ("CPAP Supply Replacement Schedules", "Quantity/frequency limits for masks, tubing, filters aligned to DME standards."),
    ("Home Oxygen Qualification Criteria", "Qualifying blood gas/oximetry criteria for home oxygen."),
    ("Enteral Nutrition Prior Authorization", "PA for enteral formula and pumps when oral intake insufficient."),
    ("Parenteral Nutrition Prior Authorization", "PA for TPN under gut-failure criteria."),
    ("Negative Pressure Wound Therapy Prior Authorization", "PA for NPWT initiation and continuation."),
    ("Insulin Pump and CGM Medical Benefit Criteria", "Medical-benefit pathway for pumps/CGM when not exclusively pharmacy."),
    ("Prosthetic Limb Prior Authorization", "PA for prostheses with functional level (K-level) documentation."),
    ("Speech Generating Device Prior Authorization", "PA for SGD after speech-language evaluation."),
]:
    add("Medical PA", "DME & prosthetics", name, "PRIOR_AUTH", "UM_LEADER", ["COMMERCIAL", "MA", "MEDICAID"], definition)

for name, definition in [
    ("Hereditary Cancer Gene Panel Prior Authorization", "PA for multi-gene hereditary cancer panels with pretest counseling criteria."),
    ("Pharmacogenomic Testing Coverage Criteria", "Limits PGx panels to indications with actionable drug-gene pairs."),
    ("Direct-to-Consumer Lab Noncoverage", "Excludes member-initiated DTC lab testing lacking order/medical necessity."),
    ("Preferred Laboratory Network Steerage", "Steers outpatient labs to preferred freestanding labs when clinically appropriate."),
    ("Drug Testing Frequency Limits for Chronic Pain", "Limits definitive/presumptive UDT frequency in chronic opioid therapy."),
]:
    add("Medical PA", "Laboratory", name, "PRIOR_AUTH", "UM_LEADER", ["COMMERCIAL", "MA"], definition)

for name, definition in [
    ("Hyperbaric Oxygen Therapy Prior Authorization", "PA for HBO limited to accepted wound/crush/radiation indications."),
    ("Non-Emergency Ambulance Prior Authorization", "PA for scheduled ground ambulance when alternatives unsafe."),
    ("Air Ambulance Medical Necessity Review", "Post-service/preservice review for air transport medical necessity."),
    ("Cosmetic Surgery Exclusion Policy", "Excludes cosmetic procedures; defines reconstructive exceptions."),
    ("Gender-Affirming Surgery Coverage Criteria", "LOB-specific criteria for gender-affirming surgical benefits where covered."),
    ("Experimental and Investigational Services Policy", "Framework for E/I determinations and exception review."),
]:
    add("Medical PA", "Other medical", name, "PRIOR_AUTH", "UM_LEADER", ["COMMERCIAL", "MA", "MEDICAID"], definition)

# ─── C. Concurrent / clinical criteria ───────────────────────────────────────
for name, definition in [
    ("Inpatient vs Observation Status Determination", "Applies industry inpatient vs observation criteria (e.g., MCG/InterQual-style) at admission."),
    ("Inpatient Concurrent Stay Review", "Ongoing medical necessity review for acute inpatient days."),
    ("Discharge Planning Requirements", "Requires documented discharge plan and post-acute arrangements before continued stay approval."),
    ("Readmission Relatedness Review", "Evaluates related readmissions for payment and quality interventions."),
    ("Out-of-Network Inpatient Authorization", "Requires auth for elective OON inpatient; emergency stabilization exceptions apply."),
    ("NICU Concurrent Review", "Level-of-care concurrent review for neonatal intensive care."),
    ("Behavioral Health Inpatient Concurrent Review", "Concurrent review for psych IP using BH level-of-care criteria."),
    ("MCG-Style Clinical Criteria for Inpatient Admissions", "Admission review against licensed clinical guidelines for intensity of service/severity of illness."),
]:
    add("Clinical criteria", "Concurrent review", name, "CLINICAL_CRITERIA", "UM_LEADER", ["COMMERCIAL", "MA", "MEDICAID"], definition)

# ─── D. Site of care ─────────────────────────────────────────────────────────
for name, definition in [
    ("Specialty Infusion Site-of-Care Optimization", "Steers medically appropriate infusions from hospital outpatient to ASC/office/home."),
    ("Oncology Infusion Site Steerage", "Site-of-care policy for oncology infusions when clinical safety allows lower-cost sites."),
    ("Ambulatory Surgery Center Preference", "Prefers ASC over HOPD for listed ambulatory procedures when clinically appropriate."),
    ("Freestanding Imaging Steerage", "Steers advanced imaging to freestanding centers vs hospital outpatient when equivalent."),
    ("Home Infusion Preference", "Prefers home infusion for stable patients meeting safety criteria."),
    ("Home Sleep Testing Before Facility PSG", "Site-of-care preference pairing HSAT-first with facility exceptions."),
    ("Dialysis Home Modality Preference", "Encourages home dialysis modalities when clinically suitable."),
    ("Urgent Care Preference Over Non-Emergent ER", "Channel management steering non-emergent care to UC/retail clinic."),
]:
    add("Site of care", "Channel management", name, "SITE_OF_CARE", "UM_LEADER", ["COMMERCIAL", "MA"], definition)

# ─── E. Pharmacy ─────────────────────────────────────────────────────────────
for name, definition in [
    ("Pharmacy Prior Authorization Program", "Drug PA requiring clinical criteria before coverage at point of sale."),
    ("Non-Formulary Exception Review", "Review pathway for non-formulary drugs when formulary alternatives unsuitable."),
    ("Value Prior Authorization Program", "Streamlined PA emphasizing lower-net-cost clinically equivalent options."),
    ("Specialty Pharmacy Exclusive Network", "Requires selected specialty drugs to dispense via specialty pharmacy network."),
    ("Medical vs Pharmacy Benefit Channeling", "Defines white/brown/clear bagging and which benefit pays for specialty drugs."),
    ("Split-Fill Specialty Program", "Initial partial fills for titrated/high-waste specialty therapies."),
    ("Refill-Too-Soon Edit Policy", "POS edit preventing early refills outside vacation/lost-med exceptions."),
    ("Concurrent DUR Safety Edits", "Real-time drug-drug, duplicate therapy, and dose edits at adjudication."),
]:
    add("Pharmacy", "UM mechanisms", name, "PRIOR_AUTH", "UM_LEADER", ["COMMERCIAL", "MA"], definition)

for name, definition in [
    ("GLP-1 Step Therapy for Type 2 Diabetes", "Requires preferred antihyperglycemics before GLP-1 coverage for T2D by formulary."),
    ("GLP-1 Coverage Criteria for Obesity", "Separate obesity indication criteria/exclusions by LOB and benefit design."),
    ("Insulin Preferred Product and Biosimilar Step", "Step to preferred insulin/biosimilar before non-preferred brands."),
    ("PCSK9 Inhibitor Step Therapy", "Requires statin optimization before PCSK9 coverage."),
    ("Asthma and COPD Biologic Step Therapy", "Step through preferred controllers/biologics pathways."),
    ("Dermatology Biologic Step Therapy", "Step therapy for psoriasis/atopic dermatitis biologics."),
    ("Rheumatology Biologic Step Therapy for RA", "Preferred biologic/biosimilar pathways for rheumatoid arthritis."),
    ("IBD Biologic Step Therapy", "Step therapy for Crohn’s/UC specialty therapies."),
    ("Migraine CGRP Step Therapy", "Requires preferred migraine preventives before CGRP antagonists."),
    ("MS Disease-Modifying Therapy Prior Authorization", "PA/step for MS DMTs by efficacy/safety/cost tiering."),
    ("ADHD Stimulant Quantity Limits and Preferred Agents", "QL and preferred agent rules for stimulants (commercial formulary patterns)."),
    ("Opioid Analgesic Utilization Management", "PA/QL/MME limits for opioid analgesics; distinguishes acute vs chronic."),
    ("Medication-Assisted Treatment Access Policy", "Ensures access pathway for buprenorphine/naltrexone MAT without inappropriate barriers."),
    ("Hepatitis C Direct-Acting Antiviral Prior Authorization", "PA for DAAs with fibrosis/prescriber criteria per LOB evolution."),
    ("HIV Antiretroviral Formulary Management", "Preferred ARV regimens and exception pathways."),
    ("Oncology Oral Specialty Prior Authorization", "PA for oral oncolytics with indication and companion testing rules."),
    ("Growth Hormone Prior Authorization", "PA for somatropin by pediatric/adult indication criteria."),
    ("Gene Therapy One-Time High-Cost Prior Authorization", "PA for gene therapies at designated centers with outcomes agreements where used."),
    ("Biosimilar Preferencing Policy", "Non-medical switch/preferencing framework favoring biosimilars when clinically appropriate."),
    ("Blood Glucose Test Strip Step Therapy", "Prefers lower-cost strip platforms before non-preferred brands."),
]:
    add("Pharmacy", "Therapeutic programs", name, "STEP_THERAPY", "UM_LEADER", ["COMMERCIAL", "MA"], definition)

for name, definition in [
    ("Opioid Quantity Limit — Acute Pain", "Days’ supply and MME limits for acute opioid initiations."),
    ("Opioid Quantity Limit — Chronic Pain", "Ongoing QL/MME and documentation requirements for chronic opioid therapy."),
    ("Benzodiazepine Quantity Limits", "QL to reduce chronic benzodiazepine exposure risk."),
    ("Specialty Drug Days’ Supply Limits", "Limits specialty fills to 30-day supply unless exception."),
    ("CGM and Diabetes Supply Quantity Limits", "Unit limits for sensors/transmitters/strips per benefit period."),
]:
    add("Pharmacy", "Quantity limits", name, "QUANTITY_LIMIT", "UM_LEADER", ["COMMERCIAL", "MA", "MEDICAID"], definition)

for name, definition in [
    ("Preferred Generic Drug Tier Design", "Benefit design steering to generics via tiered cost share."),
    ("Specialty Tier Coinsurance Design", "Defines specialty tier coinsurance and OOP treatment by product."),
    ("Mandatory Mail-Order Maintenance Medications", "Requires mail for listed maintenance drugs where product rules allow."),
    ("90-Day Retail Maintenance Program", "Allows/requires 90-day retail for maintenance meds at preferred pharmacies."),
]:
    add("Pharmacy", "Benefit design", name, "BENEFIT", "UM_LEADER", ["COMMERCIAL"], definition)

# ─── F. Behavioral health ────────────────────────────────────────────────────
for name, definition in [
    ("Psychiatric Inpatient Prior Authorization", "PA/concurrent review for acute psychiatric hospitalization."),
    ("Psychiatric Residential Treatment Authorization", "LOC authorization for residential BH treatment."),
    ("Partial Hospitalization and IOP Authorization", "Authorizes PHP/IOP using BH level-of-care criteria."),
    ("Applied Behavior Analysis Prior Authorization", "PA for ABA with diagnostic and treatment-plan requirements."),
    ("Neuropsychological Testing Prior Authorization", "PA for extended NP testing batteries."),
    ("Eating Disorder Level-of-Care Authorization", "LOC criteria for IP/residential/PHP eating disorder care."),
    ("SUD Detoxification Authorization", "Authorization for medically monitored withdrawal management."),
    ("SUD Residential and IOP Authorization", "ASAM-aligned LOC authorization for SUD continuing care."),
    ("TMS Prior Authorization", "PA for transcranial magnetic stimulation after antidepressant failures."),
    ("ECT Authorization Criteria", "Criteria for electroconvulsive therapy coverage."),
    ("Esketamine Treatment Prior Authorization", "PA for esketamine with REMS and failed-therapy criteria."),
    ("Mental Health Parity NQTL Documentation Policy", "Operational policy ensuring MH/SUD NQTLs are comparable to medical/surgical."),
]:
    add("Behavioral health", "UM & parity", name, "PRIOR_AUTH", "UM_LEADER", ["COMMERCIAL", "MA", "MEDICAID"], definition)

# ─── G. Visit limits ─────────────────────────────────────────────────────────
for name, definition in [
    ("Physical Therapy Visit Limit", "Annual or episode visit limits for PT with medical necessity extension pathway."),
    ("Occupational Therapy Annual Limit", "Visit limits for OT services."),
    ("Speech Therapy Visit Limit", "Visit limits for ST services."),
    ("Chiropractic Visit Limit", "Visit limits for chiropractic manipulation where covered."),
    ("Cardiac Rehabilitation Session Limit", "Session caps for Phase II cardiac rehab."),
    ("Pulmonary Rehabilitation Session Limit", "Session caps for pulmonary rehab."),
    ("Acupuncture Visit Limit", "Visit limits where acupuncture benefit exists."),
]:
    add("Visit limits", "Therapies", name, "DURATION_FREQUENCY_LIMIT", "UM_LEADER", ["COMMERCIAL", "MA", "MEDICAID"], definition)

# ─── H. Coverage exclusions ──────────────────────────────────────────────────
for name, definition in [
    ("Experimental and Investigational Exclusion Framework", "Plan-level E/I exclusion with exception/appeal pathway."),
    ("Cosmetic Services Exclusion", "Excludes cosmetic services; lists reconstructive carve-ins."),
    ("Custodial Care Exclusion", "Excludes custodial/non-skilled long-term care services."),
    ("Convenience Care Exclusion", "Excludes services solely for convenience of member/provider."),
    ("Hearing Aid Coverage Criteria", "Defines hearing aid benefits/limits by LOB and age."),
    ("Vision Hardware vs Medical Eye Disease", "Separates routine vision hardware from medical ophthalmology coverage."),
    ("Surrogacy Exclusion Policy", "Excludes surrogacy-related services unless mandated/rider."),
]:
    add("Coverage", "Exclusions & edge benefits", name, "COVERAGE", "COMPLIANCE", ["COMMERCIAL", "MA", "MEDICAID"], definition)

# ─── I. Cost share / benefit ─────────────────────────────────────────────────
for name, definition in [
    ("Emergency vs Urgent Care Cost Share Differential", "Higher ER cost share than urgent care for non-emergent steering."),
    ("Telehealth Cost Sharing Parity Policy", "Defines when telehealth cost share matches in-person by LOB."),
    ("Advanced Imaging Member Cost Share Design", "Coinsurance/copay design for advanced imaging."),
    ("Specialty Pharmacy Coinsurance Design", "Member cost share rules for specialty tier."),
    ("ACA Preventive Services Zero Cost Share", "Zero cost share for USPSTF/ACIP/HRSA preventive services on non-grandfathered commercial."),
    ("Value-Based Insurance Design Waivers", "Reduced cost share for high-value chronic disease services/drugs."),
]:
    add("Benefit design", "Cost sharing", name, "COST_SHARING", "STRATEGY", ["COMMERCIAL", "MA"], definition)

# ─── J. Network / referral / access ──────────────────────────────────────────
for name, definition in [
    ("PCP Referral Requirement for Specialist Visits", "Requires PCP referral before specialty visits in gatekept products."),
    ("Out-of-Network Elective Services Restriction", "Restricts elective OON services without approved gap exception."),
    ("Tiered Network Specialist Steerage", "Differential benefits favoring tier-1 specialists/facilities."),
    ("Centers of Excellence Requirement — Transplant", "Requires COE transplant networks for coverage."),
    ("Centers of Excellence Requirement — Bariatric", "Requires designated bariatric COE facilities."),
    ("Centers of Excellence Requirement — Complex Cancer", "Steers complex cancer surgery/care to COE programs."),
    ("Preferred Dialysis Network Policy", "Network preference for dialysis providers."),
    ("Preferred Pharmacy Network Policy", "Lower cost share at preferred pharmacies."),
    ("Telehealth Vendor Network Rules", "Defines covered telehealth vendors and modality rules."),
    ("Continuity of Care After Provider Termination", "Transition coverage when a provider leaves the network."),
    ("Maximum Wait Time for Specialist Appointments", "Network adequacy wait-time standards for specialty access."),
    ("Behavioral Health Appointment Access Standards", "Access-time standards for BH initial and follow-up appointments."),
    ("Provider Specialty Eligibility for High-Cost Codes", "Limits billing of selected codes to eligible specialties."),
]:
    add("Network & access", "Network rules", name, "NETWORK_RESTRICTION", "NETWORK", ["COMMERCIAL", "MA", "MEDICAID"], definition)

# Fix types for referral / access / provider eligibility rows
# (we'll normalize in builder for specific names)

# ─── K. Payment integrity ────────────────────────────────────────────────────
for name, definition in [
    ("Bundled Payment for Joint Replacement", "Episode bundle payment for elective joint replacement across facility/professional."),
    ("Maternity Episode Bundle", "Case/episode payment construct spanning delivery and postpartum window."),
    ("Cardiac Episode Bundle", "Episode payment for defined cardiac procedures/admissions."),
    ("DRG Inpatient Payment Policy", "Inpatient facility payment by MS-DRG/APR-DRG as contracted."),
    ("Multiple Procedure Payment Reduction", "Applies MPPR to secondary procedures in same session."),
    ("Assistant Surgeon Payment Rules", "Payment criteria for assistant-at-surgery modifiers."),
    ("NCCI and MUE Claims Edit Policy", "Applies NCCI PTP and MUE edits before payment."),
    ("Unbundling and Incidental Denial Policy", "Denies incidental/unbundled components already in primary procedure."),
    ("Hospital-Acquired Condition Nonpayment", "Nonpayment adjustments for HAC/never events per CMS-style rules."),
    ("Related Readmission Payment Adjustment", "Payment adjustment policy for related readmissions within window."),
    ("Coordination of Benefits Administration", "Primary/secondary payer determination and COB payment order."),
    ("Third-Party Liability and Subrogation", "Recovery from liable third parties when another party is responsible."),
    ("Timely Filing Limit — Provider Claims", "Denies claims filed after timely filing limit unless exception."),
]:
    add("Payment", "Payment & integrity", name, "PAYMENT_POLICY", "PAYMENT_INTEGRITY", ["COMMERCIAL", "MA", "MEDICAID"], definition)

# ─── L. Care management ──────────────────────────────────────────────────────
for name, definition in [
    ("Complex Case Management Program", "Identifies and manages high-cost/complex members with interdisciplinary CM."),
    ("Diabetes Disease Management Program", "DM program with outreach, adherence, and gap closure."),
    ("Heart Failure Disease Management Program", "CHF DM focusing on transitions, meds, and readmit reduction."),
    ("COPD Disease Management Program", "COPD DM with exacerbation prevention focus."),
    ("CKD Disease Management Program", "CKD staging outreach and nephrology coordination."),
    ("Maternity Management Program", "Prenatal risk screening and preterm-prevention outreach."),
    ("Transition of Care Post-Discharge Program", "Post-IP outreach to reduce readmissions."),
    ("Emergency Department Frequent Utilizer Program", "CM intervention for repeated non-emergent ED use."),
    ("Medication Therapy Management Program", "MTM for polypharmacy / Part D-style comprehensive reviews."),
    ("Medicare Stars Gap Closure Program", "MA quality gap closure for Stars measures."),
]:
    add("Care management", "Population programs", name, "COMPOSITE", "UM_LEADER", ["COMMERCIAL", "MA", "MEDICAID"], definition)

# ─── M. Administrative ───────────────────────────────────────────────────────
for name, definition in [
    ("Prior Authorization Submission and Turnaround Standards", "Channels, required clinicals, and decision turnaround time standards."),
    ("Peer-to-Peer Review Opportunity Policy", "Gives ordering clinicians a P2P pathway before/after adverse determination."),
    ("Member Appeal and Grievance Timelines", "Internal appeal/grievance clocks per LOB regulation."),
    ("External Review / IRO Process", "Independent review organization pathway after internal appeal."),
    ("Continuity of Medications During Appeal", "Continuation of therapy rules during pending appeals where required."),
    ("Retrospective Authorization Window", "Limited retrospective auth for urgent services when preservice not feasible."),
    ("Provider Reconsideration / Dispute Process", "Provider claim/UM dispute pathway distinct from member appeals."),
    ("Medical Records Request Standards", "Timelines and minimum content for records requests supporting UM/payment."),
]:
    add("Administrative", "UM operations", name, "ADMINISTRATIVE_REQUIREMENT", "COMPLIANCE", ["COMMERCIAL", "MA", "MEDICAID"], definition)

# ─── N. Digital ──────────────────────────────────────────────────────────────
for name, definition in [
    ("Telehealth Covered Services List", "Defines which services are covered via telehealth by LOB."),
    ("Audio-Only Telehealth Coverage Rules", "When audio-only visits are covered vs video-required."),
    ("Remote Patient Monitoring Coverage Criteria", "Coverage criteria for RPM devices and monitoring codes."),
    ("Digital Therapeutics Coverage Criteria", "Coverage framework for prescription digital therapeutics."),
    ("Store-and-Forward Teledermatology Coverage", "Coverage for asynchronous dermatology eConsults where enabled."),
]:
    add("Digital care", "Virtual care", name, "COVERAGE", "UM_LEADER", ["COMMERCIAL", "MA", "MEDICAID"], definition)

# ─── O. Dental / vision / hearing edge ───────────────────────────────────────
for name, definition in [
    ("Medical-Dental Crossover Trauma Policy", "Medical coverage for dental services secondary to accidental trauma."),
    ("Oncology-Related Dental Clearance Coverage", "Limited dental services medically necessary for oncology treatment."),
    ("Medical Eye Disease vs Routine Vision Separation", "Coverage separation between routine vision and medical ophthalmology."),
    ("Cochlear Implant Prior Authorization", "PA for cochlear implants with audiologic criteria."),
    ("Hearing Aid Benefit and Replacement Cycle", "Hardware benefit limits and replacement intervals by LOB."),
]:
    add("Ancillary", "Dental vision hearing", name, "COVERAGE", "UM_LEADER", ["COMMERCIAL", "MA", "MEDICAID"], definition)

# ─── P. Blues / multi-state ──────────────────────────────────────────────────
for name, definition in [
    ("BlueCard Home Plan Medical Policy Application", "Home plan medical policy generally governs BlueCard claims."),
    ("BlueCard Host Plan Local Rules Application", "Defines when host plan local rules/pricing apply."),
    ("National Account Custom Benefit Administration", "Administration of national-account custom plan documents."),
    ("Away-From-Home Care / Guest Membership Rules", "Coverage rules for members receiving care outside service area."),
]:
    add("Blues association", "Inter-plan", name, "ADMINISTRATIVE_REQUIREMENT", "COMPLIANCE", ["COMMERCIAL", "MA"], definition)

# ─── Q. Regulatory overlays ──────────────────────────────────────────────────
for name, definition in [
    ("No Surprises Act Emergency Services No-PA Rule", "Emergency services covered without prior auth; balance-billing protections."),
    ("Mental Health Parity Comparative Analysis Policy", "Requires documented NQTL comparative analyses for MH/SUD vs med/surg."),
    ("Medicare NCD and LCD Precedence Policy", "MA coverage follows applicable NCDs/LCDs and CMS guidance."),
    ("Medicaid EPSDT Coverage Obligation", "EPSDT requires covering medically necessary pediatric services under Medicaid."),
    ("North Carolina Mandated Benefit Administration", "Administers NC DOI mandated benefits applicable to fully insured products."),
    ("ACA Essential Health Benefits Mapping", "Maps EHB benchmark benefits for ACA individual/small group products."),
]:
    add("Regulatory", "Mandates", name, "ADMINISTRATIVE_REQUIREMENT", "COMPLIANCE", ["COMMERCIAL", "MA", "MEDICAID"], definition)


TYPE_OVERRIDES = {
    "PCP Referral Requirement for Specialist Visits": "REFERRAL_REQUIREMENT",
    "Maximum Wait Time for Specialist Appointments": "ACCESS_AVAILABILITY_RULE",
    "Behavioral Health Appointment Access Standards": "ACCESS_AVAILABILITY_RULE",
    "Provider Specialty Eligibility for High-Cost Codes": "PROVIDER_ELIGIBILITY",
    "Preferred Generic Drug Tier Design": "BENEFIT",
    "Cosmetic Surgery Exclusion Policy": "COVERAGE",
    "Experimental and Investigational Services Policy": "COVERAGE",
    "Coronary Calcium Scoring Coverage Criteria": "COVERAGE",
    "Orthobiologics and PRP Noncoverage": "COVERAGE",
    "Interventional Pain Regenerative Injection Noncoverage": "COVERAGE",
    "Direct-to-Consumer Lab Noncoverage": "COVERAGE",
    "Home Sleep Apnea Testing Preference": "SITE_OF_CARE",
    "Home Sleep Testing Before Facility PSG": "SITE_OF_CARE",
    "Preferred Laboratory Network Steerage": "NETWORK_RESTRICTION",
    "Pharmacy Prior Authorization Program": "PRIOR_AUTH",
    "Non-Formulary Exception Review": "PRIOR_AUTH",
    "Value Prior Authorization Program": "PRIOR_AUTH",
    "Opioid Analgesic Utilization Management": "COMPOSITE",
    "Gene Therapy One-Time High-Cost Prior Authorization": "PRIOR_AUTH",
    "Oncology Oral Specialty Prior Authorization": "PRIOR_AUTH",
    "Growth Hormone Prior Authorization": "PRIOR_AUTH",
    "Hepatitis C Direct-Acting Antiviral Prior Authorization": "PRIOR_AUTH",
    "MS Disease-Modifying Therapy Prior Authorization": "PRIOR_AUTH",
    "ADHD Stimulant Quantity Limits and Preferred Agents": "QUANTITY_LIMIT",
    "Specialty Pharmacy Exclusive Network": "NETWORK_RESTRICTION",
    "Medical vs Pharmacy Benefit Channeling": "ADMINISTRATIVE_REQUIREMENT",
    "Split-Fill Specialty Program": "QUANTITY_LIMIT",
    "Refill-Too-Soon Edit Policy": "ADMINISTRATIVE_REQUIREMENT",
    "Concurrent DUR Safety Edits": "ADMINISTRATIVE_REQUIREMENT",
    "HIV Antiretroviral Formulary Management": "BENEFIT",
    "Biosimilar Preferencing Policy": "STEP_THERAPY",
    "Medication-Assisted Treatment Access Policy": "COVERAGE",
}


def build():
    seen = set()
    policies = []
    for domain, subdomain, name, ptype, owner, lobs, definition in RAW:
        if name in seen:
            raise SystemExit(f"Duplicate policy name: {name}")
        seen.add(name)
        ptype = TYPE_OVERRIDES.get(name, ptype)
        policies.append(
            {
                "name": name,
                "policy_type": ptype,
                "owner_role": owner,
                "domain": domain,
                "subdomain": subdomain,
                "lobs": lobs,
                "markets": ["NC"],
                "status": "ACTIVE",
                "description": f"{definition} {DISCLAIMER}",
                "illustrative_standards_aligned": True,
                "not_verbatim_bcbsnc_policy": True,
                "jurisdiction": "NC",
                "standards_basis": [
                    "U.S. payer UM common practice",
                    "Blues-style medical/pharmacy program structure",
                    "CMS/ACA/MHPAEA concepts where noted by LOB",
                ],
            }
        )

    doc = {
        "catalog_version": "2026.10.29",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "accuracy_contract": {
            "claim": "Industry-standard / Blues-aligned illustrative program catalog for NC-oriented demos",
            "not_claiming": "Verbatim Blue Cross NC medical policies, CUMG text, or formulary NDC lists",
            "why": "Proprietary BCBS NC policy text is not publicly reproducible at 100% fidelity; mislabeling would reduce credibility",
        },
        "count": len(policies),
        "policies": policies,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2))
    print(f"Wrote {len(policies)} policies -> {OUT}")
    from collections import Counter
    print("by_type", dict(Counter(p["policy_type"] for p in policies)))
    print("by_domain", dict(Counter(p["domain"] for p in policies)))


if __name__ == "__main__":
    build()
