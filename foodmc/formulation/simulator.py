"""
Formulation Simulator — Monte Carlo simulation for recipe/formulation optimization.

Simulates how ingredient variability (cost fluctuations, composition variation)
affects total product cost, nutritional profile, and formulation feasibility.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from foodmc.utils.engine import MonteCarloEngine


class Ingredient:
    """Represents a single ingredient with its variability profile."""

    def __init__(
        self,
        name: str,
        mean_cost: float,
        std_cost: float,
        mean_pct: float,
        std_pct: float,
        unit: str = "₹/kg",
        nutrition: Optional[Dict[str, float]] = None,
        cost_distribution: str = "normal",
        pct_distribution: str = "normal",
    ):
        """
        Parameters
        ----------
        name : str
            Ingredient name (e.g., "Wheat Flour", "Sugar").
        mean_cost : float
            Average cost per kg.
        std_cost : float
            Standard deviation of cost (price volatility).
        mean_pct : float
            Average percentage in the formulation (0-100).
        std_pct : float
            Standard deviation of percentage (process variation).
        unit : str
            Cost unit for display.
        nutrition : dict, optional
            Nutritional values per 100g. Keys can include:
            'calories', 'protein', 'fat', 'carbs', 'fiber', 'sugar', 'sodium'
        cost_distribution : str
            Distribution for cost sampling ('normal', 'uniform', 'triangular', 'lognormal').
        pct_distribution : str
            Distribution for percentage sampling.
        """
        self.name = name
        self.mean_cost = mean_cost
        self.std_cost = std_cost
        self.mean_pct = mean_pct
        self.std_pct = std_pct
        self.unit = unit
        self.nutrition = nutrition or {}
        self.cost_distribution = cost_distribution
        self.pct_distribution = pct_distribution


class FormulationResult:
    """Container for formulation simulation results."""

    def __init__(
        self,
        ingredients: List[Ingredient],
        total_costs: np.ndarray,
        ingredient_costs: Dict[str, np.ndarray],
        ingredient_pcts: Dict[str, np.ndarray],
        nutrition_totals: Dict[str, np.ndarray],
        n_simulations: int,
        engine: MonteCarloEngine,
    ):
        self.ingredients = ingredients
        self.total_costs = total_costs
        self.ingredient_costs = ingredient_costs
        self.ingredient_pcts = ingredient_pcts
        self.nutrition_totals = nutrition_totals
        self.n_simulations = n_simulations
        self.engine = engine

    def summary(self) -> Dict[str, Any]:
        """Get summary statistics for total formulation cost."""
        return self.engine.summary_stats(self.total_costs)

    def cost_breakdown(self) -> pd.DataFrame:
        """Get per-ingredient cost contribution statistics."""
        rows = []
        for ing in self.ingredients:
            costs = self.ingredient_costs[ing.name]
            rows.append({
                "Ingredient": ing.name,
                "Mean Cost Contribution": f"{np.mean(costs):.2f}",
                "Std Dev": f"{np.std(costs):.2f}",
                "% of Total": f"{np.mean(costs) / np.mean(self.total_costs) * 100:.1f}%",
                "5th Percentile": f"{np.percentile(costs, 5):.2f}",
                "95th Percentile": f"{np.percentile(costs, 95):.2f}",
            })
        return pd.DataFrame(rows)

    def nutrition_summary(self) -> pd.DataFrame:
        """Get nutritional profile statistics."""
        if not self.nutrition_totals:
            return pd.DataFrame()
        rows = []
        for nutrient, values in self.nutrition_totals.items():
            stats = self.engine.summary_stats(values)
            rows.append({
                "Nutrient": nutrient.title(),
                "Mean": f"{stats['mean']:.2f}",
                "Std Dev": f"{stats['std']:.2f}",
                "P5": f"{stats['p5']:.2f}",
                "P95": f"{stats['p95']:.2f}",
                "CV%": f"{stats['cv']:.1f}%",
            })
        return pd.DataFrame(rows)

    def probability_cost_exceeds(self, threshold: float) -> float:
        """Probability that total cost exceeds a budget threshold."""
        return self.engine.probability_above(self.total_costs, threshold)

    def probability_cost_within(self, low: float, high: float) -> float:
        """Probability that total cost falls within a budget range."""
        return self.engine.probability_between(self.total_costs, low, high)

    def report(self, filepath: str = "formulation_report.html") -> str:
        """Generate HTML report."""
        from foodmc.reporting.html_report import generate_formulation_report
        return generate_formulation_report(self, filepath)

    def __repr__(self) -> str:
        stats = self.summary()
        return (
            f"FormulationResult(\n"
            f"  ingredients={len(self.ingredients)},\n"
            f"  simulations={self.n_simulations:,},\n"
            f"  mean_cost={stats['mean']:.2f},\n"
            f"  cost_95CI=({stats['p5']:.2f}, {stats['p95']:.2f})\n"
            f")"
        )


class FormulationSimulator:
    """
    Monte Carlo simulator for food formulation optimization.

    Simulates how ingredient price volatility and process variation
    affect total product cost and nutritional composition.

    Examples
    --------
    >>> sim = FormulationSimulator()
    >>> sim.add_ingredient("Flour", mean_cost=45, std_cost=5, mean_pct=55, std_pct=2,
    ...     nutrition={"calories": 364, "protein": 10.3, "carbs": 76.3, "fat": 1.0})
    >>> sim.add_ingredient("Sugar", mean_cost=42, std_cost=8, mean_pct=25, std_pct=1.5,
    ...     nutrition={"calories": 387, "protein": 0, "carbs": 100, "fat": 0})
    >>> sim.add_ingredient("Butter", mean_cost=450, std_cost=30, mean_pct=15, std_pct=1,
    ...     nutrition={"calories": 717, "protein": 0.9, "fat": 81, "carbs": 0.1})
    >>> sim.add_ingredient("Salt", mean_cost=20, std_cost=2, mean_pct=1.5, std_pct=0.3,
    ...     nutrition={"sodium": 38758})
    >>> results = sim.run(n_simulations=10000)
    >>> print(results.summary())
    >>> print(results.cost_breakdown())
    >>> results.report("biscuit_formulation.html")
    """

    def __init__(self, random_state: int = 42, batch_size_kg: float = 100.0):
        """
        Parameters
        ----------
        random_state : int
            Random seed for reproducibility.
        batch_size_kg : float
            Batch size in kg for cost calculation.
        """
        self.ingredients: List[Ingredient] = []
        self.engine = MonteCarloEngine(random_state=random_state)
        self.random_state = random_state
        self.batch_size_kg = batch_size_kg

    def add_ingredient(
        self,
        name: str,
        mean_cost: float,
        std_cost: float,
        mean_pct: float,
        std_pct: float,
        unit: str = "₹/kg",
        nutrition: Optional[Dict[str, float]] = None,
        cost_distribution: str = "normal",
        pct_distribution: str = "normal",
    ) -> "FormulationSimulator":
        """
        Add an ingredient to the formulation.

        Parameters
        ----------
        name : str
            Ingredient name.
        mean_cost : float
            Average cost per kg.
        std_cost : float
            Cost standard deviation (price volatility).
        mean_pct : float
            Average percentage in formula (0-100).
        std_pct : float
            Percentage standard deviation (process variation).
        unit : str
            Cost unit.
        nutrition : dict, optional
            Nutritional values per 100g of this ingredient.
        cost_distribution : str
            Distribution type for cost.
        pct_distribution : str
            Distribution type for percentage.

        Returns
        -------
        self
            For method chaining.
        """
        ingredient = Ingredient(
            name=name,
            mean_cost=mean_cost,
            std_cost=std_cost,
            mean_pct=mean_pct,
            std_pct=std_pct,
            unit=unit,
            nutrition=nutrition,
            cost_distribution=cost_distribution,
            pct_distribution=pct_distribution,
        )
        self.ingredients.append(ingredient)
        return self

    def run(self, n_simulations: int = 10000) -> FormulationResult:
        """
        Run Monte Carlo simulation.

        Parameters
        ----------
        n_simulations : int
            Number of simulation iterations.

        Returns
        -------
        FormulationResult
            Object with simulation results, statistics, and reporting.
        """
        if not self.ingredients:
            raise ValueError("No ingredients added. Use add_ingredient() first.")

        ingredient_costs = {}
        ingredient_pcts = {}
        nutrition_totals: Dict[str, np.ndarray] = {}

        total_costs = np.zeros(n_simulations)

        for ing in self.ingredients:
            # Sample costs
            if ing.cost_distribution == "normal":
                costs = self.engine.sample(
                    "normal", {"mean": ing.mean_cost, "std": ing.std_cost}, n_simulations
                )
            elif ing.cost_distribution == "lognormal":
                mu = np.log(ing.mean_cost ** 2 / np.sqrt(ing.std_cost ** 2 + ing.mean_cost ** 2))
                sigma = np.sqrt(np.log(1 + (ing.std_cost / ing.mean_cost) ** 2))
                costs = self.engine.sample(
                    "lognormal", {"mean": mu, "sigma": sigma}, n_simulations
                )
            else:
                costs = self.engine.sample(
                    "normal", {"mean": ing.mean_cost, "std": ing.std_cost}, n_simulations
                )

            costs = np.clip(costs, 0, None)  # Cost can't be negative

            # Sample percentages
            pcts = self.engine.sample(
                "normal", {"mean": ing.mean_pct, "std": ing.std_pct}, n_simulations
            )
            pcts = np.clip(pcts, 0, 100)  # Percentage bounds

            # Cost contribution = (percentage/100) * batch_size * cost_per_kg
            contribution = (pcts / 100) * self.batch_size_kg * costs
            total_costs += contribution

            ingredient_costs[ing.name] = contribution
            ingredient_pcts[ing.name] = pcts

            # Nutrition calculation
            if ing.nutrition:
                for nutrient, value_per_100g in ing.nutrition.items():
                    # Nutrient contribution = (pct/100) * batch_size * (value_per_100g / 100)
                    # Per kg of final product
                    nutrient_contribution = (pcts / 100) * (value_per_100g / 100)
                    if nutrient not in nutrition_totals:
                        nutrition_totals[nutrient] = np.zeros(n_simulations)
                    nutrition_totals[nutrient] += nutrient_contribution

        return FormulationResult(
            ingredients=self.ingredients,
            total_costs=total_costs,
            ingredient_costs=ingredient_costs,
            ingredient_pcts=ingredient_pcts,
            nutrition_totals=nutrition_totals,
            n_simulations=n_simulations,
            engine=self.engine,
        )
