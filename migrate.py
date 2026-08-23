#!/usr/bin/env python3
"""
Kommo CRM to Chatwoot Migration Tool
====================================
Migrates leads, contacts, conversation history, notes, and stages from Kommo
to a self-hosted Chatwoot instance.

Usage:
  python migrate.py --funnel "TotalTv USA" [--limit 10] [--dry-run] [--force]
"""

import os
import sys
import argparse
import datetime
import logging
from typing import Dict, List, Any, Optional

from config import Config
from core.stage_resolver import StageResolver
from core.state_tracker import StateTracker
from core.report_generator import ReportGenerator
from core.kommo_client import KommoClient
from core.chatwoot_client import ChatwootClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("migration")

def print_banner(title: str):
    width = 80
    print("\n" + "=" * width)
    print(f" {title.upper()}")
    print("=" * width)

def print_section(title: str):
    print("\n" + "-" * 80)
    print(f"[*] {title}")
    print("-" * 80)

def main():
    parser = argparse.ArgumentParser(description="Kommo to Chatwoot Funnel Migration Tool")
    parser.add_argument("--funnel", "-f", required=True, help="Exact name of the Kommo Funnel / Pipeline (e.g. 'TotalTv USA')")
    parser.add_argument("--limit", "-l", type=int, default=10, help="Max unmigrated leads to process in this run (Default: 10, use 0 for unlimited)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate migration without making write calls to Chatwoot")
    parser.add_argument("--force", action="store_true", help="Re-sync leads that were previously migrated")
    
    args = parser.parse_args()
    funnel_name = args.funnel.strip()
    limit = args.limit
    dry_run = args.dry_run
    force = args.force

    print_banner(f"Kommo -> Chatwoot Migration: Funnel '{funnel_name}'" + (" [DRY-RUN MODE]" if dry_run else ""))

    # 1. Validate configuration
    Config.validate_kommo()
    Config.validate_chatwoot(dry_run=dry_run)

    # 2. Initialize Clients & Modules
    kommo = KommoClient(
        subdomain=Config.KOMMO_SUBDOMAIN,
        access_token=Config.KOMMO_ACCESS_TOKEN
    )
    
    chatwoot = None
    if not dry_run:
        chatwoot = ChatwootClient(
            base_url=Config.CHATWOOT_BASE_URL,
            account_id=Config.CHATWOOT_ACCOUNT_ID,
            api_token=Config.CHATWOOT_API_TOKEN,
            inbox_id=Config.CHATWOOT_INBOX_ID
        )

    stage_resolver = StageResolver(Config.STAGE_OVERRIDES_PATH)
    state_tracker = StateTracker(Config.STATE_FILE_PATH)
    report_gen = ReportGenerator(Config.LOCAL_REPORT_PATH)

    # 3. Dynamically resolve Funnel / Pipeline from Kommo
    print_section(f"Resolving Pipeline '{funnel_name}' from Kommo API")
    pipeline = kommo.get_pipeline_by_name(funnel_name)
    if not pipeline:
        print(f"\n[!] Error: Pipeline '{funnel_name}' not found in Kommo.")
        print("    Available pipelines:")
        for p in kommo.get_pipelines():
            print(f"      - \"{p.get('name')}\" (ID: {p.get('id')})")
        sys.exit(1)

    pipeline_id = pipeline["id"]
    statuses_map = pipeline["statuses"] # Dict[status_id, status_name]
    state_tracker.set_pipeline_id(funnel_name, pipeline_id)

    print(f"[+] Found Pipeline '{pipeline['name']}' (ID: {pipeline_id}) with {len(statuses_map)} stages:")
    stage_corrections_used = {}
    for sid, sname in statuses_map.items():
        corrected, is_overridden = stage_resolver.resolve_stage(sname, pipeline_name=funnel_name)
        _, stage_slug, _ = stage_resolver.get_labels(funnel_name, sname)
        stage_corrections_used[sname] = {
            "corrected": corrected,
            "overridden": is_overridden,
            "label": stage_slug
        }
        status_tag = f"-> Corrected: '{corrected}'" if is_overridden else "(No override)"
        print(f"    - Stage [{sid}]: \"{sname}\" {status_tag} | Label: '{stage_slug}'")

    # 4. Fetch all Leads in Pipeline
    print_section(f"Fetching Leads for Funnel '{funnel_name}'")
    all_leads = kommo.get_leads_in_pipeline(pipeline_id)
    total_leads_count = len(all_leads)
    
    migrated_lead_ids = state_tracker.get_migrated_lead_ids(funnel_name)
    
    if force:
        leads_to_evaluate = all_leads
    else:
        leads_to_evaluate = [l for l in all_leads if l["id"] not in migrated_lead_ids]

    unmigrated_count = len(leads_to_evaluate)
    
    # Apply limit
    if limit > 0:
        leads_batch = leads_to_evaluate[:limit]
    else:
        leads_batch = leads_to_evaluate

    batch_count = len(leads_batch)

    print(f"\n[LEAD BATCH SUMMARY]")
    print(f"  * Total leads matching funnel in Kommo: {total_leads_count}")
    print(f"  * Already migrated in previous runs:    {len(migrated_lead_ids)}")
    print(f"  * Remaining unmigrated leads:           {unmigrated_count}")
    print(f"  * Processing in this run:               {batch_count} lead(s)" + (f" (capped by --limit {limit})" if limit > 0 else " (unlimited)"))

    if batch_count == 0:
        print("\n[+] All leads in this funnel have already been migrated! Nothing to process.")
        sys.exit(0)

    # 5. Process Leads Batch
    print_section(f"Processing {batch_count} Lead(s)")

    stats = {
        "contacts_created": 0,
        "contacts_updated": 0,
        "conversations_created": 0,
        "messages_migrated": 0,
        "labels_applied": 0,
        "errors": []
    }

    today_str = datetime.date.today().strftime("%Y-%m-%d")

    for idx, lead in enumerate(leads_batch, 1):
        lead_id = lead["id"]
        lead_name = lead.get("name") or f"Lead #{lead_id}"
        status_id = lead.get("status_id")
        raw_stage_name = statuses_map.get(status_id, f"Stage #{status_id}")
        
        funnel_label, stage_label, corrected_stage = stage_resolver.get_labels(funnel_name, raw_stage_name)
        channel_label = kommo.get_lead_channel(lead_id)
        labels = [funnel_label, stage_label, channel_label]

        print(f"\n[{idx}/{batch_count}] Processing Kommo Lead #{lead_id} ('{lead_name}') | Stage: '{corrected_stage}' | Channel: '{channel_label}'")

        try:
            # 5a. Fetch linked Contact details
            contacts = lead.get("_embedded", {}).get("contacts", [])
            contact_ids = [c["id"] for c in contacts if "id" in c]
            
            contact_info = {"name": lead_name, "phone": "", "email": ""}
            if contact_ids:
                primary_contact_id = contact_ids[0]
                contact_info = kommo.get_contact_details(primary_contact_id)
            
            print(f"    Contact: Name='{contact_info['name']}', Phone='{contact_info['phone']}', Email='{contact_info['email']}'")

            # 5b. Fetch history / notes
            history_messages, last_message_date = kommo.get_lead_history(lead_id, contact_ids)
            print(f"    History: {len(history_messages)} message(s)/note(s) | Last Active Date: {last_message_date}")
            print(f"    Labels:  {labels}")

            cw_contact_id = None
            cw_conv_id = None

            if dry_run:
                # Dry run simulation
                cw_contact_id = 999000 + idx
                cw_conv_id = 888000 + idx
                stats["contacts_created"] += 1
                stats["conversations_created"] += 1
                stats["messages_migrated"] += len(history_messages)
                stats["labels_applied"] += len(labels)
                print(f"    [DRY-RUN] Would create Contact ID #{cw_contact_id}, Conversation ID #{cw_conv_id} with labels {labels}")
            else:
                # 5c. Chatwoot Contact Create / Update
                custom_attrs = {
                    "kommo_lead_id": lead_id,
                    "kommo_pipeline": funnel_name,
                    "kommo_stage": corrected_stage
                }
                c_res = chatwoot.create_or_update_contact(
                    name=contact_info["name"],
                    phone_number=contact_info["phone"],
                    email=contact_info["email"],
                    custom_attributes=custom_attrs
                )
                cw_contact_id = c_res["id"]
                if c_res["action"] == "created":
                    stats["contacts_created"] += 1
                else:
                    stats["contacts_updated"] += 1

                # 5d. Chatwoot Conversation Create
                conv_custom_attrs = {
                    "kommo_lead_id": lead_id,
                    "funnel": funnel_name,
                    "stage": corrected_stage
                }
                cw_conv_id = chatwoot.create_conversation(
                    contact_id=cw_contact_id,
                    custom_attributes=conv_custom_attrs,
                    status="resolved"
                )
                stats["conversations_created"] += 1

                # 5e. Insert Messages
                for msg in history_messages:
                    chatwoot.create_message(
                        conversation_id=cw_conv_id,
                        content=msg["content"],
                        message_type=msg["message_type"],
                        private=False
                    )
                    stats["messages_migrated"] += 1

                # 5f. Apply Labels
                chatwoot.apply_labels_to_conversation(cw_conv_id, labels)
                stats["labels_applied"] += len(labels)

                # 5g. Update Idempotency State
                state_tracker.record_lead_migration(
                    funnel_name=funnel_name,
                    lead_id=lead_id,
                    chatwoot_contact_id=cw_contact_id,
                    chatwoot_conversation_id=cw_conv_id,
                    stage_id=status_id,
                    stage_name_kommo=raw_stage_name,
                    stage_name_corrected=corrected_stage,
                    labels=labels,
                    messages_migrated_count=len(history_messages),
                    last_message_date=last_message_date,
                    migrated_at=today_str,
                    status="success"
                )

            # 5h. Log to Excel workbook
            report_gen.log_lead_migration(
                funnel_name=funnel_name,
                lead_id=lead_id,
                contact_name=contact_info["name"],
                contact_phone=contact_info["phone"],
                contact_email=contact_info["email"],
                stage_name=corrected_stage,
                chatwoot_contact_id=cw_contact_id,
                chatwoot_conversation_id=cw_conv_id,
                labels_applied=labels,
                messages_migrated_count=len(history_messages),
                last_message_date=last_message_date,
                migration_date=today_str,
                status="success" if not dry_run else "dry_run"
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error processing Lead #{lead_id}: {error_msg}")
            stats["errors"].append({"lead_id": lead_id, "error": error_msg})
            
            # Log error in state & excel
            state_tracker.record_lead_migration(
                funnel_name=funnel_name,
                lead_id=lead_id,
                chatwoot_contact_id=None,
                chatwoot_conversation_id=None,
                stage_id=status_id,
                stage_name_kommo=raw_stage_name,
                stage_name_corrected=corrected_stage,
                labels=labels,
                messages_migrated_count=0,
                last_message_date=today_str,
                migrated_at=today_str,
                status="error",
                error=error_msg
            )
            report_gen.log_lead_migration(
                funnel_name=funnel_name,
                lead_id=lead_id,
                contact_name=contact_info.get("name", ""),
                contact_phone=contact_info.get("phone", ""),
                contact_email=contact_info.get("email", ""),
                stage_name=corrected_stage,
                chatwoot_contact_id=None,
                chatwoot_conversation_id=None,
                labels_applied=labels,
                messages_migrated_count=0,
                last_message_date=today_str,
                migration_date=today_str,
                status="error",
                error_detail=error_msg
            )

    # 6. Final Summary
    print_banner(f"Migration Summary: Funnel '{funnel_name}'" + (" [DRY-RUN]" if dry_run else ""))
    print(f"  * Contacts Created:      {stats['contacts_created']}")
    print(f"  * Contacts Updated:      {stats['contacts_updated']}")
    print(f"  * Conversations Created: {stats['conversations_created']}")
    print(f"  * Messages Inserted:     {stats['messages_migrated']}")
    print(f"  * Labels Applied:        {stats['labels_applied']}")
    print(f"  * Excel Report:          {Config.LOCAL_REPORT_PATH} (Sheet: '{funnel_name[:31]}')")
    print(f"  * State File:            {Config.STATE_FILE_PATH}")

    if stats["errors"]:
        print(f"\n[!] Encounted {len(stats['errors'])} Error(s):")
        for err in stats["errors"]:
            print(f"    - Lead #{err['lead_id']}: {err['error']}")
    else:
        print("\n[+] All leads in batch processed successfully with zero errors!")

if __name__ == "__main__":
    main()
