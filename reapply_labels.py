#!/usr/bin/env python3
"""
Retroactive label re-application script.
Re-applies funnel + stage labels to all conversations already in the state file.
Run this AFTER manually creating label definitions in Chatwoot Settings > Labels.
"""
import json
import requests
import sys
import os

# Load .env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

BASE_URL  = os.environ["CHATWOOT_BASE_URL"].rstrip("/")
ACCOUNT   = os.environ["CHATWOOT_ACCOUNT_ID"]
TOKEN     = os.environ["CHATWOOT_API_TOKEN"].strip()
STATE_FILE = os.path.join(os.path.dirname(__file__), "output", "migration_state.json")

HEADERS = {
    "api_access_token": TOKEN,
    "Content-Type": "application/json",
    "Accept": "application/json",
}

def apply_labels(conversation_id: int, labels: list[str]) -> bool:
    url = f"{BASE_URL}/api/v1/accounts/{ACCOUNT}/conversations/{conversation_id}/labels"
    r = requests.post(url, headers=HEADERS, json={"labels": labels}, timeout=15)
    if r.status_code in (200, 201):
        actual = r.json().get("payload", [])
        return actual == sorted(labels) or set(actual) == set(labels)
    print(f"  ERROR {r.status_code}: {r.text[:120]}")
    return False

def main():
    with open(STATE_FILE) as f:
        state = json.load(f)

    funnels = state.get("funnels", {})
    total = 0
    ok = 0

    for funnel_name, funnel_data in funnels.items():
        leads = funnel_data.get("leads", {})
        print(f"\n[Funnel: {funnel_name}] — {len(leads)} leads in state")
        for lead_id, info in leads.items():
            cid    = info.get("chatwoot_conversation_id")
            labels = info.get("labels", [])
            status = info.get("status")
            if not cid or not labels or status != "success":
                continue
            total += 1
            success = apply_labels(cid, labels)
            icon = "✓" if success else "✗"
            print(f"  {icon} Lead #{lead_id} → Conv #{cid} | Labels: {labels}")
            if success:
                ok += 1

    print(f"\n{'='*60}")
    print(f"Re-applied labels: {ok}/{total} conversations updated successfully.")
    if ok < total:
        print("Some conversations failed — check errors above.")
        sys.exit(1)
    else:
        print("All done!")

if __name__ == "__main__":
    main()
