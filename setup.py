from setuptools import setup, find_packages

setup(
    name="context-packer",
    version="0.1.0",
    description="CLI tool to pack repository structure and code into a single Markdown file for LLMs.",
    author="RVckitt",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "context-packer=context_packer.cli:run",
        ],
    },
    python_requires=">=3.8",
)
