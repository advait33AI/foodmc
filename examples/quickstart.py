"""
FoodMC Examples — Complete walkthrough of all simulation modules.

Run: python examples/quickstart.py
"""

from foodmc import (
    FormulationSimulator,
    ShelfLifeSimulator,
    QualitySimulator,
    NutritionSimulator,
)


def example_biscuit_formulation():
    """
    Example 1: Biscuit Formulation Cost Simulation
    ================================================
    A biscuit manufacturer wants to understand how ingredient
    price volatility affects their per-batch production cost.
    """
    print("\n" + "=" * 60)
    print("🍪 Example 1: Biscuit Formulation Cost Simulation")
    print("=" * 60)

    sim = FormulationSimulator(batch_size_kg=100)

    sim.add_ingredient(
        "Wheat Flour", mean_cost=38, std_cost=4, mean_pct=55, std_pct=1.5,
        nutrition={"calories": 364, "protein": 10.3, "carbs": 76.3, "fat": 1.0, "fiber": 2.7},
    )
    sim.add_ingredient(
        "Sugar", mean_cost=42, std_cost=6, mean_pct=22, std_pct=1.0,
        nutrition={"calories": 387, "protein": 0, "carbs": 100, "fat": 0, "sugar": 100},
    )
    sim.add_ingredient(
        "Palm Oil", mean_cost=95, std_cost=12, mean_pct=12, std_pct=0.8,
        nutrition={"calories": 884, "protein": 0, "fat": 100, "carbs": 0},
    )
    sim.add_ingredient(
        "Milk Powder", mean_cost=320, std_cost=25, mean_pct=5, std_pct=0.5,
        nutrition={"calories": 496, "protein": 26.3, "fat": 26.7, "carbs": 38.4},
    )
    sim.add_ingredient(
        "Butter", mean_cost=450, std_cost=35, mean_pct=4, std_pct=0.3,
        nutrition={"calories": 717, "protein": 0.9, "fat": 81, "carbs": 0.1},
    )
    sim.add_ingredient(
        "Salt", mean_cost=18, std_cost=2, mean_pct=1.2, std_pct=0.2,
        nutrition={"sodium": 38758},
    )
    sim.add_ingredient(
        "Baking Powder", mean_cost=150, std_cost=10, mean_pct=0.8, std_pct=0.1,
    )

    results = sim.run(n_simulations=10000)

    print(f"\n📊 Cost Summary:")
    stats = results.summary()
    print(f"   Mean batch cost: ₹{stats['mean']:.2f}")
    print(f"   Std deviation:   ₹{stats['std']:.2f}")
    print(f"   Best case (P5):  ₹{stats['p5']:.2f}")
    print(f"   Worst case (P95): ₹{stats['p95']:.2f}")
    print(f"   CV: {stats['cv']:.1f}%")

    print(f"\n📋 Cost Breakdown:")
    print(results.cost_breakdown())

    print(f"\n🥗 Nutritional Profile (per 100g):")
    print(results.nutrition_summary())

    budget = stats["mean"] * 1.1
    prob = results.probability_cost_exceeds(budget)
    print(f"\n💰 Probability cost exceeds ₹{budget:.0f} (10% over mean): {prob:.1%}")

    results.report("biscuit_formulation_report.html")
    return results


def example_juice_shelf_life():
    """
    Example 2: Fruit Juice Shelf Life Prediction
    ==============================================
    A juice manufacturer needs to determine the shelf life
    of a new mango juice variant stored at ambient temperature.
    """
    print("\n" + "=" * 60)
    print("🧃 Example 2: Fruit Juice Shelf Life Prediction")
    print("=" * 60)

    sim = ShelfLifeSimulator()
    sim.configure(
        ea_mean=85,              # kJ/mol — typical for vitamin C degradation
        ea_std=6,                # uncertainty from lab studies
        temp_mean=30,            # Indian ambient temperature
        temp_std=5,              # seasonal variation
        initial_quality=100,     # initial vitamin C retention %
        quality_std=4,           # batch-to-batch variation
        threshold=50,            # unacceptable below 50% retention
        reaction_order=1,        # first-order degradation
        ref_rate=0.008,          # degradation rate at 25°C
        ref_rate_std=0.0015,     # uncertainty in rate
        ref_temp=25,             # reference temperature
        quality_attribute="Vitamin C Retention (%)",
    )

    results = sim.run(n_simulations=10000)

    stats = results.summary()
    rec_95 = results.recommended_shelf_life(0.95)
    rec_99 = results.recommended_shelf_life(0.99)

    print(f"\n📊 Shelf Life Summary:")
    print(f"   Mean shelf life:     {stats['mean']:.0f} days")
    print(f"   Std deviation:       {stats['std']:.0f} days")
    print(f"   Recommended (95%):   {rec_95:.0f} days")
    print(f"   Conservative (99%):  {rec_99:.0f} days")

    for days in [90, 120, 150, 180]:
        prob = results.probability_lasts(days)
        print(f"   P(lasts ≥ {days} days): {prob:.1%}")

    results.report("juice_shelflife_report.html")
    return results


def example_packaging_quality():
    """
    Example 3: Snack Packaging Quality Control
    ============================================
    A snack manufacturer monitors critical quality parameters
    on their packaging line.
    """
    print("\n" + "=" * 60)
    print("📦 Example 3: Snack Packaging Quality Control")
    print("=" * 60)

    sim = QualitySimulator()

    sim.add_parameter(
        "Net Weight", target=50, lsl=48.5, usl=52,
        process_mean=50.3, process_std=0.6,
        unit="g", mean_shift_std=0.15,
    )
    sim.add_parameter(
        "Seal Strength", target=3.5, lsl=2.8, usl=4.5,
        process_mean=3.55, process_std=0.25,
        unit="N/15mm",
    )
    sim.add_parameter(
        "Moisture Content", target=2.5, lsl=1.5, usl=3.5,
        process_mean=2.6, process_std=0.35,
        unit="%",
    )
    sim.add_parameter(
        "Headspace O₂", target=1.0, lsl=0, usl=2.0,
        process_mean=0.9, process_std=0.3,
        unit="%",
    )

    results = sim.run(n_simulations=10000)

    print(f"\n📊 Quality Summary:")
    print(results.summary())

    for param in results.parameters:
        name = param["name"]
        prob = results.probability_in_spec(name)
        print(f"   {name}: {prob:.2%} in spec")

    results.report("quality_report.html")
    return results


def example_nutrition_compliance():
    """
    Example 4: Protein Bar Nutritional Label Compliance
    ====================================================
    A protein bar manufacturer wants to verify their nutritional
    label declarations meet FSSAI requirements.
    """
    print("\n" + "=" * 60)
    print("🏷️  Example 4: Protein Bar Nutrition Label Compliance")
    print("=" * 60)

    sim = NutritionSimulator(regulation="FSSAI")

    sim.add_nutrient("calories", declared=250, actual_mean=258,
                     actual_std=12, unit="kcal")
    sim.add_nutrient("protein", declared=20, actual_mean=19.2,
                     actual_std=1.5, unit="g")
    sim.add_nutrient("fat", declared=8, actual_mean=8.4,
                     actual_std=0.8, unit="g")
    sim.add_nutrient("carbs", declared=30, actual_mean=31.2,
                     actual_std=2.0, unit="g")
    sim.add_nutrient("sugar", declared=12, actual_mean=11.5,
                     actual_std=1.2, unit="g")
    sim.add_nutrient("fiber", declared=5, actual_mean=4.8,
                     actual_std=0.6, unit="g")
    sim.add_nutrient("sodium", declared=200, actual_mean=215,
                     actual_std=25, unit="mg")

    results = sim.run(n_simulations=10000)

    print(f"\n📊 Compliance Summary ({results.regulation}):")
    print(results.summary())
    print(f"\n🎯 Overall compliance (all nutrients): {results.overall_compliance():.1%}")

    results.report("nutrition_compliance_report.html")
    return results


if __name__ == "__main__":
    r1 = example_biscuit_formulation()
    r2 = example_juice_shelf_life()
    r3 = example_packaging_quality()
    r4 = example_nutrition_compliance()

    print("\n" + "=" * 60)
    print("✅ All examples complete! Check the generated HTML reports.")
    print("=" * 60)
