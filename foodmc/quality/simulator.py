"""
Quality Simulator — Monte Carlo simulation for process capability & quality control.

Simulates production process variation to calculate Cpk, defect rates,
and probability of meeting specifications.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from foodmc.utils.engine import MonteCarloEngine


class QualityResult:
    """Container for quality simulation results."""

    def __init__(
        self,
        parameters: List[Dict[str, Any]],
        simulations: Dict[str, np.ndarray],
        cpk_values: Dict[str, np.ndarray],
        defect_rates: Dict[str, np.ndarray],
        n_simulations: int,
        engine: MonteCarloEngine,
    ):
        self.parameters = parameters
        self.simulations = simulations
        self.cpk_values = cpk_values
        self.defect_rates = defect_rates
        self.n_simulations = n_simulations
        self.engine = engine

    def summary(self) -> pd.DataFrame:
        """Get summary for all quality parameters."""
        rows = []
        for param in self.parameters:
            name = param["name"]
            sims = self.simulations[name]
            cpk_vals = self.cpk_values[name]
            defects = self.defect_rates[name]
            stats = self.engine.summary_stats(sims)

            rows.append({
                "Parameter": name,
                "Unit": param.get("unit", ""),
                "Target": param.get("target", "N/A"),
                "LSL": param.get("lsl", "N/A"),
                "USL": param.get("usl", "N/A"),
                "Mean": f"{stats['mean']:.3f}",
                "Std Dev": f"{stats['std']:.4f}",
                "Cpk (mean)": f"{np.mean(cpk_vals):.3f}",
                "Cpk (P5)": f"{np.percentile(cpk_vals, 5):.3f}",
                "Defect Rate": f"{np.mean(defects) * 100:.3f}%",
                "Yield": f"{(1 - np.mean(defects)) * 100:.2f}%",
            })
        return pd.DataFrame(rows)

    def cpk_summary(self, parameter: str) -> Dict[str, float]:
        """Get Cpk statistics for a specific parameter."""
        return self.engine.summary_stats(self.cpk_values[parameter])

    def probability_in_spec(self, parameter: str) -> float:
        """Probability that parameter meets specification."""
        return float(1 - np.mean(self.defect_rates[parameter]))

    def report(self, filepath: str = "quality_report.html") -> str:
        """Generate HTML report."""
        from foodmc.reporting.html_report import generate_quality_report
        return generate_quality_report(self, filepath)

    def __repr__(self) -> str:
        params = ", ".join(p["name"] for p in self.parameters)
        return (
            f"QualityResult(\n"
            f"  parameters=[{params}],\n"
            f"  simulations={self.n_simulations:,}\n"
            f")"
        )


class QualitySimulator:
    """
    Monte Carlo simulator for food process quality control.

    Simulates process variation to predict Cpk (process capability index),
    defect rates, and yield for critical quality parameters.

    Common food quality parameters:
    - Weight/fill volume (net weight compliance)
    - Moisture content
    - pH
    - Brix (sugar content)
    - Water activity (aw)
    - Texture (hardness, crispness)
    - Color values (L*, a*, b*)

    Examples
    --------
    >>> sim = QualitySimulator()
    >>> sim.add_parameter("Net Weight", target=100, lsl=97, usl=103,
    ...     process_mean=100.5, process_std=1.2, unit="g")
    >>> sim.add_parameter("Moisture", target=3.0, lsl=2.0, usl=4.0,
    ...     process_mean=3.1, process_std=0.3, unit="%")
    >>> sim.add_parameter("pH", target=4.5, lsl=4.2, usl=4.8,
    ...     process_mean=4.48, process_std=0.08, unit="")
    >>> results = sim.run(n_simulations=10000)
    >>> print(results.summary())
    """

    def __init__(self, random_state: int = 42):
        self.parameters: List[Dict[str, Any]] = []
        self.engine = MonteCarloEngine(random_state=random_state)
        self.random_state = random_state

    def add_parameter(
        self,
        name: str,
        target: float,
        lsl: float,
        usl: float,
        process_mean: float,
        process_std: float,
        unit: str = "",
        distribution: str = "normal",
        mean_shift_std: float = 0.0,
        std_variation: float = 0.0,
    ) -> "QualitySimulator":
        """
        Add a quality parameter to simulate.

        Parameters
        ----------
        name : str
            Parameter name (e.g., "Net Weight", "Moisture").
        target : float
            Target/nominal value.
        lsl : float
            Lower specification limit.
        usl : float
            Upper specification limit.
        process_mean : float
            Current process mean.
        process_std : float
            Current process standard deviation.
        unit : str
            Unit of measurement.
        distribution : str
            Distribution of process output ('normal', 'lognormal').
        mean_shift_std : float
            Std dev of process mean shift over time (drift).
            Set > 0 to model process drift.
        std_variation : float
            Variation in process std dev (0-1 as fraction).
            Set > 0 to model varying process consistency.

        Returns
        -------
        self
        """
        self.parameters.append({
            "name": name,
            "target": target,
            "lsl": lsl,
            "usl": usl,
            "process_mean": process_mean,
            "process_std": process_std,
            "unit": unit,
            "distribution": distribution,
            "mean_shift_std": mean_shift_std,
            "std_variation": std_variation,
        })
        return self

    def run(self, n_simulations: int = 10000) -> QualityResult:
        """
        Run Monte Carlo quality simulation.

        For each simulation:
        1. Sample a process mean (allowing for drift)
        2. Sample a process std (allowing for variation)
        3. Generate a batch measurement from the process
        4. Calculate Cpk and defect status

        Parameters
        ----------
        n_simulations : int
            Number of simulation iterations.

        Returns
        -------
        QualityResult
        """
        if not self.parameters:
            raise ValueError("No parameters added. Use add_parameter() first.")

        simulations = {}
        cpk_values = {}
        defect_rates = {}

        for param in self.parameters:
            name = param["name"]

            # Sample process means (with possible drift)
            if param["mean_shift_std"] > 0:
                means = self.engine.sample(
                    "normal",
                    {"mean": param["process_mean"], "std": param["mean_shift_std"]},
                    n_simulations,
                )
            else:
                means = np.full(n_simulations, param["process_mean"])

            # Sample process std devs (with possible variation)
            if param["std_variation"] > 0:
                stds = self.engine.sample(
                    "normal",
                    {"mean": param["process_std"],
                     "std": param["process_std"] * param["std_variation"]},
                    n_simulations,
                )
                stds = np.clip(stds, param["process_std"] * 0.1, None)
            else:
                stds = np.full(n_simulations, param["process_std"])

            # Generate process output
            rng = np.random.RandomState(self.random_state)
            if param["distribution"] == "normal":
                values = rng.normal(means, stds)
            else:
                values = rng.normal(means, stds)

            simulations[name] = values

            # Calculate Cpk for each simulation
            cpu = (param["usl"] - means) / (3 * stds)
            cpl = (means - param["lsl"]) / (3 * stds)
            cpk = np.minimum(cpu, cpl)
            cpk_values[name] = cpk

            # Calculate defect rates
            below_lsl = (values < param["lsl"]).astype(float)
            above_usl = (values > param["usl"]).astype(float)
            defect_rates[name] = below_lsl + above_usl

        return QualityResult(
            parameters=self.parameters,
            simulations=simulations,
            cpk_values=cpk_values,
            defect_rates=defect_rates,
            n_simulations=n_simulations,
            engine=self.engine,
        )
