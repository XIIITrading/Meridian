from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="meridian-trading-system",
    version="1.0.0",
    author="Your Name",
    description="Pre-market trading analysis system with confluence calculations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "PyQt6>=6.5.0",
        "python-dotenv>=1.0.0",
        "supabase>=2.0.0",
        "polygon-api-client>=1.12.6",
        "pandas>=2.0.3",
        "numpy>=1.24.3",
    ],
    entry_points={
        "console_scripts": [
            "meridian=main:main",
        ],
    },
)