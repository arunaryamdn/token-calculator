"""
Setup configuration for token-calculator package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="token-calculator",
    version="0.1.0",
    author="TokenCost Contributors",
    author_email="",
    description="LLM Token Optimization and Cost Management for Developers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/arunaryamdn/Know-your-tokens",
    packages=find_packages(exclude=["tests", "examples"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "tiktoken>=0.5.0",  # For OpenAI tokenization
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "all": [
            "transformers>=4.30.0",  # For other model tokenizers
            "anthropic>=0.3.0",  # For Claude tokenization
        ],
    },
    keywords="llm tokens optimization cost ai gpt claude gemini tokenizer",
    project_urls={
        "Bug Reports": "https://github.com/arunaryamdn/Know-your-tokens/issues",
        "Source": "https://github.com/arunaryamdn/Know-your-tokens",
    },
)
