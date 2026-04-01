"""Tests for FoodMC."""

import pytest
import numpy as np
from foodmc import (
    FormulationSimulator,
    ShelfLifeSimulator,
    QualitySimulator,
    NutritionSimulator,
)
from foodmc.utils.engine import MonteCarloEngine


class TestMonteCarloEngine:
    def test_normal_sampling(self):
        engine = MonteCarloEngine()
        samples = engine.sample("normal", {"mean": 100, "std": 10}, 10000)
        assert abs(np.mean(samples) - 100) < 1
        assert len(samples) == 10000

    def test_probability_between(self):
        engine = MonteCarloEngine()
        data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        prob = engine.probability_between(data, 3, 7)
        assert prob == 0.5

    def test_summary_stats(self):
        data = np.random.normal(100, 10, 10000)
        stats = MonteCarloEngine.summary_stats(data)
        assert "mean" in stats
        assert "p95" in stats
        assert "cv" in stats


class TestFormulationSimulator:
    def test_basic_simulation(self):
        sim = FormulationSimulator()
        sim.add_ingredient("Flour", mean_cost=40, std_cost=5, mean_pct=60, std_pct=2)
        sim.add_ingredient("Sugar", mean_cost=45, std_cost=6, mean_pct=30, std_pct=1)
        results = sim.run(n_simulations=5000)
        assert results.total_costs.shape[0] == 5000
        assert np.mean(results.total_costs) > 0

    def test_with_nutrition(self):
        sim = FormulationSimulator()
        sim.add_ingredient("Flour", mean_cost=40, std_cost=5, mean_pct=60, std_pct=2,
                           nutrition={"calories": 364, "protein": 10.3})
        results = sim.run(n_simulations=1000)
        assert len(results.nutrition_totals) > 0
        assert "calories" in results.nutrition_totals

    def test_cost_breakdown(self):
        sim = FormulationSimulator()
        sim.add_ingredient("A", mean_cost=10, std_cost=1, mean_pct=50, std_pct=1)
        sim.add_ingredient("B", mean_cost=20, std_cost=2, mean_pct=50, std_pct=1)
        results = sim.run(n_simulations=1000)
        df = results.cost_breakdown()
        assert len(df) == 2

    def test_empty_raises(self):
        sim = FormulationSimulator()
        with pytest.raises(ValueError):
            sim.run()

    def test_method_chaining(self):
        sim = FormulationSimulator()
        result = sim.add_ingredient("A", mean_cost=10, std_cost=1, mean_pct=50, std_pct=1)
        assert result is sim


class TestShelfLifeSimulator:
    def test_basic_simulation(self):
        sim = ShelfLifeSimulator()
        sim.configure(ea_mean=80, ea_std=5, temp_mean=25, temp_std=3,
                      initial_quality=100, quality_std=5, threshold=60)
        results = sim.run(n_simulations=5000)
        assert results.shelf_lives.shape[0] == 5000
        assert np.mean(results.shelf_lives) > 0

    def test_recommended_shelf_life(self):
        sim = ShelfLifeSimulator()
        sim.configure(ea_mean=80, ea_std=5, temp_mean=25, temp_std=3,
                      initial_quality=100, quality_std=5, threshold=60)
        results = sim.run(n_simulations=5000)
        rec_95 = results.recommended_shelf_life(0.95)
        rec_99 = results.recommended_shelf_life(0.99)
        assert rec_99 < rec_95  # More conservative

    def test_higher_temp_shorter_life(self):
        sim1 = ShelfLifeSimulator(random_state=42)
        sim1.configure(ea_mean=80, ea_std=5, temp_mean=25, temp_std=1,
                       initial_quality=100, quality_std=2, threshold=60)
        r1 = sim1.run(n_simulations=5000)

        sim2 = ShelfLifeSimulator(random_state=42)
        sim2.configure(ea_mean=80, ea_std=5, temp_mean=35, temp_std=1,
                       initial_quality=100, quality_std=2, threshold=60)
        r2 = sim2.run(n_simulations=5000)

        assert np.mean(r2.shelf_lives) < np.mean(r1.shelf_lives)

    def test_not_configured_raises(self):
        sim = ShelfLifeSimulator()
        with pytest.raises(ValueError):
            sim.run()


class TestQualitySimulator:
    def test_basic_simulation(self):
        sim = QualitySimulator()
        sim.add_parameter("Weight", target=100, lsl=97, usl=103,
                          process_mean=100, process_std=1)
        results = sim.run(n_simulations=5000)
        assert len(results.simulations) == 1
        assert results.probability_in_spec("Weight") > 0.9

    def test_high_cpk(self):
        sim = QualitySimulator()
        sim.add_parameter("Weight", target=100, lsl=94, usl=106,
                          process_mean=100, process_std=1)
        results = sim.run(n_simulations=5000)
        assert np.mean(results.cpk_values["Weight"]) > 1.5

    def test_empty_raises(self):
        sim = QualitySimulator()
        with pytest.raises(ValueError):
            sim.run()


class TestNutritionSimulator:
    def test_basic_compliance(self):
        sim = NutritionSimulator(regulation="FSSAI")
        sim.add_nutrient("calories", declared=250, actual_mean=250,
                         actual_std=5, unit="kcal")
        results = sim.run(n_simulations=5000)
        assert results.overall_compliance() > 0.9

    def test_poor_compliance(self):
        sim = NutritionSimulator(regulation="FSSAI")
        sim.add_nutrient("fat", declared=10, actual_mean=15,
                         actual_std=2, unit="g")
        results = sim.run(n_simulations=5000)
        assert results.overall_compliance() < 0.5

    def test_invalid_regulation(self):
        with pytest.raises(ValueError):
            NutritionSimulator(regulation="INVALID")

    def test_multiple_nutrients(self):
        sim = NutritionSimulator(regulation="FDA")
        sim.add_nutrient("calories", declared=200, actual_mean=205, actual_std=10, unit="kcal")
        sim.add_nutrient("protein", declared=15, actual_mean=14.5, actual_std=1, unit="g")
        results = sim.run(n_simulations=5000)
        assert len(results.nutrients) == 2
