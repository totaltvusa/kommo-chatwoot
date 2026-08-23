import json
import re
import unicodedata
import logging
from pathlib import Path
from typing import Dict, Tuple, Optional

logger = logging.getLogger("migration.stage_resolver")

def slugify(text: str) -> str:
    """
    Converts a string to a clean, lowercase, hyphenated slug.
    Handles accents/diacritics and strips punctuation.
    Example: 'Want to join?' -> 'want-to-join'
             'Logrado con éxito' -> 'logrado-con-exito'
    """
    # Normalize unicode (decompose accented chars like é -> e + accent)
    text = unicodedata.normalize("NFKD", text)
    # Encode to ASCII bytes, ignoring non-ascii, then decode back
    text = text.encode("ascii", "ignore").decode("utf-8")
    # Convert to lowercase
    text = text.lower()
    # Replace any non-alphanumeric character with a hyphen
    text = re.sub(r"[^\w\s-]", "", text).strip()
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")

class StageResolver:
    def __init__(self, overrides_path: Optional[str] = None):
        self.overrides_path = Path(overrides_path) if overrides_path else None
        self.overrides: Dict[str, str] = {}
        self.load_overrides()

    def load_overrides(self):
        """Load stage name correction mapping from JSON file."""
        if self.overrides_path and self.overrides_path.exists():
            try:
                with open(self.overrides_path, "r", encoding="utf-8") as f:
                    self.overrides = json.load(f)
                logger.info(f"Loaded {len(self.overrides)} stage override rules from '{self.overrides_path}'.")
            except Exception as e:
                logger.error(f"Failed to load stage overrides from '{self.overrides_path}': {e}")
        else:
            logger.warning(f"Stage overrides file not found at '{self.overrides_path}'. Running with empty overrides.")

    def resolve_stage(self, stage_name: str, pipeline_name: str = "") -> Tuple[str, bool]:
        """
        Resolves stage name against correction dictionary.
        Returns:
          (corrected_stage_name, is_overridden)
        Logs a warning if stage is not found in dictionary.
        """
        raw_name = stage_name.strip()
        if raw_name in self.overrides:
            corrected = self.overrides[raw_name]
            return corrected, True
        else:
            logger.warning(
                f"[STAGE OVERRIDE MISSING] Stage '{raw_name}' (Pipeline: '{pipeline_name}') "
                f"has no entry in stage_name_overrides.json. Using original name '{raw_name}'."
            )
            return raw_name, False

    def get_labels(self, funnel_name: str, stage_name: str) -> Tuple[str, str, str]:
        """
        Returns:
          (funnel_label, stage_label, corrected_stage_name)
          Example: ('funnel-totaltv-usa', 'stage-remember-joining', 'Remember Joining')
        """
        corrected_stage, _ = self.resolve_stage(stage_name, pipeline_name=funnel_name)
        
        funnel_slug = slugify(funnel_name)
        stage_slug = slugify(corrected_stage)
        
        funnel_label = f"funnel-{funnel_slug}"
        stage_label = f"stage-{stage_slug}"
        
        return funnel_label, stage_label, corrected_stage
