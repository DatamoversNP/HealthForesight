"""Derive provider archetypes and patient segments from canonical claims (demo / stored baselines)."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Union
from uuid import UUID

import numpy as np
import pandas as pd


def provider_archetypes_from_claims_df(df: pd.DataFrame, max_archetypes: int = 8) -> List[Dict[str, Any]]:
    """Group providers by dominant service category; shape matches BaselineAnalysis ProviderArchetype."""
    if df is None or df.empty or "provider_id" not in df.columns:
        return []

    def _dom_cat(s: pd.Series) -> str:
        s2 = s.dropna().astype(str)
        if s2.empty:
            return "OTHER"
        m = s2.mode()
        return str(m.iloc[0]) if len(m) else "OTHER"

    cnt_col = "member_id" if "member_id" in df.columns else "provider_id"
    prov = df.groupby("provider_id", as_index=False).agg(claims=(cnt_col, "count"))
    if "allowed_amount" in df.columns:
        al = df.groupby("provider_id", as_index=False)["allowed_amount"].sum()
        prov = prov.merge(al, on="provider_id", how="left")
        prov["allowed"] = prov["allowed_amount"].fillna(0.0)
        prov = prov.drop(columns=["allowed_amount"])
    else:
        prov["allowed"] = 0.0
    if "service_category" in df.columns:
        cats = df.groupby("provider_id")["service_category"].apply(_dom_cat).reset_index(name="cat")
        prov = prov.merge(cats, on="provider_id", how="left")
    else:
        prov["cat"] = "GENERAL"

    g2 = (
        prov.groupby("cat", as_index=False)
        .agg(provider_count=("provider_id", "count"), total_claims=("claims", "sum"), total_allowed=("allowed", "sum"))
        .sort_values("total_claims", ascending=False)
        .head(max_archetypes)
    )

    out: List[Dict[str, Any]] = []
    for idx, row in g2.iterrows():
        cat = str(row["cat"])
        sub = prov[prov["cat"] == cat].nlargest(3, "claims")
        reps = [str(x) for x in sub["provider_id"].tolist()]
        tc = int(row["total_claims"])
        ta = float(row["total_allowed"])
        pids = prov.loc[prov["cat"] == cat, "provider_id"]
        mask = df["provider_id"].isin(pids)
        sub_claims = df.loc[mask]
        um = int(sub_claims["member_id"].nunique()) if "member_id" in df.columns and len(sub_claims) else max(1, int(row["provider_count"]))
        um = max(1, um)
        out.append(
            {
                "archetype_id": len(out) + 1,
                "archetype_name": f"{cat.replace('_', ' ').title()} volume cluster",
                "provider_count": int(row["provider_count"]),
                "characteristics": {
                    "dominant_service_category": cat,
                    "claim_lines_in_window": tc,
                    "total_allowed": round(ta, 2),
                    # Radar / spider chart axes (BaselineAnalysisPage preferredKeys)
                    "total_claims": float(tc),
                    "total_cost": round(ta, 2),
                    "avg_cost_per_claim": round(ta / tc, 4) if tc else 0.0,
                    "claims_per_member": round(tc / um, 4),
                },
                "representative_providers": reps,
            }
        )
    return out


def provider_archetypes_volume_bands_from_claims_df(df: pd.DataFrame, n_bands: int = 6) -> List[Dict[str, Any]]:
    """
    ~5–6 provider archetypes by claim-volume quantiles on providers (no sklearn).
    Populates total_claims, total_cost, avg_cost_per_claim, claims_per_member for radar charts.
    """
    if df is None or df.empty or "provider_id" not in df.columns:
        return []

    cnt_col = "member_id" if "member_id" in df.columns else "provider_id"
    prov = df.groupby("provider_id", as_index=False).agg(claims=(cnt_col, "count"))
    if "allowed_amount" in df.columns:
        al = df.groupby("provider_id", as_index=False)["allowed_amount"].sum()
        prov = prov.merge(al, on="provider_id", how="left")
        prov["allowed"] = prov["allowed_amount"].fillna(0.0).astype(float)
        prov = prov.drop(columns=["allowed_amount"], errors="ignore")
    else:
        prov["allowed"] = 0.0

    n_prov = len(prov)
    if n_prov == 0:
        return []
    # Sort by activity so bands differ even when many providers share the same claim count
    prov = prov.sort_values(["claims", "allowed"], ascending=True).reset_index(drop=True)
    q = min(max(2, n_bands), n_prov)
    try:
        prov["band"] = pd.qcut(np.arange(n_prov, dtype=float), q=q, labels=False, duplicates="drop")
    except (ValueError, TypeError):
        prov["band"] = 0
    prov["band"] = pd.to_numeric(prov["band"], errors="coerce").fillna(0).astype(int)

    grouped = prov.groupby("band", as_index=False).agg(
        provider_count=("provider_id", "count"),
        total_claims=("claims", "sum"),
        total_allowed=("allowed", "sum"),
    )
    grouped = grouped.sort_values("total_claims", ascending=True).reset_index(drop=True)

    out: List[Dict[str, Any]] = []
    for rank, (_, row) in enumerate(grouped.iterrows()):
        band_id = int(row["band"])
        tc = int(row["total_claims"])
        ta = float(row["total_allowed"])
        pids = prov.loc[prov["band"] == band_id, "provider_id"]
        sub_claims = df[df["provider_id"].isin(pids)]
        um = int(sub_claims["member_id"].nunique()) if "member_id" in df.columns and len(sub_claims) else max(1, int(row["provider_count"]))
        um = max(1, um)
        sub = prov[prov["band"] == band_id].nlargest(3, "claims")
        reps = [str(x) for x in sub["provider_id"].tolist()]
        tier_label = f"Band {rank + 1} of {len(grouped)}"
        out.append(
            {
                "archetype_id": len(out) + 1,
                "archetype_name": f"Provider volume {tier_label} (by claim lines)",
                "provider_count": int(row["provider_count"]),
                "characteristics": {
                    "volume_quantile_band": band_id,
                    "total_claims": float(tc),
                    "total_cost": round(ta, 2),
                    "avg_cost_per_claim": round(ta / tc, 4) if tc else 0.0,
                    "claims_per_member": round(tc / um, 4),
                },
                "representative_providers": reps,
            }
        )
    return out


def monthly_time_series_from_claims_df(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Monthly aggregate series from claims (allowed $ or line counts) with simple trend/bands.
    Shape matches BaselineAnalysis TimeSeriesPoint (no statsmodels STL).
    """
    if df is None or df.empty or "service_date" not in df.columns:
        return []

    d = df.copy()
    d["_ts"] = pd.to_datetime(d["service_date"], errors="coerce")
    d = d.dropna(subset=["_ts"])
    if d.empty:
        return []

    d["_m"] = d["_ts"].dt.to_period("M").dt.to_timestamp()
    use_amount = "allowed_amount" in d.columns and d["allowed_amount"].notna().any()
    if use_amount:
        monthly = d.groupby("_m", as_index=True)["allowed_amount"].sum().sort_index().astype(float)
    else:
        monthly = d.groupby("_m", as_index=True).size().sort_index().astype(float)

    if monthly.empty:
        return []

    observed = monthly
    trend = observed.rolling(window=3, min_periods=1, center=True).mean()
    dev = (observed - trend).fillna(0.0)
    roll_std = observed.rolling(window=3, min_periods=1, center=True).std().fillna(0.0)
    std_band = roll_std * 1.96
    pct_band = observed * 0.05 + 1.0
    band = std_band.where(std_band > 1e-9, pct_band)
    lower = (trend - band).clip(lower=0.0)
    upper = trend + band

    out: List[Dict[str, Any]] = []
    for dt in observed.index:
        o = float(observed.loc[dt])
        t = float(trend.loc[dt]) if dt in trend.index else o
        out.append(
            {
                "date": dt.date().isoformat() if hasattr(dt, "date") else str(dt)[:10],
                "observed": o,
                "trend": t,
                "seasonal": 0.0,
                "residual": float(dev.loc[dt]) if dt in dev.index else 0.0,
                "lower_bound": float(lower.loc[dt]) if dt in lower.index else max(0.0, o * 0.9),
                "upper_bound": float(upper.loc[dt]) if dt in upper.index else o * 1.1,
                "confidence_level": 0.95,
            }
        )
    return out


def _benchmark_rows_from_claims_slice(
    label: str,
    g: pd.DataFrame,
    months: int,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if g is None or len(g) == 0:
        return rows
    n = len(g)
    um = int(g["member_id"].nunique()) if "member_id" in g.columns else 0
    mm = float(um * months) if um and months else float(um or n)
    mm = max(mm, 1.0)
    total_allowed = float(g["allowed_amount"].sum()) if "allowed_amount" in g.columns else 0.0
    total_paid = float(g["paid_amount"].sum()) if "paid_amount" in g.columns else 0.0
    util_per_1k = (n / mm * 1000.0) if mm else 0.0
    allowed_pmpm = total_allowed / mm
    paid_pmpm = total_paid / mm if total_paid else 0.0
    cpm = n / max(um, 1)
    seg_dim = None
    seg_val = None
    if label != "Overall":
        if label.startswith("Market:"):
            seg_dim = "Market"
            seg_val = label.split(":", 1)[-1].strip()
        else:
            seg_dim = "LOB"
            seg_val = label
    rows.append(
        {
            "metric_name": "total_claims_per_1k",
            "metric_value": float(util_per_1k),
            "unit": "per_1k",
            "segment": seg_dim,
            "segment_value": seg_val,
            "confidence_interval_lower": None,
            "confidence_interval_upper": None,
            "sample_size": n,
        }
    )
    rows.append(
        {
            "metric_name": "cost_pmpm",
            "metric_value": float(allowed_pmpm),
            "unit": "PMPM",
            "segment": seg_dim,
            "segment_value": seg_val,
            "confidence_interval_lower": None,
            "confidence_interval_upper": None,
            "sample_size": int(mm),
        }
    )
    rows.append(
        {
            "metric_name": "claims_per_member",
            "metric_value": float(cpm),
            "unit": "count",
            "segment": seg_dim,
            "segment_value": seg_val,
            "confidence_interval_lower": None,
            "confidence_interval_upper": None,
            "sample_size": um or n,
        }
    )
    if total_paid > 0:
        rows.append(
            {
                "metric_name": "paid_pmpm_total",
                "metric_value": float(paid_pmpm),
                "unit": "PMPM",
                "segment": seg_dim,
                "segment_value": seg_val,
                "confidence_interval_lower": None,
                "confidence_interval_upper": None,
                "sample_size": int(mm),
            }
        )
    return rows


def patient_segments_from_claims_df(df: pd.DataFrame, max_segments: int = 12) -> List[Dict[str, Any]]:
    """Segment members by LOB × utilization tertile; shape matches BaselineAnalysis PatientSegment."""
    if df is None or df.empty or "member_id" not in df.columns:
        return []

    mem = df.groupby("member_id", as_index=False).agg(claims=("member_id", "count"))
    if "allowed_amount" in df.columns:
        al = df.groupby("member_id", as_index=False)["allowed_amount"].sum()
        mem = mem.merge(al, on="member_id", how="left")
        mem["allowed"] = mem["allowed_amount"].fillna(0.0)
        mem = mem.drop(columns=["allowed_amount"])
    else:
        mem["allowed"] = 0.0
    if "lob" in df.columns:
        lob_m = df.groupby("member_id", as_index=False)["lob"].first()
        mem = mem.merge(lob_m, on="member_id", how="left")
    else:
        mem["lob"] = "ALL"

    nuniq = mem["claims"].nunique()
    if nuniq < 2:
        mem["util_band"] = "All members"
    else:
        try:
            mem["util_band"] = pd.qcut(
                mem["claims"],
                q=min(3, nuniq),
                labels=["Lower utilization", "Middle utilization", "Higher utilization"][: min(3, nuniq)],
                duplicates="drop",
            ).astype(str)
        except Exception:
            mem["util_band"] = "All members"

    grouped = (
        mem.groupby(["lob", "util_band"], as_index=False)
        .agg(member_count=("member_id", "count"), avg_claims=("claims", "mean"), avg_allowed=("allowed", "mean"))
        .sort_values("member_count", ascending=False)
        .head(max_segments)
    )

    out: List[Dict[str, Any]] = []
    for _, row in grouped.iterrows():
        name = f"{row['lob']} · {row['util_band']}"
        out.append(
            {
                "segment_id": len(out) + 1,
                "segment_name": name,
                "member_count": int(row["member_count"]),
                "characteristics": {"lob": str(row["lob"]), "utilization_band": str(row["util_band"])},
                "utilization_profile": {
                    "avg_claim_lines_per_member": round(float(row["avg_claims"]), 2),
                    "avg_allowed_per_member": round(float(row["avg_allowed"]), 2),
                },
            }
        )
    return out


def enrich_predicted_impact_for_ui_row(predicted_impact_data: Dict[str, Any]) -> Dict[str, Any]:
    """Add provider archetype and patient segment breakdowns for Stage 3.5 UI (stored alongside aggregates)."""
    pr = predicted_impact_data.get("provider_response") or {}
    pt = predicted_impact_data.get("patient_response") or {}
    base_c = float(pr.get("compliant_pct") or 55)
    base_circ = float(pr.get("circumvention_pct") or 8)

    archetypes = [
        {
            "archetype_name": "Compliant institutional",
            "share_of_target_volume_pct": 24.0,
            "predicted_compliance_pct": min(96.0, base_c + 12),
            "predicted_resistance_pct": max(2.0, 18.0 - base_circ * 0.5),
            "notes": "Health-system employed; adheres to PA pathways",
        },
        {
            "archetype_name": "Adaptive independent",
            "share_of_target_volume_pct": 28.0,
            "predicted_compliance_pct": min(92.0, base_c + 4),
            "predicted_resistance_pct": 22.0,
            "notes": "Shifts site-of-care or coding within policy guardrails",
        },
        {
            "archetype_name": "High-volume targeted specialty",
            "share_of_target_volume_pct": 22.0,
            "predicted_compliance_pct": max(38.0, base_c - 15),
            "predicted_circumvention_risk_pct": min(28.0, base_circ + 10),
            "notes": "Disproportionate share of policy-eligible services",
        },
        {
            "archetype_name": "Lag / low-touch digital",
            "share_of_target_volume_pct": 14.0,
            "predicted_compliance_pct": max(45.0, base_c - 8),
            "predicted_resistance_pct": 30.0,
            "notes": "Slower workflow adoption; higher first-pass denials",
        },
        {
            "archetype_name": "Circumvention-prone",
            "share_of_target_volume_pct": 12.0,
            "predicted_compliance_pct": max(25.0, base_c - 25),
            "predicted_circumvention_risk_pct": min(45.0, base_circ + 18),
            "notes": "Historical upcoding / alternative setting spikes",
        },
    ]

    def _rate(key: str, mult: float) -> float:
        v = float(pt.get(key) or 0.05)
        return max(0.0, min(0.95, v * mult))

    segments = [
        {
            "segment_name": "Chronic / high-risk",
            "approx_member_share_pct": 16.0,
            "predicted_defer_rate": _rate("defer_rate", 1.35),
            "predicted_substitution_rate": _rate("substitute_rate", 0.85),
            "predicted_er_fallback_rate": _rate("er_fallback_rate", 1.4),
        },
        {
            "segment_name": "Commercial active workers",
            "approx_member_share_pct": 38.0,
            "predicted_defer_rate": _rate("defer_rate", 0.75),
            "predicted_substitution_rate": _rate("substitute_rate", 1.15),
            "predicted_er_fallback_rate": _rate("er_fallback_rate", 0.9),
        },
        {
            "segment_name": "MA / duals",
            "approx_member_share_pct": 22.0,
            "predicted_defer_rate": _rate("defer_rate", 1.1),
            "predicted_substitution_rate": _rate("substitute_rate", 1.05),
            "predicted_er_fallback_rate": _rate("er_fallback_rate", 1.25),
        },
        {
            "segment_name": "Medicaid / high social need",
            "approx_member_share_pct": 14.0,
            "predicted_defer_rate": _rate("defer_rate", 1.5),
            "predicted_substitution_rate": _rate("substitute_rate", 1.2),
            "predicted_er_fallback_rate": _rate("er_fallback_rate", 1.55),
        },
        {
            "segment_name": "Pediatric / dependent",
            "approx_member_share_pct": 10.0,
            "predicted_defer_rate": _rate("defer_rate", 0.9),
            "predicted_substitution_rate": _rate("substitute_rate", 1.0),
            "predicted_er_fallback_rate": _rate("er_fallback_rate", 1.1),
        },
    ]

    predicted_impact_data["provider_archetype_predictions"] = archetypes
    predicted_impact_data["patient_segment_predictions"] = segments

    br = dict(predicted_impact_data.get("baseline_reference") or {})
    br["provider_archetype_predictions"] = archetypes
    br["patient_segment_predictions"] = segments
    predicted_impact_data["baseline_reference"] = br
    return predicted_impact_data


def fallback_baseline_analysis_result_dict(
    *,
    tenant_id: Union[UUID, str],
    analysis_id: Union[UUID, str],
    claims_df: pd.DataFrame,
    start_date: date,
    end_date: date,
    reason: str,
) -> Dict[str, Any]:
    """
    Baseline analysis payload when BaselineAnalysisEngine is unavailable.
    Includes monthly time series, ~6 provider volume bands (radar-ready), patient segments, expanded benchmarks.
    """
    total_claims = len(claims_df)
    unique_members = int(claims_df["member_id"].nunique()) if "member_id" in claims_df.columns else 0
    months = max(1, (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1)
    member_months = float(unique_members * months) if unique_members else 0.0
    total_paid = float(claims_df["paid_amount"].sum()) if "paid_amount" in claims_df.columns else 0.0
    total_allowed = float(claims_df["allowed_amount"].sum()) if "allowed_amount" in claims_df.columns else 0.0
    util_per_1k = (total_claims / member_months * 1000) if member_months > 0 else 0.0
    allowed_pmpm = (total_allowed / member_months) if member_months > 0 else 0.0

    # Volume-quantile archetypes → 5–6 radar profiles (same axes as full engine)
    pa = provider_archetypes_volume_bands_from_claims_df(claims_df, n_bands=6)
    if not pa:
        pa = provider_archetypes_from_claims_df(claims_df, max_archetypes=8)
    ps = patient_segments_from_claims_df(claims_df)
    ts = monthly_time_series_from_claims_df(claims_df)

    benchmarks: List[Dict[str, Any]] = list(_benchmark_rows_from_claims_slice("Overall", claims_df, months))
    if "lob" in claims_df.columns:
        try:
            top_lobs = claims_df["lob"].astype(str).value_counts().head(4).index.tolist()
            for lob in top_lobs:
                g = claims_df[claims_df["lob"].astype(str) == lob]
                benchmarks.extend(_benchmark_rows_from_claims_slice(str(lob), g, months))
        except Exception:
            pass
    if "market" in claims_df.columns:
        try:
            top_mk = claims_df["market"].astype(str).value_counts().head(3).index.tolist()
            for mk in top_mk:
                g = claims_df[claims_df["market"].astype(str) == mk]
                benchmarks.extend(_benchmark_rows_from_claims_slice(f"Market:{mk}", g, months))
        except Exception:
            pass
    benchmarks.append(
        {
            "metric_name": "unique_members",
            "metric_value": float(unique_members),
            "unit": "count",
            "segment": None,
            "segment_value": None,
            "confidence_interval_lower": None,
            "confidence_interval_upper": None,
            "sample_size": unique_members,
        }
    )
    if "provider_id" in claims_df.columns:
        up = int(claims_df["provider_id"].nunique())
        benchmarks.append(
            {
                "metric_name": "unique_providers",
                "metric_value": float(up),
                "unit": "count",
                "segment": None,
                "segment_value": None,
                "confidence_interval_lower": None,
                "confidence_interval_upper": None,
                "sample_size": up,
            }
        )
    benchmarks.append(
        {
            "metric_name": "total_claim_lines",
            "metric_value": float(total_claims),
            "unit": "count",
            "segment": None,
            "segment_value": None,
            "confidence_interval_lower": None,
            "confidence_interval_upper": None,
            "sample_size": int(total_claims),
        }
    )
    benchmarks.append(
        {
            "metric_name": "total_allowed_spend",
            "metric_value": float(total_allowed),
            "unit": "currency",
            "segment": None,
            "segment_value": None,
            "confidence_interval_lower": None,
            "confidence_interval_upper": None,
            "sample_size": int(total_claims),
        }
    )

    return {
        "analysis_id": str(analysis_id),
        "tenant_id": str(tenant_id),
        "generated_at": datetime.utcnow().isoformat(),
        "time_series": ts,
        "benchmarks": benchmarks,
        "provider_archetypes": pa,
        "patient_segments": ps,
        "confounder_events": [],
        "data_coverage": {
            "claims_lines": int(total_claims),
            "unique_members": unique_members,
            "window_months": months,
            "mode": "claims_segmentation_fallback",
            "reason": reason,
            "time_series": "monthly_allowed_or_volume_simple_trend",
            "provider_archetypes": "six_volume_quantile_bands",
        },
        "model_parameters": {"engine": "claims_segmentation_fallback"},
    }
