#!/usr/bin/env python3
"""Representative Payer CPT/HCPCS/HCPCS-DME schedules by catalog policy name.

Evidence class: REPRESENTATIVE_DESIGN from public code nomenclature — NOT proprietary
Blue Cross NC operative schedules. Where mapping is uncertain → UNRESOLVED (empty codes).

Do not invent confidential MUE thresholds, contracted rates, or proprietary clinical cutoffs.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# Each entry: (codes, code_system, notes)
# codes empty + unresolved=True means required schedule not yet authored.

Schedule = Dict[str, Any]


def _s(
    codes: List[str],
    *,
    system: str = "CPT",
    notes: str = "",
    unresolved: bool = False,
    not_applicable: bool = False,
    na_reason: str = "",
) -> Schedule:
    return {
        "codes": codes,
        "code_system": system,
        "evidence_class": (
            "NOT_APPLICABLE"
            if not_applicable
            else ("UNRESOLVED" if unresolved or not codes else "REPRESENTATIVE_DESIGN")
        ),
        "notes": notes or na_reason,
        "unresolved": unresolved or (not codes and not not_applicable),
        "not_applicable": not_applicable,
        "not_applicable_reason": na_reason or None,
    }


# Exact-name schedules for PRIOR_AUTH_UM and other mechanism-heavy policies
EXACT: Dict[str, Schedule] = {
    # --- Dec4 nine: do not regenerate; frozen ---
    "Outpatient MRI Prior Authorization": _s(
        ["72148", "72149", "72158"], notes="Frozen Dec4 lumbar schedule"
    ),
    "Multiple Procedure Payment Reduction (MPPR)": _s(
        [], unresolved=True, notes="Mechanical KA; product codeset may be empty"
    ),
    "Freestanding Imaging Site-of-Care Steerage": _s(
        ["72148", "72149", "72158"], notes="Aligned to imaging steerage demo fixture"
    ),
    # --- PRIOR_AUTH / UM ---
    "ACL Reconstruction Prior Authorization": _s(
        ["29888"], notes="Arthroscopically aided ACL repair/reconstruction"
    ),
    "Air Ambulance Medical Necessity Review": _s(
        ["A0430", "A0431", "A0435", "A0436"],
        system="HCPCS",
        notes="Fixed/rotary wing air ambulance + mileage",
    ),
    "Anti-Reflux Procedure Prior Authorization": _s(
        ["43280", "43279", "43281", "43282"],
        notes="Laparoscopic fundoplication / LINX-class antireflux procedures",
    ),
    "Applied Behavior Analysis Prior Authorization": _s(
        ["97151", "97152", "97153", "97154", "97155", "97156", "97157", "97158"],
        notes="Adaptive behavior treatment family",
    ),
    "Bariatric Revisional Surgery Prior Authorization": _s(
        ["43775", "43644", "43645", "43848", "43860"],
        notes="Revisional / conversion bariatric procedures",
    ),
    "Bariatric Surgery Prior Authorization": _s(
        ["43775", "43644", "43645", "43846", "43847"],
        notes="Primary bariatric sleeve/bypass",
    ),
    "Bone Densitometry Frequency Limits": _s(
        ["77080", "77081", "77085"], notes="DXA axial/peripheral/VFA"
    ),
    "Bone Growth Stimulator Prior Authorization": _s(
        ["E0747", "E0748", "E0760"], system="HCPCS", notes="Osteogenesis stimulators"
    ),
    "Breast MRI Medical Necessity Criteria": _s(
        ["77046", "77047", "77048", "77049"], notes="Breast MRI with/without CAD"
    ),
    "Breast Reduction Medical Necessity": _s(
        ["19318"], notes="Reduction mammaplasty"
    ),
    "Bunion and Forefoot Elective Surgery Prior Authorization": _s(
        ["28285", "28289", "28292", "28296", "28297", "28298", "28299"],
        notes="Hallux valgus / bunionectomy family",
    ),
    "Cancer Clinical Trial Routine Cost Coverage": _s(
        [],
        not_applicable=True,
        na_reason="Coverage obligation is benefit/administrative; not a fixed CPT schedule",
    ),
    "Capsule Endoscopy Prior Authorization": _s(
        ["91110", "91111"], notes="GI tract capsule endoscopy"
    ),
    "Cardiac CT Angiography Prior Authorization": _s(
        ["75574"], notes="CTA heart with contrast"
    ),
    "Cardiac Implantable Device Prior Authorization": _s(
        ["33206", "33207", "33208", "33249", "33270"],
        notes="Pacemaker / ICD insert family (representative)",
    ),
    "Cardiac Rehabilitation Authorization": _s(
        ["93797", "93798"], notes="Physician services for outpatient cardiac rehab"
    ),
    "Cardiac Stress Testing Prior Authorization": _s(
        ["93015", "93016", "93017", "93018", "78452"],
        notes="Cardiovascular stress test + myocardial perfusion SPECT",
    ),
    "Cataract Surgery Second-Eye and Specialty Lens Rules": _s(
        ["66984", "66982", "66991"],
        notes="Cataract extraction with IOL; complex / femto-adjacent codes as design",
    ),
    "Colonoscopy Screening and Surveillance Intervals": _s(
        ["45378", "45380", "45385", "G0121", "G0105"],
        system="CPT/HCPCS",
        notes="Diagnostic/screening colonoscopy family",
    ),
    "Complex Hernia Repair Prior Authorization": _s(
        ["49591", "49592", "49593", "49594", "49595", "49596"],
        notes="Anterior abdominal hernia repair (2023+ family)",
    ),
    "CPAP Supply Replacement Schedules": _s(
        ["E0601", "A7030", "A7031", "A7032", "A7033", "A7034", "A7035"],
        system="HCPCS",
        notes="CPAP device + mask/supply HCPCS",
    ),
    "Custom Orthotic and Brace Prior Authorization": _s(
        ["L1900", "L1902", "L1904", "L1906", "L1930", "L1960"],
        system="HCPCS",
        notes="Ankle/foot orthoses representative set",
    ),
    "Diagnostic Cardiac Catheterization Appropriateness": _s(
        ["93451", "93452", "93453", "93454", "93455", "93456", "93457", "93458"],
        notes="Cardiac cath / coronary angiography family",
    ),
    "Drug Testing Frequency Limits for Chronic Pain": _s(
        ["80305", "80306", "80307", "G0480", "G0481", "G0482", "G0483"],
        system="CPT/HCPCS",
        notes="Presumptive/definitive drug testing",
    ),
    "Eating Disorder Level-of-Care Authorization": _s(
        [],
        unresolved=True,
        notes="LOC is revenue/UB and benefit driven; CPT schedule requires product design",
    ),
    "ECT Authorization Criteria": _s(
        ["90870"], notes="Electroconvulsive therapy"
    ),
    "Elective Delivery Before 39 Weeks Restriction": _s(
        ["59400", "59510", "59610", "59618"],
        notes="Global OB delivery codes — gestational age rule is clinical, not code-only",
    ),
    "Elective Joint Arthroplasty Prior Authorization": _s(
        ["27130", "27447", "23472"],
        notes="THA / TKA / TSA primary arthroplasty",
    ),
    "Enteral Nutrition Prior Authorization": _s(
        ["B4034", "B4035", "B4036", "B4150", "B4152", "B4153", "B4154"],
        system="HCPCS",
        notes="Enteral formula / supply HCPCS",
    ),
    "Epidural Steroid Injection Prior Authorization": _s(
        ["62321", "62323", "64483", "64484"],
        notes="Interlaminar / transforaminal ESI family",
    ),
    "Esketamine Treatment Prior Authorization": _s(
        ["G2082", "G2083"], system="HCPCS", notes="Esketamine nasal spray administration"
    ),
    "Eyelid Surgery Medical Necessity": _s(
        ["15820", "15821", "15822", "15823"], notes="Blepharoplasty family"
    ),
    "Facet Joint Intervention Prior Authorization": _s(
        ["64490", "64491", "64492", "64493", "64494", "64495", "64633", "64635"],
        notes="Facet injection / RFA family",
    ),
    "Facility Polysomnography Prior Authorization": _s(
        ["95810", "95811"], notes="Attended PSG / titration"
    ),
    "Fertility Preservation with Oncology Coverage": _s(
        ["89258", "89337", "0058T"],
        notes="Cryopreservation / oocyte representative set",
    ),
    "Gender-Affirming Surgery Coverage Criteria": _s(
        ["55970", "55980", "19303", "19318", "54125", "56805"],
        notes="Representative GAS CPT set — product schedule UNRESOLVED for full catalog",
    ),
    "Growth Hormone Prior Authorization": _s(
        ["J2941"], system="HCPCS", notes="Somatropin injection HCPCS — NDCs product-specific UNRESOLVED"
    ),
    "Hepatitis C Direct-Acting Antiviral Prior Authorization": _s(
        [],
        unresolved=True,
        notes="NDC/formulary product schedule required; no fixed CPT",
    ),
    "Hereditary Cancer Gene Panel Prior Authorization": _s(
        ["81432", "81433", "81162", "81216"],
        notes="Hereditary breast/ovarian / cancer gene panels representative",
    ),
    "High-Risk Obstetrics Case Management Referral": _s(
        [],
        not_applicable=True,
        na_reason="Case management referral trigger — not a procedure code schedule",
    ),
    "Home Health Episode Authorization": _s(
        ["G0151", "G0152", "G0153", "G0299", "G0300"],
        system="HCPCS",
        notes="Home health discipline visit HCPCS",
    ),
    "Home Oxygen Qualification Criteria": _s(
        ["E0424", "E0431", "E0434", "E0439", "E1390", "E1392"],
        system="HCPCS",
        notes="Oxygen system HCPCS",
    ),
    "Hospice Election and Concurrent Care Rules": _s(
        [],
        not_applicable=True,
        na_reason="Benefit election / concurrent care — not CPT-driven",
    ),
    "Hysterectomy Route Medical Necessity": _s(
        ["58150", "58260", "58570", "58571", "58572", "58573"],
        notes="Abdominal / vaginal / laparoscopic hysterectomy",
    ),
    "Infertility Diagnostic Coverage Criteria": _s(
        ["58340", "74740", "89320", "89321", "89322"],
        notes="HSG / semen analysis representative diagnostics",
    ),
    "Infertility Treatment Prior Authorization": _s(
        ["58970", "58974", "58976", "89280", "89281"],
        notes="ART / IVF laboratory and retrieval family",
    ),
    "Inpatient Concurrent and Continued-Stay Review Program": _s(
        [],
        not_applicable=True,
        na_reason="Inpatient LOC / DRG concurrent review — not outpatient CPT PA schedule",
    ),
    "Inpatient Rehabilitation Facility Authorization": _s(
        [],
        not_applicable=True,
        na_reason="IRF authorization uses CMG/revenue/admission criteria",
    ),
    "Insertable Cardiac Monitor Prior Authorization": _s(
        ["33285", "33286"], notes="Subcutaneous cardiac rhythm monitor insert/removal"
    ),
    "Insulin Pump and CGM Medical Benefit Criteria": _s(
        ["E0784", "A9276", "A9277", "A9278", "K0553", "K0554"],
        system="HCPCS",
        notes="Insulin pump + CGM supplies",
    ),
    "Interventional Radiology Procedure Prior Authorization": _s(
        ["37220", "37221", "37224", "37225", "37226", "37227", "37228", "37229"],
        notes="Revascularization IR family (representative)",
    ),
    "Intrathecal Drug Pump Prior Authorization": _s(
        ["62362", "62350", "62351"], notes="Implantable pump / catheter"
    ),
    "Long-Term Acute Care Hospital Authorization": _s(
        [],
        not_applicable=True,
        na_reason="LTACH admission authorization — not CPT schedule",
    ),
    "Low-Dose CT Lung Cancer Screening Criteria": _s(
        ["71271"], notes="LDCT thorax for lung cancer screening"
    ),
    "Manual Wheelchair Medical Necessity": _s(
        ["K0001", "K0002", "K0003", "K0004", "K0005"],
        system="HCPCS",
        notes="Manual wheelchair base codes",
    ),
    "Medical Oncology Regimen Prior Authorization": _s(
        [],
        unresolved=True,
        notes="Regimen PA is HCPCS J-code / NDC product specific — schedule UNRESOLVED",
    ),
    "Mental Health Parity NQTL Documentation Policy": _s(
        [],
        not_applicable=True,
        na_reason="Parity documentation obligation — not a code schedule",
    ),
    "Neuropsychological Testing Prior Authorization": _s(
        ["96132", "96133", "96136", "96137", "96138", "96139"],
        notes="Neuropsychological testing evaluation/admin",
    ),
    "NICU Level-of-Care Authorization": _s(
        [],
        not_applicable=True,
        na_reason="NICU LOC / revenue codes — not outpatient CPT PA",
    ),
    "Non-Emergency Ambulance Prior Authorization": _s(
        ["A0426", "A0428", "A0425"],
        system="HCPCS",
        notes="Ground ambulance ALS/BLS non-emergency + mileage",
    ),
    "Noninvasive Ventilation Prior Authorization": _s(
        ["E0470", "E0471", "E0466"],
        system="HCPCS",
        notes="Respiratory assist / NIV devices",
    ),
    "Nuclear Cardiology Prior Authorization": _s(
        ["78451", "78452", "78453", "78454"],
        notes="Myocardial perfusion imaging",
    ),
    "Oncology Genomic Profiling Prior Authorization": _s(
        ["81445", "81450", "81455", "81479"],
        notes="Tumor genomic sequencing panels representative",
    ),
    "Oncology Oral Specialty Prior Authorization": _s(
        [],
        unresolved=True,
        notes="Oral oncolytic NDCs required — UNRESOLVED",
    ),
    "Outpatient CT / CTA Prior Authorization": _s(
        ["70450", "70460", "70470", "70496", "70498", "71250", "71260", "71270", "71275", "72125", "72126", "72127", "72128", "72129", "72130", "72131", "72132", "72133", "74150", "74160", "74170", "74174", "74175", "74176", "74177", "74178"],
        notes="Common outpatient CT/CTA anatomic family (representative)",
    ),
    "Panniculectomy Medical Necessity": _s(
        ["15830", "15847"], notes="Excision excessive skin abdomen / panniculectomy"
    ),
    "Parenteral Nutrition Prior Authorization": _s(
        ["B4164", "B4168", "B4172", "B4176", "B4178", "B4180", "B4185", "B4189"],
        system="HCPCS",
        notes="Parenteral nutrition solution HCPCS",
    ),
    "Partial Hospitalization and IOP Authorization": _s(
        ["H0035", "S9480", "G0129", "G0176", "G0177"],
        system="HCPCS",
        notes="PHP/IOP behavioral health HCPCS",
    ),
    "PCI Elective Appropriateness Review": _s(
        ["92920", "92928", "92933", "92943"],
        notes="Percutaneous coronary intervention family",
    ),
    "Peripheral Vascular Intervention Prior Authorization": _s(
        ["37220", "37221", "37224", "37225", "37226", "37227", "37228", "37229", "37230", "37231"],
        notes="Lower extremity revascularization",
    ),
    "PET / PET-CT Prior Authorization": _s(
        ["78811", "78812", "78813", "78814", "78815", "78816"],
        notes="PET / PET-CT tumor imaging",
    ),
    "Pharmacogenomic Testing Coverage Criteria": _s(
        ["81225", "81226", "81227", "81291", "81479"],
        notes="Common PGx gene tests + unlisted molecular",
    ),
    "Power Mobility Device Prior Authorization": _s(
        ["K0800", "K0801", "K0802", "K0813", "K0814", "K0815", "K0816", "K0820", "K0821", "K0822", "K0823"],
        system="HCPCS",
        notes="POV / power wheelchair group codes",
    ),
    "Private Duty Nursing Prior Authorization": _s(
        ["T1000", "T1002", "T1003"],
        system="HCPCS",
        notes="Private duty / RN/LPN nursing hours",
    ),
    "Prostate Procedure Prior Authorization": _s(
        ["55866", "55840", "55842", "55845", "52601"],
        notes="Prostatectomy / TURP representative",
    ),
    "Prosthetic Limb Prior Authorization": _s(
        ["L5500", "L5510", "L5520", "L5530", "L5600", "L5610"],
        system="HCPCS",
        notes="Lower limb prosthesis preparatory/definitive representative",
    ),
    "Psychiatric Inpatient Prior Authorization": _s(
        [],
        not_applicable=True,
        na_reason="Psych inpatient uses revenue/LOC — not outpatient CPT PA schedule",
    ),
    "Psychiatric Residential Treatment Authorization": _s(
        ["H0017", "H0018", "H0019"],
        system="HCPCS",
        notes="Behavioral health residential HCPCS",
    ),
    "Pulmonary Rehabilitation Authorization": _s(
        ["G0424", "94625", "94626"],
        system="CPT/HCPCS",
        notes="Pulmonary rehab sessions",
    ),
    "Retransplant Prior Authorization": _s(
        [],
        unresolved=True,
        notes="Organ-specific transplant CPT/DRG schedule required",
    ),
    "Sinus Surgery Prior Authorization": _s(
        ["31253", "31254", "31255", "31256", "31267", "31276", "31287", "31288"],
        notes="Endoscopic sinus surgery family",
    ),
    "Skilled Nursing Facility Authorization": _s(
        [],
        not_applicable=True,
        na_reason="SNF authorization uses RUG/PDPM / revenue — not CPT PA",
    ),
    "Sleep Surgery Prior Authorization": _s(
        ["42145", "21685", "42950"],
        notes="UPPP / hyoid / pharyngoplasty representative",
    ),
    "Speech Generating Device Prior Authorization": _s(
        ["E2500", "E2502", "E2504", "E2506", "E2508", "E2510"],
        system="HCPCS",
        notes="SGD device HCPCS",
    ),
    "Spinal Cord Stimulator Trial and Implant Prior Authorization": _s(
        ["63650", "63655", "63685"],
        notes="SCS percutaneous/laminectomy implant + generator",
    ),
    "Spinal Decompression Without Fusion Prior Authorization": _s(
        ["63030", "63042", "63047", "63056"],
        notes="Laminotomy / laminectomy decompression",
    ),
    "Spine Fusion Prior Authorization": _s(
        ["22551", "22558", "22612", "22630", "22633"],
        notes="Cervical/lumbar arthrodesis representative",
    ),
    "Spine Surgery Prior Authorization": _s(
        ["63030", "63047", "22612", "22633", "22842", "22853"],
        notes="Mixed decompression/fusion/instrumentation — prefer split policies when product-defined",
    ),
    "Structural Heart Procedure Prior Authorization": _s(
        ["33361", "33362", "33363", "33364", "33365", "33418", "33419"],
        notes="TAVR / mitral clip representative",
    ),
    "SUD Detoxification Authorization": _s(
        ["H0010", "H0011", "H0012"],
        system="HCPCS",
        notes="Alcohol/drug services detox HCPCS",
    ),
    "SUD Residential and IOP Authorization": _s(
        ["H0017", "H0018", "H0019", "H0015"],
        system="HCPCS",
        notes="SUD residential / IOP",
    ),
    "TMS Prior Authorization": _s(
        ["90867", "90868", "90869"], notes="Transcranial magnetic stimulation"
    ),
    "Tonsillectomy and Adenoidectomy Criteria": _s(
        ["42820", "42821", "42825", "42826", "42830", "42831"],
        notes="Tonsillectomy / adenoidectomy",
    ),
    "Transplant Evaluation and Listing Authorization": _s(
        [],
        unresolved=True,
        notes="Organ-specific evaluation CPT + center network rules UNRESOLVED",
    ),
    "UM Reduction for under age 45 and B1C": _s(
        [],
        unresolved=True,
        notes="Internal program label — scope/codes require product clarification; do not invent cohort rules",
    ),
    "UM Validation ": _s(
        [],
        unresolved=True,
        notes="Placeholder catalog name — schedule UNRESOLVED until product renames/defines policy",
    ),
    "Upper Endoscopy Frequency Criteria": _s(
        ["43235", "43239", "43249"], notes="EGD diagnostic / biopsy / dilation"
    ),
    "Value Prior Authorization Program": _s(
        [],
        not_applicable=True,
        na_reason="Program umbrella across services — constituent PA policies configured individually",
    ),
    "Freestanding Imaging Steerage": _s(
        ["72148", "72149", "72158", "70553", "71260"],
        notes="Imaging steerage anchors; Dec4 SOS fixture remains frozen separately",
    ),
    "Outpatient Therapy Coverage and Payment": _s(
        ["97110", "97112", "97140", "97530", "97161", "97162", "97163"],
        notes="Outpatient PT coverage/payment anchors",
    ),
    "Eating Disorder Level-of-Care Authorization": _s(
        ["H0017", "H0018", "H0019", "H0035", "S9480"],
        system="HCPCS",
        notes="Behavioral health LOC HCPCS anchors — full LOC criteria remain product-specific",
    ),
    "Varicose Vein Ablation Prior Authorization": _s(
        ["36475", "36476", "36478", "36479", "37765", "37766"],
        notes="Endovenous ablation / stab phlebectomy",
    ),
    "Vertebral Augmentation Prior Authorization": _s(
        ["22510", "22511", "22512", "22513", "22514", "22515"],
        notes="Vertebroplasty / kyphoplasty",
    ),
    # --- SITE OF CARE ---
    "Ambulatory Surgery Center Preference": _s(
        ["27447", "29827", "43239", "66984"],
        notes="Representative ASC-eligible elective procedures",
    ),
    "Home Sleep Apnea Testing Preference": _s(
        ["95800", "95801", "G0398", "G0399", "G0400"],
        system="CPT/HCPCS",
        notes="HSAT vs facility PSG preference",
    ),
    "Home Sleep Testing Before Facility PSG": _s(
        ["95800", "95801", "95810"], notes="HSAT before attended PSG pathway"
    ),
    "Infusion Site-of-Care Optimization": _s(
        ["96413", "96415", "96365", "96366"],
        notes="Chemo/infusion admin — site steerage; drug J-codes product-specific",
    ),
    "Oncology Infusion Site Steerage": _s(
        ["96413", "96415", "96417"], notes="Chemo IV infusion admin"
    ),
    "Specialty Infusion Site-of-Care Optimization": _s(
        ["96413", "96365"], notes="Specialty infusion admin; J-codes UNRESOLVED"
    ),
    "Urgent Care Preference Over Non-Emergent ER": _s(
        ["99281", "99282", "99283", "99284", "99285", "99213", "99214"],
        notes="ED E/M vs office/urgent care E/M comparison set",
    ),
    # --- THERAPY ---
    "Hyperbaric Oxygen Therapy Prior Authorization": _s(
        ["99183", "G0277"], system="CPT/HCPCS", notes="HBOT physician attendance / facility"
    ),
    "Negative Pressure Wound Therapy Prior Authorization": _s(
        ["97605", "97606", "97607", "97608"], notes="NPWT"
    ),
    "Proton Beam Therapy Coverage Criteria": _s(
        ["77520", "77522", "77523", "77525"], notes="Proton treatment delivery"
    ),
    "Radiation Therapy Modality Prior Authorization": _s(
        ["77427", "77385", "77386", "77301"],
        notes="Radiation treatment management / IMRT planning representative",
    ),
    "Speech Therapy Visit Limit": _s(
        ["92507", "92508", "92521", "92522", "92523", "92524"],
        notes="Speech-language treatment / evaluation",
    ),
    "PAP Therapy Initiation and Compliance": _s(
        ["E0601", "A7030", "A7034"], system="HCPCS", notes="PAP initiation supplies"
    ),
    # --- BENEFIT LIMITS ---
    "Acupuncture Visit Limit": _s(["97810", "97811", "97813", "97814"]),
    "Cardiac Rehabilitation Session Limit": _s(["93797", "93798"]),
    "Chiropractic Visit Limit": _s(["98940", "98941", "98942"]),
    "Occupational Therapy Annual Limit": _s(["97165", "97166", "97167", "97168", "97530", "97535"]),
    "Physical Therapy Visit Limit": _s(["97161", "97162", "97163", "97164", "97110", "97140"]),
    "Pulmonary Rehabilitation Session Limit": _s(["G0424", "94625", "94626"], system="CPT/HCPCS"),
    "Annual Maximum Benefit for Durable Medical Equipment": _s(
        [],
        not_applicable=True,
        na_reason="Benefit dollar cap — applies across DME HCPCS universe",
    ),
    # --- MEDICAL NECESSITY / COVERAGE ---
    "Cochlear Implant Prior Authorization": _s(
        ["69930", "L8614", "L8619"], system="CPT/HCPCS", notes="Cochlear implant surgery + device"
    ),
    "Coronary Calcium Scoring Coverage Criteria": _s(["75571"]),
    "Outpatient Advanced Imaging Medical Necessity Criteria": _s(
        ["70551", "70552", "70553", "72141", "72142", "72146", "72147", "72148", "72149", "72158", "73718", "73719", "73720", "73721", "73722", "73723"],
        notes="Common MRI MN set — distinct from lumbar-only MRI PA policy",
    ),
    "Remote Patient Monitoring Coverage Criteria": _s(
        ["99453", "99454", "99457", "99458"], notes="RPM setup/device/treatment"
    ),
}


# Non-code / payment / pharmacy / network / admin — honest NOT_APPLICABLE or HCPCS anchors
MORE: Dict[str, Schedule] = {
    # ADMINISTRATIVE — not CPT-driven
    **{
        n: _s([], not_applicable=True, na_reason="Administrative / regulatory process policy — not a procedure code schedule")
        for n in [
            "ACA Essential Health Benefits Mapping",
            "Away-From-Home Care / Guest Membership Rules",
            "BlueCard Home Plan Medical Policy Application",
            "BlueCard Host Plan Local Rules Application",
            "Continuity of Medications During Appeal",
            "Documentation Requirement for High-Cost Services",
            "External Review / IRO Process",
            "Medicaid EPSDT Coverage Obligation",
            "Medical Records Request Standards",
            "Member Appeal and Grievance Timelines",
            "Mental Health Parity Comparative Analysis Policy",
            "National Account Custom Benefit Administration",
            "No Surprises Act Emergency Services No-PA Rule",
            "North Carolina Mandated Benefit Administration",
            "Peer-to-Peer Review Opportunity Policy",
            "Prior Authorization Submission and Turnaround Standards",
            "Provider Reconsideration / Dispute Process",
            "Retrospective Authorization Window",
        ]
    },
    "Concurrent DUR Safety Edits": _s(
        [], not_applicable=True, na_reason="Pharmacy DUR edit — NDC/GCN product rules, not CPT"
    ),
    "Refill-Too-Soon Edit Policy": _s(
        [], not_applicable=True, na_reason="Pharmacy claim edit — days-supply/NDC, not CPT"
    ),
    # PROVIDER_NETWORK
    **{
        n: _s([], not_applicable=True, na_reason="Network / access / COE / referral rule — taxonomy/network IDs not CPT schedule")
        for n in [
            "Behavioral Health Appointment Access Standards",
            "Centers of Excellence Requirement — Bariatric",
            "Centers of Excellence Requirement — Complex Cancer",
            "Centers of Excellence Requirement — Transplant",
            "Continuity of Care After Provider Termination",
            "Maximum Wait Time for Specialist Appointments",
            "Nonparticipating Provider Exception Coverage Rules",
            "Out-of-Network Elective Services Restriction",
            "PCP Referral Requirement for Specialist Visits",
            "Preferred Dialysis Network Policy",
            "Provider Specialty Eligibility for High-Cost Codes",
            "Specialist Provider Eligibility for Specialty Services",
            "Telehealth Vendor Network Rules",
            "Tiered Network Restriction for High-Cost Procedures",
        ]
    },
    # PAYMENT — mechanism params; avoid inventing contracted rates; use service anchors where useful
    "Multiple Procedure Payment Reduction": _s(
        [], unresolved=True, notes="Frozen Dec4 MPPR KA may use empty product codeset; mechanical fixture preserved"
    ),
    "Multiple Procedure Payment Reduction (MPPR)": _s(
        [], unresolved=True, notes="Frozen Dec4 MPPR; mechanical KA"
    ),
    "Assistant Surgeon Payment Rules": _s(
        ["80", "81", "82", "AS"], system="MODIFIER", notes="Assistant surgeon modifiers — % reduction is Representative design not contracted rate"
    ),
    "Bundled Payment for Joint Replacement": _s(
        ["27130", "27447"], notes="THA/TKA episode anchors — episode price UNRESOLVED (no invented rate)"
    ),
    "Total Joint Replacement Episode Bundled Payment": _s(
        ["27130", "27447"], notes="Episode anchors; bundled price UNRESOLVED"
    ),
    "Cardiac Episode Bundle": _s(
        ["33533", "92928", "93458"], notes="CABG/PCI/cath anchors — episode price UNRESOLVED"
    ),
    "Maternity Episode Bundle": _s(
        ["59400", "59510"], notes="Global OB anchors — episode price UNRESOLVED"
    ),
    "DRG Inpatient Payment Policy": _s(
        [], not_applicable=True, na_reason="DRG/MS-DRG grouper methodology — not outpatient CPT schedule"
    ),
    "Hospital-Acquired Condition Nonpayment": _s(
        [], not_applicable=True, na_reason="HAC/POA inpatient payment adjustment — ICD/POA driven"
    ),
    "Related Readmission Payment Adjustment": _s(
        [], not_applicable=True, na_reason="Readmission payment rule — claim/DRG timing, not CPT PA"
    ),
    "Coordination of Benefits Administration": _s(
        [], not_applicable=True, na_reason="COB adjudication process"
    ),
    "Third-Party Liability and Subrogation": _s(
        [], not_applicable=True, na_reason="TPL/subrogation process"
    ),
    "Timely Filing Limit — Provider Claims": _s(
        [], not_applicable=True, na_reason="Claim filing deadline policy"
    ),
    "ACA Preventive Services Zero Cost Share": _s(
        ["99385", "99386", "99395", "99396", "G0438", "G0439"],
        system="CPT/HCPCS",
        notes="Representative preventive visit anchors — USPSTF full schedule product-specific",
    ),
    "Advanced Imaging Member Cost Share Design": _s(
        ["70553", "72148", "71260"], notes="Imaging cost-share design anchors — copay amounts UNRESOLVED product terms"
    ),
    "Emergency vs Urgent Care Cost Share Differential": _s(
        ["99283", "99284", "99285", "99213", "99214"], notes="ED vs UC E/M anchors — dollar differentials UNRESOLVED"
    ),
    "Urgent Care Copay Increase": _s(
        ["99213", "99214"], notes="UC E/M anchors — copay amount is Representative design parameter UNRESOLVED numeric"
    ),
    "Telehealth Cost Sharing Parity": _s(
        ["99213", "99214", "99441", "99442", "99443"], notes="Telehealth E/M parity anchors"
    ),
    "Telehealth Cost Sharing Parity Policy": _s(
        ["99213", "99214", "99441", "99442", "99443"], notes="Telehealth E/M parity anchors"
    ),
    "Facility Fee Schedule and Bundled Payment Adjustments": _s(
        [], unresolved=True, notes="Fee schedule tables proprietary/product — do not invent rates"
    ),
    "Preferred Generic Drug Tier": _s(
        [], not_applicable=True, na_reason="Formulary tier design — NDC/GCN not CPT"
    ),
    "Primary Care Shared Savings Quality Incentive Program": _s(
        [], not_applicable=True, na_reason="VBP incentive program — attribution/quality metrics"
    ),
    "Value-Based Insurance Design Waivers": _s(
        [], not_applicable=True, na_reason="VBID benefit design waivers"
    ),
    # PHARMACY — HCPCS J-code class anchors where public; NDC lists remain UNRESOLVED
    "ADHD Stimulant Quantity Limits and Preferred Agents": _s(
        [], unresolved=True, notes="NDC/preferred agent list required — not inventing product NDCs"
    ),
    "Benzodiazepine Quantity Limits": _s(
        [], unresolved=True, notes="NDC quantity limits — product list UNRESOLVED"
    ),
    "Opioid Quantity Limit - Chronic Pain": _s(
        [], unresolved=True, notes="MME/NDC schedule UNRESOLVED — do not invent MME thresholds as verified"
    ),
    "Opioid Quantity Limit — Acute Pain": _s(
        [], unresolved=True, notes="Acute opioid days-supply product rule UNRESOLVED"
    ),
    "Opioid Quantity Limit — Chronic Pain": _s(
        [], unresolved=True, notes="Chronic opioid MME/NDC UNRESOLVED"
    ),
    "Biologic Step Therapy for Rheumatoid Arthritis": _s(
        ["J0135", "J1438", "J3262", "J9312"], system="HCPCS", notes="RA biologic J-code class anchors — step order is Representative design"
    ),
    "Rheumatology Biologic Step Therapy for RA": _s(
        ["J0135", "J1438", "J3262", "J9312"], system="HCPCS", notes="RA biologic J-code anchors"
    ),
    "Dermatology Biologic Step Therapy": _s(
        ["J3357", "J0717"], system="HCPCS", notes="Derm biologic J-code anchors (partial)"
    ),
    "IBD Biologic Step Therapy": _s(
        ["J1745", "J0717"], system="HCPCS", notes="IBD biologic J-code anchors"
    ),
    "Asthma and COPD Biologic Step Therapy": _s(
        ["J2182", "J2356", "J0517"], system="HCPCS", notes="Respiratory biologic J-code anchors"
    ),
    "Migraine CGRP Step Therapy": _s(
        ["J3032", "J3031"], system="HCPCS", notes="CGRP antagonist injection HCPCS anchors"
    ),
    "PCSK9 Inhibitor Step Therapy": _s(
        ["J3490"], system="HCPCS", notes="PCSK9 often billed J3490/NDC — product NDCs UNRESOLVED"
    ),
    "GLP-1 Coverage Criteria for Obesity": _s(
        ["J3490"], system="HCPCS", notes="GLP-1 obesity products — specific NDCs UNRESOLVED; class PA only"
    ),
    "GLP-1 Step Therapy for Type 2 Diabetes": _s(
        ["J3490"], system="HCPCS", notes="GLP-1 diabetes — NDCs UNRESOLVED"
    ),
    "Insulin Preferred Product and Biosimilar Step": _s(
        ["J1815", "J1817"], system="HCPCS", notes="Insulin injection HCPCS — preferred NDC list UNRESOLVED"
    ),
    "CGM and Diabetes Supply Quantity Limits": _s(
        ["A9276", "A9277", "A9278", "K0553", "K0554"], system="HCPCS", notes="CGM supply HCPCS"
    ),
    "Blood Glucose Test Strip Step Therapy": _s(
        ["A4253"], system="HCPCS", notes="Blood glucose test strips"
    ),
    "Biosimilar Preferencing Policy": _s(
        [], not_applicable=True, na_reason="Preferencing rule across biologic classes — per-product NDC mapping UNRESOLVED"
    ),
    "Commercial Preferred Drug Formulary Design": _s(
        [], not_applicable=True, na_reason="Formulary design document — not a CPT/HCPCS schedule"
    ),
    "HIV Antiretroviral Formulary Management": _s(
        [], unresolved=True, notes="ARV NDC formulary UNRESOLVED — do not invent"
    ),
    "Oncology Immunotherapy Step Therapy": _s(
        ["J9271", "J9299", "J9228"], system="HCPCS", notes="Checkpoint inhibitor J-code anchors (partial)"
    ),
    "Non-Formulary Exception Review": _s(
        [], not_applicable=True, na_reason="Exception process — applies to non-formulary NDCs generally"
    ),
    "Pharmacy Prior Authorization Program": _s(
        [], not_applicable=True, na_reason="Program umbrella — constituent drug lists product-specific"
    ),
    "Preferred Pharmacy Network Policy": _s(
        [], not_applicable=True, na_reason="Pharmacy network rule"
    ),
    "Specialty Pharmacy Exclusive Network": _s(
        [], not_applicable=True, na_reason="Specialty pharmacy network rule"
    ),
    "Specialty Pharmacy Coinsurance Design": _s(
        [], not_applicable=True, na_reason="Benefit coinsurance design"
    ),
    "Specialty Drug Days’ Supply Limits": _s(
        [], unresolved=True, notes="Specialty NDC days-supply list UNRESOLVED"
    ),
    "Specialty Drug Site-of-Administration Management": _s(
        ["96413", "96365"], notes="Admin codes for site channeling; drug J-codes product-specific"
    ),
    "Medical vs Pharmacy Benefit Channeling": _s(
        [], not_applicable=True, na_reason="Benefit channel rule across medical/pharmacy"
    ),
    "Split-Fill Specialty Program": _s(
        [], not_applicable=True, na_reason="Specialty fill program rule"
    ),
    "Durable Medical Equipment Quantity Limits": _s(
        ["E0601", "E0431", "K0001"], system="HCPCS", notes="Representative DME quantity-limit anchors"
    ),
    # MEDICAL NECESSITY / coverage exclusions
    "Cosmetic Services Exclusion": _s(
        ["15820", "15821", "15822", "15823", "19318", "30400"], notes="Common cosmetic CPT anchors for exclusion testing"
    ),
    "Cosmetic Surgery Exclusion Policy": _s(
        ["15820", "15821", "19318", "30400"], notes="Cosmetic exclusion anchors"
    ),
    "Convenience Care Exclusion": _s(
        [], not_applicable=True, na_reason="Benefit exclusion category — service list product-specific"
    ),
    "Custodial Care Exclusion": _s(
        [], not_applicable=True, na_reason="Custodial vs skilled determination — not fixed CPT"
    ),
    "Surrogacy Exclusion Policy": _s(
        [], not_applicable=True, na_reason="Benefit exclusion"
    ),
    "Direct-to-Consumer Lab Noncoverage": _s(
        ["80053", "80061", "85025"], notes="Common lab panels for DTC noncoverage illustration"
    ),
    "Interventional Pain Regenerative Injection Noncoverage": _s(
        ["0232T", "0481T"], notes="PRP / regenerative investigational codes"
    ),
    "Orthobiologics and PRP Noncoverage": _s(
        ["0232T"], notes="PRP noncoverage anchor"
    ),
    "Experimental and Investigational Exclusion Framework": _s(
        [], not_applicable=True, na_reason="Framework policy — applies across investigational determinations"
    ),
    "Experimental and Investigational Services Policy": _s(
        [], not_applicable=True, na_reason="Framework E&I policy"
    ),
    "Experimental Treatment Coverage Exclusion": _s(
        [], not_applicable=True, na_reason="E&I exclusion framework"
    ),
    "Emerging Treatment Experimental Investigational Exclusion": _s(
        [], not_applicable=True, na_reason="E&I exclusion framework"
    ),
    "ACA Preventive Screening Coverage Requirements": _s(
        ["77067", "G0101", "G0121", "45378", "71271"], system="CPT/HCPCS", notes="Preventive screening anchors"
    ),
    "Hearing Aid Benefit and Replacement Cycle": _s(
        ["V5010", "V5011", "V5014", "V5254", "V5255", "V5256", "V5257"], system="HCPCS", notes="Hearing aid HCPCS"
    ),
    "Hearing Aid Coverage Criteria": _s(
        ["V5010", "V5254", "V5255", "V5256", "V5257"], system="HCPCS", notes="Hearing aid HCPCS"
    ),
    "Audio-Only Telehealth Coverage Rules": _s(
        ["99441", "99442", "99443"], notes="Telephone E/M"
    ),
    "Store-and-Forward Teledermatology Coverage": _s(
        ["G2010", "99451", "99452"], system="CPT/HCPCS", notes="Store-and-forward / e-consult"
    ),
    "Telehealth Covered Services List": _s(
        ["99213", "99214", "99441", "99442", "99443", "90832", "90834"], notes="Representative telehealth-covered E/M + psychotherapy"
    ),
    "Digital Therapeutics Coverage Criteria": _s(
        [], unresolved=True, notes="DTx HCPCS/NDC product list UNRESOLVED"
    ),
    "Behavioral Health Inpatient Concurrent Review": _s(
        [], not_applicable=True, na_reason="Inpatient BH concurrent review — revenue/LOC"
    ),
    "Inpatient Concurrent Stay Review": _s(
        [], not_applicable=True, na_reason="Inpatient concurrent review"
    ),
    "Inpatient vs Observation Status Determination": _s(
        [], not_applicable=True, na_reason="Status determination — not outpatient CPT PA"
    ),
    "NICU Concurrent Review": _s(
        [], not_applicable=True, na_reason="NICU concurrent review"
    ),
    "Discharge Planning Requirements": _s(
        [], not_applicable=True, na_reason="Discharge planning process"
    ),
    "Readmission Relatedness Review": _s(
        [], not_applicable=True, na_reason="Readmission relatedness review process"
    ),
    "Out-of-Network Inpatient Authorization": _s(
        [], not_applicable=True, na_reason="OON inpatient auth — facility/DRG driven"
    ),
    "MCG Clinical Criteria for Inpatient Admissions": _s(
        [], unresolved=True, notes="Licensed MCG content not redistributed — criteria UNRESOLVED"
    ),
    "MCG-Style Clinical Criteria for Inpatient Admissions": _s(
        [], unresolved=True, notes="Illustrative label only — do not invent MCG criteria"
    ),
    "Medical Eye Disease vs Routine Vision Separation": _s(
        ["92002", "92004", "92012", "92014", "92250"], notes="Ophthalmology medical eye exam anchors vs routine vision"
    ),
    "Vision Hardware vs Medical Eye Disease": _s(
        ["V2020", "V2100", "92004", "92014"], system="CPT/HCPCS", notes="Vision hardware vs medical eye"
    ),
    "Medical-Dental Crossover Trauma Policy": _s(
        ["41899", "D7140"], system="CPT/CDT", notes="Dental trauma crossover anchors"
    ),
    "Medication-Assisted Treatment Access Policy": _s(
        ["H0020", "J0571", "J0572", "J0573", "J0574", "J0575"], system="HCPCS", notes="MAT dosing/admin anchors"
    ),
    "Oncology-Related Dental Clearance Coverage": _s(
        ["D0150", "D0180"], system="CDT", notes="Dental clearance before oncology therapy"
    ),
    # SITE OF CARE remaining
    "Dialysis Home Modality Preference": _s(
        ["90966", "90965", "90945", "90947"], notes="Home/facility dialysis"
    ),
    "Home Health Care Preference": _s(
        ["G0151", "G0152", "G0299"], system="HCPCS", notes="Home health preference anchors"
    ),
    "Home Infusion Preference": _s(
        ["96413", "96365"], notes="Infusion admin — prefer home when clinically appropriate"
    ),
    "Preferred Laboratory Network Steerage": _s(
        ["80053", "80061", "85025"], notes="Common lab panels for network steerage"
    ),
    "SNF and Home Health Authorization Coverage Rules": _s(
        [], not_applicable=True, na_reason="Post-acute auth coverage rules — LOC/revenue"
    ),
    "Tiered Network Specialist Steerage": _s(
        [], not_applicable=True, na_reason="Network tier steerage"
    ),
    # COMPOSITE / programs
    **{
        n: _s([], not_applicable=True, na_reason="Program/composite policy — constituent mechanisms configured separately")
        for n in [
            "Advanced Imaging Comprehensive Control",
            "Advanced Imaging Control Bundle",
            "Cardiac Imaging Comprehensive Control",
            "CKD Disease Management Program",
            "Complex Case Management Program",
            "COPD Disease Management Program",
            "Diabetes Disease Management Program",
            "Elective Surgery Comprehensive Management",
            "Emergency Department Frequent Utilizer Program",
            "Heart Failure Disease Management Program",
            "Maternity Management Program",
            "Medicare Stars Gap Closure Program",
            "Medication Therapy Management Program",
            "Opioid Analgesic Utilization Management",
            "Specialty Drug Comprehensive Management",
            "Transition of Care Post-Discharge Program",
        ]
    },
    # CODING
    "Modifier and Code-Bundling Claim Edit Policy": _s(
        ["59", "XE", "XP", "XS", "XU", "25", "NCCI"], system="MODIFIER", notes="Bundling/modifier edit semantics — NCCI tables versioned externally"
    ),
    "NCCI and MUE Claims Edit Policy": _s(
        [], unresolved=True, notes="Authoritative NCCI/MUE files required — do not invent MUE values"
    ),
    "Unbundling and Incidental Denial Policy": _s(
        [], unresolved=True, notes="Requires versioned edit pairs — UNRESOLVED without source file"
    ),
    # THERAPY remaining
    "CAR-T and Cellular Therapy Prior Authorization": _s(
        ["Q2041", "Q2042", "Q2053", "Q2054", "Q2055", "Q2056"], system="HCPCS", notes="CAR-T product HCPCS anchors"
    ),
    "Gene Therapy One-Time High-Cost Prior Authorization": _s(
        ["J3399", "J3398"], system="HCPCS", notes="Gene therapy HCPCS anchors (partial)"
    ),
    "MS Disease-Modifying Therapy Prior Authorization": _s(
        ["J2323", "J2350", "J1595"], system="HCPCS", notes="MS DMT injection anchors"
    ),
    # BENEFIT remaining
    "90-Day Retail Maintenance Program": _s(
        [], not_applicable=True, na_reason="Retail pharmacy days-supply program"
    ),
    "Mandatory Mail-Order Maintenance Medications": _s(
        [], not_applicable=True, na_reason="Mail-order channel rule"
    ),
    "Preferred Generic Drug Tier Design": _s(
        [], not_applicable=True, na_reason="Formulary tier design"
    ),
    "Specialty Tier Coinsurance Design": _s(
        [], not_applicable=True, na_reason="Benefit coinsurance design"
    ),
    # TELEHEALTH / PATHWAY / MEDICARE
    "Virtual Visit Eligibility and Reimbursement Rules": _s(
        ["99213", "99214", "99441", "99442", "99443"], notes="Virtual visit E/M"
    ),
    "Oncology Evidence-Based Clinical Pathway": _s(
        [], unresolved=True, notes="Pathway content licensed/product-specific UNRESOLVED"
    ),
    "Provider Network Change Continuity of Care Coverage": _s(
        [], not_applicable=True, na_reason="Continuity of care coverage rule"
    ),
    "Medicare NCD and LCD Precedence Policy": _s(
        [], not_applicable=True, na_reason="Precedence framework across NCD/LCD — not a single code schedule"
    ),
}


def lookup(policy_name: str) -> Schedule:
    key = policy_name.strip()
    if key in EXACT:
        return EXACT[key]
    if key in MORE:
        return MORE[key]
    if policy_name in EXACT:
        return EXACT[policy_name]
    if policy_name in MORE:
        return MORE[policy_name]
    return _s(
        [],
        unresolved=True,
        notes="No representative schedule authored yet for this catalog name",
    )


def coverage_stats(names: List[str]) -> Dict[str, int]:
    resolved = unresolved = na = 0
    for n in names:
        s = lookup(n)
        if s["not_applicable"]:
            na += 1
        elif s["unresolved"]:
            unresolved += 1
        else:
            resolved += 1
    return {
        "total": len(names),
        "representative_codes_ready": resolved,
        "unresolved": unresolved,
        "not_applicable": na,
    }
