from setuptools import setup, find_packages
from pathlib import Path

long_description = (Path(__file__).parent / "README.md").read_text(encoding="utf-8")

setup(
    name="foodmc",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Monte Carlo Simulation Toolkit for Food R&D — formulation, shelf life, quality & nutrition compliance.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/foodmc",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        "matplotlib>=3.4.0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Manufacturing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering",
    ],
    keywords="monte-carlo food-science formulation shelf-life quality-control nutrition fssai simulation",
)
