#!/bin/bash

# Activate virtual environment and run tests
source .venv/bin/activate

# Add the project root to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run tests
python -m pytest app/tests/ -v
