# Contributing to FoodMC

Thanks for your interest! Here's how to contribute.

## Quick Start

```bash
git clone https://github.com/yourusername/foodmc.git
cd foodmc
pip install -e .
python -m pytest tests/ -v
```

## How to Contribute

1. **Fork** the repo
2. **Create a branch**: `git checkout -b feature/your-feature`
3. **Make changes** and add tests
4. **Run tests**: `python -m pytest tests/ -v`
5. **Commit**: `git commit -m "feat: description"`
6. **Push** and open a **Pull Request**

## Adding a New Simulator Module

1. Create `foodmc/your_module/simulator.py` with a `YourSimulator` class
2. Follow the pattern: `configure()` → `run()` → returns `YourResult`
3. Add report generation in `foodmc/reporting/html_report.py`
4. Add tests in `tests/`
5. Export from `foodmc/__init__.py`
6. Add examples and update README

## Ideas for Contributions

- Sensitivity analysis (tornado charts)
- Q10 shelf life method
- Weibull distribution support
- Sensory panel simulation
- Streamlit web interface
- Water activity (aw) prediction module

## Code Style

- PEP 8
- NumPy-style docstrings
- Type hints on function signatures

Thank you for helping make food R&D more data-driven!
