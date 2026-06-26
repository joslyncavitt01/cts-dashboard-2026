#!/bin/bash
# Run this once a week (or anytime) to refresh the dashboard data.

set -e

cd "$(dirname "$0")"

# Create virtual environment on first run
if [ ! -d ".venv" ]; then
  echo "Setting up Python environment (first run only)..."
  python3 -m venv .venv
  .venv/bin/pip install --quiet google-cloud-bigquery
fi

echo "Fetching adoption data from BigQuery..."
.venv/bin/python fetch_data.py

echo "Pushing to GitHub..."
git add data/adoptions.json
git diff --staged --quiet && echo "No new data." && exit 0
git commit -m "Update adoption data $(date +'%Y-%m-%d')"
git push origin main

echo "Done. Dashboard will update in ~30 seconds."
