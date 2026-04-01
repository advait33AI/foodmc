"""
Shelf Life Simulator — Monte Carlo simulation for shelf life prediction.

Uses the Arrhenius equation to model degradation kinetics with uncertainty
in activation energy, storage temperature, and initial quality parameters.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from foodmc.utils.engine import MonteCarloEngine


class ShelfLifeResult:
    """Container for shelf life simulation results."""

    def __init__(
        self,
        shelf_lives: np.ndarray,
        degradation_curves: Dict[str, np.ndarray],
        parameters: Dict[str, Any],
        n_simulations: int,
        engine: MonteCarloEngine,
    ):
        self.shelf_lives = shelf_lives
        self.degradation_curves = degradation_curves
        self.parameters = parameters
        self.n_simulations = n_simulations
        self.engine = engine

    def summary(self) -> Dict[str, float]:
        """Get shelf life summary statistics."""
        return self.engine.summary_stats(self.shelf_lives)

    def probability_lasts(self, days: float) -> float:
        """Probability that product lasts at least 'days' days."""
        return self.engine.probability_above(self.shelf_lives, days)

    def recommended_shelf_life(self, confidence: float = 0.95) -> float:
        """
        Recommended shelf life at given confidence level.

        This is the conservative estimate — the number of days by which
        we're confident (e.g., 95%) the product is still acceptable.
        """
        return float(np.percentile(self.shelf_lives, (1 - confidence) * 100))

    def report(self, filepath: str = "shelflife_report.html") -> str:
        """Generate HTML report."""
        from foodmc.reporting.html_report import generate_shelflife_report
        return generate_shelflife_report(self, filepath)

    def __repr__(self) -> str:
        stats = self.summary()
        return (
            f"ShelfLifeResult(\n"
            f"  simulations={self.n_simulations:,},\n"
            f"  mean_shelf_life={stats['mean']:.1f} days,\n"
            f"  95%_confidence={self.recommended_shelf_life(0.95):.1f} days,\n"
            f"  range=({stats['min']:.1f}, {stats['max']:.1f}) days\n"
            f")"
        )


class ShelfLifeSimulator:
    """
    Monte Carlo simulator for shelf life prediction using Arrhenius kinetics.

    Models food degradation as a function of:
    - Activation energy (Ea) — sensitivity to temperature
    - Storage temperature — with daily/seasonal fluctuation
    - Initial quality — batch-to-batch variation
    - Critical quality threshold — when product becomes unacceptable

    The Arrhenius equation:
        k = A * exp(-Ea / (R * T))

    where k is the reaction rate constant, Ea is activation energy,
    R is the gas constant, T is absolute temperature (Kelvin).

    Examples
    --------
    >>> sim = ShelfLifeSimulator()
    >>> sim.configure(
    ...     ea_mean=80,           # kJ/mol activation energy
    ...     ea_std=5,             # uncertainty in Ea
    ...     temp_mean=25,         # °C storage temperature
    ...     temp_std=3,           # temperature fluctuation
    ...     initial_quality=100,  # initial quality score
    ...     quality_std=5,        # batch variation
    ...     threshold=60,         # quality threshold (unacceptable below this)
    ...     reaction_order=1,     # first-order degradation
    ... )
    >>> results = sim.run(n_simulations=10000)
    >>> print(f"Recommended shelf life: {results.recommended_shelf_life():.0f} days")
    """

    R = 8.314e-3  # Gas constant in kJ/(mol·K)

    def __init__(self, random_state: int = 42):
        self.engine = MonteCarloEngine(random_state=random_state)
        self.random_state = random_state
        self.config = {}

    def configure(
        self,
        ea_mean: float = 80.0,
        ea_std: float = 5.0,
        temp_mean: float = 25.0,
        temp_std: float = 3.0,
        initial_quality: float = 100.0,
        quality_std: float = 5.0,
        threshold: float = 60.0,
        reaction_order: int = 1,
        ref_rate: float = 0.01,
        ref_rate_std: float = 0.002,
        ref_temp: float = 25.0,
        quality_attribute: str = "Overall Quality",
    ) -> "ShelfLifeSimulator":
        """
        Configure shelf life simulation parameters.

        Parameters
        ----------
        ea_mean : float
            Mean activation energy in kJ/mol.
            Typical values: 40-120 kJ/mol for food degradation.
        ea_std : float
            Std dev of activation energy.
        temp_mean : float
            Mean storage temperature in °C.
        temp_std : float
            Temperature fluctuation (std dev in °C).
        initial_quality : float
            Initial quality score (e.g., 100 = fresh).
        quality_std : float
            Batch-to-batch variation in initial quality.
        threshold : float
            Quality score below which product is unacceptable.
        reaction_order : int
            Degradation reaction order (0 or 1).
        ref_rate : float
            Reference degradation rate at ref_temp (units/day).
        ref_rate_std : float
            Uncertainty in reference rate.
        ref_temp : float
            Reference temperature for rate constant (°C).
        quality_attribute : str
            Name of the quality attribute being measured.

        Returns
        -------
        self
        """
        self.config = {
            "ea_mean": ea_mean,
            "ea_std": ea_std,
            "temp_mean": temp_mean,
            "temp_std": temp_std,
            "initial_quality": initial_quality,
            "quality_std": quality_std,
            "threshold": threshold,
            "reaction_order": reaction_order,
            "ref_rate": ref_rate,
            "ref_rate_std": ref_rate_std,
            "ref_temp": ref_temp,
            "quality_attribute": quality_attribute,
        }
        return self

    def run(self, n_simulations: int = 10000, max_days: int = 730) -> ShelfLifeResult:
        """
        Run Monte Carlo shelf life simulation.

        Parameters
        ----------
        n_simulations : int
            Number of simulation iterations.
        max_days : int
            Maximum days to simulate (cap for very stable products).

        Returns
        -------
        ShelfLifeResult
        """
        if not self.config:
            raise ValueError("Not configured. Call configure() first.")

        c = self.config

        # Sample uncertain parameters
        ea_samples = self.engine.sample(
            "normal", {"mean": c["ea_mean"], "std": c["ea_std"]}, n_simulations
        )
        ea_samples = np.clip(ea_samples, 10, 200)

        temp_samples = self.engine.sample(
            "normal", {"mean": c["temp_mean"], "std": c["temp_std"]}, n_simulations
        )

        initial_q = self.engine.sample(
            "normal", {"mean": c["initial_quality"], "std": c["quality_std"]}, n_simulations
        )
        initial_q = np.clip(initial_q, c["threshold"], None)

        ref_rates = self.engine.sample(
            "normal", {"mean": c["ref_rate"], "std": c["ref_rate_std"]}, n_simulations
        )
        ref_rates = np.clip(ref_rates, 1e-6, None)

        # Convert temperatures to Kelvin
        T_storage = temp_samples + 273.15
        T_ref = c["ref_temp"] + 273.15

        # Arrhenius: k = k_ref * exp((Ea/R) * (1/T_ref - 1/T_storage))
        rate_constants = ref_rates * np.exp(
            (ea_samples / self.R) * (1.0 / T_ref - 1.0 / T_storage)
        )
        rate_constants = np.clip(rate_constants, 1e-8, None)

        # Calculate shelf life based on reaction order
        if c["reaction_order"] == 0:
            # Zero-order: Q = Q0 - k*t → t = (Q0 - threshold) / k
            shelf_lives = (initial_q - c["threshold"]) / rate_constants
        else:
            # First-order: Q = Q0 * exp(-k*t) → t = ln(Q0/threshold) / k
            shelf_lives = np.log(initial_q / c["threshold"]) / rate_constants

        shelf_lives = np.clip(shelf_lives, 0, max_days)

        # Generate degradation curves for visualization (using mean parameters)
        time_points = np.arange(0, max_days + 1, 1)
        mean_rate = np.mean(rate_constants)
        mean_q0 = np.mean(initial_q)

        if c["reaction_order"] == 0:
            mean_curve = mean_q0 - mean_rate * time_points
        else:
            mean_curve = mean_q0 * np.exp(-mean_rate * time_points)

        # P5 and P95 curves
        rate_p5 = np.percentile(rate_constants, 5)
        rate_p95 = np.percentile(rate_constants, 95)

        if c["reaction_order"] == 0:
            curve_optimistic = mean_q0 - rate_p5 * time_points
            curve_pessimistic = mean_q0 - rate_p95 * time_points
        else:
            curve_optimistic = mean_q0 * np.exp(-rate_p5 * time_points)
            curve_pessimistic = mean_q0 * np.exp(-rate_p95 * time_points)

        degradation_curves = {
            "time": time_points,
            "mean": np.clip(mean_curve, 0, None),
            "optimistic": np.clip(curve_optimistic, 0, None),
            "pessimistic": np.clip(curve_pessimistic, 0, None),
        }

        return ShelfLifeResult(
            shelf_lives=shelf_lives,
            degradation_curves=degradation_curves,
            parameters=self.config,
            n_simulations=n_simulations,
            engine=self.engine,
        )
