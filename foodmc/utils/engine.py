"""
Core Monte Carlo engine used by all simulators.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any


class MonteCarloEngine:
    """
    Core Monte Carlo simulation engine.

    Supports multiple probability distributions commonly used
    in food science and process engineering.
    """

    DISTRIBUTIONS = {
        "normal": np.random.normal,
        "uniform": np.random.uniform,
        "triangular": np.random.triangular,
        "lognormal": np.random.lognormal,
        "beta": np.random.beta,
    }

    def __init__(self, random_state: int = 42):
        self.rng = np.random.RandomState(random_state)
        self.random_state = random_state

    def sample(
        self,
        distribution: str,
        params: Dict[str, float],
        n_samples: int = 10000,
    ) -> np.ndarray:
        """
        Generate random samples from a specified distribution.

        Parameters
        ----------
        distribution : str
            One of: 'normal', 'uniform', 'triangular', 'lognormal', 'beta'
        params : dict
            Distribution parameters:
            - normal: {'mean': float, 'std': float}
            - uniform: {'low': float, 'high': float}
            - triangular: {'low': float, 'mode': float, 'high': float}
            - lognormal: {'mean': float, 'sigma': float}
            - beta: {'a': float, 'b': float, 'scale': float}
        n_samples : int
            Number of Monte Carlo samples.

        Returns
        -------
        np.ndarray
            Array of random samples.
        """
        rng = np.random.RandomState(self.random_state)

        if distribution == "normal":
            return rng.normal(params["mean"], params["std"], n_samples)
        elif distribution == "uniform":
            return rng.uniform(params["low"], params["high"], n_samples)
        elif distribution == "triangular":
            return rng.triangular(params["low"], params["mode"], params["high"], n_samples)
        elif distribution == "lognormal":
            return rng.lognormal(params["mean"], params["sigma"], n_samples)
        elif distribution == "beta":
            scale = params.get("scale", 1.0)
            return rng.beta(params["a"], params["b"], n_samples) * scale
        else:
            raise ValueError(
                f"Unknown distribution '{distribution}'. "
                f"Supported: {list(self.DISTRIBUTIONS.keys())}"
            )

    @staticmethod
    def percentile_interval(data: np.ndarray, confidence: float = 0.95) -> Tuple[float, float]:
        """Calculate confidence interval using percentiles."""
        alpha = (1 - confidence) / 2
        lower = np.percentile(data, alpha * 100)
        upper = np.percentile(data, (1 - alpha) * 100)
        return (float(lower), float(upper))

    @staticmethod
    def probability_above(data: np.ndarray, threshold: float) -> float:
        """Calculate probability of exceeding a threshold."""
        return float(np.mean(data > threshold))

    @staticmethod
    def probability_below(data: np.ndarray, threshold: float) -> float:
        """Calculate probability of being below a threshold."""
        return float(np.mean(data < threshold))

    @staticmethod
    def probability_between(data: np.ndarray, low: float, high: float) -> float:
        """Calculate probability of being within a range."""
        return float(np.mean((data >= low) & (data <= high)))

    @staticmethod
    def summary_stats(data: np.ndarray) -> Dict[str, float]:
        """Calculate comprehensive summary statistics."""
        return {
            "mean": float(np.mean(data)),
            "median": float(np.median(data)),
            "std": float(np.std(data)),
            "min": float(np.min(data)),
            "max": float(np.max(data)),
            "p5": float(np.percentile(data, 5)),
            "p25": float(np.percentile(data, 25)),
            "p75": float(np.percentile(data, 75)),
            "p95": float(np.percentile(data, 95)),
            "cv": float(np.std(data) / np.mean(data) * 100) if np.mean(data) != 0 else 0,
            "skewness": float(_skewness(data)),
            "n_simulations": len(data),
        }


def _skewness(data: np.ndarray) -> float:
    """Calculate skewness."""
    n = len(data)
    mean = np.mean(data)
    std = np.std(data)
    if std == 0:
        return 0.0
    return float((n / ((n - 1) * (n - 2))) * np.sum(((data - mean) / std) ** 3)) if n > 2 else 0.0
