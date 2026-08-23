import logging
import datetime
from typing import Dict, List, Any, Optional, Tuple
from core.rate_limiter import RateLimitedSession

logger = logging.getLogger("migration.kommo_client")

class KommoClient:
    """
    Client for interacting with Kommo REST API v4.
    """
    def __init__(self, subdomain: str, access_token: str, base_domain: str = "kommo.com"):
        self.subdomain = subdomain.strip().replace(f".{base_domain}", "").replace("https://", "").replace("http://", "")
        self.access_token = access_token.strip()
        self.base_domain = base_domain
        self.base_url = f"https://{self.subdomain}.{self.base_domain}/api/v4"
        
        self.session = RateLimitedSession(max_retries=5, backoff_base=1.5)
        self.session.session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "User-Agent": "Kommo-Chatwoot-Migrator/1.0"
        })

    def get_pipelines(self) -> List[Dict[str, Any]]:
        """Fetches all pipelines and their stages from Kommo."""
        url = f"{self.base_url}/leads/pipelines"
        resp = self.session.get(url, timeout=15)
        if resp.status_code == 200:
            return resp.json().get("_embedded", {}).get("pipelines", [])
        elif resp.status_code == 204:
            return []
        else:
            raise RuntimeError(f"Failed to fetch pipelines: HTTP {resp.status_code} - {resp.text}")

    def get_pipeline_by_name(self, funnel_name: str) -> Optional[Dict[str, Any]]:
        """
        Dynamically finds a pipeline by its name (case-insensitive search).
        Returns pipeline dict containing:
          - id: int
          - name: str
          - statuses: Dict[int, str] (mapping status_id -> status_name)
        """
        pipelines = self.get_pipelines()
        target_name_clean = funnel_name.strip().lower()
        
        for p in pipelines:
            if p.get("name", "").strip().lower() == target_name_clean:
                statuses_map = {}
                raw_statuses = p.get("_embedded", {}).get("statuses", [])
                for s in raw_statuses:
                    statuses_map[s["id"]] = s.get("name", "").strip()
                
                return {
                    "id": p["id"],
                    "name": p["name"].strip(),
                    "statuses": statuses_map,
                    "raw": p
                }
        return None

    def get_leads_in_pipeline(self, pipeline_id: int) -> List[Dict[str, Any]]:
        """
        Fetches all leads in the specified pipeline using pagination.
        """
        all_leads = []
        page = 1
        limit = 250

        while True:
            url = f"{self.base_url}/leads"
            params = {
                "filter[pipeline_id][]": pipeline_id,
                "limit": limit,
                "page": page,
                "with": "contacts,loss_reasons"
            }
            resp = self.session.get(url, params=params, timeout=20)
            
            if resp.status_code == 204:
                # No more content
                break
            elif resp.status_code == 200:
                data = resp.json()
                leads = data.get("_embedded", {}).get("leads", [])
                if not leads:
                    break
                all_leads.extend(leads)
                
                # Check if there is a next page
                links = data.get("_links", {})
                if "next" not in links or len(leads) < limit:
                    break
                page += 1
            else:
                logger.error(f"Error fetching leads page {page}: HTTP {resp.status_code} - {resp.text}")
                break

        return all_leads

    def get_contact_details(self, contact_id: int) -> Dict[str, Any]:
        """
        Fetches contact details and extracts name, phone, and email.
        """
        url = f"{self.base_url}/contacts/{contact_id}"
        resp = self.session.get(url, timeout=15)
        if resp.status_code != 200:
            logger.warning(f"Could not fetch contact #{contact_id}: HTTP {resp.status_code}")
            return {"id": contact_id, "name": f"Contact #{contact_id}", "phone": "", "email": ""}

        data = resp.json()
        name = data.get("name") or f"{data.get('first_name', '')} {data.get('last_name', '')}".strip() or f"Contact #{contact_id}"
        
        phone = ""
        email = ""
        
        custom_fields = data.get("custom_fields_values") or []
        for cf in custom_fields:
            code = (cf.get("field_code") or "").upper()
            fname = (cf.get("field_name") or "").lower()
            vals = cf.get("values") or []
            
            if code == "PHONE" or "phone" in fname or "teléfono" in fname or "telefono" in fname:
                if vals and not phone:
                    phone = str(vals[0].get("value", "")).strip()
            elif code == "EMAIL" or "email" in fname or "correo" in fname:
                if vals and not email:
                    email = str(vals[0].get("value", "")).strip()

        return {
            "id": contact_id,
            "name": name,
            "first_name": data.get("first_name", ""),
            "last_name": data.get("last_name", ""),
            "phone": phone,
            "email": email,
            "raw": data
        }

    def get_lead_history(self, lead_id: int, contact_ids: List[int]) -> Tuple[List[Dict[str, Any]], str]:
        """
        Fetches notes and event history for a lead.
        Returns:
          (formatted_messages, last_message_date_str)
        """
        history_items = []
        timestamps = []

        # 1. Fetch Lead Notes
        url_lnotes = f"{self.base_url}/leads/{lead_id}/notes"
        resp_ln = self.session.get(url_lnotes, timeout=15)
        if resp_ln.status_code == 200:
            notes = resp_ln.json().get("_embedded", {}).get("notes", [])
            for n in notes:
                ntype = n.get("note_type")
                params = n.get("params", {})
                created_at = n.get("created_at") or 0
                timestamps.append(created_at)
                
                text = (
                    params.get("text")
                    or params.get("message")
                    or params.get("body")
                    or n.get("text")
                )
                if text:
                    dt = datetime.datetime.fromtimestamp(created_at, tz=datetime.timezone.utc)
                    date_str = dt.strftime("%Y-%m-%d")
                    history_items.append({
                        "timestamp": created_at,
                        "date_str": date_str,
                        "content": f"[Original date: {date_str}] {text}",
                        "message_type": "outgoing" if n.get("created_by") else "incoming",
                        "source": f"note_{ntype}"
                    })

        # 2. Fetch Contact Notes
        for cid in contact_ids:
            url_cnotes = f"{self.base_url}/contacts/{cid}/notes"
            resp_cn = self.session.get(url_cnotes, timeout=15)
            if resp_cn.status_code == 200:
                c_notes = resp_cn.json().get("_embedded", {}).get("notes", [])
                for n in c_notes:
                    params = n.get("params", {})
                    created_at = n.get("created_at") or 0
                    timestamps.append(created_at)
                    text = params.get("text") or params.get("message") or n.get("text")
                    if text:
                        dt = datetime.datetime.fromtimestamp(created_at, tz=datetime.timezone.utc)
                        date_str = dt.strftime("%Y-%m-%d")
                        history_items.append({
                            "timestamp": created_at,
                            "date_str": date_str,
                            "content": f"[Original date: {date_str}] {text}",
                            "message_type": "incoming",
                            "source": "contact_note"
                        })

        # 3. Fetch Events to establish last active date if no notes were found
        url_events = f"{self.base_url}/events"
        params = {"filter[entity]": "lead", "filter[entity_id][]": lead_id, "limit": 50}
        resp_ev = self.session.get(url_events, params=params, timeout=15)
        if resp_ev.status_code == 200:
            events = resp_ev.json().get("_embedded", {}).get("events", [])
            for ev in events:
                cat = ev.get("created_at")
                if cat:
                    timestamps.append(cat)

        # Sort history items chronologically
        history_items.sort(key=lambda x: x["timestamp"])

        # Determine last message date
        if timestamps:
            max_ts = max(timestamps)
            last_date_str = datetime.datetime.fromtimestamp(max_ts, tz=datetime.timezone.utc).strftime("%Y-%m-%d")
        else:
            last_date_str = datetime.date.today().strftime("%Y-%m-%d")

        return history_items, last_date_str

    def get_lead_channel(self, lead_id: int) -> str:
        """
        Queries GET /api/v4/talks to retrieve the channel origin for a lead.
        Returns a clean channel label string (e.g. 'channel-telegram').
        """
        url = f"{self.base_url}/talks"
        params = {"filter[entity_type]": "lead", "filter[entity_id][]": lead_id}
        origin_map = {
            "telegram": "channel-telegram",
            "facebook": "channel-facebook",
            "instagram_business": "channel-instagram",
            "waba": "channel-whatsapp-api",
            "com.amocrm.amocrmwa": "channel-whatsapp-lite",
        }
        try:
            resp = self.session.get(url, params=params, timeout=15)
            if resp.status_code == 200:
                talks = resp.json().get("_embedded", {}).get("talks", [])
                if talks:
                    origin = talks[0].get("origin", "")
                    return origin_map.get(origin, f"channel-{origin}" if origin else "channel-unknown")
        except Exception as e:
            logger.warning(f"Failed to fetch talk channel for lead #{lead_id}: {e}")
        return "channel-unknown"
