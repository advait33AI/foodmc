"""
FoodMC — Monte Carlo Simulation Toolkit for Food R&D
=====================================================

Simulate, optimize, and de-risk food product development decisions
using Monte Carlo methods. Built by food scientists, for food scientists.

Modules:
    - formulation: Recipe cost & nutrition optimization under ingredient variability
    - shelflife: Shelf life prediction with uncertainty quantification
    - quality: Process capability & quality control simulation
    - nutrition: Nutritional label compliance probability analysis

Usage:
    >>> from foodmc import FormulationSimulator
    >>> sim = FormulationSimulator()
    >>> sim.add_ingredient("Flour", mean_cost=45, std_cost=5, mean_pct=60, std_pct=2)
    >>> results = sim.run(n_simulations=10000)
    >>> results.report("formulation_report.html")
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__license__ = "MIT"

from foodmc.formulation.simulator import FormulationSimulator
from foodmc.shelflife.simulator import ShelfLifeSimulator
from foodmc.quality.simulator import QualitySimulator
from foodmc.nutrition.simulator import NutritionSimulator

__all__ = [
    "FormulationSimulator",
    "ShelfLifeSimulator",
    "QualitySimulator",
    "NutritionSimulator",
]
