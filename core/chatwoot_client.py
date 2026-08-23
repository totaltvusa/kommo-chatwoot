import logging
from typing import Dict, List, Any, Optional, Set
from core.rate_limiter import RateLimitedSession

logger = logging.getLogger("migration.chatwoot_client")

class ChatwootClient:
    """
    Client for interacting with Chatwoot REST API v1.
    """
    def __init__(self, base_url: str, account_id: str, api_token: str, inbox_id: str):
        self.base_url = base_url.rstrip("/")
        self.account_id = str(account_id)
        self.api_token = api_token.strip()
        self.inbox_id = int(inbox_id)
        self.api_prefix = f"{self.base_url}/api/v1/accounts/{self.account_id}"
        
        self.session = RateLimitedSession(max_retries=5, backoff_base=1.5)
        self.session.session.headers.update({
            "api_access_token": self.api_token,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Kommo-Chatwoot-Migrator/1.0"
        })
        self._cached_labels: Optional[Set[str]] = None
        self._labels_endpoint_broken: bool = False  # skip retry storm if /labels returns persistent 500

    def search_contact(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Searches for an existing contact by phone, email, or query string.
        """
        if not query or not query.strip():
            return None
            
        url = f"{self.api_prefix}/contacts/search"
        resp = self.session.get(url, params={"q": query.strip()}, timeout=15)
        
        if resp.status_code == 200:
            payload = resp.json().get("payload", [])
            if payload:
                return payload[0]
        return None

    def create_or_update_contact(
        self,
        name: str,
        phone_number: str = "",
        email: str = "",
        custom_attributes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Idempotently creates or updates a contact.
        Searches first by phone number or email to avoid duplicates.
        """
        existing = None
        if phone_number:
            existing = self.search_contact(phone_number)
        if not existing and email:
            existing = self.search_contact(email)
            
        payload: Dict[str, Any] = {
            "name": name or "Unnamed Contact",
            "custom_attributes": custom_attributes or {}
        }
        if phone_number:
            payload["phone_number"] = phone_number
        if email:
            payload["email"] = email

        if existing:
            contact_id = existing["id"]
            url = f"{self.api_prefix}/contacts/{contact_id}"
            resp = self.session.put(url, json=payload, timeout=15)
            if resp.status_code in (200, 201):
                return {"id": contact_id, "action": "updated", "data": resp.json().get("payload", {})}
            else:
                # If update failed (e.g. invalid phone format), return existing
                logger.warning(f"Could not update contact #{contact_id}: HTTP {resp.status_code} - {resp.text}")
                return {"id": contact_id, "action": "existing", "data": existing}
        else:
            url = f"{self.api_prefix}/contacts"
            # Chatwoot requires inbox_id for contact creation if contact is linked to inbox
            payload["inbox_id"] = self.inbox_id
            resp = self.session.post(url, json=payload, timeout=15)
            if resp.status_code in (200, 201):
                created = resp.json().get("payload", {}).get("contact", resp.json().get("payload", {}))
                return {"id": created["id"], "action": "created", "data": created}
            else:
                # If creation fails because of format, retry with minimal fields
                logger.warning(f"Contact creation failed: HTTP {resp.status_code} - {resp.text}. Retrying with name only.")
                fallback_payload = {"name": name or "Unnamed Contact", "inbox_id": self.inbox_id}
                fb_resp = self.session.post(url, json=fallback_payload, timeout=15)
                if fb_resp.status_code in (200, 201):
                    created = fb_resp.json().get("payload", {}).get("contact", fb_resp.json().get("payload", {}))
                    return {"id": created["id"], "action": "created", "data": created}
                else:
                    raise RuntimeError(f"Failed to create contact in Chatwoot: HTTP {fb_resp.status_code} - {fb_resp.text}")

    def create_conversation(
        self,
        contact_id: int,
        custom_attributes: Optional[Dict[str, Any]] = None,
        status: str = "resolved"
    ) -> int:
        """
        Creates a conversation for the contact in the configured inbox.
        Returns the new conversation ID.
        """
        url = f"{self.api_prefix}/conversations"
        payload = {
            "inbox_id": self.inbox_id,
            "contact_id": contact_id,
            "status": status,
            "custom_attributes": custom_attributes or {}
        }
        resp = self.session.post(url, json=payload, timeout=15)
        if resp.status_code in (200, 201):
            data = resp.json()
            return data.get("id") or data.get("conversation_id")
        else:
            raise RuntimeError(f"Failed to create conversation: HTTP {resp.status_code} - {resp.text}")

    def create_message(
        self,
        conversation_id: int,
        content: str,
        message_type: str = "incoming",
        private: bool = False
    ) -> Dict[str, Any]:
        """
        Creates a message in a conversation.
        message_type: 'incoming' (from contact) or 'outgoing' (from agent)
        """
        url = f"{self.api_prefix}/conversations/{conversation_id}/messages"
        payload = {
            "content": content,
            "message_type": message_type,
            "private": private
        }
        resp = self.session.post(url, json=payload, timeout=15)
        if resp.status_code in (200, 201):
            return resp.json()
        else:
            raise RuntimeError(f"Failed to create message in conversation #{conversation_id}: HTTP {resp.status_code} - {resp.text}")

    def ensure_labels_exist(self, labels: List[str]):
        """
        Ensures labels exist in Chatwoot account.
        Uses a single no-retry probe on the first call; if the /labels endpoint
        is persistently returning 500, sets _labels_endpoint_broken=True and skips
        all future attempts to avoid the retry storm.
        """
        if self._labels_endpoint_broken:
            return

        # One-shot probe of the GET endpoint (no retries via a raw session call)
        if self._cached_labels is None:
            self._cached_labels = set()
            try:
                url = f"{self.api_prefix}/labels"
                resp = self.session.session.get(
                    url,
                    headers={"api_access_token": self.api_token, "Accept": "application/json"},
                    timeout=8
                )
                if resp.status_code == 200:
                    for item in resp.json().get("payload", []):
                        self._cached_labels.add(item.get("title"))
                elif resp.status_code >= 500:
                    logger.warning(
                        f"Account /labels endpoint returned {resp.status_code} — "
                        "skipping label pre-creation for all leads (labels will still be "
                        "applied directly to each conversation)."
                    )
                    self._labels_endpoint_broken = True
                    return
            except Exception as e:
                logger.debug(f"Account labels probe error: {e}")
                self._labels_endpoint_broken = True
                return

        for label in labels:
            if label not in self._cached_labels:
                try:
                    url = f"{self.api_prefix}/labels"
                    color = "#1f93ff" if label.startswith("funnel-") else "#7c3aed"
                    payload = {
                        "title": label,
                        "description": f"Auto-created migration label for {label}",
                        "color": color,
                        "show_on_sidebar": True
                    }
                    resp = self.session.session.post(
                        url,
                        json=payload,
                        headers={"api_access_token": self.api_token, "Content-Type": "application/json"},
                        timeout=8
                    )
                    if resp.status_code in (200, 201, 422):
                        self._cached_labels.add(label)
                    elif resp.status_code >= 500:
                        self._labels_endpoint_broken = True
                        logger.warning("Account /labels POST also returned 500 — disabling label pre-creation.")
                        return
                except Exception as e:
                    logger.debug(f"Label creation error for '{label}': {e}")

    def apply_labels_to_conversation(self, conversation_id: int, labels: List[str]):
        """
        Attaches labels to a conversation.
        Pre-creation of account labels is attempted once; if the endpoint is broken
        we skip it and apply labels directly (Chatwoot accepts existing labels regardless).
        """
        self.ensure_labels_exist(labels)
        url = f"{self.api_prefix}/conversations/{conversation_id}/labels"
        payload = {"labels": labels}
        resp = self.session.post(url, json=payload, timeout=15)
        if resp.status_code not in (200, 201):
            logger.warning(f"Could not apply labels to conversation #{conversation_id}: HTTP {resp.status_code} - {resp.text}")
