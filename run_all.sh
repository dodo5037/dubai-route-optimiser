#!/usr/bin/env bash
# Runs the experiments (about 5 minutes: the optimiser gets 10 s per day), charts and tests.
set -euo pipefail
cd "$(dirname "$0")/src"
python run_experiments.py
python charts.py
cd .. && python -m pytest -q
