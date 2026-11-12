"""Application engines versus the independent oracle on generated lines."""

from uepi_api.services.expansion_demo_scenarios import (
    INFUSION_KNOWN,
    MUE_KNOWN_LINES,
    PTP_KNOWN_LINES,
    THERAPY_KNOWN,
    apply_infusion_soc,
    apply_ncci_mue,
    apply_ncci_ptp,
    apply_therapy_coverage,
)
from uepi_api.services.reimbursement_mppr import KNOWN_ANSWER_LINES as MPPR_LINES
from uepi_api.services.reimbursement_mppr import apply_mppr
from uepi_api.services.reimbursement_sos import KNOWN_ANSWER_LINES as SOS_LINES
from uepi_api.services.reimbursement_sos import apply_sos
from uepi_api.services.synthetic_population import simulate_payment_population
from uepi_common.synthetic_payer.generate import generate_events, generate_population
from uepi_common.synthetic_payer.oracle import (
    oracle_infusion,
    oracle_infusion_by_claim,
    oracle_mppr,
    oracle_mue,
    oracle_ptp,
    oracle_sos,
    oracle_therapy,
)
from uepi_common.synthetic_payer.pilot import run_pilot


def _same_money(engine: dict, oracle: dict) -> None:
    totals = engine["totals"]
    assert abs(totals["baseline_paid"] - oracle["baseline_paid"]) < 0.02
    assert abs(totals["post_policy_paid"] - oracle["post_policy_paid"]) < 0.02
    assert abs(totals["payment_impact"] - oracle["payment_impact"]) < 0.02


def test_fixture_engines_match_the_independent_oracle():
    _same_money(apply_mppr(MPPR_LINES), oracle_mppr(MPPR_LINES))
    _same_money(apply_sos(SOS_LINES), oracle_sos(SOS_LINES))
    _same_money(apply_ncci_ptp(PTP_KNOWN_LINES), oracle_ptp(PTP_KNOWN_LINES))
    _same_money(apply_ncci_mue(MUE_KNOWN_LINES), oracle_mue(MUE_KNOWN_LINES))
    _same_money(apply_therapy_coverage(THERAPY_KNOWN), oracle_therapy(THERAPY_KNOWN))
    _same_money(apply_infusion_soc(INFUSION_KNOWN), oracle_infusion(INFUSION_KNOWN))


def test_generated_population_matches_engines_and_stays_synthetic():
    population = generate_population(300, seed=20261106)
    lines = generate_events(population, seed=20261106)
    engines = simulate_payment_population(lines)
    oracle = {
        "mppr_favorable": oracle_mppr([row for row in lines if row["policy_key"] == "mppr"], 0.5),
        "sos_policy": oracle_sos([row for row in lines if row["policy_key"] == "sos"], 0.8),
        "sos_neutral": oracle_sos([row for row in lines if row["policy_key"] == "sos"], 1.0),
        "sos_adverse": oracle_sos([row for row in lines if row["policy_key"] == "sos"], 1.1),
        "ptp": oracle_ptp([row for row in lines if row["policy_key"] == "ptp"]),
        "mue": oracle_mue([row for row in lines if row["policy_key"] == "mue"]),
        "therapy": oracle_therapy([row for row in lines if row["policy_key"] == "therapy"]),
        "infusion": oracle_infusion_by_claim([row for row in lines if row["policy_key"] == "infusion"]),
    }
    for key, expected in oracle.items():
        _same_money(engines[key], expected)
        assert engines[key]["catalog_class"] == "DEMO_SYNTHETIC"
    assert engines["sos_neutral"]["totals"]["payment_impact"] == 0
    assert engines["sos_adverse"]["totals"]["payment_impact"] < 0
    report = run_pilot(300, seed=20261106)
    assert report["status"] == "PASS"
