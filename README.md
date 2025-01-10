# policy-check-aggregator
This repository contains a Python script (`sentinel_check.py`) that queries Terraform Cloud (TFC) to retrieve policy checks (Sentinel) for multiple workspaces and runs, then aggregates the results into a single CSV file named `sentinel_check_results.csv` to see which ones are passing/failing various Sentinel policies.
