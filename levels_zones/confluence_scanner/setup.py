# C:\XIIITradingSystems\Meridian\levels_zones\confluence_scanner\setup.py

"""
Setup script for Zone Scanner
"""

from setuptools import setup, find_packages

setup(
    name='zone-scanner',
    version='1.0.0',
    description='Zone-First M15 Confluence Scanner',
    author='XIII Trading Systems',
    packages=find_packages(),
    install_requires=[
        'pandas>=2.0.0',
        'numpy>=1.24.0',
        'requests>=2.28.0',
        'python-dotenv>=1.0.0',
        'scipy>=1.10.0',
    ],
    entry_points={
        'console_scripts': [
            'zone-scanner=cli:main',
        ],
    },
    python_requires='>=3.8',
)