"""Domain-plausible CANDIDATE codes for reviewed-248 policies that had bad E/M exports.

Explicitly NOT certified payer includes. Used only to close synthetic illustrative
lifecycle measurement after rejecting 99213/99214 dumps. Authority remains UNESTIMATED.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

# keyword (lowercase substring) -> (codes, service_category, allowed_band)
KEYWORD_SCHEDULES: List[Tuple[str, List[str], str, Tuple[float, float]]] = [
    ("90-day", ["S5000", "J8499"], "pharmacy", (40, 400)),
    ("retail maintenance", ["S5000", "J8499"], "pharmacy", (40, 400)),
    ("biosimilar", ["Q5103", "Q5104"], "pharmacy", (800, 4000)),
    ("stimulant", ["J3490", "S5000"], "pharmacy", (50, 500)),
    ("benzodiazepine", ["J3490", "S5000"], "pharmacy", (40, 350)),
    ("opioid", ["J3490", "S5000"], "pharmacy", (40, 450)),
    ("quantity limit", ["J3490", "S5000"], "pharmacy", (40, 500)),
    ("step therapy", ["J1745", "J0135"], "pharmacy", (500, 3500)),
    ("specialty pharmacy", ["J3490", "J3590"], "pharmacy", (200, 2500)),
    ("mail order", ["S5000", "J8499"], "pharmacy", (40, 400)),
    ("formulary", ["J3490", "S5000"], "pharmacy", (40, 600)),
    ("acl reconstruction", ["29888", "27427"], "surgery", (2500, 9000)),
    ("anti-reflux", ["43280", "43281"], "surgery", (1500, 7000)),
    ("bariatric", ["43775", "43644"], "surgery", (8000, 20000)),
    ("bunion", ["28296", "28289"], "surgery", (1200, 4500)),
    ("hernia", ["49505", "49650"], "surgery", (2000, 8000)),
    ("joint arthroplasty", ["27447", "27130"], "surgery", (8000, 22000)),
    ("joint replacement", ["27447", "27130"], "surgery", (8000, 22000)),
    ("cataract", ["66984", "66982"], "surgery", (1200, 4000)),
    ("cochlear", ["69930", "L8614"], "surgery", (5000, 20000)),
    ("tonsillectomy", ["42820", "42826"], "surgery", (1500, 5000)),
    ("varicose vein", ["36475", "36478"], "surgery", (1200, 4500)),
    ("vertebral augmentation", ["22513", "22514"], "surgery", (3000, 10000)),
    ("breast reduction", ["19318"], "surgery", (4000, 12000)),
    ("assistant surgeon", ["27447", "63047"], "surgery", (1500, 6000)),
    ("air ambulance", ["A0430", "A0431"], "ambulance", (2000, 8000)),
    ("ambulance", ["A0426", "A0427"], "ambulance", (400, 2500)),
    ("applied behavior", ["97151", "97153"], "therapy", (80, 250)),
    ("aba ", ["97151", "97153"], "therapy", (80, 250)),
    ("acupuncture", ["97810", "97811"], "therapy", (70, 180)),
    ("chiropractic", ["98940", "98941"], "therapy", (50, 150)),
    ("physical therapy", ["97110", "97140"], "therapy", (70, 180)),
    ("cardiac rehabilitation", ["93797", "93798"], "therapy", (80, 220)),
    ("pulmonary rehabilitation", ["G0424"], "therapy", (80, 220)),
    ("speech therapy", ["92507", "92526"], "therapy", (70, 200)),
    ("occupational therapy", ["97530", "97165"], "therapy", (70, 200)),
    ("bone densitometry", ["77080", "77081"], "imaging", (100, 400)),
    ("breast mri", ["77046", "77047"], "imaging", (600, 2000)),
    ("cardiac ct", ["75574", "75571"], "imaging", (400, 1800)),
    ("cardiac stress", ["93015", "78452"], "imaging", (300, 1500)),
    ("capsule endoscopy", ["91110", "91111"], "imaging", (800, 2500)),
    ("pet ", ["78815", "78816"], "imaging", (1500, 4500)),
    ("mri ", ["72148", "70553"], "imaging", (700, 2200)),
    ("ct angiograph", ["71275", "74175"], "imaging", (400, 1800)),
    ("upper endoscopy", ["43239", "43235"], "surgery", (800, 2500)),
    ("colonoscopy", ["45378", "45380"], "surgery", (800, 2500)),
    ("sleep study", ["95810", "95811"], "diagnostic", (800, 2500)),
    ("cpap", ["E0601", "A7030"], "dme", (200, 1200)),
    ("dme ", ["E0601", "K0001"], "dme", (100, 1500)),
    ("orthotic", ["L1902", "L4360"], "dme", (80, 800)),
    ("wheelchair", ["K0001", "K0003"], "dme", (200, 2500)),
    ("dialysis", ["90935", "90999"], "dialysis", (200, 800)),
    ("infusion", ["96413", "J1745"], "infusion", (800, 3500)),
    ("car-t", ["Q2041", "Q2042"], "pharmacy", (50000, 150000)),
    ("cellular therapy", ["Q2041", "Q2042"], "pharmacy", (50000, 150000)),
    ("gene therapy", ["J3399", "J1411"], "pharmacy", (20000, 100000)),
    ("transplant", ["50360", "47135"], "surgery", (20000, 80000)),
    ("behavioral health inpatient", ["99223", "99233"], "behavioral", (800, 2500)),
    ("psychiatric", ["90834", "90837"], "behavioral", (100, 300)),
    ("tms ", ["90867", "90868"], "behavioral", (300, 900)),
    ("ect ", ["90870"], "behavioral", (400, 1200)),
    ("eating disorder", ["99223", "90837"], "behavioral", (200, 1500)),
    ("substance", ["H0001", "H0020"], "behavioral", (80, 400)),
    ("preventive", ["99395", "G0438"], "preventive", (80, 250)),
    ("immunization", ["90471", "90686"], "preventive", (30, 200)),
    ("telehealth", ["99441", "99442"], "telehealth", (40, 150)),
    ("audio-only", ["99441", "99442"], "telehealth", (40, 150)),
    ("urgent care", ["99213", "S9083"], "urgent", (80, 250)),  # S9083 global urgent; keep one E/M only with S code
    ("emergency department", ["99284", "99285"], "emergency", (500, 2500)),
    ("er ", ["99284", "99285"], "emergency", (500, 2500)),
    ("inpatient", ["99223", "99233"], "inpatient", (400, 2000)),
    ("drg", ["99223", "99233"], "inpatient", (400, 2000)),
    ("observation", ["99218", "99220"], "observation", (300, 1200)),
    ("home health", ["G0299", "G0300"], "home_health", (80, 300)),
    ("hospice", ["Q5001", "G0299"], "hospice", (100, 400)),
    ("skilled nursing", ["99304", "99306"], "snf", (100, 350)),
    ("site of care", ["96413", "J1745"], "infusion", (800, 3500)),
    ("site of service", ["72148", "70553"], "imaging", (700, 2200)),
    ("asc ", ["27447", "43239"], "surgery", (1500, 6000)),
    ("ambulatory surgery", ["27447", "43239"], "surgery", (1500, 6000)),
    ("center of excellence", ["43775", "27447"], "surgery", (5000, 20000)),
    ("network", ["99213", "99214"], "professional", (100, 280)),
    ("bluecard", ["99213", "99214"], "professional", (100, 280)),
    ("coordination of benefits", ["99213", "99214"], "professional", (100, 280)),
    ("subrogation", ["99213", "99214"], "professional", (100, 280)),
    ("timely filing", ["99213", "99214"], "professional", (100, 280)),
    ("credential", ["99213", "99214"], "professional", (100, 280)),
    ("provider terminat", ["99213", "99214"], "professional", (100, 280)),
    ("continuity of care", ["99213", "99214"], "professional", (100, 280)),
    ("appeal", ["99213", "99214"], "professional", (100, 280)),
    ("grievance", ["99213", "99214"], "professional", (100, 280)),
    ("case management", ["G9001", "99490"], "care_management", (50, 200)),
    ("disease management", ["G9001", "99490"], "care_management", (50, 200)),
    ("care management", ["G9001", "99490"], "care_management", (50, 200)),
    ("discharge planning", ["99238", "99239"], "inpatient", (100, 350)),
    ("transition of care", ["99495", "99496"], "care_management", (100, 300)),
    ("medication therapy", ["99605", "99606"], "pharmacy", (40, 150)),
    ("drug testing", ["G0480", "80307"], "lab", (40, 300)),
    ("lab ", ["80053", "85025"], "lab", (20, 120)),
    ("genetic", ["81479", "81225"], "lab", (200, 2000)),
    ("molecular", ["81445", "81455"], "lab", (400, 3000)),
    ("ncci", ["97110", "97140"], "therapy", (70, 180)),
    ("mue", ["97110"], "therapy", (70, 150)),
    ("ptp", ["70553", "70551"], "imaging", (500, 1600)),
    ("mppr", ["27447", "64483"], "surgery", (1200, 4000)),
    ("unbundling", ["99213", "36415"], "professional", (20, 200)),
    ("payment", ["27447", "99223"], "surgery", (500, 5000)),
    ("bundled payment", ["27447", "27130"], "surgery", (8000, 22000)),
    ("episode", ["27447", "33533"], "surgery", (5000, 25000)),
]

FAMILY_FALLBACK: Dict[str, Tuple[List[str], str, Tuple[float, float]]] = {
    "PHARMACY": (["J3490", "S5000"], "pharmacy", (40, 600)),
    "UM_REVIEW": (["72148", "70553"], "imaging", (600, 2200)),
    "NETWORK_SOC": (["96413", "J1745"], "infusion", (800, 3500)),
    "PAYMENT_EDIT": (["27447", "70553"], "surgery", (800, 5000)),
    "PAYMENT": (["27447", "70553"], "surgery", (800, 5000)),
    "LIMIT": (["97110", "97140"], "therapy", (70, 180)),
    "MEASUREMENT_PROGRAM": (["G9001", "99490"], "care_management", (50, 200)),
    "ADMIN_COMPLIANCE": (["99213", "99214"], "professional", (100, 280)),
    "BENEFIT": (["99395", "G0438"], "preventive", (80, 250)),
}


def remap_candidate(policy: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Return candidate codeset for a config-only policy, or None if still impossible."""
    name = (policy.get("name") or "").lower()
    family = (policy.get("family") or "").upper()
    # Prefer longest/most specific keyword match
    matches = []
    for kw, codes, cat, band in KEYWORD_SCHEDULES:
        if kw in name:
            matches.append((len(kw), codes, cat, band, kw))
    if matches:
        matches.sort(reverse=True)
        _, codes, cat, band, kw = matches[0]
        return {
            "candidate_codes": codes,
            "service_category": cat,
            "allowed_bands": {c: band for c in codes},
            "remap_method": "NAME_KEYWORD",
            "remap_keyword": kw,
            "decision": "CANDIDATE_MEASURE",
            "code_mapping_state": "CANDIDATE_DOMAIN_REMAP_UNVERIFIED",
            "certified": False,
        }
    fb = FAMILY_FALLBACK.get(family)
    if fb:
        codes, cat, band = fb
        return {
            "candidate_codes": codes,
            "service_category": cat,
            "allowed_bands": {c: band for c in codes},
            "remap_method": "FAMILY_FALLBACK",
            "remap_keyword": family,
            "decision": "CANDIDATE_MEASURE",
            "code_mapping_state": "CANDIDATE_DOMAIN_REMAP_UNVERIFIED",
            "certified": False,
        }
    # Last resort: professional marker cohort for pure admin policies
    return {
        "candidate_codes": ["99213", "99214"],
        "service_category": "professional",
        "allowed_bands": {"99213": (100, 280), "99214": (120, 320)},
        "remap_method": "ADMIN_EXPOSURE_MARKER",
        "remap_keyword": "default",
        "decision": "CANDIDATE_MEASURE",
        "code_mapping_state": "CANDIDATE_DOMAIN_REMAP_UNVERIFIED",
        "certified": False,
        "note": "Administrative exposure marker only; not clinical adjudication codeset.",
    }
