"""
Nutrition Simulator — Monte Carlo simulation for nutritional label compliance.

Simulates how ingredient variability affects declared nutritional values
and calculates probability of regulatory compliance (FSSAI / FDA / EU).
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from foodmc.utils.engine import MonteCarloEngine


# Regulatory tolerance rules (simplified)
# Different regulations allow different tolerances for declared values
REGULATORY_RULES = {
    "FSSAI": {
        "calories": {"tolerance_type": "max", "tolerance_pct": 10},
        "protein": {"tolerance_type": "min", "tolerance_pct": -10},
        "fat": {"tolerance_type": "max", "tolerance_pct": 10},
        "carbs": {"tolerance_type": "max", "tolerance_pct": 10},
        "sugar": {"tolerance_type": "max", "tolerance_pct": 10},
        "fiber": {"tolerance_type": "min", "tolerance_pct": -10},
        "sodium": {"tolerance_type": "max", "tolerance_pct": 20},
    },
    "FDA": {
        "calories": {"tolerance_type": "max", "tolerance_pct": 20},
        "protein": {"tolerance_type": "min", "tolerance_pct": -20},
        "fat": {"tolerance_type": "max", "tolerance_pct": 20},
        "carbs": {"tolerance_type": "max", "tolerance_pct": 20},
        "sugar": {"tolerance_type": "max", "tolerance_pct": 20},
        "fiber": {"tolerance_type": "min", "tolerance_pct": -20},
        "sodium": {"tolerance_type": "max", "tolerance_pct": 20},
    },
    "EU": {
        "calories": {"tolerance_type": "range", "tolerance_abs": 20},  # kcal
        "protein": {"tolerance_type": "range_pct", "tolerance_pct": 20},
        "fat": {"tolerance_type": "range_pct", "tolerance_pct": 20},
        "carbs": {"tolerance_type": "range_pct", "tolerance_pct": 20},
        "sugar": {"tolerance_type": "range_pct", "tolerance_pct": 20},
        "fiber": {"tolerance_type": "range_pct", "tolerance_pct": 20},
        "sodium": {"tolerance_type": "range_pct", "tolerance_pct": 20},
    },
}


class NutrientProfile:
    """Represents a nutrient with its variability."""

    def __init__(
        self,
        name: str,
        declared_value: float,
        actual_mean: float,
        actual_std: float,
        unit: str = "g",
    ):
        self.name = name
        self.declared_value = declared_value
        self.actual_mean = actual_mean
        self.actual_std = actual_std
        self.unit = unit


class NutritionResult:
    """Container for nutrition simulation results."""

    def __init__(
        self,
        nutrients: List[NutrientProfile],
        simulations: Dict[str, np.ndarray],
        compliance: Dict[str, Dict[str, float]],
        regulation: str,
        n_simulations: int,
        engine: MonteCarloEngine,
    ):
        self.nutrients = nutrients
        self.simulations = simulations
        self.compliance = compliance
        self.regulation = regulation
        self.n_simulations = n_simulations
        self.engine = engine

    def summary(self) -> pd.DataFrame:
        """Get compliance summary for all nutrients."""
        rows = []
        for nut in self.nutrients:
            sims = self.simulations[nut.name]
            stats = self.engine.summary_stats(sims)
            comp = self.compliance[nut.name]

            rows.append({
                "Nutrient": nut.name.title(),
                "Declared": f"{nut.declared_value:.1f} {nut.unit}",
                "Actual Mean": f"{stats['mean']:.2f} {nut.unit}",
                "Actual Std": f"{stats['std']:.3f}",
                "CV%": f"{stats['cv']:.1f}%",
                "Compliance Rate": f"{comp['compliance_rate'] * 100:.1f}%",
                "Risk Level": comp["risk_level"],
            })
        return pd.DataFrame(rows)

    def overall_compliance(self) -> float:
        """Probability that ALL nutrients are compliant simultaneously."""
        all_compliant = np.ones(self.n_simulations, dtype=bool)
        for nut in self.nutrients:
            all_compliant &= self.compliance[nut.name]["compliant_mask"]
        return float(np.mean(all_compliant))

    def report(self, filepath: str = "nutrition_report.html") -> str:
        """Generate HTML report."""
        from foodmc.reporting.html_report import generate_nutrition_report
        return generate_nutrition_report(self, filepath)

    def __repr__(self) -> str:
        overall = self.overall_compliance()
        return (
            f"NutritionResult(\n"
            f"  regulation='{self.regulation}',\n"
            f"  nutrients={len(self.nutrients)},\n"
            f"  simulations={self.n_simulations:,},\n"
            f"  overall_compliance={overall * 100:.1f}%\n"
            f")"
        )


class NutritionSimulator:
    """
    Monte Carlo simulator for nutritional label compliance.

    Simulates how ingredient and process variability affects whether
    declared nutritional values meet regulatory requirements.

    Examples
    --------
    >>> sim = NutritionSimulator(regulation="FSSAI")
    >>> sim.add_nutrient("calories", declared=450, actual_mean=462,
    ...     actual_std=15, unit="kcal")
    >>> sim.add_nutrient("protein", declared=8.0, actual_mean=7.8,
    ...     actual_std=0.5, unit="g")
    >>> sim.add_nutrient("fat", declared=18.0, actual_mean=18.5,
    ...     actual_std=1.2, unit="g")
    >>> sim.add_nutrient("sugar", declared=22.0, actual_mean=21.5,
    ...     actual_std=1.8, unit="g")
    >>> results = sim.run(n_simulations=10000)
    >>> print(results.summary())
    >>> print(f"Overall compliance: {results.overall_compliance():.1%}")
    """

    def __init__(self, regulation: str = "FSSAI", random_state: int = 42):
        """
        Parameters
        ----------
        regulation : str
            Regulatory framework: 'FSSAI', 'FDA', or 'EU'.
        random_state : int
            Random seed.
        """
        if regulation not in REGULATORY_RULES:
            raise ValueError(
                f"Unknown regulation '{regulation}'. "
                f"Supported: {list(REGULATORY_RULES.keys())}"
            )
        self.regulation = regulation
        self.rules = REGULATORY_RULES[regulation]
        self.nutrients: List[NutrientProfile] = []
        self.engine = MonteCarloEngine(random_state=random_state)
        self.random_state = random_state

    def add_nutrient(
        self,
        name: str,
        declared: float,
        actual_mean: float,
        actual_std: float,
        unit: str = "g",
    ) -> "NutritionSimulator":
        """
        Add a nutrient to simulate.

        Parameters
        ----------
        name : str
            Nutrient name (must match regulation keys:
            'calories', 'protein', 'fat', 'carbs', 'sugar', 'fiber', 'sodium').
        declared : float
            Value declared on the nutrition label.
        actual_mean : float
            Actual mean from lab analysis.
        actual_std : float
            Standard deviation from lab analysis.
        unit : str
            Unit of measurement.

        Returns
        -------
        self
        """
        self.nutrients.append(
            NutrientProfile(
                name=name.lower(),
                declared_value=declared,
                actual_mean=actual_mean,
                actual_std=actual_std,
                unit=unit,
            )
        )
        return self

    def run(self, n_simulations: int = 10000) -> NutritionResult:
        """
        Run Monte Carlo nutrition compliance simulation.

        Parameters
        ----------
        n_simulations : int
            Number of simulation iterations.

        Returns
        -------
        NutritionResult
        """
        if not self.nutrients:
            raise ValueError("No nutrients added. Use add_nutrient() first.")

        simulations = {}
        compliance = {}

        for nut in self.nutrients:
            # Simulate actual nutrient values
            values = self.engine.sample(
                "normal",
                {"mean": nut.actual_mean, "std": nut.actual_std},
                n_simulations,
            )
            values = np.clip(values, 0, None)
            simulations[nut.name] = values

            # Check compliance against regulation
            rule = self.rules.get(nut.name)
            if rule is None:
                # No specific rule — assume ±20% tolerance
                compliant = np.abs(values - nut.declared_value) <= (
                    nut.declared_value * 0.20
                )
            else:
                compliant = self._check_compliance(
                    values, nut.declared_value, rule
                )

            compliance_rate = float(np.mean(compliant))
            risk_level = self._assess_risk(compliance_rate)

            compliance[nut.name] = {
                "compliance_rate": compliance_rate,
                "risk_level": risk_level,
                "compliant_mask": compliant,
            }

        return NutritionResult(
            nutrients=self.nutrients,
            simulations=simulations,
            compliance=compliance,
            regulation=self.regulation,
            n_simulations=n_simulations,
            engine=self.engine,
        )

    def _check_compliance(
        self, values: np.ndarray, declared: float, rule: Dict
    ) -> np.ndarray:
        """Check compliance against a specific regulatory rule."""
        tol_type = rule["tolerance_type"]

        if tol_type == "max":
            # Actual must not exceed declared + tolerance%
            upper = declared * (1 + rule["tolerance_pct"] / 100)
            return values <= upper

        elif tol_type == "min":
            # Actual must be at least declared - tolerance%
            lower = declared * (1 + rule["tolerance_pct"] / 100)
            return values >= lower

        elif tol_type == "range":
            # Actual must be within ± absolute tolerance
            tol = rule["tolerance_abs"]
            return (values >= declared - tol) & (values <= declared + tol)

        elif tol_type == "range_pct":
            # Actual must be within ± percentage tolerance
            tol = declared * rule["tolerance_pct"] / 100
            return (values >= declared - tol) & (values <= declared + tol)

        else:
            return np.ones(len(values), dtype=bool)

    @staticmethod
    def _assess_risk(compliance_rate: float) -> str:
        """Assess risk level based on compliance rate."""
        if compliance_rate >= 0.99:
            return "✅ Low"
        elif compliance_rate >= 0.95:
            return "⚠️ Medium"
        elif compliance_rate >= 0.90:
            return "🔶 High"
        else:
            return "🔴 Critical"
