"""cogemi/metrics/reliability.py

Utilities for converting Likert responses to ternary values and computing
distributional reliability across repeated / near-duplicate survey items.
"""
from itertools import combinations
from typing import Dict, List

from cogemi.metrics.divergences import Distribution, weighted_js_divergence, estimate_distribution


# ---------------------------------------------------------------------------
# Likert → ternary conversion
# ---------------------------------------------------------------------------

def likert_to_ternary(value: int, scale: int = 5) -> int:
    """Map a Likert response to ternary {-1, 0, 1}.

    Splits the scale into three equal-width bands:
      lower third  → -1 (negative / inappropriate / low)
      middle third →  0 (neutral)
      upper third  → +1 (positive / appropriate / high)

    Examples for scale=5:
      1 → -1,  2 → -1,  3 → 0,  4 → 1,  5 → 1
    Examples for scale=7:
      1,2 → -1,  3 → -1,  4 → 0,  5 → 1,  6,7 → 1
    """
    if not (1 <= value <= scale):
        raise ValueError(f"value {value} out of range [1, {scale}]")
    lo = scale / 3.0
    hi = 2 * scale / 3.0
    if value <= lo:
        return -1
    if value <= hi:
        return 0
    return 1


def discretize_likert_responses(samples: List[int], scale: int = 5) -> List[int]:
    """Convert a list of Likert values to ternary integers."""
    return [likert_to_ternary(v, scale) for v in samples]


# ---------------------------------------------------------------------------
# Distributional reliability
# ---------------------------------------------------------------------------

def distributional_consistency(dist_a: Distribution, dist_b: Distribution) -> float:
    """JS divergence between two distributions of the same repeated item.

    Lower = more consistent.  0 means identical distributions.
    Uses equal weights (each distribution treated as equally sized).
    """
    return weighted_js_divergence(dist_a, dist_b, 1.0, 1.0)


def within_scenario_reliability(distributions: List[Distribution]) -> float:
    """Mean pairwise JS divergence across all distributions for one scenario.

    Pass in the empirical distributions collected from different sub-samples
    or time-points for the same vignette.  A value near 0 indicates high
    reliability (participants respond similarly across repetitions / groups).

    Requires at least two distributions; raises ValueError otherwise.
    """
    if len(distributions) < 2:
        raise ValueError("Need at least two distributions to compute reliability.")
    pairs = list(combinations(distributions, 2))
    return sum(distributional_consistency(a, b) for a, b in pairs) / len(pairs)


def split_half_reliability(
    responses_a: List[int], responses_b: List[int]
) -> float:
    """JS divergence between distributions estimated from two equal halves.

    Split participants into two random halves, compute a distribution from
    each, then compare.  Lower = more reliable.
    """
    dist_a = estimate_distribution(responses_a)
    dist_b = estimate_distribution(responses_b)
    return distributional_consistency(dist_a, dist_b)


def confidence_weighted_distribution(
    samples: List[int],
    confidences: List[int],
    max_confidence: int = 5,
) -> Dict[int, float]:
    """Estimate a probability distribution weighting each response by confidence.

    Higher-confidence responses contribute more to the final distribution.
    Weights are normalised so they sum to 1 before counting.

    Args:
        samples: Ternary response values (-1, 0, 1).
        confidences: Confidence ratings (1–max_confidence) matching samples.
        max_confidence: Upper bound of the confidence scale.
    """
    if len(samples) != len(confidences):
        raise ValueError("samples and confidences must have equal length.")
    weights: Dict[int, float] = {-1: 0.0, 0: 0.0, 1: 0.0}
    total_weight = 0.0
    for val, conf in zip(samples, confidences):
        w = conf / max_confidence
        weights[val] = weights.get(val, 0.0) + w
        total_weight += w
    if total_weight == 0:
        return {-1: 1 / 3, 0: 1 / 3, 1: 1 / 3}
    return {k: v / total_weight for k, v in weights.items()}
