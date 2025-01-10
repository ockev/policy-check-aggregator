import os
import requests
import csv
import json

# =========================================
# Configuration
# =========================================
TFC_TOKEN = os.environ.get("TFC_TOKEN")
TFC_ORG = os.environ.get("TFC_ORG", "my-organization")
TFC_BASE_URL = os.environ.get("TFC_BASE_URL", "https://app.terraform.io/api/v2")

# How many runs per workspace to retrieve?
RUNS_TO_FETCH = 5

# How many workspaces to fetch per page
PAGE_SIZE = 100

HEADERS = {
    "Authorization": f"Bearer {TFC_TOKEN}",
    "Content-Type": "application/vnd.api+json",
}

def get_all_workspaces(page_size=100):
    """
    Returns a list of *all* workspaces in the org.
    Uses pagination to avoid 422 errors from large page sizes.
    """
    all_workspaces = []
    next_page_url = f"{TFC_BASE_URL}/organizations/{TFC_ORG}/workspaces?page%5Bsize%5D={page_size}"

    while next_page_url:
        response = requests.get(next_page_url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        all_workspaces.extend(data["data"])

        links = data.get("links", {})
        next_page_url = links.get("next")

    return all_workspaces

def get_runs_for_workspace(workspace_id, runs_to_fetch=5):
    """
    Retrieves a specified number of runs for a given workspace.
    """
    runs = []
    url = f"{TFC_BASE_URL}/workspaces/{workspace_id}/runs"
    params = {
        "page[size]": runs_to_fetch,
        "sort": "-created-at"
    }
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    data = response.json()
    runs.extend(data["data"])
    return runs

def get_policy_checks_for_run(run_id):
    """
    Retrieves the policy checks (Sentinel) for a given run.
    """
    url = f"{TFC_BASE_URL}/runs/{run_id}/policy-checks"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()["data"]

def main():
    workspaces = get_all_workspaces(page_size=PAGE_SIZE)

    # Updated output CSV filename
    with open("sentinel_check_results.csv", "w", newline="") as csvfile:
        fieldnames = [
            "workspace_id",
            "workspace_name",
            "run_id",
            "run_created_at",
            "policy_name",
            "enforcement_level",
            "policy_passed",
            "detailed_reason",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for ws in workspaces:
            ws_id = ws["id"]
            ws_name = ws["attributes"]["name"]

            runs = get_runs_for_workspace(ws_id, runs_to_fetch=RUNS_TO_FETCH)
            if not runs:
                continue

            for run in runs:
                run_id = run["id"]
                run_created_at = run["attributes"]["created-at"]

                policy_checks = get_policy_checks_for_run(run_id)
                if not policy_checks:
                    continue

                for pc in policy_checks:
                    # If status is unreachable or result is None, print debug and skip
                    status = pc["attributes"].get("status")
                    result_obj = pc["attributes"].get("result")

                    if status == "unreachable" or result_obj is None:
                        print("DEBUG: Policy check unreachable or result is None. Full JSON:")
                        print(json.dumps(pc, indent=2))
                        continue

                    # If we do have a result, it often has a 'sentinel' -> 'data' -> ...
                    sentinel_obj = result_obj.get("sentinel", {})
                    data_obj = sentinel_obj.get("data", {})

                    # Iterate over possible keys in 'data'
                    for sentinel_key, sentinel_data in data_obj.items():
                        policies_list = sentinel_data.get("policies", [])
                        for policy_item in policies_list:
                            policy_info = policy_item.get("policy", {})
                            policy_name = policy_info.get("name", "N/A")
                            enforcement_level = policy_info.get("enforcement-level", "N/A")
                            policy_passed = policy_item.get("result", None)

                            trace_obj = policy_item.get("trace", {})
                            detailed_reason = trace_obj.get("description", "No description")

                            writer.writerow({
                                "workspace_id": ws_id,
                                "workspace_name": ws_name,
                                "run_id": run_id,
                                "run_created_at": run_created_at,
                                "policy_name": policy_name,
                                "enforcement_level": enforcement_level,
                                "policy_passed": policy_passed,
                                "detailed_reason": detailed_reason,
                            })

if __name__ == "__main__":
    main()
