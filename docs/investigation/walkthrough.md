# Walkthrough: Kommo to Chatwoot Migration Tool

We have implemented the full standalone, reusable migration suite for migrating funnels from **Kommo CRM** to a self-hosted **Chatwoot** instance according to all requirements in STEP 1.

---

## 1. Project Implementation Overview

The migration suite is organized into a modular architecture in [`/home/alvez/.gemini/antigravity/scratch/kommo_chatwoot_migration/`](file:///home/alvez/.gemini/antigravity/scratch/kommo_chatwoot_migration/):

* [`migrate.py`](file:///home/alvez/.gemini/antigravity/scratch/kommo_chatwoot_migration/migrate.py): Main CLI orchestrator (`--funnel`, `--limit`, `--dry-run`, `--force`).
* [`config.py`](file:///home/alvez/.gemini/antigravity/scratch/kommo_chatwoot_migration/config.py): Environment and settings loader (`.env`).
* [`stage_name_overrides.json`](file:///home/alvez/.gemini/antigravity/scratch/kommo_chatwoot_migration/stage_name_overrides.json): Stage typo and normalization mapping dictionary.
* [`core/kommo_client.py`](file:///home/alvez/.gemini/antigravity/scratch/kommo_chatwoot_migration/core/kommo_client.py): Kommo REST API v4 client for dynamic pipeline discovery, paginated lead fetching, contacts, notes, and activity history.
* [`core/chatwoot_client.py`](file:///home/alvez/.gemini/antigravity/scratch/kommo_chatwoot_migration/core/chatwoot_client.py): Chatwoot API v1 client for contact search/create/update, conversation creation, chronological message insertion with `[Original date: YYYY-MM-DD]` prefix, and label assignment.
* [`core/stage_resolver.py`](file:///home/alvez/.gemini/antigravity/scratch/kommo_chatwoot_migration/core/stage_resolver.py): Normalizes stage names, checks overrides, emits warnings for unmapped stages, and slugifies names into `funnel-<slug>` and `stage-<slug>`.
* [`core/state_tracker.py`](file:///home/alvez/.gemini/antigravity/scratch/kommo_chatwoot_migration/core/state_tracker.py): Persistent idempotency engine (`output/migration_state.json`) ensuring resumed runs pick up only unmigrated leads.
* [`core/report_generator.py`](file:///home/alvez/.gemini/antigravity/scratch/kommo_chatwoot_migration/core/report_generator.py): `openpyxl` Excel logger managing `output/migration_log.xlsx` with one tab per funnel, in-place row updating by `Kommo Lead ID`, and file-lock protection.
* [`core/rate_limiter.py`](file:///home/alvez/.gemini/antigravity/scratch/kommo_chatwoot_migration/core/rate_limiter.py): Automatic exponential backoff and jitter for `HTTP 429` and `HTTP 5xx`.

---

## 2. Dry-Run Verification Results (`TotalTv USA`)

We executed a dry-run test against live Kommo data:
```bash
python3 migrate.py --funnel "TotalTv USA" --dry-run
```

### Stage Resolution & Overrides
* **Pipeline ID**: `6747643` ("TotalTv USA")
* **Stages Discovered**:
  * `Leads Entrantes` *(Unmapped warning emitted)* -> Label: `stage-leads-entrantes`
  * `Contacted` *(Unmapped warning emitted)* -> Label: `stage-contacted`
  * `Trials` *(Unmapped warning emitted)* -> Label: `stage-trials`
  * `Want to join?` -> Corrected to **`Want To Join`** -> Label: `stage-want-to-join`
  * `Remember Joinning` -> Corrected to **`Remember Joining`** -> Label: `stage-remember-joining`
  * `Leads ganados` -> Corrected to **`Leads Ganados`** -> Label: `stage-leads-ganados`
  * `Leads perdidos` -> Corrected to **`Leads Perdidos`** -> Label: `stage-leads-perdidos`

### Batch Execution & Safety Cap
* **Total leads matching funnel in Kommo**: 328
* **Already migrated**: 0
* **Remaining unmigrated**: 328
* **Processed in batch**: **10 leads** *(capped by default `--limit 10`)*

### Output Artifacts Generated
* **Excel Log**: [`output/migration_log.xlsx`](file:///home/alvez/.gemini/antigravity/scratch/kommo_chatwoot_migration/output/migration_log.xlsx) (Tab: `TotalTv USA` with 10 formatted rows and header).
* **State File**: [`output/migration_state.json`](file:///home/alvez/.gemini/antigravity/scratch/kommo_chatwoot_migration/output/migration_state.json).
