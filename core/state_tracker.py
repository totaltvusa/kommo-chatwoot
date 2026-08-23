import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Set, Optional

logger = logging.getLogger("migration.state_tracker")

class StateTracker:
    """
    Persistent state tracker to ensure idempotency across multiple runs.
    Maintains a mapping of kommo_lead_id -> chatwoot_conversation_id / migration details.
    """
    def __init__(self, state_file_path: str):
        self.state_file_path = Path(state_file_path)
        self.data: Dict[str, Any] = {"funnels": {}}
        self.load()

    def load(self):
        if self.state_file_path.exists():
            try:
                with open(self.state_file_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                if "funnels" not in self.data:
                    self.data["funnels"] = {}
                logger.info(f"Loaded existing migration state from '{self.state_file_path}'.")
            except Exception as e:
                logger.error(f"Failed to load state file '{self.state_file_path}': {e}. Starting fresh.")
                self.data = {"funnels": {}}
        else:
            self.data = {"funnels": {}}

    def save(self):
        """Atomically saves state data to JSON file."""
        self.state_file_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.state_file_path.with_suffix(".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            temp_path.replace(self.state_file_path)
        except Exception as e:
            logger.error(f"Failed to save state file '{self.state_file_path}': {e}")

    def get_funnel_state(self, funnel_name: str) -> Dict[str, Any]:
        if funnel_name not in self.data["funnels"]:
            self.data["funnels"][funnel_name] = {
                "pipeline_id": None,
                "last_run_at": None,
                "leads": {}
            }
        return self.data["funnels"][funnel_name]

    def set_pipeline_id(self, funnel_name: str, pipeline_id: int):
        fstate = self.get_funnel_state(funnel_name)
        fstate["pipeline_id"] = pipeline_id

    def is_lead_migrated(self, funnel_name: str, lead_id: int) -> bool:
        """Returns True only if the lead was previously migrated with status 'success'."""
        fstate = self.get_funnel_state(funnel_name)
        lead_record = fstate.get("leads", {}).get(str(lead_id))
        if lead_record and lead_record.get("status") == "success":
            return True
        return False

    def get_migrated_lead_ids(self, funnel_name: str) -> Set[int]:
        """Returns a set of all successfully migrated lead IDs for this funnel."""
        fstate = self.get_funnel_state(funnel_name)
        return {
            int(lid) for lid, rec in fstate.get("leads", {}).items()
            if rec.get("status") == "success"
        }

    def record_lead_migration(
        self,
        funnel_name: str,
        lead_id: int,
        chatwoot_contact_id: Optional[int],
        chatwoot_conversation_id: Optional[int],
        stage_id: int,
        stage_name_kommo: str,
        stage_name_corrected: str,
        labels: list,
        messages_migrated_count: int,
        last_message_date: str,
        migrated_at: str,
        status: str,
        error: Optional[str] = None
    ):
        fstate = self.get_funnel_state(funnel_name)
        fstate["leads"][str(lead_id)] = {
            "chatwoot_contact_id": chatwoot_contact_id,
            "chatwoot_conversation_id": chatwoot_conversation_id,
            "stage_id": stage_id,
            "stage_name_kommo": stage_name_kommo,
            "stage_name_corrected": stage_name_corrected,
            "labels": labels,
            "messages_migrated_count": messages_migrated_count,
            "last_message_date": last_message_date,
            "migrated_at": migrated_at,
            "status": status,
            "error": error
        }
        self.save()
