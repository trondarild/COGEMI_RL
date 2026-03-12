# metrics/divergences.py
import numpy as np
from typing import Dict, Union

Distribution = Dict[int, float]


def kl_divergence(dist1: Distribution, dist2: Distribution, epsilon: float = 1e-10) -> float:
    """
    Compute the Kullback-Leibler (KL) divergence between two distributions.

    Arguments:
    - dist1: First probability distribution ({-1: float, 0: float, 1: float})
    - dist2: Second probability distribution ({-1: float, 0: float, 1: float})
    - epsilon: Small value to avoid log(0)

    Returns:
    - KL divergence value (float)
    """
    d1 = np.asarray([dist1[-1], dist1[0], dist1[1]]) if not isinstance(dist1, np.ndarray) else dist1
    d2 = np.asarray([dist2[-1], dist2[0], dist2[1]]) if not isinstance(dist2, np.ndarray) else dist2
    d1 = np.clip(d1, epsilon, 1)
    d2 = np.clip(d2, epsilon, 1)
    return float(np.sum(d1 * np.log(d1 / d2)))


def weighted_js_divergence(
    dist1: Distribution,
    dist2: Distribution,
    weight1: float,
    weight2: float
) -> float:
    """
    Compute the symmetrized Jensen-Shannon divergence between two distributions.

    Arguments:
    - dist1: First probability distribution
    - dist2: Second probability distribution
    - weight1: Weight (e.g. sample count) for the first distribution
    - weight2: Weight (e.g. sample count) for the second distribution

    Returns:
    - Symmetrized JS divergence value (float)
    """
    dist1_array = np.array([dist1[-1], dist1[0], dist1[1]])
    dist2_array = np.array([dist2[-1], dist2[0], dist2[1]])

    # Compute the mixture distribution
    mix = (weight1 * dist1_array + weight2 * dist2_array) / (weight1 + weight2)

    return 0.5 * kl_divergence(dist1_array, mix) + 0.5 * kl_divergence(dist2_array, mix)


def estimate_distribution(samples: Union[list, np.ndarray]) -> Distribution:
    """
    Compute a probability distribution from a list of samples.

    Arguments:
    - samples: List of observed values (-1, 0, or 1)

    Returns:
    - Normalized probability distribution: {-1: float, 0: float, 1: float}
    """
    unique, counts = np.unique(samples, return_counts=True)
    total = len(samples)

    # Compute probabilities
    dist: Distribution = {int(val): count / total for val, count in zip(unique, counts)}

    # Ensure all possible values (-1, 0, 1) have a minimum probability
    for val in [-1, 0, 1]:
        if val not in dist:
            dist[val] = 1e-5

    # Normalize probabilities
    total_prob = sum(dist.values())
    dist = {key: value / total_prob for key, value in dist.items()}

    return dist
