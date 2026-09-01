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
* **LLM Engine**: **Anthropic Claude Haiku 4.5** (`claude-haiku-4-5`) via `@n8n/n8n-nodes-langchain.lmChatAnthropic` with credential `Anthropic account` (`ZbUWSAq6JlKInA64`).
  * **Sampling Parameters**: Deterministic greedy decoding (`temperature: 0`).
  * ⚠️ **STRICT MANDATE (NO OPENAI)**: OpenAI is permanently decommissioned. Under NO circumstance will OpenAI models be used.
* **Multi-Brand Routing (`¿Qué Empresa?`)**:
  * **Brand A: TotalTv USA**:
    * Inboxes:
      * **Inbox 6**: Telegram (`@TvTotalUSAbot`).
      * **Inbox 14**: Instagram (`@tvtotalusa`) via Zernio API.
      * **Inbox 17**: Facebook Messenger (`Facebook - TotalTv USA`) via Zernio API.
      * **Inbox 4**: WhatsApp (`TTvAlertsMovistar`).
    * Service: Mega OTT panel.
    * Audience: USA & International (English / Spanish bilingual auto-detection).
    * Auto-Labeling: Automatically tagged with `funnel-totaltv-usa`, channel labels (`channel-facebook`, `channel-instagram`, `channel-telegram`, `channel-whatsapp`), and initial stage `stage-incoming-leads`.
    * Connected Tools:
      1. `Call 'getpaymentlink'` (`3dBu0SNABE2pKCqU`): Payment link generator.
      2. `Call 'create_trial_tool'` (`e1R7zQorWBaaqgou`): Mega OTT 24h trial generator (tracked via Chatwoot attributes `trial_1_id`, `trial_2_id`).
      3. `Call 'transfer_to_human_tool'` (`xam0WV65gvTbXcIx`): Human support escalation (applies 'human' label, adds private note, dual Telegram & WhatsApp Evolution API notifications to `584146130135`).
  * **Brand B: TVTotal24 / TOTAL TV Latina**:
    * Inboxes:
      * **Inbox 10**: Telegram (`@tvtotal24_bot`).
      * **Inbox 13**: Instagram (`@tvtotal24`) via Zernio API.
      * **Inbox 15**: TikTok (`@tvtotal24`) via API Channel.
      * **Inbox 16**: WhatsApp (`lat-whatscol`) via Evolution API.
    * Auto-labels: Automatically tagged with `funnel-totaltv-latina`, channel labels (`channel-whatsapp-lite`, `channel-instagram`, `channel-telegram`, etc.), and initial stage `stage-lead-entrantes`.
    * Service: MVPlay (Xtream-Masters) panel.
    * Audience: Latin America / Venezuela (Spanish).
    * Payment Methods: Zelle (`pagos@totaltvlatina.com`), Binance Pay USDT (`ID: 22628239` - Super Discount), Pago Móvil (Bancamiga, 04246861135, J405259221, ArialStore C.A.).
    * Connected Tools:
      1. `calcular_pago_movil` (`4AYo7CX3Ou1K2yXH`): Real-time BCV exchange rate & Bs calculation.
      2. `crear_prueba_tvtotal24` (`kh10aaenUURvi7Ji`): Automated MVPlay 4h trial generator (tracked via Chatwoot attributes `tvtotal_trial_1_id`, `tvtotal_trial_2_id`).
      3. `Call 'transfer_to_human_tool'` (`xam0WV65gvTbXcIx`): Human support escalation (applies 'human' label, adds private note, dual Telegram & WhatsApp Evolution API notifications to `584146130135`).
* **Formatting, Composing Presence & Response Pipeline**:
  1. `Formatear Respuesta`: Formats text (plain Markdown for Telegram vs `*bold*` & URL flattening for Meta/WhatsApp/Instagram) and computes a human typing delay (random 2 to 5 seconds).
  2. `Activar Escribiendo en Chatwoot`: Sends `POST /toggle_typing_status` (`typing_status: "on"`) to simulate active typing across all channels.
  3. `Wait Typing Delay`: Waits 2 to 5 seconds.
  4. `Responder en Chatwoot`: Sends `POST /messages` to Chatwoot, which broadcasts the response to Evolution API (WhatsApp), Telegram, or Zernio (Instagram).

---

## 2. Business Rules & Operational Policies

### Free Trial Policies
* **TotalTv USA (Mega OTT)**:
  * Duration: 24 hours (1 device).
  * Panel: Mega OTT.
  * Attributes: `trial_1_id`, `trial_2_id`.
* **TVTotal24 (MVPlay / TOTAL TV Latina)**:
  * Duration: 4 hours (starts upon creation; NEVER state that it starts upon first login).
  * Panel in TotalTV app: Select **TOTALTV LATINA**.
  * Attributes: `tvtotal_trial_1_id`, `tvtotal_trial_2_id` (100% isolated from Mega OTT).
  * Username format: `NombreApellido` (without spaces or accents, e.g. `AlbertoRincon`). If missing, left empty for auto-generation.
  * Password format: Customer's clean phone number. If rejected by MVPlay, auto-fallback creates line with panel-generated password.
  * Reseller Notes: ONLY customer's full name (no email, no phone).
  * Server URLs:
    * Server / DNS: `http://wk.mvpl.uk:2082`
    * Smarters DNS: Always label as **`DNS para Smarters: http://cdn01link.uk:2095`**
* **General Trial Rules**:
  * Mandatory collection before creation: Full Name (`contact_name`), Email (`email`), Phone (`phone`).
  * Limit: Up to 2 free trials per customer. (The 2-trial limit is internal and NEVER mentioned upfront; upon delivering the 2nd trial, explicitly state it is the final free trial).

### Payment & QR Code Rules
* **Pago Móvil**:
  * Standard response gives clean text only: Total amount in Bs, Bank (Bancamiga), Phone (04246861135), RIF (J405259221), Beneficiary (ArialStore C.A.), request transfer screenshot.
  * DO NOT mention the daily exchange rate in standard response; only provide the exchange rate if the customer explicitly asks for it.
  * Deliver QR code link (`Arialstorepm.jpeg`) ONLY if the customer explicitly asks for the QR code.
* **Zelle**:
  * TotalTv USA: `acalimanr@gmail.com`. QR delivered only upon explicit request.
  * TVTotal24: `pagos@totaltvlatina.com`. QR delivered only upon explicit request (`Zelle Lat.jpeg`).
* **Binance Pay (TVTotal24)**:
  * Pay ID: `22628239`. Super discount pricing: 1 Month , 3 Months , 12 Months .

---

## 3. Workflow Catalog

| Workflow ID | Name | Role / Status |
| :--- | :--- | :--- |
| `n0zgnS1vlOGNcGNY` | `Chatwoot + IA Agent` | **Active / Main Gateway** (Claude Haiku 4.5, 0-temp, 3s debounce, multi-brand router) |
| `kh10aaenUURvi7Ji` | `Tool - Create MVPlay Trial` | **Active Subworkflow / Tool** (Automated MVPlay Xtream-Masters trial generator for TVTotal24) |
| `4AYo7CX3Ou1K2yXH` | `Tool - Calcular Pago Movil` | **Active Subworkflow / Tool** (Pago Móvil rate scraping & Bs calculation for TVTotal24) |
| `e1R7zQorWBaaqgou` | `Create Mega OTT Trial Tool` | **Active Subworkflow / Tool** (Mega OTT Trial generator for TotalTv USA) |
| `3dBu0SNABE2pKCqU` | `getpaymentlink` | **Active Subworkflow / Tool** (Payment link generator for TotalTv USA) |
| `xam0WV65gvTbXcIx` | `Transfer to Human Tool` | **Active Subworkflow / Tool** (Human agent escalation - dual Telegram & WhatsApp Evolution API `TTvAlertsMovistar` to `584146130135`) |
| `XC1jY6Vkbgdu5iIz` | `Cron - Followup Stage Fase de Pruebas to Que Te Parecio` | **Active Cron** (Executes every 2 hours on even hours: `0 */2 * * *`) |
| `KRwjH3njrF4qRdph` | `Cron - Followup Stage Trials to Want to Join` | **Active Cron** (Executes every 2 hours on even hours: `0 */2 * * *`) |
| `1IlXjaNv0rc9laJy` | `Cron - Followup Stage Incoming Leads to Contacted` | **Active Cron** (Executes every 2 hours on even hours: `0 */2 * * *`) |
| `p8dS1jx73xvpbrkj` | `Telegram to N8N` | Active |
| `TfILC2hXao6SLQfE` | `Zelle Webhook` | Active |
| `OrUMncnYf5wezbpU` | `AmoCRM Webhook` | Active |
| `uD5sM2ruGXYSlpY3` | `Chatwoot Webhook` | Active |
| `OQzmQUISGM6ShdKT` | `AmoCRM Contact Update` | Active |
| `asQhO3WgzQW4gR5P` | `Agent - TotalTv USA` | Inactive / Deprecated |
| `Vfweu0rjoTT3FUl1` | `Agent - TVTotal24 (Latina)` | Inactive / Deprecated |

---

## 4. API Endpoints & Credentials Reference

* **MVPlay (Xtream-Masters) API**:
  * Endpoint: `http://1395.cooteg.ch:2095/pooqkDEG/reseller/index.php`
  * User: `TtvLat2025`
  * API Key: `ace3cacdfd48afdec756ec214ec0793f`
  * Package ID for Demo: `2` (Demo 3 Horas / TVTotal24)
  * Server DNS: `http://wk.mvpl.uk:2082`, `http://cdn01link.uk:2095`
* **Chatwoot API**:
  * Base URL: `https://project1-chatwoot.efebpb.easypanel.host`
  * Access Token: `nuwRKpG2bBAQBpRFznfvrMpT`
  * Account ID: `1`
* **Evolution API (WhatsApp Gateway)**:
  * Server URL: `https://project1-evolution-api.efebpb.easypanel.host`
  * Global API Key: `429683C4C977415CAAFCCE10F7D57E11`
  * Credential ID in n8n: `ecGN8GlLnzNz5Lq5` (`Evolution account 2`)
  * Instances:
    * `lat-whatscol` (TVTotal24 WhatsApp Colombia: `+57 300 9476271` -> Chatwoot Inbox ID 16).
    * `TTvAlertsMovistar` (Administrative / Human Handover Alerts -> Chatwoot Inbox ID 4).
  * Chatwoot Webhook URL: `https://project1-evolution-api.efebpb.easypanel.host/chatwoot/webhook/{instance}`
  * Presence Endpoint: `POST /chat/sendPresence/{instance}` (`{"presence": "composing"}`)
* **n8n Instance**:
  * URL: `https://n8n.ac4.club`

---

## 5. Git Synchronization Protocol

* **Local Repository**: `/mnt/Data/Projects for Antigravity/kommo-chatwoot`
* **Remote Repository**: `git@github.com:totaltvusa/kommo-chatwoot.git`
* **Branch**: `main`

---

## 6. Detailed Changelog & Implementation History

### August 30, 2026
* **WhatsApp (Evolution API / Chatwoot API Channel) & Universal Typing Simulation**:
  * **Human-like simulation**:
    * Dynamic calculation of typing delay between 2 and 5 seconds based on response length ($delay = \min(5, \max(2, \text{round}(\text{text.length} \times 0.015 + 2)))$).
    * `Simular Presencia (Evolution API)`: Calls `POST /chat/sendPresence/{{instance}}` with `composing` status for WhatsApp recipients.
    * `Activar Escribiendo en Chatwoot`: Universally triggers Chatwoot's typing status endpoint (`POST .../toggle_typing_status`) so agents see typing state.
    * Non-blocking `Wait Typing Delay` node (2 to 5 seconds) before dispatching the response.
  * **Outbound Message Delivery & Chatwoot Synchronization**:
    * `Enviar WhatsApp (Evolution API)`: Dispatches text message to WhatsApp via Evolution API `POST /message/sendText/{{instance}}`.
    * `Responder en Chatwoot`: Outgoing message syncs back to Chatwoot conversation thread (`POST .../messages`) so human agents see full chat history in real-time, and native channels (Telegram / Instagram via Zernio) deliver seamlessly.
### August 31, 2026
* **TikTok (@tvtotal24) Channel Setup & Routing**:
  * Created Chatwoot Inbox **ID 15**: `TikTok - TvTotal24` (type `Channel::Api`, identifier `iRSzyHJxMbVuAu7zDXtEAfYZ`).
  * Assigned all support agents (1, 2, 3, 4) to Inbox 15.
  * Created Chatwoot Automation Rule **ID 8** (`TikTok TVTotal24 Auto Labels`): Automatically tags new conversations with `funnel-totaltv-latina` and `channel-tiktok`.
  * Updated n8n router switch node `¿Qué Empresa?` in `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY`):
    * Excluded inbox 15 from TotalTv USA.
    * Routed inbox 15 directly to `AI Agent - TVTotal24` with full TVTotal24 operational rules and tools.
  * Synchronized updated workflow JSON to `workflows/router_chatwoot_ia.json`.

