# Project Persistence Context: Kommo-Chatwoot & n8n Architecture

> **Master Persistence Document**
> This file is the single source of truth for the architecture, active workflows, credentials, routing logic, and system prompt policies across development machines.
> **Daily Routine**: Run `git pull origin main` before starting work; inspect this document to maintain uniform context; commit and `git push origin main` upon any change.

---

## 1. Core Architecture Overview

* **Inbound Gateway**: Chatwoot Inboxes (Telegram, WhatsApp/Meta, API).
* **Webhook Ingestion**: Chatwoot webhook posts `message_created` events to `https://n8n.ac4.club/webhook/chatwoot-inbound-webhook`.
* **n8n Orchestration Workflow**: `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY`).
* **Debounce & Aggregation**: 3-second non-blocking wait (`Wait 3s`) + Chatwoot message query (`GET /messages`) + deduplication code node (`Preparar Mensaje`) that clusters consecutive lines into a single prompt.
* **LLM Engine**: **Anthropic Claude 3.5 Sonnet** (`claude-3-5-sonnet-20241022`) via `@n8n/n8n-nodes-langchain.lmChatAnthropic` with credential `Anthropic account` (`ZbUWSAq6JlKInA64`).
  * **Sampling Parameters**: Deterministic greedy decoding (`temperature: 0`, `topP: 0.001`).
  * ⚠️ **STRICT MANDATE (NO OPENAI)**: OpenAI is permanently decommissioned. Under NO circumstance will OpenAI models be used. Even if requested in future sessions, the assistant MUST confirm with the user and remind them of this strict directive.
* **Tools Connected to AI Agent**:
  1. `Call 'getpaymentlink'` (`3dBu0SNABE2pKCqU`): Generates payment links for Crypto (BTC/USDT -20%), CashApp (+10%), and Credit/Debit/PayPal (+10%).
  2. `Call 'create_trial_tool'` (`e1R7zQorWBaaqgou`): Direct Mega OTT demo generation tool for 24-hour trials (1 device).
  3. `Call 'transfer_to_human_tool'` (`xam0WV65gvTbXcIx`): Human support escalation for explicit customer handover requests.
* **Formatting & Response Pipeline**: Single-pass linear formatting (`Formatear Respuesta`) detecting channel type (plain Markdown for Telegram vs `*bold*` & URL flattening for Meta/WhatsApp) $\rightarrow$ `POST /messages` to Chatwoot (`Responder en Chatwoot`).

---

## 2. Business Rules & Master Prompt Policy

* **Language Rules**: Dynamic per-turn detection (responds in the language of the user's latest message, Spanish or English). Proper names, emails, phone numbers, and short confirmations do NOT trigger a language switch.
* **Payment Methods**:
  * **Zelle**: Base price to `acalimanr@gmail.com`. General listing NEVER includes the QR image link; QR code link is only delivered if customer explicitly asks to pay with Zelle or requests the QR.
  * **Crypto (BTC/USDT)**: -20% discount.
  * **CashApp**: +10% surcharge.
  * **Card / PayPal**: +10% surcharge.
* **Free Trials**:
  * 24-hour duration (1 device).
  * Upfront presentation NEVER mentions "up to 2 trials" (internal rule only).
  * Requires 3 fields: Full Name, Email, Phone number (preferably WhatsApp).
  * Up to 2 trials per customer: 2nd trial explicitly warns that it is the last allowed trial.

---

## 3. Workflow Catalog

| Workflow ID | Name | Role / Status |
| :--- | :--- | :--- |
| `n0zgnS1vlOGNcGNY` | `Chatwoot + IA Agent` | **Active / Main Gateway** (Anthropic Claude 3.5 Sonnet, 0-temp, 3s debounce, tools) |
| `3dBu0SNABE2pKCqU` | `getpaymentlink` | **Active Subworkflow / Tool** (Payment link generation) |
| `e1R7zQorWBaaqgou` | `Create Mega OTT Trial Tool` | **Active Subworkflow / Tool** (Mega OTT Trial generator) |
| `xam0WV65gvTbXcIx` | `Transfer to Human Tool` | **Active Subworkflow / Tool** (Human agent escalation) |
| `p8dS1jx73xvpbrkj` | `Telegram to N8N` | Active |
| `TfILC2hXao6SLQfE` | `Zelle Webhook` | Active |
| `OrUMncnYf5wezbpU` | `AmoCRM Webhook` | Active |
| `uD5sM2ruGXYSlpY3` | `Chatwoot Webhook` | Active |
| `OQzmQUISGM6ShdKT` | `AmoCRM Contact Update` | Active |
| `asQhO3WgzQW4gR5P` | `Agent - TotalTv USA` | Inactive / Deprecated (consolidated into main) |
| `4AYo7CX3Ou1K2yXH` | `Tool - Calcular Pago Movil` | **Active Subworkflow / Tool** (Pago Movil rate & calculation for TVTotal24) |

---

## 4. Git Synchronization Protocol

* **Local Repository**: `/mnt/Data/Projects for Antigravity/kommo-chatwoot`
* **Remote Repository**: `git@github.com:totaltvusa/kommo-chatwoot.git`
* **Branch**: `main`
