"""
Recovery Probability Scoring Module
====================================
Deterministic formula — no LLM required. Instant calculation.

Score = 0 to 100
  70+ : Green  — High recovery probability (MONITOR / one-time link likely enough)
  40-69: Orange — Medium recovery (needs nudge)
  <40  : Red    — Low probability (needs human or ESCALATE)
"""

# Failure reason weights: how likely is self/easy recovery?
DIAGNOSIS_SCORES = {
    "bank_decline_temporary":        80,   # Server was down — usually fixes itself
    "bank_decline":                  60,   # Generic bank decline — might be temporary
    "insufficient_funds":            50,   # Customer's balance issue — recoverable with nudge
    "card_expired":                  45,   # Need new card — moderate friction
    "payment_method_recovery":       45,
    "upi_link_expired":              55,   # Quick fix — resend link
    "technical_error":               65,   # Our side / Razorpay — usually retryable
    "unknown_error":                 30,   # Unknown = risky
    "customer_cancelled":            5,    # Intentional — very low recovery chance
    "mandate_cancelled":             5,
    "fraud_detected":                0,    # Do not attempt recovery
}

def _diagnosis_base_score(diagnosis: str) -> int:
    """Map raw diagnosis string to a base score."""
    if not diagnosis:
        return 30
    diagnosis_lower = diagnosis.lower()
    for key, score in DIAGNOSIS_SCORES.items():
        if key in diagnosis_lower:
            return score
    return 30  # default for unknown reasons


def calculate_recovery_score(
    tenure_days: int,
    diagnosis: str,
    amount_paise: int,
    opt_out: bool
) -> int:
    """
    Returns a recovery probability score from 0 to 100.
    
    Args:
        tenure_days: How long the customer has been with the platform
        diagnosis: Failure reason / error code string
        amount_paise: Amount at risk in paise (100 paise = 1 INR)
        opt_out: Whether the customer has opted out
    
    Returns:
        int: Score 0-100
    """
    # Opt-out = instant zero. Do not contact.
    if opt_out:
        return 0

    # Base score from failure reason
    score = _diagnosis_base_score(diagnosis)

    # Tenure bonus: loyal customers are more likely to pay
    # 0-30 days: no bonus
    # 31-180 days: +5
    # 181-365 days: +10
    # 365+ days: +15
    if tenure_days > 365:
        score += 15
    elif tenure_days > 180:
        score += 10
    elif tenure_days > 30:
        score += 5

    # Amount penalty: higher amount = less likely to recover instantly
    # < 500 INR (50000 paise): no penalty
    # 500–5000 INR: -5
    # 5000–50000 INR: -10
    # > 50000 INR: -20
    if amount_paise > 5_000_000:  # > 50,000 INR
        score -= 20
    elif amount_paise > 500_000:  # > 5,000 INR
        score -= 10
    elif amount_paise > 50_000:   # > 500 INR
        score -= 5

    # Clamp to [0, 100]
    return max(0, min(100, score))


def score_label(score: int) -> str:
    """Return a human readable label for a score."""
    if score >= 70:
        return "HIGH"
    elif score >= 40:
        return "MEDIUM"
    else:
        return "LOW"
