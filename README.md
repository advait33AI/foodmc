<div align="center">

# 🧪 FoodMC

### Monte Carlo Simulation Toolkit for Food R&D

**Simulate. Quantify. De-risk.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![No Paid APIs](https://img.shields.io/badge/paid%20APIs-none-orange.svg)](#)
[![Food Science](https://img.shields.io/badge/domain-Food%20R%26D-brightgreen.svg)](#)

<br>

```python
from foodmc import FormulationSimulator

sim = FormulationSimulator(batch_size_kg=100)
sim.add_ingredient("Flour", mean_cost=38, std_cost=4, mean_pct=55, std_pct=1.5)
sim.add_ingredient("Sugar", mean_cost=42, std_cost=6, mean_pct=22, std_pct=1.0)
results = sim.run(n_simulations=10000)
results.report("formulation_report.html")   # → Professional HTML report
```

<br>

**FoodMC** brings Monte Carlo simulation to food product development — helping R&D teams, food scientists, and quality engineers **quantify uncertainty** in formulations, shelf life predictions, process quality, and nutritional label compliance. No expensive software. No Excel hacks. Just Python.

[Modules](#-modules) · [Quick Start](#-quick-start) · [Examples](#-real-world-examples) · [Reports](#-html-reports) · [Contributing](#-contributing)

</div>

---

## 🤔 The Problem

Food R&D decisions are made under uncertainty every day:

- *"What happens to our batch cost if palm oil prices spike 20%?"*
- *"Can we guarantee 6-month shelf life if warehouse temps hit 35°C?"*
- *"What's the probability our net weight falls below the legal minimum?"*
- *"Will our nutrition label survive an FSSAI audit?"*

Most food companies answer these with **gut feel**, **single-point estimates**, or **expensive software** like @RISK, Minitab, or JMP. FoodMC gives you the same Monte Carlo power — for free, in Python, with beautiful reports.

---

## 📦 Modules

| Module | What It Does | Key Question It Answers |
|---|---|---|
| **🧬 Formulation** | Simulates recipe cost & nutrition under ingredient variability | *"What's the probability our batch cost exceeds budget?"* |
| **⏳ Shelf Life** | Predicts shelf life using Arrhenius kinetics + uncertainty | *"How many days can we safely print on the label?"* |
| **📏 Quality** | Process capability (Cpk) & defect rate simulation | *"What % of our packs will be underweight?"* |
| **🏷️ Nutrition** | Nutritional label compliance probability (FSSAI/FDA/EU) | *"Will our label pass a regulatory audit?"* |

---

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/yourusername/foodmc.git
cd foodmc
pip install -e .
```

### 1. Formulation Cost Simulation

```python
from foodmc import FormulationSimulator

sim = FormulationSimulator(batch_size_kg=100)

# Add ingredients with price volatility and process variation
sim.add_ingredient("Wheat Flour", mean_cost=38, std_cost=4,
    mean_pct=55, std_pct=1.5,
    nutrition={"calories": 364, "protein": 10.3, "carbs": 76.3, "fat": 1.0})

sim.add_ingredient("Sugar", mean_cost=42, std_cost=6,
    mean_pct=22, std_pct=1.0,
    nutrition={"calories": 387, "carbs": 100, "sugar": 100})

sim.add_ingredient("Palm Oil", mean_cost=95, std_cost=12,
    mean_pct=12, std_pct=0.8,
    nutrition={"calories": 884, "fat": 100})

sim.add_ingredient("Milk Powder", mean_cost=320, std_cost=25,
    mean_pct=5, std_pct=0.5)

results = sim.run(n_simulations=10000)

print(results.summary())
# {'mean': 5765.42, 'std': 412.31, 'p5': 5102.18, 'p95': 6453.87, ...}

print(results.cost_breakdown())
# Shows each ingredient's cost contribution with uncertainty

print(f"P(cost > ₹6000) = {results.probability_cost_exceeds(6000):.1%}")
# P(cost > ₹6000) = 28.4%

results.report("formulation_report.html")  # Generate visual report
```

### 2. Shelf Life Prediction

```python
from foodmc import ShelfLifeSimulator

sim = ShelfLifeSimulator()
sim.configure(
    ea_mean=85,              # Activation energy (kJ/mol)
    ea_std=6,                # Uncertainty from lab studies
    temp_mean=30,            # Storage temp °C (Indian ambient)
    temp_std=5,              # Seasonal variation
    initial_quality=100,     # Fresh product quality score
    quality_std=4,           # Batch-to-batch variation
    threshold=50,            # Unacceptable below this
    reaction_order=1,        # First-order kinetics
    ref_rate=0.008,          # Degradation rate at 25°C
    ref_rate_std=0.0015,     # Rate uncertainty
    quality_attribute="Vitamin C Retention (%)",
)

results = sim.run(n_simulations=10000)

print(f"Mean shelf life: {results.summary()['mean']:.0f} days")
print(f"Safe to print (95%): {results.recommended_shelf_life(0.95):.0f} days")
print(f"Conservative (99%): {results.recommended_shelf_life(0.99):.0f} days")
print(f"P(lasts ≥ 180 days): {results.probability_lasts(180):.1%}")

results.report("shelflife_report.html")
```

### 3. Quality Control (Cpk Analysis)

```python
from foodmc import QualitySimulator

sim = QualitySimulator()

sim.add_parameter("Net Weight", target=50, lsl=48.5, usl=52,
    process_mean=50.3, process_std=0.6, unit="g",
    mean_shift_std=0.15)  # Process drift over time

sim.add_parameter("Moisture", target=2.5, lsl=1.5, usl=3.5,
    process_mean=2.6, process_std=0.35, unit="%")

sim.add_parameter("Seal Strength", target=3.5, lsl=2.8, usl=4.5,
    process_mean=3.55, process_std=0.25, unit="N/15mm")

results = sim.run(n_simulations=10000)

print(results.summary())
# Shows Cpk, defect rate, and yield for each parameter

print(f"Net Weight in-spec: {results.probability_in_spec('Net Weight'):.2%}")

results.report("quality_report.html")
```

### 4. Nutrition Label Compliance

```python
from foodmc import NutritionSimulator

sim = NutritionSimulator(regulation="FSSAI")  # Also: "FDA", "EU"

sim.add_nutrient("calories", declared=250, actual_mean=258, actual_std=12, unit="kcal")
sim.add_nutrient("protein", declared=20, actual_mean=19.2, actual_std=1.5, unit="g")
sim.add_nutrient("fat", declared=8, actual_mean=8.4, actual_std=0.8, unit="g")
sim.add_nutrient("sugar", declared=12, actual_mean=11.5, actual_std=1.2, unit="g")
sim.add_nutrient("sodium", declared=200, actual_mean=215, actual_std=25, unit="mg")

results = sim.run(n_simulations=10000)

print(results.summary())
# Shows compliance rate and risk level per nutrient

print(f"Overall compliance: {results.overall_compliance():.1%}")
# Probability ALL nutrients pass simultaneously

results.report("nutrition_report.html")
```

---

## 📊 HTML Reports

Every module generates a **self-contained HTML report** with:

- Summary metrics with color-coded risk levels
- Monte Carlo distribution histograms
- Confidence intervals and percentile analysis
- Parameter-specific charts (Cpk distributions, degradation curves, compliance gauges)

Reports are single HTML files — no server needed, share via email, open in any browser.

```python
results.report("my_report.html")  # That's it
```

---

## 🔬 Real-World Examples

### Biscuit Manufacturer — Cost Risk Analysis

*"We're launching a new cream biscuit. Butter prices have been volatile. What's the risk our per-batch cost exceeds ₹7,000?"*

```python
sim = FormulationSimulator(batch_size_kg=100)
sim.add_ingredient("Flour", mean_cost=38, std_cost=4, mean_pct=55, std_pct=1.5)
sim.add_ingredient("Sugar", mean_cost=42, std_cost=6, mean_pct=22, std_pct=1.0)
sim.add_ingredient("Butter", mean_cost=450, std_cost=35, mean_pct=15, std_pct=1.0)
sim.add_ingredient("Milk Powder", mean_cost=320, std_cost=25, mean_pct=6, std_pct=0.5)
results = sim.run(n_simulations=10000)

print(f"Risk of exceeding ₹7000: {results.probability_cost_exceeds(7000):.1%}")
```

### Juice Company — Shelf Life for Export

*"We're exporting mango juice to the Middle East. Shipping containers can reach 40°C. What shelf life should we print?"*

```python
sim = ShelfLifeSimulator()
sim.configure(
    ea_mean=85, ea_std=6,
    temp_mean=35, temp_std=5,        # Hot storage conditions
    initial_quality=100, quality_std=4,
    threshold=50, reaction_order=1,
    ref_rate=0.008, ref_rate_std=0.0015,
    quality_attribute="Vitamin C Retention (%)",
)
results = sim.run(n_simulations=10000)
print(f"Print this on label: {results.recommended_shelf_life(0.95):.0f} days")
```

### Snack Company — FSSAI Audit Preparation

*"FSSAI auditors are coming. What's the probability our protein bar label will pass?"*

```python
sim = NutritionSimulator(regulation="FSSAI")
sim.add_nutrient("protein", declared=20, actual_mean=19.2, actual_std=1.5, unit="g")
sim.add_nutrient("fat", declared=8, actual_mean=8.4, actual_std=0.8, unit="g")
results = sim.run(n_simulations=10000)
print(f"Audit pass probability: {results.overall_compliance():.1%}")
```

---

## 🏗️ Project Structure

```
foodmc/
├── foodmc/
│   ├── __init__.py
│   ├── formulation/          # Recipe cost & nutrition simulation
│   │   └── simulator.py
│   ├── shelflife/            # Arrhenius-based shelf life prediction
│   │   └── simulator.py
│   ├── quality/              # Process capability (Cpk) simulation
│   │   └── simulator.py
│   ├── nutrition/            # Label compliance (FSSAI/FDA/EU)
│   │   └── simulator.py
│   ├── reporting/            # HTML report generator
│   │   └── html_report.py
│   └── utils/                # Core Monte Carlo engine
│       └── engine.py
├── tests/
│   └── test_foodmc.py
├── examples/
│   └── quickstart.py         # Run all 4 modules with real examples
├── docs/
├── setup.py
├── requirements.txt
├── LICENSE
└── README.md
```

---

## 🧮 The Math Behind It

### Monte Carlo Simulation
Instead of calculating a single "expected" value, we run thousands of simulations where each input parameter is randomly sampled from its probability distribution. This gives us a **distribution of outcomes** — showing not just what's likely, but what's possible.

### Arrhenius Kinetics (Shelf Life)
Food degradation follows the Arrhenius equation:

```
k(T) = k_ref × exp[(Ea/R) × (1/T_ref - 1/T)]
```

Where `Ea` is activation energy, `R` is the gas constant, and `T` is temperature in Kelvin. By sampling `Ea`, `T`, and initial quality from their uncertainty distributions, we get a probability distribution of shelf life — not just one number.

### Process Capability (Quality)
Cpk measures how well a process fits within specifications:

```
Cpk = min[(USL - μ)/(3σ), (μ - LSL)/(3σ)]
```

By simulating process drift and variation, we see how Cpk changes over time — critical for food safety.

---

## 🤝 Contributing

Contributions welcome! Some ideas:

- 📈 Add sensitivity analysis (tornado charts)
- 🌡️ Add Q10 method for shelf life
- 📊 Add Weibull distribution for shelf life
- 🧪 Add sensory panel simulation
- 🐳 Add Docker support
- 🌐 Add Streamlit web interface

---

## 📄 License

MIT License — see [LICENSE](LICENSE).

---

<div align="center">

**Built by a food scientist, for food scientists.**

*No expensive software licenses were harmed in the making of this project.*

</div>
