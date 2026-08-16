"""Priority scoring. The formula lives on the backend and combines multiple
factors, never AI confidence alone."""

WEIGHTS = {
    "structural_risk": 0.30,
    "population_exposure": 0.20,
    "accessibility": 0.20,
    "infrastructure_risk": 0.15,
    "evidence_confidence": 0.15,
}


def compute_priority(structural_risk, population_exposure, accessibility,
                     infrastructure_risk, evidence_confidence):
    """All inputs are 0-100. Returns (score_0_100, factors_dict)."""
    factors = {
        "structural_risk": round(structural_risk, 1),
        "population_exposure": round(population_exposure, 1),
        "accessibility": round(accessibility, 1),
        "infrastructure_risk": round(infrastructure_risk, 1),
        "evidence_confidence": round(evidence_confidence, 1),
    }
    score = sum(factors[k] * w for k, w in WEIGHTS.items())
    return round(score, 1), factors