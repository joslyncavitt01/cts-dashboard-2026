#!/bin/bash
# Run this once a week (or anytime) to refresh the dashboard data.
# Requires: pip install google-cloud-bigquery google-auth

set -e

echo "Fetching adoption data from BigQuery..."
python3 fetch_data.py

echo "Pushing to GitHub..."
git add data/adoptions.json
git diff --staged --quiet && echo "No new data." && exit 0
git commit -m "Update adoption data $(date +'%Y-%m-%d')"
git push origin main

echo "Done. Dashboard will update in ~30 seconds."
