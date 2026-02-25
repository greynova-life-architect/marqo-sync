"""Setup file for codebase-indexer package."""
from setuptools import setup, find_packages

setup(
    name="codebase-indexer",
    version="0.1.0",
    description="Semantic code search service for Continue.dev integration",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "marqo",
        "watchdog",
        "python-dotenv"
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "codebase-indexer=src.sync.main_enhanced:main",
        ],
    },
) 