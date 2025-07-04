from setuptools import setup, find_packages

setup(
    name="crewaidocsmcp",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.11",
    entry_points={
        "console_scripts": [
            "crewai-docs-mcp=main:main",
        ],
    },
)