# Terraform Cloud Policy Check Aggregator

This repository contains a Python script (`sentinel_check.py`) that queries Terraform Cloud (TFC) to retrieve policy checks (Sentinel) for multiple workspaces and runs, then aggregates the results into a single CSV file named `sentinel_check_results.csv`. It is especially useful if you need to evaluate large numbers of workspaces at scale (e.g., 1,500+) to see which ones are passing/failing various Sentinel policies.

---

## Overview

- **Purpose**: Aggregates Sentinel policy check results across many TFC workspaces.
- **Key Features**:
  - Iterates over all workspaces in a TFC organization.
  - Retrieves the last few runs (configurable) for each workspace.
  - Fetches policy check data (e.g., policy names, enforcement levels, pass/fail status).
  - Writes results to `sentinel_check_results.csv`.
  - Logs special cases to the console (e.g., if a policy check is unreachable or returns `null` data).

---

## Prerequisites

1. **Python 3** and the `requests` library:
   ```bash
   pip install requests
2. **Terraform Cloud token**: Must be exported as an environment variable `TFC_TOKEN`.
3. **Organization name** (for Terraform Cloud) set in:
   - `TFC_ORG` environment variable, **or**
   - Hard-coded within the script (not recommended).
4. **Network access**: Ensure you can reach `app.terraform.io` or your private Terraform Enterprise instance.

---

## Usage

1. **Clone or Download** this repository.

2. **Install Dependencies**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install requests
   ```
   
3. Export Environment Variables
   ```bash
    export TFC_TOKEN=<YOUR_TFC_API_TOKEN>
    export TFC_ORG=<YOUR_ORG_NAME>
   ```
   - (If you’re on a private Terraform Enterprise, also set TFC_BASE_URL accordingly.)
     
4. Run the script
   ```bash
   python sentinel_check.py
   ```
   
5. View the Results
The script will create a file called `sentinel_check_results.csv` in the same directory.  
Each row contains details such as:

- **Workspace ID & name**
- **Run ID & creation timestamp**
- **Policy name & enforcement level**
- **Policy pass/fail**
- A **`detailed_reason`** which typically includes the policy description or a brief message indicating why it passed or failed.


## Debug Logs for “Unreachable” or null Policy Checks
During execution, you may see console messages like:
```bash
DEBUG: Policy check unreachable or result is None. Full JSON:
{
   "id": "polchk-XYZ",
   "type": "policy-checks",
   "attributes": {
       "result": null,
       "status": "unreachable",
       ...
   }
}
```
This indicates **Terraform Cloud did not run (or could not run) Sentinel** for that policy check. Common causes:

- **Canceled or errored runs** where Sentinel had no opportunity to evaluate.
- **Policy set misconfiguration** (e.g., repository issues).
- **Network or service disruption** causing the policy check to remain unreachable.

### What to do:
- If these checks are **expected** (e.g., older runs, canceled runs, or misconfigured policy sets), you can ignore them.
- If **unexpected**, investigate the run status in TFC, verify your policy set is correctly configured, and ensure TFC has access to the policy source.

No CSV rows are written for these “unreachable” checks since there is no actual policy data to record.


## Notes & Customization

- **Pagination**: The script fetches workspaces in batches of `PAGE_SIZE=100`. Adjust if necessary.
- **Runs Per Workspace**: Defaults to fetching the last 5 runs. Modify the `RUNS_TO_FETCH` value in the script as desired.
- **Parallelization**: If you have thousands of workspaces, consider parallel or batch execution to speed up data collection, while respecting TFC’s API rate limits.
