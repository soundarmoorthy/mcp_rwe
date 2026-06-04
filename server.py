"""
Real-World Evidence (RWE) MCP Server
=====================================
A demo life sciences MCP server that surfaces aggregated patient-level
real-world data across multiple dimensions:
  • Age group
  • Gender
  • US Geography (Census region / state)
  • Longitudinal year (2018-2024)

Run locally over HTTP with:
    pip install -r requirements.txt
    python server.py

The MCP endpoint is http://127.0.0.1:9090/mcp and health is available at
http://127.0.0.1:9090/health. Set MCP_TRANSPORT=stdio for stdio clients.
"""

import os
import random

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

# ---------------------------------------------------------------------------
# Server bootstrap
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Synthetic data layer
# ---------------------------------------------------------------------------

HOST = os.getenv("MCP_HOST", "127.0.0.1")
PORT = int(os.getenv("MCP_PORT", "9090"))
TRANSPORT = os.getenv("MCP_TRANSPORT", "streamable-http")

# Optional TLS – set these env vars to enable HTTPS locally:
#   SSL_CERTFILE=certs/localhost.pem SSL_KEYFILE=certs/localhost-key.pem
SSL_CERTFILE = os.getenv("SSL_CERTFILE")
SSL_KEYFILE  = os.getenv("SSL_KEYFILE")

mcp = FastMCP(name="rwe-life-sciences", log_level="INFO", host=HOST, port=PORT)
SEED = 42
random.seed(SEED)


# @mcp.custom_route("/health", methods=["GET"], include_in_schema=False)
# async def health_check(_request: Request) -> JSONResponse:
#     return JSONResponse(
#         {
#             "status": "ok",
#             "service": "rwe-life-sciences",
#             "transport": TRANSPORT,
#             "mcp_endpoint": "/mcp",
#         }
#     )
#

AGE_GROUPS = ["0-17", "18-34", "35-49", "50-64", "65-74", "75+"]
GENDERS = ["Male", "Female", "Unknown/Other"]
US_REGIONS = {
    "Northeast": ["NY", "MA", "PA", "NJ", "CT", "NH", "VT", "ME", "RI"],
    "South":     ["TX", "FL", "GA", "NC", "VA", "TN", "AL", "SC", "LA", "KY", "AR", "MS", "WV", "OK", "MD", "DE", "DC"],
    "Midwest":   ["IL", "OH", "MI", "IN", "WI", "MN", "MO", "IA", "KS", "NE", "ND", "SD"],
    "West":      ["CA", "WA", "AZ", "CO", "OR", "NV", "UT", "NM", "ID", "HI", "AK", "MT", "WY"],
}
YEARS = list(range(2018, 2025))

CONDITIONS = [
    "Type 2 Diabetes",
    "Hypertension",
    "Heart Failure",
    "COPD",
    "Asthma",
    "Atrial Fibrillation",
    "Major Depressive Disorder",
    "Rheumatoid Arthritis",
    "Chronic Kidney Disease",
    "Obesity",
]

def _patient_count(base: int, jitter: float = 0.25) -> int:
    """Return a jittered integer around *base*."""
    lo = int(base * (1 - jitter))
    hi = int(base * (1 + jitter))
    return random.randint(lo, hi)

def _prevalence(age_group: str, condition: str) -> float:
    """Crude synthetic prevalence rate (%) for a given age group / condition."""
    base_rates = {
        "Type 2 Diabetes":          {"0-17": 0.3, "18-34": 1.5, "35-49": 6.0, "50-64": 14.0, "65-74": 22.0, "75+": 24.0},
        "Hypertension":             {"0-17": 0.5, "18-34": 4.0, "35-49": 18.0, "50-64": 42.0, "65-74": 60.0, "75+": 70.0},
        "Heart Failure":            {"0-17": 0.1, "18-34": 0.2, "35-49": 0.8, "50-64": 3.5, "65-74": 9.0, "75+": 14.0},
        "COPD":                     {"0-17": 0.0, "18-34": 0.3, "35-49": 2.0, "50-64": 7.0, "65-74": 12.0, "75+": 13.0},
        "Asthma":                   {"0-17": 9.0, "18-34": 8.0, "35-49": 7.5, "50-64": 7.0, "65-74": 6.5, "75+": 5.0},
        "Atrial Fibrillation":      {"0-17": 0.0, "18-34": 0.1, "35-49": 0.5, "50-64": 2.5, "65-74": 7.0, "75+": 12.0},
        "Major Depressive Disorder":{"0-17": 5.0, "18-34": 12.0, "35-49": 10.0, "50-64": 8.0, "65-74": 5.0, "75+": 4.0},
        "Rheumatoid Arthritis":     {"0-17": 0.1, "18-34": 0.4, "35-49": 1.2, "50-64": 2.5, "65-74": 3.0, "75+": 3.5},
        "Chronic Kidney Disease":   {"0-17": 0.2, "18-34": 0.5, "35-49": 1.5, "50-64": 6.0, "65-74": 14.0, "75+": 20.0},
        "Obesity":                  {"0-17": 18.0, "18-34": 28.0, "35-49": 37.0, "50-64": 40.0, "65-74": 38.0, "75+": 28.0},
    }
    return base_rates.get(condition, {}).get(age_group, 5.0)

def _avg_age_of_onset(condition: str) -> float:
    onset = {
        "Type 2 Diabetes": 52.3, "Hypertension": 48.6, "Heart Failure": 67.1,
        "COPD": 61.4, "Asthma": 12.8, "Atrial Fibrillation": 66.8,
        "Major Depressive Disorder": 32.5, "Rheumatoid Arthritis": 46.2,
        "Chronic Kidney Disease": 58.9, "Obesity": 28.4,
    }
    return onset.get(condition, 50.0)

# ---------------------------------------------------------------------------
# Tool implementation
# ---------------------------------------------------------------------------

@mcp.tool(
    name="query_rwe_patient_cohort",
    description=(
        "Query aggregated real-world evidence (RWE) for a patient cohort "
        "defined by a clinical condition of interest. Returns patient counts, "
        "prevalence rates, and healthcare utilisation metrics broken down by: "
        "age group, gender, US geographic region/state, and year (2018-2024). "
        "Data is de-identified synthetic data for demonstration purposes only."
    ),
)
def query_rwe_patient_cohort(
    condition: str,
    dimensions: list[str] | None = None,
    year_start: int = 2018,
    year_end: int = 2024,
    region: str | None = None,
) -> dict:
    """
    Parameters
    ----------
    condition   : Clinical condition to analyse. One of:
                  "Type 2 Diabetes", "Hypertension", "Heart Failure",
                  "COPD", "Asthma", "Atrial Fibrillation",
                  "Major Depressive Disorder", "Rheumatoid Arthritis",
                  "Chronic Kidney Disease", "Obesity".
    dimensions  : Subset of dimensions to return. Allowed values:
                  ["age", "gender", "geography", "longitudinal"].
                  Defaults to all four.
    year_start  : First year of longitudinal window (2018–2024). Default 2018.
    year_end    : Last year  of longitudinal window (2018–2024). Default 2024.
    region      : Optional US Census region filter: "Northeast", "South",
                  "Midwest", "West". If omitted, all regions are returned.

    Returns
    -------
    dict with keys:
        metadata    – data source, refresh date, caveats
        summary     – top-level cohort KPIs
        by_age      – breakdown by age group  (if requested)
        by_gender   – breakdown by gender     (if requested)
        by_geography– breakdown by US region / state (if requested)
        longitudinal– year-over-year trend    (if requested)
    """

    # ---- validation --------------------------------------------------------
    if condition not in CONDITIONS:
        return {
            "error": f"Unknown condition '{condition}'.",
            "valid_conditions": CONDITIONS,
        }

    all_dimensions = {"age", "gender", "geography", "longitudinal"}
    if dimensions is None:
        dimensions = list(all_dimensions)
    else:
        invalid = set(dimensions) - all_dimensions
        if invalid:
            return {
                "error": f"Invalid dimension(s): {invalid}.",
                "valid_dimensions": list(all_dimensions),
            }

    year_start = max(2018, min(year_start, 2024))
    year_end   = max(year_start, min(year_end, 2024))

    regions_to_show = (
        {region: US_REGIONS[region]} if region and region in US_REGIONS
        else US_REGIONS
    )
    if region and region not in US_REGIONS:
        return {
            "error": f"Unknown region '{region}'.",
            "valid_regions": list(US_REGIONS.keys()),
        }

    # ---- summary KPIs ------------------------------------------------------
    total_patients = _patient_count(850_000)
    diagnosed      = _patient_count(int(total_patients * 0.18))
    avg_onset      = _avg_age_of_onset(condition)
    mean_hba1c     = round(random.uniform(6.8, 8.9), 1)   # generic biomarker
    er_visits_per100 = round(random.uniform(8.5, 24.3), 1)
    readmit_rate   = round(random.uniform(0.08, 0.22), 3)

    result: dict = {
        "metadata": {
            "tool": "RWE Patient Cohort Aggregator",
            "version": "1.0.0",
            "data_source": "Simulated US Claims + EHR (demo only – not real patient data)",
            "condition_queried": condition,
            "icd10_codes": _icd10(condition),
            "data_refresh_date": "2025-01-31",
            "observation_window": f"{year_start}–{year_end}",
            "region_filter": region or "All US",
            "caveats": (
                "All figures are synthetically generated for demonstration. "
                "Do not use for clinical or regulatory decisions."
            ),
        },
        "summary": {
            "total_covered_lives": total_patients,
            "patients_with_condition": diagnosed,
            "crude_prevalence_pct": round(diagnosed / total_patients * 100, 2),
            "mean_age_of_first_diagnosis_yrs": avg_onset,
            "mean_primary_biomarker": mean_hba1c,
            "er_visits_per_100_patients_annually": er_visits_per100,
            "30_day_readmission_rate": readmit_rate,
            "mean_annual_cost_usd": _patient_count(14_200, 0.35),
        },
    }

    # ---- by age ------------------------------------------------------------
    if "age" in dimensions:
        by_age = []
        for ag in AGE_GROUPS:
            prev = _prevalence(ag, condition)
            cnt  = _patient_count(int(diagnosed * _age_weight(ag)))
            by_age.append({
                "age_group": ag,
                "patient_count": cnt,
                "prevalence_pct": round(prev + random.uniform(-0.5, 0.5), 2),
                "mean_comorbidities": round(random.uniform(1.2, 4.8), 1),
                "mean_medications": round(random.uniform(1.5, 6.2), 1),
                "hospitalisation_rate_pct": round(random.uniform(3.0, 28.0), 1),
            })
        result["by_age"] = by_age

    # ---- by gender ---------------------------------------------------------
    if "gender" in dimensions:
        by_gender = []
        weights = [0.48, 0.50, 0.02]
        for g, w in zip(GENDERS, weights):
            by_gender.append({
                "gender": g,
                "patient_count": _patient_count(int(diagnosed * w)),
                "prevalence_pct": round(random.uniform(8.0, 22.0), 2),
                "mean_age_at_diagnosis": round(avg_onset + random.uniform(-3, 3), 1),
                "treatment_adherence_pct": round(random.uniform(55.0, 82.0), 1),
            })
        result["by_gender"] = by_gender

    # ---- by geography ------------------------------------------------------
    if "geography" in dimensions:
        geo_rows = []
        for reg_name, states in regions_to_show.items():
            reg_count = _patient_count(int(diagnosed * 0.25))
            reg_row = {
                "region": reg_name,
                "patient_count": reg_count,
                "prevalence_pct": round(random.uniform(10.0, 20.0), 2),
                "states": [],
            }
            for state in states:
                state_n = _patient_count(int(reg_count / len(states)))
                reg_row["states"].append({
                    "state": state,
                    "patient_count": state_n,
                    "prevalence_pct": round(random.uniform(8.0, 24.0), 2),
                    "er_visits_per_100": round(random.uniform(6.0, 30.0), 1),
                    "mean_annual_cost_usd": _patient_count(13_800, 0.40),
                })
            geo_rows.append(reg_row)
        result["by_geography"] = geo_rows

    # ---- longitudinal ------------------------------------------------------
    if "longitudinal" in dimensions:
        long_rows = []
        base_diag = int(diagnosed * 0.80)
        for yr in range(year_start, year_end + 1):
            growth = 1 + (yr - 2018) * random.uniform(0.02, 0.05)
            yr_cnt = _patient_count(int(base_diag * growth))
            long_rows.append({
                "year": yr,
                "incident_cases": _patient_count(int(yr_cnt * 0.08)),
                "prevalent_cases": yr_cnt,
                "crude_prevalence_pct": round(yr_cnt / _patient_count(850_000) * 100, 2),
                "mean_annual_cost_usd": _patient_count(int(12_000 * (1 + (yr - 2018) * 0.04))),
                "new_treatments_initiated_pct": round(random.uniform(18.0, 45.0), 1),
                "treatment_discontinuation_pct": round(random.uniform(10.0, 30.0), 1),
            })
        result["longitudinal"] = long_rows

    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _icd10(condition: str) -> list[str]:
    mapping = {
        "Type 2 Diabetes":           ["E11", "E11.9", "E11.65"],
        "Hypertension":              ["I10", "I11", "I12"],
        "Heart Failure":             ["I50", "I50.9", "I50.1"],
        "COPD":                      ["J44", "J44.0", "J44.1"],
        "Asthma":                    ["J45", "J45.20", "J45.50"],
        "Atrial Fibrillation":       ["I48", "I48.0", "I48.2"],
        "Major Depressive Disorder": ["F32", "F33", "F32.9"],
        "Rheumatoid Arthritis":      ["M05", "M06", "M05.79"],
        "Chronic Kidney Disease":    ["N18", "N18.3", "N18.5"],
        "Obesity":                   ["E66", "E66.01", "E66.09"],
    }
    return mapping.get(condition, ["Unknown"])


def _age_weight(age_group: str) -> float:
    weights = {
        "0-17": 0.06, "18-34": 0.10, "35-49": 0.16,
        "50-64": 0.28, "65-74": 0.22, "75+": 0.18,
    }
    return weights.get(age_group, 0.16)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if TRANSPORT not in {"stdio", "sse", "streamable-http"}:
        raise ValueError(
            "MCP_TRANSPORT must be one of: stdio, sse, streamable-http"
        )

    # Build optional SSL kwargs for uvicorn when cert files are provided
    ssl_kwargs: dict = {}
    if SSL_CERTFILE and SSL_KEYFILE:
        import ssl as _ssl
        if not os.path.isfile(SSL_CERTFILE):
            raise FileNotFoundError(f"SSL_CERTFILE not found: {SSL_CERTFILE}")
        if not os.path.isfile(SSL_KEYFILE):
            raise FileNotFoundError(f"SSL_KEYFILE not found: {SSL_KEYFILE}")
        ssl_kwargs = {"ssl_certfile": SSL_CERTFILE, "ssl_keyfile": SSL_KEYFILE}
        scheme = "https"
    else:
        scheme = "http"

    if ssl_kwargs:
        print(f"🔒 HTTPS enabled  →  {scheme}://{HOST}:{PORT}/mcp")
    else:
        print(f"🌐 HTTP (no TLS)  →  {scheme}://{HOST}:{PORT}/mcp")

    mcp.run(transport=TRANSPORT, **ssl_kwargs)
