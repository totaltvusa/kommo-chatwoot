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
      * **Inbox 6**: Telegram (`@TotalTvUSAbot`, Bot Token `6744012482:AAH5zvUet_-A1R4tPFUsblDkZi-37uaxUTY`).
      * **Inbox 14**: Instagram (`@tvtotalusa`) via Zernio API.
      * **Inbox 17**: Facebook Messenger (`Facebook - TotalTv USA`) via Zernio API.
      * **Inbox 18**: WhatsApp (`WhatsAppUSA - 3059861096` / `+1 305 986 1096`) via Evolution API.
      * **Inbox 4**: WhatsApp / Admin (`TTvAlertsMovistar`).
    * Service: Mega OTT panel.
    * Audience: USA & International (English / Spanish bilingual auto-detection).
    * Auto-Labeling: Automatically tagged with `funnel-totaltv-usa`, channel labels (`channel-facebook`, `channel-instagram`, `channel-telegram`, `channel-whatsapp`, `channel-whatsapp-lite`), and initial stage `stage-incoming-leads`.
    * Connected Tools:
      1. `Call 'getpaymentlink'` (`3dBu0SNABE2pKCqU`): Payment link generator.
      2. `Call 'create_trial_tool'` (`e1R7zQorWBaaqgou`): Mega OTT 24h trial generator (tracked via Chatwoot attributes `trial_count`, `trial_1_id`, `trial_2_id`; uses `$fromAI` parameter mapping with Chatwoot regex fallback; dual Telegram & WhatsApp Evolution API notifications to `584146130135`).
      3. `Call 'transfer_to_human_tool'` (`xam0WV65gvTbXcIx`): Human support escalation (applies 'human' label, adds private note, dual Telegram & WhatsApp Evolution API notifications to `584146130135`).
  * **Brand B: TVTotal24 / TOTAL TV Latina**:
    * Inboxes:
      * **Inbox 10**: Telegram (`@tvtotal24_bot`).
      * **Inbox 13**: Instagram (`@tvtotal24`) via Zernio API.
      * **Inbox 16**: WhatsApp (`lat-whatscol`) via Evolution API.
      * **Inbox 19**: WhatsApp Cloud (`WhatsApp Cloud TVTotal24` / `+1 305 422 9099` / Phone ID `1106422772565024`) via Meta WhatsApp Cloud API.
    * Auto-labels: Automatically tagged with `funnel-totaltv-latina`, channel labels (`channel-officialwhatsapp` for Inbox 19, `channel-whatsapp-lite` for Inbox 16, `channel-instagram` for Inbox 13, `channel-telegram` for Inbox 10), and initial stage `stage-leads-entrantes`.
    * Service: MVPlay (Xtream-Masters) panel.
    * Audience: Latin America / Venezuela (Spanish).
    * Payment Methods: Zelle (`pagos@totaltvlatina.com`), Binance Pay USDT (`ID: 22628239` - Super Discount), Pago Móvil (Bancamiga, 04246861135, J405259221, ArialStore C.A.).
    * Connected Tools:
      1. `calcular_pago_movil` (`4AYo7CX3Ou1K2yXH`): Real-time live Binance P2P exchange rate & Bs calculation.
      2. `crear_prueba_tvtotal24` (`kh10aaenUURvi7Ji`): Automated MVPlay 4h trial generator (tracked via Chatwoot attributes `tvtotal_trial_count`, `tvtotal_trial_1_id`, `tvtotal_trial_2_id`; dual Telegram & WhatsApp Evolution API notifications to `584146130135`).
      3. `Call 'transfer_to_human_tool'` (`xam0WV65gvTbXcIx`): Human support escalation (applies 'human' label, adds private note, dual Telegram & WhatsApp Evolution API notifications to `584146130135`).
* **Formatting, Composing Presence & Response Pipeline**:
  1. `Formatear Respuesta`: Formats text (plain Markdown for Telegram vs `*bold*` & URL flattening for Meta/WhatsApp/Instagram/Facebook) and computes a human typing delay (random 2 to 5 seconds).
  2. `Activar Escribiendo en Chatwoot`: Inlined asynchronous call to Chatwoot's typing status endpoint (`POST .../toggle_typing_status`, `typing_status: "on"`) so agents and channels see typing state.
  3. `Wait Typing Delay`: Waits 2 to 5 seconds before dispatching.
  4. `Responder en Chatwoot`: Sends `POST /messages` to Chatwoot, which broadcasts the response to Evolution API (WhatsApp), Telegram, or triggers the outbound Zernio handler for Instagram and Facebook Messenger.
* **Zernio Meta Social Bridge (Instagram & Facebook Messenger)**:
  * **Inbound (`Zernio Inbound Webhook` -> `Procesar Inbound Zernio`)**:
    * Endpoint: `POST https://n8n.ac4.club/webhook/zernio-instagram-inbound` (subscribed to `message.received` in Zernio).
    * Handles both `platform: "instagram"` and `platform: "facebook"`.
    * Manages contacts (`ig_<id>` or `fb_<id>`) and open conversations in Chatwoot.
    * Inboxes & Auto-labels:
      * Instagram `@tvtotal24` (Account `6a8667d577555aae0139eca3`) -> Inbox 13 (`funnel-totaltv-latina`, `channel-instagram`, `stage-lead-entrantes`).
      * Instagram `@tvtotalusa` (Account `6a86600b77555aae01387fc7`) -> Inbox 14 (`funnel-totaltv-usa`, `channel-instagram`, `stage-incoming-leads`).
      * Facebook Messenger `@TotalTv2025` (Account `6a87b56c77555aae01ddcf1c`) -> Inbox 17 (`funnel-totaltv-usa`, `channel-facebook`, `stage-incoming-leads`).
  * **Outbound (`Enviar a Zernio Instagram`)**:
    * Intercepts Chatwoot outgoing non-private messages for Inboxes 13, 14, and 17.
    * Calls `POST https://api.zernio.com/v1/inbox/conversations/${participantId}/messages` using the respective API key and account ID.
    * Employs idempotency key `chatwoot_msg_${chatwootMsgId}` to guarantee zero duplicate deliveries.


---

## 2. Business Rules & Operational Policies

### Free Trial Policies
* **TotalTv USA (Mega OTT)**:
  * Duration: 24 hours (1 device).
  * Panel: Mega OTT.
  * Attributes: `trial_count`, `trial_1_id`, `trial_2_id`.
  * Admin Notifications: Simultaneous Telegram (Chat ID `40371837`) and WhatsApp (`TTvAlertsMovistar` to `584146130135`).
* **TVTotal24 (MVPlay / TOTAL TV Latina)**:
  * Duration: 4 hours (starts upon creation; NEVER state that it starts upon first login).
  * Panel in TotalTV app: Select **TOTALTV LATINA**.
  * Attributes: `tvtotal_trial_count`, `tvtotal_trial_1_id`, `tvtotal_trial_2_id`, `tvtotal_trial_1_username`, `tvtotal_trial_2_username` (100% isolated from Mega OTT; officially registered in Chatwoot UI).
  * Username format: `NombreApellido` for trial 1, `NombreApellido2` for trial 2 (without spaces or accents, e.g. `AlbertoRincon`). If already exists in MVPlay, automatically falls back to empty username/password for unique panel auto-generation.
  * Password format: Customer's clean phone number. If auto-fallback triggered, panel generates unique password.
  * Reseller Notes: ONLY customer's full name (no email, no phone).
  * Server URLs:
    * Server / DNS: `http://wk.mvpl.uk:2082`
    * Smarters DNS: Always label as **`DNS para Smarters: http://cdn01link.uk:2095`**
  * Admin Notifications: Simultaneous Telegram (Chat ID `40371837`) and WhatsApp (`TTvAlertsMovistar` to `584146130135`).
* **General Trial Rules & AI Guardrails**:
  * Mandatory collection before creation: Full Name (`contact_name`), Email (`email`), Phone (`phone`).
  * Limit: Up to 2 free trials per customer. (The 2-trial limit is internal and NEVER mentioned upfront; upon delivering the 2nd trial, explicitly state it is the final free trial).
  * **Mandatory Tool Delegation (Zero Memory-Based Checks)**: The AI Agent is strictly forbidden from evaluating trial count, active status, or limits from chat history. Whenever a customer asks for a trial or another trial, the AI MUST execute the respective trial tool, which reads the CRM custom attributes as the sole authority.
  * **Stage Transition & Label Cleanup**: Upon trial generation, the conversation is automatically tagged with `stage-trials` (TotalTv USA) or `stage-fase-de-pruebas` (TVTotal24), and ANY previous `stage-*` label (e.g. `stage-incoming-leads`, `stage-lead-entrantes`, `stage-contacted`, `stage-contactado`) is strictly removed while preserving all other labels (`funnel-*`, `channel-*`, `human`).

### Payment & QR Code Rules
* **Pago Móvil**:
  * Standard response gives clean text only: Total amount in Bs, Bank (Bancamiga), Phone (04246861135), RIF (J405259221), Beneficiary (ArialStore C.A.), request transfer screenshot.
  * Real-time exchange rate: Automatically scraped from live Binance P2P USDT/VES orders via `this.helpers.httpRequest` (with automatic fallback to DolarAPI Paralelo and Oficial).
  * DO NOT mention the daily exchange rate in standard response; only provide the exchange rate if the customer explicitly asks for it.
  * Deliver QR code link (`Arialstorepm.jpeg`) ONLY if the customer explicitly asks for the QR code.
* **Zelle**:
  * TotalTv USA: `acalimanr@gmail.com`. QR delivered only upon explicit request.
  * TVTotal24: `pagos@totaltvlatina.com`. QR delivered only upon explicit request (`Zelle Lat.jpeg`).
* **Binance Pay (TVTotal24)**:
  * Pay ID: `22628239`. Super discount pricing: 1 Month $5, 3 Months $14, 12 Months $50.

---

## 3. Workflow Catalog

| Workflow ID | Name | Role / Status |
| :--- | :--- | :--- |
| `n0zgnS1vlOGNcGNY` | `Chatwoot + IA Agent` | **Active / Main Gateway** (Claude Haiku 4.5, 0-temp, 3s debounce, multi-brand router, Google Sheets Customer DB check, strict no-credential-hallucination & human transfer rules) |
| `kh10aaenUURvi7Ji` | `Tool - Create MVPlay Trial` | **Active Subworkflow / Tool** (Automated MVPlay Xtream-Masters trial generator for TVTotal24) |
| `4AYo7CX3Ou1K2yXH` | `Tool - Calcular Pago Movil` | **Active Subworkflow / Tool** (Pago Móvil rate scraping & Bs calculation for TVTotal24) |
| `e1R7zQorWBaaqgou` | `Create Mega OTT Trial Tool` | **Active Subworkflow / Tool** (Mega OTT Trial generator for TotalTv USA) |
| `3dBu0SNABE2pKCqU` | `getpaymentlink` | **Active Subworkflow / Tool** (Payment link generator for TotalTv USA) |
| `xam0WV65gvTbXcIx` | `Transfer to Human Tool` | **Active Subworkflow / Tool** (Human agent escalation - dual Telegram & WhatsApp Evolution API `TTvAlertsMovistar` to `584146130135`, clean JSON tool response) |
| `XC1jY6Vkbgdu5iIz` | `Cron - Followup Stage Fase de Pruebas to Que Te Parecio` | **Active Cron** (Executes every 2 hours on even hours: `0 */2 * * *`) |
| `KRwjH3njrF4qRdph` | `Cron - Followup Stage Trials to Want to Join` | **Active Cron** (Executes every 2 hours on even hours: `0 */2 * * *`) |
| `1IlXjaNv0rc9laJy` | `Cron - Followup Stage Incoming Leads to Contacted` | **Active Cron** (Executes every 2 hours on even hours: `0 */2 * * *`) |
| `TfILC2hXao6SLQfE` | `Latin vence hoy y vence4` | **Active Outbound Notifier** (Daily 9 AM expiration WhatsApp templates via Meta Cloud API + batchUpdate red text on expired DnSpace rows + Chatwoot Contact/Conversation/Private Note Sync) |
| `943Yu3CZMD4dzRCI` | `Mega expires TODAY (Vence HOY)` | **Active Outbound Notifier** (Mega OTT Daily 9 AM expiration notifier) |
| `F7M6sLe1lo4zUObT` | `Mega expires SOON (Vence 4 días)` | **Active Outbound Notifier** (Mega OTT 4-day expiration notifier) |
| `p8dS1jx73xvpbrkj` | `Card2CryptoLink` | **Active Subworkflow / Tool** |
| `OrUMncnYf5wezbpU` | `Card2Crypto to ME` | **Active Outbound Notifier** |
| `uD5sM2ruGXYSlpY3` | `NowPayments to me` | **Active Outbound Notifier** (Telegram alert upon finished crypto payments) |
| `OQzmQUISGM6ShdKT` | `Telnyx to ME` | **Active Outbound Notifier** |
| `hAHmBsRVDc4Hyt6g` | `Ecwid to Client & me 2.0` | **Active Ingestion / Outbound Notifier** (Ecwid Gmail order trigger -> payment notifications via Email, Telnyx SMS & WhatsApp with 'Customer' and '.' fallbacks) |
| `asQhO3WgzQW4gR5P` | `Cron - Autoclose Inactive Conversations (48h)` | **Active Cron** (Executes at 0, 6, 12, 18h `0 0,6,12,18 * * *`; resolves conversations after 48h customer inactivity, strips `human` tag, applies `autoclosed`) |
| `Lcyro95g4yg39bdD` | `Sync Mega to MegaData` | **Active / Standalone Ingestion** (Syncs Mega sheet + MegaOTT API properties and creates/dumps to `MegaData` tab in Google Sheets) |
| `Vfweu0rjoTT3FUl1` | `Agent - TVTotal24 (Latina)` | Inactive / Deprecated |


---

## 4. API Endpoints & Credentials Reference

* **Meta WhatsApp Cloud API (WhatsApp Cloud TVTotal24)**:
  * Phone Number ID: `1106422772565024`
  * Display Phone Number: `+1 305-422-9099` (E.164: `+13054229099`, Verified Name: `TTV Mensajes`)
  * WABA ID: `3483325768503437`
  * App ID: `27469809309376250`
  * Business ID: `1323943205921780`
  * Credential ID in n8n: `5mdJEz0fPigGF7Wc` (`WhatsApp 3054229099`)
  * Chatwoot Inbox ID: **19** (`WhatsApp Cloud TVTotal24`, `Channel::Whatsapp`)
  * Chatwoot Webhook Callback URL: `https://project1-chatwoot.efebpb.easypanel.host/webhooks/whatsapp/+13054229099`
  * Chatwoot Webhook Verify Token: `62f0684bf292fe9dd1e87dbd924044c6`
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
    * `3059861096` (TotalTv USA WhatsApp: `+1 305 986 1096` -> Chatwoot Inbox ID 18).
    * `lat-whatscol` (TVTotal24 WhatsApp Colombia: `+57 300 9476271` -> Chatwoot Inbox ID 16).
    * `TTvAlertsMovistar` (Administrative / Human Handover Alerts -> Chatwoot Inbox ID 4).
  * Chatwoot Webhook URL: `https://project1-evolution-api.efebpb.easypanel.host/chatwoot/webhook/{instance}`
  * Presence Endpoint: `POST /chat/sendPresence/{instance}` (`{"presence": "composing"}`)
* **Zernio API (Meta / Social Bridge)**:
  * Base URL: `https://zernio.com/api/v1`
  * Global Webhook Endpoint: `https://n8n.ac4.club/webhook/zernio-instagram-inbound` (Event: `message.received`)
  * TotalTv USA Account:
    * API Key: `sk_997f75cb81b8ed42a9764a99aab59b5a1389a3a91c29b1311fe8d31e4e337135`
    * Instagram: Account ID `6a86600b77555aae01387fc7` (`@tvtotalusa` -> Chatwoot Inbox 14)
    * Facebook Messenger: Account ID `6a87b56c77555aae01ddcf1c` (Page: `TotalTv USA` / `@TotalTv2025`, Page ID: `634477526407306` -> Chatwoot Inbox 17)
  * TVTotal24 Latina Account:
    * API Key: `sk_ad87ef37da3670603641edd90966dfa359fe77f6c4a23d10f807b707c1b5cbf1`
    * Instagram: Account ID `6a8667d577555aae0139eca3` (`@tvtotal24` -> Chatwoot Inbox 13)
* **n8n Instance**:
  * URL: `https://n8n.ac4.club`

---

## 5. Git Synchronization Protocol

* **Local Repositories**:
  * macOS: `/Users/alvezcaliman/Documents/AntigravityProjects/kommo-chatwoot`
  * Linux: `/mnt/Data/Projects for Antigravity/kommo-chatwoot`
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

### September 1, 2026
* **WhatsApp Colombia Instance Setup (`lat-whatscol`)**:
  * Registered Evolution API instance `lat-whatscol` (`+57 300 9476271`) connected to Chatwoot Inbox **ID 16** (`lat-whatscol`, `Channel::Api`).
  * Webhook configured: `https://project1-evolution-api.efebpb.easypanel.host/chatwoot/webhook/lat-whatscol`.
  * Configured auto-labeling in `Preparar Mensaje`: `funnel-totaltv-latina` and `channel-whatsapp-lite`.
* **Inlined Composing State & Human-like Typing Simulation Pipeline**:
  * Fixed payload propagation by inlining `toggle_typing_status: on` directly inside `Formatear Respuesta` as an asynchronous non-blocking request, preventing node data overwrite.
  * Preserved 2 to 5 second random human delay before `Responder en Chatwoot`.
* **Dynamic Initial Stage Labeling on Conversation Entry**:
  * Updated `Preparar Mensaje` in `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY`):
    * TVTotal24 Latina (Inboxes 10, 13, 15, 16): automatically assigns `stage-lead-entrantes` if no stage exists.
    * TotalTv USA (Inboxes 1, 4, 6, 14, 17, 18): automatically assigns `stage-incoming-leads` if no stage exists.
    * Preserves any existing stages without overwriting.
* **New 20-Hour Followup Cron Workflow (`1IlXjaNv0rc9laJy`)**:
  * Created and published `Cron - Followup Stage Incoming Leads to Contacted` in n8n (`active: true`, scheduled `0 */2 * * *`).
  * Fetches open conversations tagged with `stage-lead-entrantes` or `stage-incoming-leads`.
  * If 20+ hours elapsed since last customer message:
    * Automatically detects conversation language (English vs Spanish).
    * Sends a courteous closing & availability message matching the brand and customer language.
    * Transitions stage: `stage-lead-entrantes` -> `stage-contactado` (TVTotal24) or `stage-incoming-leads` -> `stage-contacted` (TotalTv USA).
    * Preserves all other labels (`funnel-*`, `channel-*`).
    * Sets custom attribute `stage_contacted_followup_at` to prevent repeated executions.
  * Exported to `workflows/cron_followup_incoming_leads.json`.
* **Facebook Messenger (@TotalTv2025) Integration via Zernio**:
  * Created Chatwoot Inbox **ID 17**: `Facebook - TotalTv USA` (type `Channel::Api`, identifier `w9RpnGQPi2rZWC7ATsw4ixX4`).
  * Updated `Preparar Mensaje` to tag incoming Facebook messages with `funnel-totaltv-usa`, `channel-facebook`, and `stage-incoming-leads`.
  * Updated `Formatear Respuesta` to apply Meta markdown formatting (`*bold*`, flat links) for Inbox 17.
  * Updated `Procesar Inbound Zernio` in `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY`):
    * Enabled platform `facebook` alongside `instagram`.
    * Maps Page `@TotalTv2025` (Account `6a87b56c77555aae01ddcf1c`) to Inbox 17.
    * Contact identifier prefix `fb_<participantId>`.
  * Updated `Enviar a Zernio Instagram` in `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY`):
    * Added handler for Inbox 17 to dispatch outgoing messages via Zernio API `POST /v1/inbox/conversations/${participantId}/messages` with idempotency key `chatwoot_msg_${chatwootMsgId}`.
  * Exported updated workflow to `workflows/router_chatwoot_ia.json`.

### September 1-2, 2026
* **Telegram TotalTv USA Bot Migration**:
  * Switched Telegram bot on Chatwoot Inbox **ID 6** from `@TvTotalUSAbot` to `@TotalTvUSAbot` with token `6744012482:AAH5zvUet_-A1R4tPFUsblDkZi-37uaxUTY`.
  * Updated Inbox name to `TotalTvUSAbot`.
  * Verified Chatwoot webhook registration via Telegram API (`https://project1-chatwoot.efebpb.easypanel.host/webhooks/telegram/6744012482:AAH5zvUet_-A1R4tPFUsblDkZi-37uaxUTY`). All routing, rules, and AI behaviors remain identical.
* **Mega OTT Trial Customer Data Mapping & WhatsApp Alert**:
  * Fixed missing customer data (`contact_name`, `email`, `phone`) in Mega OTT trial generator (`e1R7zQorWBaaqgou`):
    * Replaced `$parameter.*` expressions with `$fromAI(...)` in `Call 'create_trial_tool'` (and `crear_prueba_tvtotal24`) within `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY`).
    * Enhanced `Generar Credenciales` with multi-tier fallback: direct parameters -> trigger query -> Chatwoot conversation `meta.sender` -> Chatwoot recent messages regex scanner.
  * Added node `Notificar WhatsApp (Evolution API)` in `Create Mega OTT Trial Tool`:
    * Dispatches trial details to `584146130135` using instance `TTvAlertsMovistar` via Evolution API (`ecGN8GlLnzNz5Lq5`).
    * Configured with `onError: continueRegularOutput` alongside Telegram `Notificar Administrador`.
  * Synchronized updated workflow JSONs to `workflows/router_chatwoot_ia.json` and `workflows/tool_create_mega_ott_trial.json`.
* **Automatic Prior Stage Cleanup on Trial Generation**:
  * Updated `Agregar Etiqueta Stage Trials` in `Create Mega OTT Trial Tool` (`e1R7zQorWBaaqgou`): Filters out any existing `stage-*` labels (e.g. `stage-incoming-leads`, `stage-contacted`) before applying `stage-trials`.
  * Updated `Agregar Etiqueta Stage Fase de Pruebas` in `Tool - Create MVPlay Trial` (`kh10aaenUURvi7Ji`): Filters out any existing `stage-*` labels (e.g. `stage-lead-entrantes`, `stage-contactado`) before applying `stage-fase-de-pruebas`.
  * Preserves all other labels (`funnel-*`, `channel-*`, `human`) and keeps conversations strictly in a single active stage.
* **Strict Monolingual Response & Dual-Layer Language Defense**:
  * Fixed language mixing in `AI Agent` (TotalTv USA) and `AI Agent - TVTotal24` (Latina):
    * Provided separate, fully localized subscription plans templates for English (`1 Month: 1 Device: $9... Optional Adult Content: FREE`) and Spanish (`1 Mes: 1 Dispositivo: $9... Contenido Adulto opcional: GRATIS`).
    * Added strict negative constraints (`STRICT PROHIBITION IN ENGLISH RESPONSES`) forbidding Spanish words like `Mes`, `Dispositivo`, `Contenido Adulto opcional`, `GRATIS`, `Año` when replying in English.
    * Added `HISTORICAL CHAT MEMORY OVERRIDE` to explicitly instruct the model to ignore and never copy previous contaminated assistant messages from chat memory.
    * Integrated a deterministic bilingual sanitizer in `Formatear Respuesta` that automatically detects English contexts and translates any leaked Spanish plan tokens into 100% pure English before dispatch to Chatwoot/Telegram/WhatsApp/Meta.
  * Synchronized updated workflow to `workflows/router_chatwoot_ia.json`.
* **Mandatory Tool Delegation for Free Trials (Zero Memory-Based Verification)**:
  * Fixed issue where AI Agent hallucinated active trial or limit reached from chat memory instead of consulting Chatwoot:
    * Enforced `CRITICAL MANDATE — TOOL DELEGATION (ZERO MEMORY-BASED ELIGIBILITY CHECKS)` in both `AI Agent` (TotalTv USA) and `AI Agent - TVTotal24`: AI is strictly forbidden from evaluating trial count, active status, or limits from chat history.
    * Whenever a customer requests a trial, asks for another trial, or asks to test again, the AI is mandated to execute `create_trial_tool` (or `crear_prueba_tvtotal24`).
    * Updated tool descriptions in n8n langchain tool nodes to clarify that the CRM database is the sole authority on trial eligibility.
    * Published workflow `n0zgnS1vlOGNcGNY` to active production.
* **Dual Admin Notifications (Telegram & WhatsApp) in TVTotal24 MVPlay Trial Tool**:
  * Added `Notificar Administrador` (Telegram) to `Tool - Create MVPlay Trial` (`kh10aaenUURvi7Ji`):
    * Dispatches trial info to Telegram chat `40371837` with customer name, email, phone, credentials, and DNS URLs.
  * Added `Notificar WhatsApp (Evolution API)` to `Tool - Create MVPlay Trial` (`kh10aaenUURvi7Ji`):
    * Dispatches trial alert via Evolution API instance `TTvAlertsMovistar` to `584146130135`.
  * Configured both notification nodes with `onError: continueRegularOutput` so trial generation output to the AI agent is never blocked.
  * Updated `Evaluar Historial y Preparar Datos` to output `contact_name`, `email`, and `phone` for notification payloads.
  * Published workflow to active production and synchronized to `workflows/tool_create_mvplay_trial.json`.
* **MVPlay Username Conflict Prevention & Auto-Generation Fallback**:
  * Fixed issue where MVPlay trial 2 attempted to reuse trial 1 username (`AlvezCaliman`), causing `STATUS_EXISTS_USERNAME`:
    * Updated username generator in `Evaluar Historial y Preparar Datos` to create unique usernames per trial (`NombreApellido` for trial 1, `NombreApellido2` for trial 2).
    * Added IF node `¿Es Éxito Línea?` and fallback HTTP node `Crear Linea Auto MVPlay` (empty username/password) to ensure 100% success even if a custom username collides in MVPlay.
    * Hardened `Procesar Respuesta MVPlay` to strictly validate `resp.status === 'STATUS_SUCCESS'` and actual line credentials returned by MVPlay API, eliminating dummy fallback data.
    * Published workflow to active production and synchronized to `workflows/tool_create_mvplay_trial.json`.
* **Real-time Live Binance P2P Rate & Transfer to Human Tool Fix**:
  * Fixed Pago Móvil exchange rate calculation in `Tool - Calcular Pago Movil` (`4AYo7CX3Ou1K2yXH`):
    * Replaced sandbox-blocked `fetch` with `this.helpers.httpRequest` to fetch live Binance P2P rates (currently 963+ Bs) instead of falling back to hardcoded 938.30 Bs.
    * Added tiered fallback: Binance P2P -> DolarAPI Paralelo -> DolarAPI Oficial -> 963.00 Bs base.
  * Fixed `Transfer to Human Tool` (`xam0WV65gvTbXcIx`) 404 failure:
    * Defined `account_id` and `conversation_id` in `Call 'transfer_to_human_tool'` workflowInputs schema so parameters are passed by LangChain agent.
    * Added `Preparar Datos Transferencia` node to resolve conversation and account IDs (with fallback regex parsing and Chatwoot open conversation query).
    * Added `onError: continueRegularOutput` on Chatwoot API calls to prevent failure.
  * Reset TVTotal24 trial custom attributes for contact 1246 in Chatwoot via API.
  * Published all updated workflows and synced JSONs.
* **Registered TVTotal24 Custom Attributes in Chatwoot UI**:
  * Created official Custom Attribute Definitions in Chatwoot via API for account 1:
    * `TVTotal24 Trial Count` (`tvtotal_trial_count`, number): tracks number of trials (0, 1, 2).
    * `TVTotal24 Trial 1 ID` (`tvtotal_trial_1_id`, text)
    * `TVTotal24 Trial 1 Username` (`tvtotal_trial_1_username`, text)
    * `TVTotal24 Trial 2 ID` (`tvtotal_trial_2_id`, text)
    * `TVTotal24 Trial 2 Username` (`tvtotal_trial_2_username`, text)
  * Updated `Tool - Create MVPlay Trial` (`kh10aaenUURvi7Ji`):
    * Reads `tvtotal_trial_count` (if 0 or cleared, resets to trial 1).
    * Writes `tvtotal_trial_count` alongside line IDs on trial generation.
  * Published workflow to active production and synchronized to `workflows/tool_create_mvplay_trial.json`.
* **Harden 20-Hour Followup Crons & Prevent Duplicate Sends**:
  * Fixed custom attributes overwrite bug in Chatwoot API (`POST /conversations/{id}/custom_attributes` wipes unprovided keys) by merging existing custom attributes before persisting tracking timestamps (`stage_contacted_followup_at`, `stage_want_to_join_followup_at`, `stage_que_te_parecio_followup_at`).
  * Enforced strict repeat prevention guards in `Cron - Followup Stage Trials to Want to Join` (`KRwjH3njrF4qRdph`) and `Cron - Followup Stage Fase de Pruebas to Que Te Parecio` (`XC1jY6Vkbgdu5iIz`), preventing infinite 2-hour repeat loops on active or trial stages.
  * Added brand and inbox isolation across all crons (TotalTv USA inboxes 1, 4, 6, 14, 17 vs TVTotal24 inboxes 10, 13, 15, 16).
  * Expanded `Cron - Followup Stage Incoming Leads to Contacted` (`1IlXjaNv0rc9laJy`) to support plural label `stage-leads-entrantes`, singular `stage-lead-entrantes`, `stage-incoming-leads`, and open conversations without stage labels.
  * Added automated prior stage label cleanup when applying new stage labels (`stage-contactado`, `stage-contacted`, `stage-want-to-join`, `stage-que-te-parecio`).
  * Published all updated workflows to active production and synchronized local workflow JSON files.

### September 3, 2026
* **Canned Responses / Quick Replies Formatting Remediation (ProseMirror / WhatsApp `\` Cleanup)**:
  * Resolved issue where canned responses imported from Kommo CRM rendered with trailing backslashes `\` at the end of each line when dispatched to WhatsApp (Evolution API), Meta, or Telegram.
  * Root Cause: Chatwoot's ProseMirror WYSIWYG editor treats single isolated newlines (`\n`) within a text block as hard line breaks (`<br>`), which are serialized to standard Markdown as `\\\n`. Downstream channels (such as WhatsApp Baileys in Evolution API) do not parse backslashes as line breaks, rendering literal `\` characters.
  * Remediation: Executed an automated batch migration script across all 132 canned responses via Chatwoot API (`PATCH /api/v1/accounts/1/canned_responses/{id}`), converting single isolated newlines into distinct paragraph blocks (`\n\n`) and removing all residual backslashes.
  * Verified that canned responses (e.g. `/meses`) now serialize cleanly as paragraphs with zero trailing backslashes across all delivery channels.
* **Telegram Channel Verification & Webhook Refresh**:
  * Inspected Telegram integration for TotalTv USA bot (`@TotalTvUSAbot`, token `6744012482:AAH5zvUet_-A1R4tPFUsblDkZi-37uaxUTY`) on Chatwoot Inbox **ID 6**.
  * Verified and refreshed Telegram webhook pointing to `https://project1-chatwoot.efebpb.easypanel.host/webhooks/telegram/6744012482:AAH5zvUet_-A1R4tPFUsblDkZi-37uaxUTY`.
  * Flushed pending updates queue in Telegram API (`pending_update_count: 0`).
* **TotalTv USA WhatsApp Instance Setup (`3059861096` -> Inbox ID 18)**:
  * Registered Evolution API instance `3059861096` (`+1 305 986 1096`) connected to Chatwoot Inbox **ID 18** (`WhatsAppUSA - 3059861096`, `Channel::Api`).
  * Configured webhook in Evolution API: `https://project1-evolution-api.efebpb.easypanel.host/chatwoot/webhook/3059861096`.
  * Assigned agents 1, 2, 3, 4 to Inbox 18 in Chatwoot.
  * Updated n8n router workflow `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY`):
    * `Preparar Mensaje`: Automatically tags incoming messages on Inbox 18 with `funnel-totaltv-usa`, `channel-whatsapp-lite`, and initial stage `stage-incoming-leads`.
    * `¿Qué Empresa?`: Automatically routes Inbox 18 to TotalTv USA `AI Agent`.
    * `Formatear Respuesta`: Applies Meta markdown formatting (`*bold*`, flat links) and typing status for Inbox 18.
  * Updated 20-Hour follow-up crons (`1IlXjaNv0rc9laJy`, `KRwjH3njrF4qRdph`, `XC1jY6Vkbgdu5iIz`) to support Inbox 18 under TotalTv USA policies.
  * Published all updated workflows to active production and synchronized local workflow JSON files.

### September 4, 2026
* **WhatsApp Cloud API Channel Integration & Outbound Template Tracking in Chatwoot**:
  * **Chatwoot WhatsApp Cloud Channel Setup**:
    * Created native WhatsApp Cloud Inbox **ID 19**: `WhatsApp Cloud TVTotal24` (`Channel::Whatsapp`).
    * Configured credentials: Phone Number ID `1106422772565024`, WABA ID `3483325768503437`, Phone `+13054229099`.
    * Assigned support agents (1, 2, 3, 4) to Inbox 19.
    * Webhook Callback URL: `https://project1-chatwoot.efebpb.easypanel.host/webhooks/whatsapp/+13054229099`
    * Webhook Verify Token: `62f0684bf292fe9dd1e87dbd924044c6`
    * **HMAC Inbound Webhook Signature Remediation**: Configured Meta App Secret `e0246891a6e9598fba78f42c28bdca6f` in Chatwoot Inbox 19 `provider_config.app_secret`. Prior to this configuration, Chatwoot returned `200 OK` but silently discarded payloads due to missing HMAC-SHA256 signature verification on the `X-Hub-Signature-256` header.
  * **Kommo CRM Disconnection & Meta Subscribed Apps Verification**:
    * Disconnected phone `+1 305 422 9099` from Kommo CRM and removed Kommo partner integration in Meta Business Manager.
    * Re-subscribed N8N Meta App (`27469809309376250`) to WABA `3483325768503437` webhook subscriptions (`POST /v21.0/3483325768503437/subscribed_apps`).
  * **Outbound WhatsApp Sync Logic in n8n**:
    * Updated workflow `Latin vence hoy y vence4` (`TfILC2hXao6SLQfE`):
      * Added `SyncChatwootVenceHoy` after node `VenceHoy`: searches/creates contact in Chatwoot, ensures conversation exists in Inbox 19, and injects private note with outbound template name (`vencehoy`) and exact text.
      * Added `SyncChatwootVence4dias` after node `Vence4dias`: searches/creates contact in Chatwoot, ensures conversation exists in Inbox 19, and injects private note with outbound template name (`vencepronto`) and exact text.
      * Configured both nodes with `onError: continueRegularOutput` for fail-safe non-blocking execution.
    * Exported workflow JSON to `workflows/latin_vence_hoy_y_vence4.json`.
* **Inbound AI Routing to TVTotal24 (Latina) & Labeling Remediation**:
  * **Chatwoot Automation Rule #9**:
    * Created rule `WhatsApp Cloud TVTotal24 Auto Labels` (Rule ID `9`) triggered on `conversation_created` for `inbox_id == 19`.
    * Applies exact tags: `funnel-totaltv-latina`, `channel-officialwhatsapp`, `stage-leads-entrantes`.
  * **Router Workflow `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY`) Remediation**:
    * `Preparar Mensaje`:
      * Fixed webhook body parsing to robustly extract payload from `$('Webhook').first().json` with direct Chatwoot API fallback (`GET /conversations/{id}`) if `inbox_id` is missing.
      * Added Inbox 19 to TVTotal24 brand evaluation (`isTVTotal24` = inboxes 10, 13, 15, 16, 19).
      * Configured exact labels: removes USA labels, adds `funnel-totaltv-latina`, `channel-officialwhatsapp` (specifically for Inbox 19), and initial stage `stage-leads-entrantes`.
      * Configured node mode to `runOnceForAllItems` to ensure complete batch execution without empty `$json` proxies.
    * `¿Qué Empresa?` (Switch Node):
      * Cleaned output rules with `fallbackOutput: "none"` (eliminating orphaned 3rd output).
      * Output 0: `TotalTv USA` (`brand == "totaltvusa"`) $\to$ Connected to `AI Agent` (TotalTv USA).
      * Output 1: `TVTotal24 (Latina)` (`brand == "tvtotal24"`) $\to$ Connected to `AI Agent - TVTotal24` (Tivi).
  * **n8n Production Workflow Publication**:
    * Identified root cause of persistent staging behavior: n8n was maintaining modifications in draft state (`versionId`) while executing previous frozen production versions (`activeVersionId`).
    * Executed `publish_workflow` to promote draft versions to active production on:
      * `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY`) $\to$ `activeVersionId: e80fc4a0-daa9-49cb-8e10-f909180bad63`
      * `Cron - Followup Stage Fase de Pruebas to Que Te Parecio` (`XC1jY6Vkbgdu5iIz`) $\to$ `activeVersionId: aec991bf-855d-464e-bb8e-6bf8c59420ff`
      * `Cron - Followup Stage Incoming Leads to Contacted` (`1IlXjaNv0rc9laJy`) $\to$ `activeVersionId: 8cd1ea6e-a5e0-4d2b-b3a5-15b84b50d608`
  * **Follow-up Crons Support**:
    * Updated 20-hour follow-up crons (`XC1jY6Vkbgdu5iIz` and `1IlXjaNv0rc9laJy`) to include Inbox 19 under TVTotal24 Latina policies and Meta Markdown formatting.
  * **Repository Synchronization**:
    * Updated workflow exports in `/workflows/` and committed to branch `main`.

* **AI Agents System Prompt Updates: TotalTv USA (Toto) & Leads Ganados Policy**:
  * **TotalTv USA Agent Identity (`Toto`)**:
    * Assigned official assistant name **Toto**.
    * Configured initial greeting and identity mandate: Introduces itself as **Toto, AI Agent for Total TV** in English (*"Hello! I'm Toto, AI Agent for Total TV..."*) and Spanish (*"¡Hola! Soy Toto, AI Agent for Total TV..."*).
  * **Won Leads (`leads-ganados`) Free Trial Policy**:
    * Enforced strict rule across both agents (**Toto** for TotalTv USA & **Tivi** for TVTotal24):
      * If a conversation or contact has the label `leads-ganados` (or `stage-leads-ganados`), the AI agent is strictly forbidden from proactively offering or suggesting free trials during greetings, queries, or subscription plans presentation.
      * If and ONLY IF the customer explicitly asks for a free trial (e.g. *"dame una prueba"*, *"can I get a trial?"*), the AI agent processes and delivers the trial using the standard verification tool flow.
  * **Context Ingestion Pipeline in `Preparar Mensaje`**:
    * Updated `Preparar Mensaje` in `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY`):
      * Evaluates if conversation labels contain `leads-ganados` / `stage-leads-ganados`.
      * Automatically injects `[CLIENT CONTEXT: Label leads-ganados = ACTIVE ...]` tag into the prompt input for LLM awareness.
  * **n8n Production Deployment**:
    * Promoted and published updated workflow `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY`) to active production.
    * Synchronized local workflow JSON and markdown prompt documentation (`prompts/agent_prompt.md`, `prompts/tvtotal24_prompt.md`).

* **Conversation Auto-Assignment: Team "General Support" & Agent "Total TV" (`acalimanr@gmail.com`)**:
  * **Chatwoot Automation Rule #4 Update**:
    * Updated Rule ID 4 (`Asignar nuevas conversaciones a General Support y Total TV`) triggered on `conversation_created`.
    * Configured dual actions:
      * `assign_team`: `[1]` (*General Support*).
      * `assign_agent`: `[3]` (*Total TV* - `acalimanr@gmail.com`).
  * **Cross-Channel Inbox Members Provisioning**:
    * Enrolled Agent 3 (`Total TV` - `acalimanr@gmail.com`) and support agents across all account inboxes (4, 6, 7, 8, 10, 13, 14, 16, 17, 18, 19) to ensure Chatwoot permits agent assignment on any channel.
  * **Router Workflow Assignment Verification**:
    * Added auto-assignment fallback in `Preparar Mensaje` (`Chatwoot + IA Agent` - `n0zgnS1vlOGNcGNY`): if incoming conversation lacks assignment to Team 1 or Agent 3, it calls `POST /conversations/{id}/assignments` (`assignee_id: 3`, `team_id: 1`).
    * Deployed and published updated workflow in n8n production.

* **48-Hour Inactivity Autoclose & Human Label Stripping Workflow**:
  * **New Active Cron Workflow (`asQhO3WgzQW4gR5P`)**:
    * Workflow Name: `Cron - Autoclose Inactive Conversations (48h)`.
    * Schedule: Executes at hours 0, 6, 12, 18 (`0 0,6,12,18 * * *`).
    * Evaluates all open Chatwoot conversations (`status=open`).
    * Inactivity threshold: $\ge 48$ hours since the last non-private incoming message from the customer (or since conversation creation if no customer message).
    * Autoclose Actions:
      1. **Label Updates**: Strips `human` tag (guaranteeing that if the customer messages back in the future, the AI agent can reply immediately), applies `autoclosed` tag, and preserves all other labels (`funnel-*`, `channel-*`, `stage-*`).
      2. **Status Resolution**: Dispatches `POST /conversations/{id}/toggle_status` (`status: "resolved"`).
  * **Router Reopening Remediation**:
    * Updated `Preparar Mensaje` in `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY`): when an autoclosed conversation reopens upon receiving a new customer message, it automatically removes the `autoclosed` tag and resumes AI assistance seamlessly.
  * **Production Deployment**:
    * Deployed and published active production version in n8n.
    * Synchronized local workflow export to `workflows/cron_autoclose_inactive_conversations.json` and registered in `workflows/export_workflows.py`.

* **Google Sheets Customer Database Check & Won Leads Handling**:
  * **Spreadsheet Document**: `Clientes TotalTV` (`1SNRbfgomUgtac58UmIMlH8UzizBXrTDVogxJEt-z9A0`, Credential: `Pw5wN2L5UopOruaj`).
    * **TotalTv USA Inboxes** (4, 6, 14, 17, 18): Sheet **`Mega`** (GID `51202947`).
    * **TVTotal24 Inboxes** (10, 13, 15, 16, 19): Sheet **`DnSpace`** (GID `1823373862`).
  * **Search & Match Criteria**:
    * Match by **`Teléfono`** (normalized numeric comparison, suffix match $\ge 7$ digits / 10 digits) or **`Email`** (case-insensitive).
  * **Existing Client Actions (Match Found)**:
    1. **Contact Bio Update**: Updates Chatwoot Contact's Bio (`additional_attributes.description`) with the value of column **`1ra compra`**.
    2. **Contact Name Sync**: Forms full name from **`Nombre`** + **`Apellido`** and updates contact name if unnamed.
    3. **Conversation Stage Labels**: Strips ALL stage labels (`stage-*`) and applies **`stage-leads-ganados`** (preserving all `funnel-*`, `channel-*`, `autoclosed`, etc. labels).
    4. **AI Agent Behavior (Toto & Tivi)**:
       - Injects `[CLIENT CONTEXT: Existing customer in database (stage-leads-ganados)...]` with registered Name, Email, Phone, and 1ra Compra.
       - **Zero Proactive Trial Rule**: AI agent never proactively offers free trials to existing clients.
       - **Zero Data Collection Rule**: If an existing client explicitly asks for a free trial or asks to speak with a human agent, the AI agent **DOES NOT ASK FOR NAME, PHONE, OR EMAIL** because their data is already registered. The AI agent immediately invokes the respective tool (`create_trial_tool` / `crear_prueba_tvtotal24` / `transfer_to_human_tool`) using their known registered data.
  * **New Client Actions (No Match Found)**:
    - Standard new lead flow proceeds normally (assigns `stage-incoming-leads` or `stage-leads-entrantes` if no stage is present, and collects 3 data points upon trial request).
  * **Production Deployment**:
    - Updated `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY` / activeVersionId `36f6d68c-e902-475b-9906-14a2dbddd6c0`) with nodes `¿Requiere Buscar en Sheet?`, `Leer Sheet DnSpace`, `Leer Sheet Mega`, `Evaluar Cliente DnSpace`, and `Evaluar Cliente Mega`.
    - Synchronized prompts (`prompts/agent_prompt.md`, `prompts/tvtotal24_prompt.md`).
    - Local workflow definitions exported and verified.

* **Audit & Autoclose of $\ge 48\text{h}$ Inactive Conversations**:
  * **Chatwoot Audit**: Analyzed all 23 open conversations. Identified 10 conversations with $\ge 48$ hours of customer inactivity (IDs: 1323, 1324, 1314, 1309, 1310, 1313, 14, 1295, 1306, 13).
  * **Resolution Executed**: Stripped `human` tag, applied `autoclosed` tag, and changed status to `resolved` on all 10 inactive conversations.
  * **Remaining Active Queue**: Confirmed exactly 13 active conversations remain open in Chatwoot, all having $< 48$ hours of recent interaction.
  * **Active Cron Deployment**: Workflow `Cron - Autoclose Inactive Conversations (48h)` (`asQhO3WgzQW4gR5P` / activeVersionId `e54ef1cb-f576-4b13-964a-8169d839073b`) published and active in n8n on schedule `0 0,6,12,18 * * *`.

* **Fix: Latin vence hoy y vence4 (`TfILC2hXao6SLQfE`) - Red Text on Expired Rows in `DnSpace`**:
  * **Root Cause**:
    1. Previous switch node had rule 2 ("Limpiar registros pasados") conditioned on `PLAY === 'SENT'`. Expired rows with `PLAY === ""` or `PLAY === 'SENT4'` were ignored and never sent to the red text formatting node.
    2. Date parsing using rigid `toDateTime()` failed when Google Sheet date cells were formatted as `DD/MM/YYYY` or `DD-MM-YYYY`.
    3. HTTP Request node was executing individual per-item `batchUpdate` requests instead of a consolidated batch payload.
  * **Solution & Architecture**:
    1. Replaced rigid Switch logic with Code Node `Evaluar Vencimiento y Categorizar` normalizing dates across `YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY`, `MM/DD/YYYY` in America/Caracas timezone.
    2. Categorizes all clients with `venceIso < todayStr` into `vencidos_pasados` regardless of `PLAY` column value.
    3. Added `PrepararBatchRojo` Code Node that clusters all expired rows into a single `batchUpdate` `repeatCell` payload targeting `sheetId: 1823373862`, startColumnIndex 5 to endColumnIndex 6 (Column F: "Vence"), applying red foreground text color (`{ red: 0.85, green: 0.1, blue: 0.1 }`).
    4. Concurrently cleans `PLAY` to `" "` via `LimpiarSENTVencidos` node.
  * **Production Deployment & Verification**:
    - Deployed and published active production version `653dbc16-4bb5-49ca-ad17-46bcb5b00d52` in n8n.
    - Executed live test (Execution ID `4973`) with status `success`.
    - Synchronized local workflow file `workflows/latin_vence_hoy_y_vence4.json`.

### September 6, 2026
* **Downloader Code and App Download URL Update Across AI Agents**:
  * **Objective & Context**: Updated the Downloader installation instructions for the TotalTv application across both brand agents (TotalTv USA - Toto and TVTotal24 Latina - Tivi).
  * **Values Updated**:
    * Downloader code updated from `910992` to **`5533902`** for Firestick, Android TV, and Google TV devices.
    * Android Smartphone direct download link updated from `http://aftv.news/910992` to **`http://aftv.news/5533902`**.
  * **Components Updated**:
    * `prompts/agent_prompt.md` (TotalTv USA).
    * `prompts/tvtotal24_prompt.md` (TVTotal24 Latina).
    * Synchronized and injected into live n8n router workflow `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY`).
    * Synchronized local files and exported to `workflows/router_chatwoot_ia.json`.

* **Channel Labels & Stage Leads Entrantes Backfill in Chatwoot**:
  * **Context**: Conversations handled by TVTotal24 Latina on WhatsApp Cloud (`+1 305 422 9099`, Inbox 19) were receiving `funnel-totaltv-latina`, but required `channel-officialwhatsapp` and `stage-leads-entrantes`.
  * **Remediation**:
    * Verified and updated routing logic in `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY`) node `Asignar Etiquetas Latina` to guarantee `channel-officialwhatsapp` and `stage-leads-entrantes` tags on Inbox 19 conversations.
    * Executed retroactive script across recent active Chatwoot conversations ensuring all appropriate channel and stage labels are properly attached.

* **Customer Name & Channel Username Sync to Chatwoot Contact**:
  * **Objective & Context**: When an incoming message matches an existing customer in Google Sheets (`Clientes TotalTV` - sheet `Mega` for TotalTv USA or `DnSpace` for TVTotal24):
    1. The contact's default name recorded by the channel integration (WhatsApp push name, Instagram handle, Facebook username, Telegram username) is preserved and stored into Chatwoot's **Company Name** field (`additional_attributes.company_name`).
    2. The contact's primary display name (`name`) in Chatwoot is substituted with the customer's full name formed by columns **`Nombre`** and **`Apellido`** from the Google Sheet.
    3. The contact's Bio (`additional_attributes.description`) retains the **`1ra compra`** date.
    4. Conversation stage is tagged with **`stage-leads-ganados`** and the AI agent is provided full customer context (Zero proactive trial & zero data collection rules).
  * **Root Cause of Previous Failure**:
    * Restrictive regex guard `if (fullName && (!contactName || /^\+?\d+$/.test(contactName) || contactName.toLowerCase().includes('user')))` prevented updating names when the channel name contained characters, spaces, or words other than purely digits or 'user' (e.g., "Alvez Movistar", "€| R€¥").
    * Contact update was additionally enclosed in `if (contactId && firstPurchase)`, blocking updates if `1ra compra` was missing.
    * The default channel username was not being mapped to `company_name`.
  * **Remediation Implemented in `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY`)**:
    * `Preparar Mensaje`:
      * Extracts `contact_additional_attributes` and `contact_company_name`.
      * Configured `already_leads_ganados: canBypassSheet` where `canBypassSheet = isAlreadyLeadsGanados && Boolean(contactCompanyName)`, ensuring existing customers previously tagged with `stage-leads-ganados` but lacking `company_name` and full name are routed to the sheet to self-heal.
    * `Evaluar Cliente DnSpace` & `Evaluar Cliente Mega`:
      * Extracts sheet `Nombre` + `Apellido` as `fullName`.
      * Preserves existing company name if already stored; otherwise maps the default channel push name/handle (`contactName`) to `updatePayload.additional_attributes.company_name`.
      * Sets `updatePayload.name = fullName` and `updatePayload.additional_attributes.description = firstPurchase`.
      * Updates downstream variables `client_name` and `contact_name` so AI prompts immediately reflect the customer's verified real name.
  * **Production Deployment**:
    * Published workflow `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY`) to active production (`activeVersionId: b3278fdf-ae5e-46d5-8796-f0038981779f`).
    * Exported workflow to `workflows/router_chatwoot_ia.json` via `python3 workflows/export_workflows.py`.

* **AI Agent Data Collection Rules Refinement (Trials vs. Human Transfer vs. Greetings vs. Existing Clients)**:
  * **Objective & Business Rules**:
    1. **Free Trial Requests (`pidiendo una prueba`)**: The AI Agent MUST imperatively and obligatorily require all 3 data points: **Full Name** (at least 2 words: first and last name), valid **Email**, and **Phone** with country code (with explicit international format guidance: `codpais+telefono`). In TVTotal24 Latina, time availability for 4 continuous hours must also be confirmed. Only for free trial requests are all 3 data points required.
    2. **Human Agent Transfer (`pidiendo hablar con un humano`)**: Transferring to a human agent does NOT require email or phone number! Knowing at least the customer's name suffices. If the customer's name is already known (via context, profile, or previous messages), `Call 'transfer_to_human_tool'` is called immediately. If the name is unknown, the AI asks solely for their name (e.g. "¿Con quién tengo el gusto para comunicarte con un asesor?"), never email or phone, and transfers immediately upon receiving it.
    3. **Greetings & Courtesy (`saludando`)**: Knowing at least the name suffices. The AI must NEVER ask for email or phone during greetings or polite conversations.
    4. **Existing Clients (`si el cliente ya existe` / `stage-leads-ganados`)**: Under NO circumstance are full name, email, or phone asked from existing clients because their data is already registered in the system. The respective tools (`create_trial_tool` / `crear_prueba_tvtotal24` or `Call 'transfer_to_human_tool'`) are executed directly using their known registered data.
  * **Implementation Across Components**:
    * `prompts/agent_prompt.md` (TotalTv USA - Toto):
      * Updated `GREETING & INITIAL INTERACTION` with strict prohibition on requesting email or phone during greetings.
      * Updated `FREE TRIAL POLICY & WORKFLOW` with `CRITICAL MANDATE — DATA COLLECTION SCOPE`.
      * Updated `HUMAN HANDOVER / TRANSFER TO HUMAN`: knowing at least the name suffices, strictly forbidden from asking email/phone, immediate tool execution if name or existing client is known.
    * `prompts/tvtotal24_prompt.md` (TVTotal24 Latina - Tivi):
      * Updated `RULE 2.1 — GREETINGS AND COURTESY`.
      * Updated `FREE TRIAL POLICY & FLOW` with `REGLA GENERAL OBLIGATORIA DE RECOLECCIÓN DE DATOS`.
      * Updated `HUMAN HANDOVER / TRANSFER TO HUMAN`: tool invocation via `Call 'transfer_to_human_tool'`, name-only requirement, zero email/phone requirement.
    * `workflows/router_chatwoot_ia.json` (`n0zgnS1vlOGNcGNY`):
      * Updated nodes `Preparar Mensaje`, `Evaluar Cliente DnSpace`, and `Evaluar Cliente Mega` to supply `[CLIENT CONTEXT: Known Contact Name: ...]` when valid person names are detected on non-existing leads, allowing immediate transfer or personalized greeting without redundant questioning.
      * Injected updated prompts into node parameters for `AI Agent` and `AI Agent - TVTotal24`.
  * **Production Deployment**:
    * Published workflow `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY`) to active production (`activeVersionId: 7dbd7bf9-d120-4458-8fbd-f0507443b5cb`).
    * Synchronized local workflow files via `python3 workflows/export_workflows.py`.

* **Flexible Trial Handling for Existing Clients (Self vs. Family/Friend)**:
  * **Objective & Context**: When an existing client (`stage-leads-ganados`) requests a free trial, they might be requesting it for themselves or for a family member or friend (e.g. "tengo un hermano, Jason, que quiere probar").
  * **Business Logic**:
    1. **Check Chat History**: If the client already specified who the trial is for and provided their details (e.g., recipient's name, email, phone), use those details directly.
    2. **Confirm Recipient if Not Specified**: If the client asks generically for a trial, confirm whether they want it under their own registered details or if it is for a family member or friend and they want to provide the recipient's details.
    3. **If for Themselves**: Do not ask for their data again; execute the trial tool immediately with their registered data from context.
    4. **If for a Family Member/Friend**: Collect the recipient's required data (full name with at least 2 words, valid email, and phone with country code) and generate the trial under that person's data.
  * **Components Updated**:
    - `prompts/agent_prompt.md`: Updated `FLEXIBLE TRIAL HANDLING (SELF vs. FAMILY / FRIEND)`.
    - `prompts/tvtotal24_prompt.md`: Updated `GESTIÓN FLEXIBLE DE PRUEBAS PARA CLIENTES EXISTENTES (PARA SÍ MISMO O PARA UN TERCERO / FAMILIAR / AMIGO)`.
    - `workflows/router_chatwoot_ia.json`: Updated `Preparar Mensaje`, `Evaluar Cliente DnSpace`, and `Evaluar Cliente Mega` context tags.
    - n8n workflow published to production (`activeVersionId: 7dbd7bf9-d120-4458-8fbd-f0507443b5cb`).

* **Ecwid Order Parser & Notification Fallbacks Update (`Ecwid to Client & me 2.0` - `hAHmBsRVDc4Hyt6g`)**:
  * **Objective & Problem Statement**:
    * When orders are placed in Ecwid for TotalTv USA, order confirmation and payment notification messages are dispatched across Email (Gmail), SMS (Telnyx), and WhatsApp (Meta Cloud API / Evolution API).
    * Previously, when parsing customer data from the Ecwid notification email in node `TomaDatosDelEmail`, missing fields defaulted to `"No encontrado"`.
    * This produced undesirable outputs such as greeting the customer with `"Dear No encontrado"`, email subjects reading `"No, your TotalTv Order..."` (due to `.split(' ')[0]`), and missing connections, amounts, or adult content reading `"No encontrado"`.
  * **Business Rules Implemented**:
    1. **Customer Name Fallback**:
       * If the customer's name cannot be extracted from the email subject/body, it must strictly default to **`"Customer"`** (greeting reads `"Dear Customer"` and email subject reads `"Customer, your TotalTv Order..."`).
    2. **Connections, Amount & Adult Content Fallbacks**:
       * If the number of connections (`Conns`), total amount (`TotalAmount`), or adult programming (`Adult`) cannot be extracted, they must strictly default to a single dot **`"."`** instead of `"No encontrado"`.
  * **Implementation Across Workflow Nodes**:
    * `TomaDatosDelEmail` (`4dadaf29-3fad-48f6-9552-f684451d67dd`):
      * Rewrote extraction helper `extract(regex, text, index, fallback)` with default fallback `"."`.
      * `CustomerName`: Fallback set to `"Customer"`. Added guard: `(rawCustomerName && rawCustomerName !== "No encontrado" && rawCustomerName !== ".") ? rawCustomerName : "Customer"`.
      * `Conns`: Fallback set to `"."`.
      * `Adult`: Fallback set to `"."`.
      * `TotalAmount`: If missing or non-numeric, fallback set to `"."`.
    * Downstream Notification & Formatting Nodes:
      * `Formatear Mensaje Zelle`: Cleanly handles `Adult: .` and `Total Amount: .` (or `$X`), defaults customer name to `"Customer"`.
      * `Formatear Mensaje` (Whop / Pay by link): Cleanly handles `Adult: .` and `Total: .` (or `$X`), defaults customer name to `"Customer"`.
      * `Formatear Mensaje Crypto`: Cleanly handles `Adult: .` and `Total: .` (or `$X`), defaults customer name to `"Customer"`.
      * `Email Zelle a Cliente` (Gmail): Updated subject to use `Customer` when name is missing; updated HTML message to display `.` for missing amount and `Dear Customer`.
      * `Email Link a Cliente`, `Email Link a Cliente1`, `Email NowPayLink a Cliente`: Updated HTML templates to prevent `$NaN` when `TotalAmount` is `.` (displaying `.` for missing amounts), and cleanly rendering `Adult: .` when adult info is absent.
      * `WhatsMeZelle`, `Notificarme Link Cashapp`, `Notificarme Link NowPay`, `Whatsme Link NowPay`, `Whatsme Link PdCash`: Updated formatting expressions to use `Customer` and `.` fallbacks.
  * **Production Deployment**:
    * Enabled MCP access on workflow `hAHmBsRVDc4Hyt6g`.
    * Applied all 13 node operations atomically in n8n.
    * Published workflow `Ecwid to Client & me 2.0` (`activeVersionId: cd4d61f1-2fbb-4a9a-b279-a7c7172f1136`).
    * Added `ecwid_to_client_and_me_2` to `workflows/export_workflows.py`.
    * Exported workflow JSON to `workflows/ecwid_to_client_and_me_2.json`.

### September 7, 2026
* **Human Handover Confirmation & Extended Office Hours Message (`Transfer to Human Tool` & AI Agents)**:
  * **Problem Statement**:
    * When transferring to human support, AI agents (Toto and Tivi) were mistakenly generating error messages to customers claiming that the transfer could not be done ("no se pudo hacer la transferencia"), despite the transfer succeeding in the backend (the conversation was labeled `human` and the admin received Telegram & WhatsApp alerts).
  * **Root Cause & Remediation**:
    1. **Tool Output Normalization (`xam0WV65gvTbXcIx`)**:
       * Added a dedicated terminal Code node `Respuesta Tool Transferencia` that always returns a clean, structured JSON response (`status: "success"`, `human_transfer: "completed"`, `message: "La conversación ha sido transferida exitosamente a un asesor humano."`).
       * Added `onError: "continueRegularOutput"` across notification nodes (`Notificar Administrador`, `Nota privada Chatwoot`, `Notificar WhatsApp`) so notification latency or transient errors never affect the tool's success response to the LLM.
       * Deployed and published active production version `bec45d34-f869-4174-8232-88767013947d` in n8n.
    2. **AI Agent Prompt Directives**:
       * Updated `HUMAN HANDOVER / TRANSFER TO HUMAN` in `prompts/agent_prompt.md` and `prompts/tvtotal24_prompt.md`.
       * Enforced mandatory rule: Calling `Call 'transfer_to_human_tool'` is ALWAYS successful. Agents are strictly forbidden from stating or apologizing that the transfer failed.
       * Mandated clear, reassuring confirmation message: Customers must be informed that they have been transferred to human support and will be assisted shortly within extended office hours (*"horario extendido de oficina"*).
  * **Production Deployment**:
    * Injected updated prompts into `AI Agent` and `AI Agent - TVTotal24` in router workflow `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY` / activeVersionId `f11dc553-fc5f-4437-b639-1ef9414e8aa5`).
    * Synchronized local files and exported via `workflows/export_workflows.py`.

* **Existing Client Credentials & Login Support: Strict Zero-Hallucination Policy**:
  * **Problem Statement**:
    * An existing subscriber in TotalTv USA asked for their credentials, and the AI agent invented/hallucinated a fictional username and password rather than acknowledging it does not know active credentials and transferring them to a human agent.
  * **Business Rule Implemented**:
    * **Zero Knowledge of Active Credentials**: AI agents (Toto and Tivi) have NO access to active customer service credentials in the Mega OTT or MVPlay subscription database.
    * **Strict Prohibition on Fabricating Credentials**: AI agents are STRICTLY FORBIDDEN from inventing, guessing, or generating any username/password when an existing subscriber asks for their login details, forgotten credentials, or renewal access.
    * **Standard Handover Flow**:
      1. Explain politely that, for security and privacy reasons, the AI agent does not have direct access to active service credentials.
      2. **Immediately execute `Call 'transfer_to_human_tool'`** (without asking for any data, since they are an existing client).
      3. Inform the customer that a human support advisor will verify their account in the panel and safely supply their credentials shortly within extended office hours.
  * **Production Deployment**:
    * Added dedicated sections in `prompts/agent_prompt.md` (*EXISTING CLIENT CREDENTIALS & LOGIN SUPPORT (STRICT ZERO HALLUCINATION RULE)*) and `prompts/tvtotal24_prompt.md` (*SOPORTE DE CREDENCIALES Y ACCESOS PARA CLIENTES EXISTENTES (PROHIBICIÓN ESTRICTA DE INVENTAR CREDENCIALES)*).
    * Deployed and published in `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY`).

* **Fix: Facebook TotalTv USA (Inbox 17 / Zernio) "Failed to Send" Messages**:
  * **Problem Statement**:
    * In conversation #1338 (and other conversations in Inbox 17: Facebook - TotalTv USA via Zernio), messages were successfully dispatched to Zernio API and delivered to Facebook, but Chatwoot displayed red "failed to send" badges (`status: "failed"`).
  * **Root Cause**:
    * In Chatwoot, Inbox 17 is configured as an API Channel (`Channel::Api`).
    * The channel's `webhook_url` attribute was stored as the literal string `"null"` (4 characters: `'n','u','l','l'`) instead of empty string `""`.
    * Whenever Chatwoot's background worker processed messages in this channel, it attempted to open an HTTP callback connection to host `null:80` (`Failed to open TCP connection to null:80 (getaddrinfo(3): Name does not resolve)`). Because DNS resolution on `"null"` failed, Chatwoot marked all messages in the inbox as `failed`.
  * **Remediation**:
    * Updated Inbox 17 channel configuration via Chatwoot API (`PATCH /api/v1/accounts/1/inboxes/17`, `channel: { webhook_url: "" }`).
    * Audited all other inboxes (13, 14, 16, 18, 4, 19, 6, 10, 7, 8) to verify that none contain `"null"` or invalid callback URLs.
    * Verified resolution with test message in conversation #1338, confirming message status is now immediately recorded as `sent`.

### September 13-14, 2026
* **Cross-Brand Google Sheets Search Fallback & Contact Auto-Enrichment Fix**:
  * **Problem Statement**:
    * Several incoming customer conversations were failing to match their corresponding record in the Google Sheets database (`Clientes TotalTV` - Doc ID `1SNRbfgomUgtac58UmIMlH8UzizBXrTDVogxJEt-z9A0`), even though their phone numbers matched sheet records.
    * As a result, the expected automatic operations were not triggering: the contact name was not updated to `Nombre` + `Apellido`, the default channel handle was not saved to `company_name`, the first purchase date was not written to `bio` (`additional_attributes.description`), and the conversation remained without the `stage-leads-ganados` label.
  * **Root Causes Diagnosed**:
    1. **Strict Brand-Locked Sheet Routing**:
       * The switch node `¿Requiere Buscar en Sheet?` routed strictly by the brand detected from the inbox. TotalTv USA (e.g. Inbox 18) only searched sheet `Mega`, while TVTotal24 Latina (e.g. Inbox 16, 19) only searched sheet `DnSpace`.
       * If a customer registered in `DnSpace` messaged the TotalTv USA WhatsApp inbox (such as Guillermo Montero #1230 / Conv #1381), the workflow never checked `DnSpace` and failed to identify the customer.
    2. **Column Header Matching Sensitivity**:
       * Direct object property access like `row['Teléfono']` or `row['Nombre']` returned `undefined` whenever sheet columns had whitespace variations, casing discrepancies, or alternative naming.
    3. **Phone Number Format Nuances**:
       * Formats such as Venezuelan numbers with leading zeros (`0414...` vs `58414...`), Mexican WhatsApp `1` prefix (`521...` vs `52...`), and Spanish 9-digit numbers failed strict string comparison.
    4. **Premature Abort on `human` Conversations**:
       * In node `Preparar Mensaje`, `if (labels.includes('human')) return [];` completely terminated workflow execution before the Google Sheets lookup, skipping contact enrichment entirely for human-managed conversations.
  * **Remediation & Architecture Implemented in `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY`)**:
    1. **Non-Blocking `human` Flag**:
       * In `Preparar Mensaje`, conversations with the `human` label now set `skip_ai_response: true` instead of aborting. This allows the workflow to flow through sheet lookup and contact enrichment, while the switch node `¿Qué Empresa?` checks `skip_ai_response != true` to suppress LLM message generation.
    2. **Robust Multi-Regex Field Extractor (`getField`)**:
       * Normalized field extraction across `tel|phone|cel|movil|whats`, `email|correo`, `nombre`, `apellido`, and `1ra.*compra|primera.*compra|fecha.*compra|compra`.
    3. **Multi-Format Phone Matcher (`phonesMatch`)**:
       * Cleans non-digits, checks exact match, suffix match ($\ge 7$ digits), last-10-digits, last-9-digits, and Mexican `521` normalization.
    4. **Cross-Sheet Fallback Routing**:
       * TotalTv USA Path: `Leer Sheet Mega` $\to$ `Evaluar Cliente Mega` $\to$ `¿Encontró en Mega?`. If false $\to$ `Leer Sheet DnSpace (Fallback)` $\to$ `Evaluar DnSpace (Fallback)` $\to$ `¿Qué Empresa?`.
       * TVTotal24 Latina Path: `Leer Sheet DnSpace` $\to$ `Evaluar Cliente DnSpace` $\to$ `¿Encontró en DnSpace?`. If false $\to$ `Leer Sheet Mega (Fallback)` $\to$ `Evaluar Mega (Fallback)` $\to$ `¿Qué Empresa?`.
    5. **Complete Contact Enrichment**:
       * If found:
         * Preserves default channel handle into `additional_attributes.company_name`.
         * Sets `name` to `Nombre` + `Apellido`.
         * Sets `additional_attributes.description` (Bio) to first purchase date (`1ra compra`).
         * Removes any prior `stage-*` labels and applies `stage-leads-ganados`.
  * **Production Deployment & Live Verification**:
    * Published workflow `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY`) to active production (`activeVersionId: 46b3c455-e75d-46e8-80c6-3b33b668e958`).
    * Verified live on Chatwoot contacts:
      * **Guillermo Montero** (Conv #1381, Contact #1230): Bio set to `2022-06-20`, labeled `stage-leads-ganados` (without `human`).
      * **Lazaro Figueredo** (Conv #1372, Contact #1173): Channel handle `"EFGroning"` preserved in `company_name`, name updated to `"Lazaro Figueredo"`, bio set to `2026-08-17`, labeled `stage-leads-ganados` (without `human`).
      * **Luis Villar** (Conv #1365, Contact #1240): Bio set to `2025-11-16`, labeled `stage-leads-ganados` (without `human`).
    * **Preservación de la Etiqueta `human`**:
      * El workflow de n8n nunca agrega la etiqueta `human` por su propia cuenta; solo reemplaza etiquetas que comienzan por `stage-*` por `stage-leads-ganados`. Si una conversación ya poseía `human`, se respeta y conserva; si no la tenía, jamás se le coloca. (La aparición temporal de dicha etiqueta en las pruebas provino de los scripts de simulación webhook y fue removida de inmediato).
    * Exported workflow to `workflows/router_chatwoot_ia.json`.

* **WhatsApp Trailing Backslashes (`\`) Fix via Webhook Sanitizing Proxy (`Proxy - Chatwoot to Evolution API`)**:
  * **Problem Statement**:
    * Messages sent from Chatwoot to WhatsApp across Evolution API channels (such as TVTotal24 Latina `lat-whatscol` - Inbox 16 and TotalTv USA `3059861096` - Inbox 18) were arriving on customers' phones with literal backslash characters (`\`) at the end of each line (e.g. `http://smrts.wxn.ch:2095\`).
    * Customers copying URLs or credentials inadvertently copied the trailing backslash, causing login and playlist connection errors (e.g. Conversation #1382 with Guillermo Montero).
  * **Root Cause**:
    1. **Chatwoot ProseMirror Serialization**:
       * In the Chatwoot web interface, the message input editor uses ProseMirror. Whenever a human agent inserts a line break (`<br>`), presses `Shift+Enter`, or pastes multiline text, Chatwoot's Markdown serializer translates the line break into Markdown hard-break syntax: `\\\n` (a backslash followed by a newline).
    2. **Evolution API Bug in Outgoing Message Webhook**:
       * In Evolution API (`src/api/integrations/chatbot/chatwoot/services/chatwoot.service.ts` line 1339 & 1454), the handler for `body.message_type === 'outgoing'` replaces bold/italic symbols, but fails to strip `\\\n` before passing the text to Baileys (`textMessage`). (By contrast, the developers did include `.replace(/\\\r\n|\\\n|\n/g, '\n')` for template messages at line 1592, but missed normal outgoing messages).
       * Baileys dispatches the text verbatim to WhatsApp, which renders the backslash as a literal visible character.
  * **Solution & Architecture**:
    1. **n8n Sanitizing Webhook Proxy (`Proxy - Chatwoot to Evolution API` - `ecfTEElylV4snTHG`)**:
       * Created and published an active webhook proxy in n8n (`https://n8n.ac4.club/webhook/chatwoot-evolution-proxy?instance={instance}`).
       * Intercepts Chatwoot's outgoing channel webhook before it reaches Evolution API.
       * Cleans trailing backslashes before newlines (`/\\+(\r?\n|$)/g`) and standalone backslash lines (`/^[ \t]*\\+[ \t]*$/gm`) in `body.content` and `body.conversation.messages`.
       * Forwards the clean JSON payload to Evolution API: `POST https://project1-evolution-api.efebpb.easypanel.host/chatwoot/webhook/{instance}`.
       * Relays Evolution API's HTTP 200 `{ message: "bot" }` response back to Chatwoot.
    2. **Chatwoot Inboxes Routing Update**:
       * Reconfigured `webhook_url` across all Evolution API inboxes:
         * **Inbox 16** (`lat-whatscol`): `https://n8n.ac4.club/webhook/chatwoot-evolution-proxy?instance=lat-whatscol`
         * **Inbox 18** (`WhatsAppUSA - 3059861096`): `https://n8n.ac4.club/webhook/chatwoot-evolution-proxy?instance=3059861096`
         * **Inbox 4** (`TTvAlertsMovistar`): `https://n8n.ac4.club/webhook/chatwoot-evolution-proxy?instance=TTvAlertsMovistar`
    3. **Canned Responses Sanitization**:
       * Batch cleaned backslashes from canned responses `zelle` (#25) and `zelle_usa` (#97).
  * **Production Deployment**:
    * Workflow `ecfTEElylV4snTHG` published to active production (`activeVersionId: c15e5bcd-f50a-4f4b-8b40-89d49b99972c`).
    * Registered in `workflows/export_workflows.py` and exported to `workflows/proxy_chatwoot_evolution.json`.

---

## 18. Mandatory Technical & Administrative Triage Protocol (Prohibition on Premature Human Handover)

* **Problem & Root Cause**:
  * The AI agents for TotalTv USA (`Toto`) and TVTotal24 (`Tivi`) were prematurely transferring conversations to human support (`Call 'transfer_to_human_tool'` / adding the `human` label) without giving customer attention or diagnostic triage.
  * Triggers as simple as "tengo problemas de señal", "la tv se queda colgada", "no se ven las series", "mi cuenta está vencida", or "ya hice el pago" caused immediate handover even though the customer had never asked to speak with a human.
  * Root causes identified:
    1. System prompts previously instructed: "...OR when an existing customer requests their active service credentials / technical human support." The LLMs interpreted any technical complaint as "technical human support" warranting immediate tool execution.
    2. Earlier prompt versions strictly prohibited asking for phone on human handover, meaning agents transferred without ensuring support had customer contact information.
    3. `clientContextPrefix` in n8n code nodes previously contained: "3. If asking for a human, transfer immediately!", which combined with vague issue detection triggered impulsive transfers.
* **Architecture & Business Rules Implemented**:
  1. **Strict Prohibition on Premature Handover**:
     * The AI agent must NEVER transfer conversations to human support upon initial issue reports, complaints, signal failures, playback errors, expired accounts, or payment announcements.
     * Handover is strictly gated to:
       a) Explicit, unambiguous customer request to speak to a person / human support ("quiero hablar con un humano", "pásame a una persona", "un asesor por favor", "talk to human", "speak with someone").
       b) Retrieval of forgotten active account credentials (which the AI does not have access to in panels).
       c) After completing mandatory technical or administrative triage when human panel intervention is required.
  2. **Customer Identification Before Handover**:
     * Customer Name and Phone number MUST be known before executing `Call 'transfer_to_human_tool'`.
     * If the customer is an existing client (`stage-leads-ganados`) or if name and phone are already known in context or previous messages, DO NOT ask again.
     * If the customer is new or name/phone are unknown, the AI MUST politely request Name and Phone number before transferring.
  3. **Technical Triage Protocol**:
     * Mandatory diagnostic data collected before any technical escalation:
       - **Detailed description of failure**: Specific channel, movie, or series failing, and exact error code or message on screen.
       - **Service Username**: Account username (`nombre de usuario`).
       - **Application & Device**: Exact app used (TotalTv native app, Smarters, XCIPTV, Downloader, etc.) and device (Firestick, Smart TV, Android Box, Smartphone, Roku, etc.).
     * Agent suggests basic troubleshooting (restarting app/router) or escalates with full diagnostic data.
  4. **Administrative & Billing Triage Protocol**:
     * Mandatory payment data collected before any billing escalation:
       - **Payment Method**: Method used (Zelle, Crypto, CashApp, Card/PayPal for USA; Pago Móvil, Zelle, Binance for Latina).
       - **Exact Amount**: Exact amount paid/transferred.
       - **Payment Receipt / Reference**: Reference number, transaction ID, or screenshot/capture.
       - **Service Username / Registered Email**: For account renewal/reactivation.
     * Agent escalates to billing human support only after collecting payment details.
  5. **Inclusion of Collected Case Info in Internal Notes & Admin Alerts**:
     * When transferring to human, all collected case details MUST be included in the Chatwoot private note and the admin alerts.
     * **Tool Parameter Mapping**: `Call 'transfer_to_human_tool'` in `n0zgnS1vlOGNcGNY` defines `workflowInputs` with `reason` and `case_details` via `$fromAI`, allowing the LLM to pass a structured triage summary.
     * **`Transfer to Human Tool` (`xam0WV65gvTbXcIx`)**:
       - Extracts `reason` and `case_details` from trigger arguments.
       - Fallback: If `case_details` is omitted, queries Chatwoot API (`GET /conversations/{id}/messages`) for recent incoming client messages.
       - Generates structured, rich payloads:
         1. **Chatwoot Private Note** (Markdown): Includes Motivo, Contacto, Teléfono, Email, Canal/Inbox, Conversación ID, and complete **INFORMACIÓN RECOPILADA DEL CASO**.
         2. **Telegram Admin Alert** (HTML, escaped): Dispatched to chatId `40371837`.
         3. **WhatsApp Evolution API Alert** (WhatsApp Markdown): Dispatched to instance `TTvAlertsMovistar` (`584146130135`).
* **Nodes & Files Synchronized**:
  * `prompts/agent_prompt.md`: Updated with mandatory tool parameters (`reason` and `case_details`).
  * `prompts/tvtotal24_prompt.md`: Updated with mandatory tool parameters (`reason` y `case_details`).
  * n8n Workflow `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY`):
    - Node `AI Agent`: `options.systemMessage` updated.
    - Node `AI Agent - TVTotal24`: `options.systemMessage` updated.
    - Node `Call 'transfer_to_human_tool'`: `description` and `workflowInputs` updated with `reason` and `case_details` mapped via `$fromAI`.
    - Nodes `Preparar Mensaje`, `Evaluar Cliente Mega`, `Evaluar DnSpace (Fallback)`, `Evaluar Cliente DnSpace`, and `Evaluar Mega (Fallback)`: `clientContextPrefix` updated with triage instructions.
    - Live version published: `8d839f25-eaae-490c-b9a3-e0df14c0a1a4`.
  * n8n Workflow `Transfer to Human Tool` (`xam0WV65gvTbXcIx`):
    - Node `Preparar Datos Transferencia`: extracts `reason` and `case_details`.
    - Node `Agregar etiqueta human`: builds `private_note_content`, `telegram_text`, and `whatsapp_text` with collected case info.
    - Node `Nota privada Chatwoot`: sends structured private note.
    - Node `Notificar Administrador`: sends HTML Telegram alert.
    - Node `Notificar WhatsApp (Evolution API)`: sends WhatsApp alert.
    - Node `Respuesta Tool Transferencia`: returns success payload with reason and confirmation.
    - Live version published: `feaf5cdc-3bf4-47b3-b9d3-851d0a0568f5`.
  * Exported and verified: `workflows/router_chatwoot_ia.json` and `workflows/tool_transfer_to_human.json`.

---

## 19. Automated Credentials Recovery for TVTotal24 / MVPlay (`obtener_credenciales_tvtotal24`)

* **Objective & Context**:
  * Allow the AI agent for TVTotal24 / Latina (`Tivi`) to autonomously retrieve and deliver active service credentials (username, password, and DNS URLs) when an existing customer (`stage-leads-ganados`) requests their forgotten credentials or access details.
  * Mega OTT / TotalTv USA credential recovery was deferred for a later phase as per explicit user instruction.
* **API Research & Findings**:
  * **MVPlay Panel API** (`http://1395.cooteg.ch:2095/pooqkDEG/reseller/index.php`):
    * Endpoint `action=get_lines&search={term}` performs search across both `reseller_notes` (customer full name) and `username`.
    * Tested with live accounts (`Lázaro Figueredo` id 213418, `Carlos Abreu` id 41663, `Andres Tablante` id 97231) confirming exact and partial token matching.
  * **Mega OTT API** (`https://megaiptv.biz:8000/api/v1`):
    * `GET /subscriptions` returns 405 Method Not Allowed; endpoint requires exact numeric subscription ID (`GET /subscriptions/{id}`), making direct name/username searches impossible without pre-indexed mapping.
* **Strict Business Constraints**:
  * **Zero "Most Apps" Wording**: Under NO circumstance will the AI or tool mention the phrase "most apps". The connection URLs are strictly labeled as:
    * 🌐 **Servidor / DNS:** `http://wk.mvpl.uk:2082`
    * 📺 **DNS para Smarters:** `http://cdn01link.uk:2095`
  * **Restricted to Existing Clients**: Credential recovery is strictly enabled for customers with label `stage-leads-ganados`. If credentials cannot be found automatically or if the user is not verified, the agent transfers to a human agent with reason `Recuperación de Credenciales`.
* **Subworkflow `Tool - Obtener Credenciales MVPlay` (`gyTc5A6r5TNRgJCs`)**:
  * **Nodes**:
    1. `Execute Workflow Trigger`: Inputs `contact_name` (from AI), `conversation_id`, and `account_id` (from Chatwoot context).
    2. `Preparar Busqueda`: Sanitizes search term (lowercased, accents removed).
    3. `Consultar MVPlay`: HTTP GET to MVPlay API `action=get_lines&search={term}`.
    4. `Procesar Credenciales MVPlay`: Robust token-matching scoring algorithm matching tokens in `reseller_notes` (requiring `tokenMatches > 0` before awarding active/non-trial bonuses). Also posts a Chatwoot private audit note if `conversation_id` is supplied.
    5. `Respuesta Tool`: Returns JSON payload:
       - If found: `{ status: 'found', username, password, dns: 'http://wk.mvpl.uk:2082', dns_smarters: 'http://cdn01link.uk:2095', cliente: reseller_notes, instructions_for_ai: "..." }`.
       - If not found: `{ status: 'not_found', message: "...", instructions_for_ai: "..." }`.
  * Active version: `8a4e7255-f939-458f-a473-223130b2af36`.
* **Integration into `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY`)**:
  * Added tool node `obtener_credenciales_tvtotal24` (`@n8n/n8n-nodes-langchain.toolWorkflow`, version 2.2) at canvas position `[1360, 616]`.
  * Connected to `AI Agent - TVTotal24` as `ai_tool`.
  * Updated system prompt in `prompts/tvtotal24_prompt.md` and node `AI Agent - TVTotal24`:
    - Protocol for asking/verifying full name for clients with `stage-leads-ganados`.
    - Execution of `obtener_credenciales_tvtotal24`.
    - Delivery template with strict prohibition of "most apps".
    - Fallback escalation to `Call 'transfer_to_human_tool'` if not found or unverified.
  * Active version: `5c746f0a-a4e3-47e1-b0dc-c173ddee19b0`.
* **Export & Synchronization**:
  * Added `tool_get_mvplay_credentials: 'gyTc5A6r5TNRgJCs'` to `workflows/export_workflows.py`.
  * Exported `workflows/tool_get_mvplay_credentials.json` and updated `workflows/router_chatwoot_ia.json`.

---

## 20. Mandatory Customer Notification on Human Transfer Across All Scenarios

* **Requirement & Context**:
  * In all circumstances where a conversation is transferred to a human agent, regardless of the reason (explicit customer request, completion of technical triage, completion of administrative/billing triage, manual credential recovery, or unhandled inquiries), the customer **MUST ALWAYS BE EXPLICITLY INFORMED** that the transfer has been completed.
* **Root Causes & Gaps Addressed**:
  * **Hallucinated Transfer Errors**: In certain cases (e.g. Conv #1376), LLM agents executed `Call 'transfer_to_human_tool'` successfully, but hallucinated that a "momentary technical issue" occurred and stated they would "retry transferring later", confusing the customer even though the conversation was already labeled `human`, logged in private notes, and alerted to admins.
  * **Soft / Omitted Notification**: In administrative or technical triage flows, prompts previously directed agents to "confirm that billing will verify" or "confirm that technical team will review", causing LLMs to reply with generic statements like "gracias, revisaremos tu comprobante" without explicitly stating that the conversation was officially handed off to a human support agent.
* **Multi-Layer Architecture Implementation**:
  1. **System Prompts (`prompts/agent_prompt.md` and `prompts/tvtotal24_prompt.md`)**:
     * Integrated absolute top-level mandate:
       - **REGLA OBLIGATORIA E IMPERATIVA — INFORMAR AL CLIENTE SOBRE LA TRANSFERENCIA A HUMANO**: In all transfers for ANY reason, the final response MUST explicitly confirm that the transfer to human support has been completed.
       - Strictly prohibited: silent transfers, finishing without notifying, and apologizing for non-existent transfer errors.
     * Reinforced across all individual scenario instructions (Direct Request, Technical Triage, Billing Triage, Credential Recovery).
  2. **Subworkflow `Transfer to Human Tool` (`xam0WV65gvTbXcIx`)**:
     * Node `Respuesta Tool Transferencia`: Updated `instructions_for_ai` to enforce a mandatory, ineludible directive for the agent to confirm the transfer explicitly in the final customer message.
     * Active version published: `5dd39738-c2ca-462c-a3ce-59646deb8b6b`.
  3. **Main Router Workflow `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY`)**:
     * Node `Call 'transfer_to_human_tool'`: Updated description to explicitly include the mandatory customer notification requirement.
     * Node `Formatear Respuesta` (Fail-Safe Code Node):
       - Added regex detection to sanitize and replace any hallucinated error excuses (e.g. "inconveniente técnico momentáneo", "no se pudo transferir", "error al transferir") with the correct, polite transfer confirmation.
       - Added execution check for `Call 'transfer_to_human_tool'`: if the tool ran in the execution but the output text omitted transfer keywords (`transferid*`, `transferencia`, `soporte humano`, `asesor`, `human support`), automatically appends the explicit confirmation message in the customer's language.
     * Active version published: `89827e56-09b9-4e43-a771-2cb6dc2f6703`.
  4. **Export & Persistence**:
     * Workflows synchronized and exported to `workflows/router_chatwoot_ia.json` and `workflows/tool_transfer_to_human.json`.

---

## 21. MegaOTT API & Reseller Panel Synchronization Architecture Investigation

* **Objective & User Requirements**:
  * Implement an automated synchronization process to fetch the complete subscription catalog from MegaOTT (`action=user&sub=list`) and write it into a new tab named **`MegaData`** within Google Sheets document **`Clientes TotalTv`** (`1SNRbfgomUgtac58UmIMlH8UzizBXrTDVogxJEt-z9A0`).
  * Process 100% of delivered properties without omissions, dynamically constructing column headers from the union of all detected keys.
  * Maintain tabular cell integrity by serializing nested objects and arrays into plain-text JSON.
  * Print console summary reporting total records processed, total columns generated, and confirmation of dump into `MegaData`.

* **Infrastructure Audit & Technical Discoveries**:
  1. **MegaOTT REST API (`https://megaott.net/api/v1`)**:
     * **Authentication**: Laravel Sanctum Bearer Token `1655|Uk2GI2EUH0v8NIcUFjGwLeKLlp14bVmEi2rcGSuJ48ec8236`.
     * **User Verification**: `GET /api/v1/user` responds `200 OK` with user `TotalTvUSA` (`id: 52298`, `credit: 4.48`).
     * **Single Subscription Retrieval**: `GET /api/v1/subscriptions/{id}` responds `200 OK` with full object schema containing 16 properties (`type`, `id`, `username`, `password`, `mac_address`, `package`, `template`, `max_connections`, `forced_country`, `adult`, `note`, `whatsapp_telegram`, `paid`, `expiring_at`, `dns_link`, `dns_link_for_samsung_lg`, `portal_link`).
     * **Bulk Listing Restriction**: `GET /api/v1/subscriptions` returns `405 Method Not Allowed` with `allow: POST` (the REST endpoint only supports subscription creation). Official documentation at `https://megaott.net/docs/subscriptions` confirms no bulk listing route is exposed on `/api/v1/subscriptions`.
  2. **Xtream UI / ZapX Panel API (`panel_api.php?action=user&sub=list`)**:
     * Parameter `action=user&sub=list` belongs to the standard Xtream UI reseller panel specification.
     * Host `http://xvgtfqif.sljur.com/panel_api.php` was confirmed operational with custom User-Agent, returning `{"user_info":{"auth":0}}` when missing reseller web password.
     * The environment holds the API Bearer Token for `megaott.net`, but not the plain-text web panel password for user `TotalTvUSA`.
  3. **Implementation & Successful Execution**:
     * Built and deployed n8n workflow **`Sync Mega to MegaData`** (`Lcyro95g4yg39bdD`):
       - Trigger: Manual Trigger + Webhook Trigger (`POST https://n8n.ac4.club/webhook/sync-mega-megadata`).
       - Step 1: Reads all records from tab `"Mega"` in Google Sheets `Clientes TotalTv` (`1SNRbfgomUgtac58UmIMlH8UzizBXrTDVogxJEt-z9A0`) using credential `Pw5wN2L5UopOruaj`.
       - Step 2: Extracts identifiers and iteratively enriches records via MegaOTT REST API (`GET https://megaott.net/api/v1/subscriptions/{id}`) using Bearer Token `1655|Uk2GI2EUH0v8NIcUFjGwLeKLlp14bVmEi2rcGSuJ48ec8236`.
       - Step 3: Dynamically accumulates 100% of keys into unique column headers and serializes complex data structures.
       - Step 4: Ensures tab **`MegaData`** exists in Google Sheets via `batchUpdate` (`addSheet`), with non-blocking error handling.
       - Step 5: Dumps 100% of tabular records into `MegaData!A1` via Google Sheets REST API (`PUT /values/MegaData!A1?valueInputOption=USER_ENTERED`).
       - Step 6: Emits structured sync summary.
     * **Live Production Run**:
       - Workflow published with `activeVersionId: 2cd416ab-c67e-40fc-89df-2b5bb3dab5b4`.
       - Webhook triggered and execution `6382` completed with `status: success`.
       - Tab **`MegaData`** created and fully populated in Google Sheet `Clientes TotalTv`.

* **Limitación Crítica de Arquitectura y Decisión Pendiente (MegaOTT)**:
  > [!IMPORTANT]
  > **TOMA DE NOTA ARQUITECTÓNICA**:
  > **AL NO CONTAR CON EL ID DE SUSCRIPCION, NO PODEMOS CONSULTAR CLIENTES EN MEGA.OTT. DEBEMOS DETERMINAR CÓMO EXTENDER SUSCRIPCIONES SI NO TENEMOS ESE DATO.**
  * **Detalle Técnico del Bloqueo**:
    1. **Ausencia de ID en Google Sheets**: La hoja *"Mega"* en el archivo de Google Sheets `Clientes TotalTv` (`1SNRbfgomUgtac58UmIMlH8UzizBXrTDVogxJEt-z9A0`) contiene columnas como `Usuario`, `Nombre`, `Apellido`, `Vence`, `Email`, `Teléfono`, pero **NO contiene el ID numérico de suscripción (`subscription_id`)** de MegaOTT.
    2. **Limitación de la API de MegaOTT**: La API REST de MegaOTT (`https://megaott.net/api/v1`) **no permite búsquedas por nombre de usuario, teléfono ni correo electrónico**. Todos sus endpoints operativos (`GET /api/v1/subscriptions/{id}` y `POST /api/v1/subscriptions/{id}/extend`) exigen estrictamente el ID numérico entero de la suscripción.
    3. **Impacto Operativo**: Sin el ID de suscripción numérico, no es posible consultar datos enriquecidos ni ejecutar renovaciones o extensiones automáticas de cuentas vía API en MegaOTT de forma directa.
    4. **Política del Workflow de Sincronización (`Sync Mega to MegaData` - `Lcyro95g4yg39bdD`)**:
       - Dispone de un `Manual Trigger` y un `Webhook Trigger` (`POST https://n8n.ac4.club/webhook/sync-mega-megadata`).
       - No posee un cron recurrente para evitar ejecuciones innecesarias; se activa únicamente bajo demanda o invocación programática cuando se requiere sincronizar o poblar la hoja `MegaData`.
    5. **Próximo Paso Arquitectónico**:
       - Evaluar métodos alternativos para obtener el mapeo inicial de `Usuario` $\leftrightarrow$ `subscription_id` (por ejemplo, exportación masiva CSV desde el panel web de revendedor o scraping autenticado) o definir el mecanismo operativo para renovar/extender suscripciones cuando solo se disponga del nombre de usuario.

---

## 22. Multimodal Vision Pipeline: Automated Payment Receipt & App Screenshot Error Diagnosis

* **Objective & Operational Architecture**:
  * Implemented an automated vision analysis and verification pipeline within the inbound gateway workflow `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY`).
  * When a customer sends an image attachment in Chatwoot (screenshots, transfer receipts, checkout confirmations, app error screens), the workflow downloads the image blob, converts it to base64, and calls **Claude 3.5 Sonnet Vision** (`POST https://api.anthropic.com/v1/messages` using credential `ZbUWSAq6JlKInA64`).
* **Structured Vision JSON Extraction & Supported Image Types**:
  * The vision model returns a strict JSON object categorizing the image:
    1. **Payment Receipts (`is_payment_receipt: true`)**:
       - `payment_method` (`pago_movil`, `zelle`, `pd_cash`, `cashapp`, `nowpayments`, `card_payment`, `binance`, `stripe`, `paypal`, `other`, `none`)
       - `amount`, `currency` (`VES`, `USD`, `EUR`, `USDT`, `BTC`, `OTHER`), `date_time`, `bank_origin`, `reference_number`, `destination_phone`, `destination_rif`, `destination_email`
    2. **App Screenshots & Technical Error Screens (`is_payment_receipt: false`, `is_app_screenshot_or_error: true`)**:
       - `app_name`: App identified (e.g., IPTV Smarters Pro, Smarters Player Lite, XCIPTV, Tivimate, Downloader, IBO Player, SS IPTV, Web browser, etc.).
       - `device_type`: Device identified (e.g., Smart TV, Firestick, iPhone, Android, PC, Mac, etc.).
       - `screen_type`: Screen type (e.g., Login screen, Error modal, Playlist setup, Playback error, Channel list, etc.).
       - `detected_error`: Exact error text/code read from screen (e.g., "Invalid Details", "Check Network", "Playlist Expired", "Code 500", "None").
       - `app_diagnosis_summary`: Technical diagnosis of what is shown on screen and recommended solution.
* **Automated Verification Rules**:
  1. **Pago Móvil (Bolívares / VES / Bs)**:
     - Phone verification: Must match **`04246861135`** (or `4246861135`).
     - RIF verification: Must match **`J405259221`** or **`405259221`** (ArialStore C.A. / Bancamiga).
     - Result: Marked as `VERIFIED_CORRECT` if phone/RIF match; otherwise tagged as `DISCREPANCY_DETECTED`.
  2. **Zelle**:
     - TVTotal24 Latina (Inboxes 10, 13, 15, 16, 19): Must match **`pagos@totaltvlatina.com`**.
     - TotalTv USA (Inboxes 4, 6, 14, 17, 18): Must match **`acalimanr@gmail.com`**.
     - Result: Marked as `VERIFIED_CORRECT` if matching official email; otherwise tagged as `DISCREPANCY_DETECTED`.
  3. **Payment Gateways & Third Parties (pd.cash, Cash App, NOWPayments, Card Payments, Binance Pay, Stripe, PayPal)**:
     - Classified as `is_payment_receipt: true` and processed with extracted transaction/order parameters passed to human support.
* **Context Injection & Agent Action**:
  * Formats a structured context block injected into the prompt for **Toto** (TotalTv USA) and **Tivi** (TVTotal24):
    - **Payment Receipts**: `[PAYMENT RECEIPT DETECTED IN ATTACHMENT: ...]` -> AI thanks customer, passes details to `transfer_to_human_tool`, and confirms transfer.
    - **App Screenshots & Technical Errors**: `[TECHNICAL SCREENSHOT DIAGNOSIS IN ATTACHMENT: ...]` -> AI acknowledges the app and error observed, provides targeted troubleshooting steps, and if human escalation is needed, passes App Name, Device, and Error in `reason` and `case_details` for `transfer_to_human_tool` so internal notes and admin alerts receive full technical diagnostic context.
* **Production Deployment**:
  * Deployed and published in `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY` / activeVersionId `9c478d8b-53d1-4428-8966-7a4b0bfcecca`).
  * System prompts updated in `prompts/agent_prompt.md` and `prompts/tvtotal24_prompt.md`.
  * Local definitions exported and verified via `python3 workflows/export_workflows.py`.

---

## 23. Fix: Double AI Responses per Customer Message (Duplicate Branching Removal)

* **Problem Statement**:
  * AI agents for both TotalTv USA (`Toto`) and TVTotal24 (`Tivi`) were responding twice to every incoming customer message across multiple inboxes (e.g. Inboxes 16, 17, 18).
  * The two responses were not identical copies; rather, the AI generated two distinct messages in rapid succession (2 to 5 seconds apart) for a single customer incoming message.
* **Root Cause**:
  * In workflow `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY`), when the multimodal Vision pipeline was added, node `Preparar Mensaje` was inadvertently left connected to **BOTH** `¿Requiere Buscar en Sheet?` **AND** `¿Tiene Imagen Adjunta?` at the same time.
  * Node `¿Tiene Imagen Adjunta?` also routes downstream to `¿Requiere Buscar en Sheet?` (both on the "Sin Imagen" fallback and after vision analysis on "Con Imagen").
  * Consequently, every single incoming webhook triggered two parallel downstream branches simultaneously:
    - **Branch 1**: `Preparar Mensaje` $\to$ `¿Requiere Buscar en Sheet?` $\to$ `¿Qué Empresa?` $\to$ `AI Agent` $\to$ `Responder en Chatwoot` (Response #1).
    - **Branch 2**: `Preparar Mensaje` $\to$ `¿Tiene Imagen Adjunta?` $\to$ `¿Requiere Buscar en Sheet?` $\to$ `¿Qué Empresa?` $\to$ `AI Agent` $\to$ `Responder en Chatwoot` (Response #2).
* **Remediation & Architecture Fix**:
  * Removed the direct redundant connection from `Preparar Mensaje` to `¿Requiere Buscar en Sheet?`.
  * The pipeline is now strictly sequential and single-branch:
    - `Preparar Mensaje` $\to$ `¿Tiene Imagen Adjunta?`
      - **Con Imagen**: `Analizar Imagen (Visión Anthropic)` $\to$ `Procesar Resultado Visión` $\to$ `¿Requiere Buscar en Sheet?`
      - **Sin Imagen**: `¿Requiere Buscar en Sheet?`
    - Downstream: `¿Requiere Buscar en Sheet?` $\to$ `¿Qué Empresa?` $\to$ `AI Agent` (single invocation) $\to$ `Formatear Respuesta` $\to$ `Wait Typing Delay` $\to$ `Responder en Chatwoot` (single delivery).
* **Production Deployment**:
  * Applied `removeConnection` to n8n workflow `n0zgnS1vlOGNcGNY` and published active version `a38ef866-0951-4844-b5d9-35ba0a6cbb94`.
  * Exported and verified via `workflows/router_chatwoot_ia.json`.

---

## 24. Duplicate Transfer Alert Suppression, Phone Call Prohibition Mandate, & MegaOTT Trial Template Enforcement

* **Objective & Problem Statements**:
  1. **Telegram Transfer Notification Duplication**: When customers were transferred to human support, administrators received duplicate Telegram/WhatsApp alerts up to 4-5 times per conversation if consecutive messages arrived or if `transfer_to_human_tool` was re-invoked.
  2. **Phone Call Prohibition Mandate**: AI Agents (Toto and Tivi) were strictly prohibited from ever mentioning, suggesting, offering, or promising phone calls (received or emitted). The service is 100% text-chat-only.
  3. **MegaOTT Trial Template Requirement**: 24-hour trials created on the MegaOTT platform must always be generated using the template named "English" (`template_id: 2218`).

* **Remediation & Technical Implementation**:
  1. **Duplicate Telegram & WhatsApp Alert Suppression (`tool_transfer_to_human` - `xam0WV65gvTbXcIx`)**:
     * Modified node `Agregar etiqueta human` to check if `labels` array already contained `'human'` before appending, returning boolean flag `already_had_human`.
     * Added `n8n-nodes-base.if` node **`¿Primera Transferencia?`**:
       - **First Transfer (`already_had_human == false`)**: Routes to `Notificar Administrador` (Telegram HTML push) and `Notificar WhatsApp (Evolution API)`, creates private note in Chatwoot, and returns success response to AI Agent.
       - **Subsequent Transfer (`already_had_human == true`)**: Skips Telegram and WhatsApp external notifications to prevent spamming admin channels, while adding internal private notes to Chatwoot and returning standard success status to AI Agent.
     * Deployed and published active production version `c9bbf2ff-f6d8-4c9b-8d39-a5317e2c1a3b`.

  2. **Strict Prohibition on Phone Calls (100% Text-Chat-Only)**:
     * Updated `prompts/agent_prompt.md` (TotalTv USA - Toto) and `prompts/tvtotal24_prompt.md` (TVTotal24 Latina - Tivi) with `STRICT PROHIBITION ON PHONE CALLS (100% TEXT CHAT ONLY)` section.
     * Strict rules enforced: Neither incoming calls from customers nor outgoing calls from support may be mentioned, offered, or suggested under any circumstance. Support is provided exclusively via text chat in the active conversation channel.
     * Injected updated prompts into node parameters for `AI Agent` and `AI Agent - TVTotal24` in `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY`), and updated backup files `agent_totaltv_usa.json` and `agent_tvtotal24_latina.json`.
     * Deployed and published active production version `d53d98e8-59e6-4394-86e5-efe1135f360e`.

  3. **MegaOTT Trial Template Enforcement (`tool_create_mega_ott_trial` - `e1R7zQorWBaaqgou`)**:
     * Verified MegaOTT REST API parameter for reseller template is `template_id` and the numeric ID for template "English" / "English-EU" is **`2218`**.
     * Updated HTTP Request nodes `Crear Linea - Teléfono`, `Crear Linea - Email`, and `Crear Linea - Auto` to pass `template_id: 2218` in form-urlencoded body parameters.
     * Deployed and published active production version `6f2d6d98-8e8c-464d-b32c-148c5b284b64`.

* **Production Sync & Git Integration**:
  * Executed `python3 workflows/export_workflows.py` to synchronize all production workflows into local git repository.
  * Committed and pushed all prompt and workflow updates to git `main`.

---

## 25. "TotalTv Support" Google Doc Ingestion Pipeline & Dynamic Feedback Loop

* **Objective & Architectural Overview**:
  * Integrated a live dynamic knowledge base and automated feedback loop connecting Google Doc **"TotalTv Support"** (`totaltvusa@gmail.com`) to the AI Agents for **TotalTv USA** (`Toto`) and **TVTotal24** (`Tivi`).
  * Allows administrators to add, update, or remove technical and administrative troubleshooting situations in real time without modifying workflow code.
  * Enables dynamic date/time evaluation (e.g. *"si el cliente no accede desde antes del 15 de septiembre de 2026..."*) and brand-scoped filtering (`[TotalTv USA]`, `[TVTotal24]`, `[General]`).
  * Automatically logs unhandled/unresolved customer queries to section `# CONSULTAS PENDIENTES / SIN RESPUESTA` in the Google Doc when transferred to human support.

* **Pipeline Components & Node Architecture**:
  1. **Dynamic Ingestion Node (`Procesar Soporte TotalTv` in `n0zgnS1vlOGNcGNY`)**:
     * Node type: `n8n-nodes-base.code` (version 2), positioned right before `¿Qué Empresa?`.
     * Configured with Document ID variable (`TOTALTV_SUPPORT_DOC_ID`).
     * Calls Google Docs API (`GET https://docs.googleapis.com/v1/documents/{TOTALTV_SUPPORT_DOC_ID}`) via credential `googleSheetsOAuth2Api` (`Pw5wN2L5UopOruaj`).
     * Parses sections `# TÉCNICA` and `# ADMINISTRATIVA`, filters rules based on brand tags, evaluates date conditions against current date ($now), and injects `[DOCUMENTO DE SOPORTE TOTALTV SUPPORT (BASE DE CONOCIMIENTO VIVA...)]` into the AI context block.
     * Degrades gracefully if the doc ID is not yet provided or doc is inaccessible.
     * Production active version published: `ca2234df-24e4-43a4-9b71-115152cf4e5c`.

  2. **Automated Unresolved Query Logger (`Registrar Consulta Pendiente Google Doc` in `xam0WV65gvTbXcIx`)**:
     * Node type: `n8n-nodes-base.code` (version 2), connected to `¿Primera Transferencia?` (output 0).
     * When a conversation is transferred to human support for the first time (`already_had_human == false`), extracts timestamp, brand, conversation ID, transfer reason, and case details.
     * Calls Google Docs API (`POST https://docs.googleapis.com/v1/documents/{TOTALTV_SUPPORT_DOC_ID}:batchUpdate`) with `insertText` request targeting the end of the document to append:
       `- [YYYY-MM-DD HH:MM] [Brand] [Conv #ID] Motivo: {reason} | Detalles: {case_details}`
     * Production active version published: `96f3e5a6-d759-479f-b799-d53f16d20099`.

* **Production Sync & Git Integration**:
  * Workflows exported via `python3 workflows/export_workflows.py`.
  * Committed and pushed to git `main` (`13a1238`).

---

## 26. Google Doc ID Binding & Sept 2026 Support Cases Extraction

* **Objective & Implementation**:
  * Linked exact Google Doc ID `14VkDzxSnwQHZ6ezEZskeQ3lfLIXw5S0n2onK3I6yYdE` (Document **"TotalTv Support"** owned by `totaltvusa@gmail.com`) as default hardcoded fallback in nodes `Procesar Soporte TotalTv` (`router_chatwoot_ia.json` / workflow `n0zgnS1vlOGNcGNY`) and `Registrar Consulta Pendiente Google Doc` (`tool_transfer_to_human.json` / workflow `xam0WV65gvTbXcIx`).
  * Analyzed all 92 Chatwoot conversations from September 1st–15th, 2026 across both TotalTv USA and TVTotal24 brands, extracting 7 recurring technical and administrative support situations with tested solutions to populate the Google Doc sections.

* **Production Deployment & Synchronization**:
  * Published updated n8n workflows:
    - `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY` / active version `b8fdbbc7-a1c2-4bda-b7bc-10cc86d02d65`)
    - `Transfer to Human Tool` (`xam0WV65gvTbXcIx` / active version `c9b29f94-d41c-4092-b3af-33d20a54afd0`)
  * Exported workflows and committed to git `main` (`418acd6`).

---

## 27. 5-Second Rolling Debounce Pipeline, Multi-Message Aggregation & IPTV Smarters Support Rule Priority

* **Objective & Problem Statements**:
  1. **Dynamic Rolling Debounce (5-Second Wait & Timer Reset)**: Customers typing multiple consecutive lines or sending messages in rapid succession triggered multiple parallel n8n executions, causing double/multiple AI responses.
  2. **IPTV Smarters Support Rule Enforcement**: In conversation #1392, when a customer reported IPTV Smarters login/playlist failure, the AI gave generic diagnostic replies instead of enforcing the explicit Google Doc rule requiring them to recreate the user profile with alternative URLs (`http://smrts.wxn.ch:2095`, `http://cdn01link.uk:2095`, `http://node01hub.uk:2082`).
  3. **Multimodal Attachment Extraction**: Image attachments sent without text were sometimes missed if Chatwoot ActiveStorage links or nested webhook attachments were not fully parsed.

* **Remediation & Technical Implementation**:
  1. **5-Second Rolling Debounce Node (`Espera 5s`)**:
     - Added node `Espera 5s` (`n8n-nodes-base.wait`, 5 seconds) right after `¿Es mensaje entrante?`.
     - In `Preparar Mensaje`, added rolling debounce check: fetches `GET /conversations/{id}/messages` from Chatwoot API. If `Date.now() - lastIncomingTimestamp < 4500` ms, the execution yields (`skip_ai_response: true`) to the newer execution currently waiting its 5 seconds.
     - Concatenates all unhandled customer messages sent in the latest burst into a single unified prompt.
     - Collects all image attachments from all messages in the burst, ensuring zero image attachments are missed.
  2. **Support Knowledge Base Parser & Prompt Priority Overrides**:
     - Updated `Procesar Soporte TotalTv` to parse all lines in `# TÉCNICA` and `# ADMINISTRATIVA` (regardless of hyphen/bullet formatting) and flexibly match brand tags (`[tvtotal24]`, `(tvtotal24:)`, `tvtotal24:`, etc.).
     - Injected mandatory override rules into `agent_prompt.md`, `tvtotal24_prompt.md`, `AI Agent`, and `AI Agent - TVTotal24`: TotalTv Support Document rules take 100% top priority. For IPTV Smarters login/playlist failures on TVTotal24, agents MUST instruct customers to recreate the user profile with the alternative URLs (`http://smrts.wxn.ch:2095`, `http://cdn01link.uk:2095`, `http://node01hub.uk:2082`).

* **Production Deployment & Git Integration**:
  * Published active production workflow `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY` / active version `2ab94c6b-3932-4969-8415-7cf85ddaafd5`).
  * Exported workflows via `python3 workflows/export_workflows.py`.
  * Committed and pushed all updates to git `main`.

---

## 28. Intent-Driven Greeting & Context Continuation Rules

* **Objective & Problem Statement**:
  - When a customer sent a message containing plan durations or payment intent (e.g. `"one month"`, `"1 mes"`, `"3 meses"`, `"One year"`, `"pagar"`, `"cashapp"`, `"zelle"`, `"dime el monto"`), the AI agents (Toto and Tivi) were previously outputting generic greetings (e.g. *"Hello! I'm Toto, AI Agent for Total TV. How can I help you today?"*) without addressing the customer's specific input in that turn.

* **Remediation & Mandate Enforced**:
  - Added **GREETING, CONTEXT CONTINUATION & INTENT DRIVEN RESPONSES** rules across all prompts (`agent_prompt.md`, `tvtotal24_prompt.md`, `AI Agent`, and `AI Agent - TVTotal24`).
  - Mandatory rule: AI agents MAY greet briefly, BUT MUST IMMEDIATELY ADDRESS AND CONTINUE WITH THE CUSTOMER'S TOPIC IN THE VERY SAME RESPONSE:
    - **Plan duration keywords (`"one month"`, `"1 mes"`, `"3 meses"`, `"1 year"`)**: Brief greeting + present exact pricing breakdown for that duration across 1, 2, and 3 devices + present payment options (Zelle, Crypto with 20% discount, CashApp, Card2Crypto/PayPal, Pago Móvil) + ask how many devices or preferred payment method.
    - **Payment intent keywords (`"pagar"`, `"cashapp"`, `"zelle"`, `"dime el monto"`, `"quiero comprar"`)**: Brief greeting + assume immediate purchase intent + present pricing/payment details + ask for plan duration and devices.

* **Production Deployment & Synchronization**:
  - Published active version in n8n `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY` / active version `ca5e6ff9-6a75-4761-ab61-11ac053da88d`).
  - Exported workflows via `python3 workflows/export_workflows.py`.
  - Committed and pushed to git `main`.

---

## 29. Brand-Scoped Support Separation & TVTotal24 Smarters URL Fix

* **Objective & Problem Statement**:
  - The TotalTv USA AI agent (`Toto`) was delivering TVTotal24-specific IPTV Smarters troubleshooting instructions (including TVTotal24 server URLs `http://smrts.wxn.ch:2095`, `http://cdn01link.uk:2095`, `http://node01hub.uk:2082`) to TotalTv USA customers (inboxes tagged `funnel-totaltv-usa`).
  - **Root Cause**:
    1. `prompts/agent_prompt.md` contained a hardcoded section `TOTALTV SUPPORT DOCUMENT OVERRIDE & SMARTERS APP LOGIC` that explicitly listed the TVTotal24 Smarters URLs.
    2. Node `Procesar Soporte TotalTv` in workflow `n0zgnS1vlOGNcGNY` included a hardcoded example referencing TVTotal24 Smarters URLs in instruction #1 of `supportContextBlock`, which was injected universally across all brand executions.

* **Remediation & Technical Implementation**:
  1. **Prompt Sanitization (`prompts/agent_prompt.md`)**:
     - Removed the brand-specific Smarters URL instructions from `agent_prompt.md`.
     - Replaced with a brand-neutral `TOTALTV SUPPORT DOCUMENT OVERRIDE` section requiring `Toto` to prioritize rules from the live Google Doc dynamically without hardcoded external brand URLs.
     - Kept TVTotal24 Smarters URL rules exclusively in `prompts/tvtotal24_prompt.md` and `AI Agent - TVTotal24` system prompt.
  2. **Workflow Node De-Coupling (`Procesar Soporte TotalTv`)**:
     - Updated instruction #1 in `supportContextBlock` to be brand-neutral: *"1. Si la situación reportada por el cliente coincide con alguna de las instrucciones anteriores, APLICA DIRECTAMENTE LA SOLUCIÓN INDICADA EN EL DOCUMENTO para ayudar al cliente sin preguntas adicionales innecesarias."*
  3. **Workflow Backups & n8n Sync**:
     - Updated node parameters for `AI Agent` in `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY`).
     - Synchronized backup file `workflows/agent_totaltv_usa.json`.

* **Production Deployment & Git Integration**:
  - Published active production version `edbdfe86-e861-4975-b300-a5891399d713`.
  - Workflows exported and synced to local git repository.

---

## 30. Absolute Brand Segregation: Device Policy Partition & Cross-Brand Contamination Elimination

* **Objective & Problem Statement**:
  - Customers in TVTotal24 (Latina) inboxes were being asked how many devices they needed (e.g. 1, 2 or 3 devices) and given multi-device pricing tiers upon greeting or inquiring about plans and payments.
  - Furthermore, cross-brand contamination risks existed where one brand's payment methods (e.g., CashApp in TVTotal24 or Binance Pay ID in TotalTv USA) could leak into customer responses.

* **Root Cause**:
  - When intent-driven greetings and continuation rules were implemented in Section 28, the template from `agent_prompt.md` (TotalTv USA) was inadvertently copied into Section 2.1 of `prompts/tvtotal24_prompt.md`, which instructed the agent to:
    1. *"Presentar los precios de esa duración específica para 1, 2 y 3 dispositivos."*
    2. *"Preguntar cuántos dispositivos necesita o qué medio de pago prefiere."*
    3. Included `"cashapp"` in intent keywords.
  - In TVTotal24, accounts operate on single-account fixed duration pricing (1 Mes $8, 3 Meses $24, etc.) without any multi-device tiers. Device tiers belong exclusively to TotalTv USA (Mega OTT).

* **Remediation & Strict Brand Partitioning**:
  1. **TVTotal24 Latina (`prompts/tvtotal24_prompt.md`, `agent_tvtotal24_latina.json`, `AI Agent - TVTotal24`)**:
     - Added strict top-level mandate:
       `⛔ MANDATO ESTRICTO — NUNCA PREGUNTAR NÚMERO DE DISPOSITIVOS:`
       - Fixed pricing per duration ONLY (1 Mes: 8$, 3 Meses: 24$, 6 Meses: 48$, 12 Meses: 84$; Binance discounts: 5$, 14$, 50$).
       - Strictly forbidden from asking how many devices the customer needs, offering device tiers, or conditioning plans to device counts.
       - Removed all occurrences of `"cashapp"` from intent triggers.
       - Strictly limited to official TVTotal24 payment methods: Zelle (`pagos@totaltvlatina.com`), Binance Pay USDT (ID `22628239`), and Pago Móvil (Bancamiga).
  2. **TotalTv USA (`prompts/agent_prompt.md`, `agent_totaltv_usa.json`, `AI Agent`)**:
     - Added strict top-level mandate:
       `⛔ STRICT MANDATE — NO TVTOTAL24 METHODS, CURRENCY OR SERVERS:`
       - Strictly forbidden from mentioning Pago Móvil, Bolívares (Bs), Binance Pay ID 22628239, or Venezuelan payment methods.
       - Strictly forbidden from providing TVTotal24 server URLs (`smrts.wxn.ch`, `cdn01link.uk`, `node01hub.uk`, `wk.mvpl.uk`). TotalTv USA DNS is exclusively `http://hbptsjrw.sljur.com` (Smarters: `http://hbptsjrw.smrtchin.com`).
       - Enforced that device tiers (1, 2, and 3 devices) belong exclusively to TotalTv USA.
       - Sanitized payment options to remove accidental `/Binance` reference.
  3. **n8n Production Deployment**:
     - Synchronized `AI Agent - TVTotal24` and `AI Agent` in workflow `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY`).
     - Published active production version `a42958af-2807-49fd-a1ad-24be356c08af`.
     - Synchronized local files `workflows/router_chatwoot_ia.json`, `workflows/agent_tvtotal24_latina.json`, and `workflows/agent_totaltv_usa.json`.

---

## 31. Internal Process Privacy Mandate: Elimination of Backend Leaks and Panel Names to Customers

* **Objective & Problem Statement**:
  - When transferring conversations to human support (especially during credential recovery or tool lookups), the AI agent was leaking backend process information and internal tool errors directly to the customer (e.g. stating *"no se consiguieron datos en mvplay"* or *"no se encontraron tus datos en el sistema"*).
  - Internal names of backend panels (such as **MVPlay**, **Mega OTT**, **Xtream-Masters**), database lookup failures, and backend API errors must NEVER be revealed to customers.
  - The customer-facing message must ONLY reference what the customer themselves explicitly stated, while all internal technical diagnostic information belongs exclusively in private notes and administrator alerts.

* **Root Cause**:
  1. In `workflows/tool_get_mvplay_credentials.json`, node `Respuesta Tool` returned `instructions_for_ai` saying *"Informa amablemente al cliente que no fue posible ubicar sus credenciales activas automáticamente en el sistema bajo ese nombre..."*.
  2. In `prompts/tvtotal24_prompt.md`, Paso 4 of the Credential Recovery section instructed the agent to *"Explicar amablemente que no fue posible ubicar automáticamente sus credenciales activas en el panel bajo ese nombre"*, causing the LLM to output internal search details.
  3. No regex fail-safe sanitizer existed in `Formatear Respuesta` to intercept accidental leaks of internal panel names or backend search errors.

* **Remediation & Technical Implementation**:
  1. **Subworkflow `Tool - Obtener Credenciales MVPlay` (`gyTc5A6r5TNRgJCs`)**:
     - Updated node `Respuesta Tool`: Injected absolute privacy mandate into `instructions_for_ai`:
       `"REGLA DE PRIVACIDAD ABSOLUTA: NUNCA le digas al cliente que no se consiguieron datos en MVPlay ni menciones fallos de búsqueda o nombres de paneles internos. Transfiérelo de inmediato a soporte humano ejecutando Call 'transfer_to_human_tool' (reason: 'Recuperación de Credenciales', case_details: 'Consulta de credenciales en MVPlay para: ' + (item.search_term || 'cliente') + ' - no se hallaron líneas activas automáticas, requiere búsqueda manual') y dile al cliente ÚNICAMENTE que lo has transferido con soporte humano para verificar sus datos de acceso y suministrarle sus credenciales directamente."`
     - Deployed and published active version `b96b5039-8eab-4b9d-b1e6-d784d4b87400`.
  2. **System Prompts (`prompts/tvtotal24_prompt.md` and `prompts/agent_prompt.md`)**:
     - Added top-level mandate:
       `⛔ PRIVACIDAD TOTAL DE PROCESO INTERNO — CERO MENCIÓN DE ERRORES O PROCESOS DE BACKEND AL CLIENTE:`
       - Strictly prohibited: mentioning internal panel names (MVPlay, Mega OTT, Xtream-Masters, reseller panel, lines database).
       - Strictly prohibited: telling the customer that data was not found in backend systems, queries failed, or tools returned negative matches.
       - Customer-facing messages must focus strictly on what the customer expressed.
       - Updated Credential Recovery Paso 4 to enforce clean, polite transfer confirmations without backend leaks.
  3. **Fail-Safe Sanitization in `Formatear Respuesta` (`Chatwoot + IA Agent` - `n0zgnS1vlOGNcGNY`)**:
     - Integrated `backendLeakRegex` in the formatting code node right before message dispatch:
       Intercepts patterns matching `no se consiguieron datos en mvplay`, `en mvplay`, `en mega ott`, `no fue posible ubicar tus credenciales automáticamente`, etc., and automatically replaces the message with a reassuring transfer confirmation:
       *"He transferido tu caso con nuestro equipo de soporte humano para que un asesor verifique tus datos de acceso y te atienda directamente. Un asesor te responderá a la brevedad posible dentro de nuestro horario extendido de oficina. ¡Muchas gracias por tu paciencia!"*
     - Deployed and published active production version `5b44b6d6-a701-4cbf-afe6-b7579aa681e2`.
  4. **Production Sync & Git Integration**:
     - Exported and synchronized local workflow files (`router_chatwoot_ia.json`, `tool_get_mvplay_credentials.json`, `agent_tvtotal24_latina.json`, `agent_totaltv_usa.json`).

---

## 32. Vision AI Payload Syntax Fix & Multi-Turn Chatwoot Conversation History Injection

* **Objective & Problem Statement**:
  1. **Vision Node Failure on Image Uploads (Conv #1366)**: When customers sent payment receipts or error screenshots, the AI agent did not respond or process the image. The executions failed with `status: error`.
  2. **Loss of Context Across Time Gaps**: When a customer returned after several minutes or hours and sent a message (e.g., `"🤷🏻‍♂️"`, `"Listo"`, `"Ya pagué"`), the AI agent greeted generically with *"¡Hola! Soy Tivi / Toto, ¿en qué puedo ayudarte?"* completely oblivious to the earlier conversation (such as already providing Bancamiga Pago Móvil details for 9.580 Bs).

* **Root Causes Identified**:
  1. **Anthropic HTTP Request Syntax Error**: In node `Analizar Imagen (Visión Anthropic)` (`router_chatwoot_ia.json`), `jsonBody` was written using `={\n "model": ... }` with handlebars `{{ $json.base64_image }}` inside raw text. In n8n expression mode (`=`), this caused a JavaScript `SyntaxError: Unexpected token ':'`, causing all image executions (e.g. 7920, 7942, 7945) to crash immediately before reaching the AI agent.
  2. **Short Time-Window Filter on Unhandled Messages**: `Preparar Mensaje` filtered incoming messages using `(nowMs - mTime) < 120000` (2 minutes), dropping images or messages sent more than 2 minutes prior even if the assistant had never responded to them.
  3. **Ephemeral In-Memory History (Simple Memory)**: Langchain `memoryBufferWindow` only existed in RAM and was cleared on server restarts or session timeouts. `Preparar Mensaje` already fetched all conversation messages from Chatwoot API (`allMessages`), but never injected prior messages into the AI prompt.

* **Remediation & Technical Implementation**:
  1. **Vision Node JSON Expression Fix (`Analizar Imagen (Visión Anthropic)`)**:
     - Converted `jsonBody` to standard evaluated expression `={{ JSON.stringify({ model: 'claude-3-5-sonnet-20241022', max_tokens: 1000, messages: [...] }) }}`.
     - Added `onError: "continueRegularOutput"` so that any external image API timeout or format issue degrades gracefully without halting the conversation.
  2. **Continuous Unhandled Message & Attachment Aggregation**:
     - Updated `Preparar Mensaje`: Incoming messages are now filtered by `mTime > lastOutgoingTimestamp` (all messages sent since the assistant's last reply, regardless of time elapsed).
     - Any image sent in any unhandled turn is captured in `collectedImageAttachments` and analyzed by Vision AI.
  3. **Chatwoot Conversation History Context Block Injection**:
     - Extracts the last 8 visible (non-private) messages from `allMessages` prior to the unhandled turn, formatting relative timestamps (e.g. `hace 7h`, `hace 30m`, `hace unos segs`) and attachment descriptions.
     - Injects `[HISTORIAL RECIENTE DE LA CONVERSACIÓN EN CHATWOOT: ...]` into the AI prompt, providing 100% resilient situational awareness across hours/days and surviving server restarts.

* **Production Deployment & Git Integration**:
  - Deployed to n8n `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY` / active version `0aa952be-83c3-4351-be40-c31650d6b1c3`).
  - Workflows exported via `export_workflows.py`.
  - Exported and synchronized local workflow files (`router_chatwoot_ia.json`, `tool_get_mvplay_credentials.json`, `agent_tvtotal24_latina.json`, `agent_totaltv_usa.json`).

---

## 33. AI Agent Iteration/Request Limit Privacy & Chatwoot Internal Note Redirection

* **Objective & Problem Statement**:
  - **Leak of Technical Stopping Messages to Customers**: Under high load, complex multi-step tool calls, or repeated tool evaluations, LangChain reached `maxIterations: 10` (or encountered API rate/request limits). By default, LangChain's AgentExecutor stops and outputs technical messages like `"Agent stopped due to max iterations."` or `"Agent stopped due to iteration limit or time limit."`.
  - Because node `Formatear Respuesta` did not intercept these engine-level stop messages, the raw technical message was passed downstream to `Responder en Chatwoot` and delivered as a standard public outgoing message (`private: false`) directly to the customer in WhatsApp / Telegram.
  - The customer was exposed to confusing internal engine errors, while Chatwoot support agents had no internal private note explaining the incident, and the conversation was not tagged for human escalation.

* **Remediation & Technical Implementation**:
  1. **Interception & Private Note Redirection in `Formatear Respuesta` (`router_chatwoot_ia.json`)**:
     - Introduced regex pattern `agentLimitRegex`:
       `/(?:agent stopped due to (?:max )?iterations?|iteration limit|time limit|max_iterations|maximum iterations|reached the maximum number of iterations|rate limit|rate_limit_exceeded|overloaded_error|too many requests|l[íi]mite m[aá]ximo de iteraciones|m[aá]ximo de iteraciones|m[aá]ximo de peticiones|detiene su funcionamiento por alcanzar un m[aá]ximo|l[íi]mite de peticiones|too many iterations)/i`
     - When an iteration/request limit or empty response is detected:
       a) **Posts a Private Internal Note (`private: true`) to Chatwoot**:
          `⚠️ [NOTA INTERNA - AGENTE IA DETENIDO POR LÍMITE O ERROR]`
          Logs the exact technical details and notes that the conversation has been automatically redirected to human support.
       b) **Applies `human` Label to Chatwoot Conversation**:
          Automatically marks the conversation with `human` via Chatwoot API so the bot will not reply further and human agents receive the case in their queue.
       c) **Replaces Public Customer-Facing Message**:
          Replaces the outgoing message with a polite and reassuring transfer confirmation adapted to the customer's language (Spanish or English):
          *"He transferido tu caso con nuestro equipo de soporte humano para que un asesor te atienda directamente. Un asesor te responderá a la brevedad posible dentro de nuestro horario extendido de oficina. ¡Muchas gracias por tu paciencia!"*
  2. **Expansion of Agent Margins & Graceful Degradation**:
     - Increased `maxIterations` from `10` to `15` on both `AI Agent` (TotalTv USA) and `AI Agent - TVTotal24` (TVTotal24 Latina) to grant 50% more headroom for complex chained tool executions (e.g. credential search fallback to transfer).
     - Configured `"onError": "continueRegularOutput"` on both agent nodes so uncaught API/network exceptions pass into `Formatear Respuesta` rather than terminating the workflow run ungracefully.
  3. **Prompt Mandate Reinforcement**:
     - Added strict prohibitions in `prompts/agent_prompt.md`, `prompts/tvtotal24_prompt.md`, and the agent system messages banning the output of iteration limits, request limits, or technical error phrases to customers.

* **Production Deployment & Git Integration**:
  - Applied updates to n8n workflow `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY` / active version `fe2f98b0-bd82-4f81-8717-a4c72d28d700`).
  - Workflows re-exported and validated with `export_workflows.py`.
  - Updated `PROJECT_CONTEXT.md`, `prompts/agent_prompt.md`, and `prompts/tvtotal24_prompt.md`.

---

## 34. Customer Service Username (`Usuario`) Custom Attribute in Chatwoot & Context Injection

* **Objective & Problem Statement**:
  - When an incoming contact was identified as an active customer in Google Sheets (`Mega` for TotalTv USA or `DnSpace` for TVTotal24 Latina), the system updated the contact's `name`, saved `1raCompra` date to `additional_attributes.description`, and applied `stage-leads-ganados`.
  - However, the customer's service username (from the `"Usuario"` column in the corresponding Google Sheet) was not stored in the Chatwoot contact card or injected into the prompt context for the AI Agent.
  - Support agents in Chatwoot could not immediately see the customer's service username in the contact card sidebar, and the AI agent had to query or lack direct visibility of the service username.

* **Remediation & Technical Implementation**:
  1. **Chatwoot Custom Attribute Definition**:
     - Created `contact_attribute` custom attribute `usuario` in Chatwoot API:
       - `attribute_key`: `"usuario"`
       - `attribute_display_name`: `"Usuario"`
       - `attribute_model`: `"contact_attribute"`
       - `attribute_display_type`: `"text"` (ID 12).
  2. **Evaluation & Fallback Nodes Update (`router_chatwoot_ia.json`)**:
     - Updated 4 evaluation nodes (`Evaluar Cliente DnSpace`, `Evaluar Cliente Mega`, `Evaluar DnSpace (Fallback)`, `Evaluar Mega (Fallback)`):
       - Extracts `sheetUsuario` using `/^(usuario|user|username)/i`.
       - Injects `sheetUsuario` into contact update payload:
         ```json
         {
           "additional_attributes": { "company_name": channelDefaultName, "description": firstPurchase, "usuario": sheetUsuario },
           "custom_attributes": { "usuario": sheetUsuario }
         }
         ```
       - Injects `Usuario: "${sheetUsuario}"` into `[CLIENT CONTEXT: Existing customer in database...]` passed to the AI agent.
       - Returns `client_usuario` in output JSON.
  3. **Message Preparation Update (`Preparar Mensaje`)**:
     - Extracts `contactUsuario` from `custom_attributes.usuario` or `additional_attributes.usuario`.
     - Injects `Usuario: "${contactUsuario}"` into cached `[CLIENT CONTEXT...]` for customers already marked with `stage-leads-ganados`.
     - Returns `contact_usuario` in JSON output.
  4. **Retrospective Backfill on September Conversations**:
     - Queried all 100 September conversations from Chatwoot across open/snoozed/resolved statuses.
     - Matched customer phone numbers and emails against all 106 rows of `Mega` and 93 rows of `DnSpace`.
     - Successfully updated 55 active customer contact cards in Chatwoot with their service `Usuario`, registered `name`, and `1ra compra` date with 0 errors.

* **Production Deployment & Git Integration**:
  - Deployed atomically to n8n workflow `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY` / active version `ef0953d3-6b20-4e4c-93d9-ff4a4e3afe41`).
  - Workflows re-exported and synchronized via `export_workflows.py`.
  - Updated `PROJECT_CONTEXT.md` and committed changes to git.

---

## 35. Automatic Human Transfer Guardrail, Internal Note Synchronization & Prompt Hardening

* **Objective & Problem Statement**:
  - In certain conversations (e.g. Conversation 1365 with Luis Villar, plus historical cases like 1342, 1378, 1380), when the AI Agent decided to transfer the customer to human support after troubleshooting, the LLM generated customer-facing confirmation text (*"Te he transferido con nuestro equipo de soporte humano..."*) directly in its response without issuing a tool call to `Call 'transfer_to_human_tool'`.
  - Because the tool function was bypassed:
    1. The `human` label was never applied to the Chatwoot conversation.
    2. The private internal note summarizing the case and customer credentials was not generated.
    3. The administrator alerts (via Telegram and Evolution API WhatsApp) were never dispatched.
    4. When the customer replied subsequently (e.g. "Gracias"), the bot woke up and responded again rather than pausing for human support.

* **Remediation & Technical Implementation**:
  1. **Automatic Transfer Guardrail in `Formatear Respuesta` (`router_chatwoot_ia.json`)**:
     - Added transfer phrase detection regex `transferPhrasesRegex`:
       `/(?:te he transferido|he transferido (?:tu|el|su|la)|transferí tu|transferido con nuestro equipo|transferida a soporte|transferirte a un asesor|un asesor (?:de nuestro equipo|humano )?te (?:atenderá|contactará|responderá)|transfer (?:your|you|the)|transferred (?:your request|you|the conversation) to (?:our )?human|an agent will (?:assist|contact|reach out to) you)/i`
     - Whenever transfer phrasing is present (or triggered by engine error/leak replacements) and `transferToolCalled` was false or the conversation lacks `human`:
       a) **Applies `human` Label**: Fetches current labels and immediately writes `human` to the conversation via Chatwoot API `POST /conversations/{id}/labels`.
       b) **Posts Internal Private Note**: Generates and posts a Markdown private note (`private: true`) to Chatwoot containing Contact Name, Phone, Email, Service Username (`Usuario`), Brand/Inbox, and the exact message sent to the client.
  2. **Reliable Conversation ID in `Call 'transfer_to_human_tool'`**:
     - Updated parameter mapping to use `$('Preparar Mensaje').first().json.conversation_id` and `account_id` instead of fragile webhook body navigation, ensuring tool calls always target the exact active conversation.
  3. **Resilient Error Handling in `Transfer to Human Tool` (`xam0WV65gvTbXcIx`)**:
     - Configured `onError: "continueRegularOutput"` on `Notificar Administrador` (Telegram), `Nota privada Chatwoot`, `Notificar WhatsApp (Evolution API)`, and `Registrar Consulta Pendiente Google Doc` to prevent transient network issues from aborting the transfer workflow.
  4. **Prompt Mandate & Smarters Escalation Hardening**:
     - Added strict prohibitions in `prompts/agent_prompt.md` and `prompts/tvtotal24_prompt.md` banning the output of transfer promises without prior execution of `Call 'transfer_to_human_tool'` in the same turn.
     - Added explicit Smarters troubleshooting escalation instructions in `tvtotal24_prompt.md` directing the agent to call the transfer tool with user and device details if alternative URLs fail to resolve login errors.
  5. **Remediation of Active Conversation 1365**:
     - Applied `human` label to conversation 1365 and posted a complete internal private note with Luis Villar's diagnostic details, app, and service username (`LuisVillar`).

* **Production Deployment & Git Integration**:
  - Deployed updates to n8n workflows `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY` / active version `4e0daa14-b798-4e3c-aeb6-2f53b448bab0`) and `Transfer to Human Tool` (`xam0WV65gvTbXcIx` / active version `26f40ba7-395f-4bcf-b072-437a2de70422`).
  - Workflows synchronized locally via `export_workflows.py`.
  - Updated `PROJECT_CONTEXT.md` and committed changes to git.

---

## 36. Image Processing (Anthropic Vision), Receipt Acknowledgment & Language Detection Hardening

* **Objective & Problem Statement**:
  - When customers sent image attachments (payment receipts such as Zelle, Pago Móvil, or Binance Pay, or technical screenshots of IPTV app errors / device screens), the AI agent froze/paralyzed without providing any response to the customer.
  - Furthermore, in cases where vision or human transfer tools executed, the agent would either remain silent or fall back to generic English canned responses even when Spanish-speaking customers were contacting TotalTv USA.

* **Root Causes & Technical Implementation**:
  1. **Obsolete Anthropic Vision Model (HTTP 404)**:
     - The HTTP request node `Analizar Imagen (Visión Anthropic)` was configured with deprecated model `claude-3-5-sonnet-20241022`, returning HTTP 404 from the Anthropic API (`{"type":"not_found_error","message":"model: claude-3-5-sonnet-20241022"}`).
     - **Fix**: Updated model to `claude-sonnet-4-6` (Anthropic's latest high-capability multimodal model active on credential `ZbUWSAq6JlKInA64`).
  2. **Binary Image Download Corruption (HTTP 400)**:
     - In `Preparar Mensaje`, image downloading via `this.helpers.httpRequest` was configured with `encoding: null`. In modern n8n Axios execution, `encoding: null` caused binary JPEG/PNG byte streams to be decoded into UTF-8 strings with replacement characters (`\xef\xbf\xbd`), expanding 79 KB images into 184 KB of corrupted base64 payloads that Anthropic rejected with HTTP 400 (`"Could not process image"`).
     - **Fix**: Changed download configuration to `encoding: 'arraybuffer'`. Image buffers are now preserved exactly in raw binary and cleanly converted to base64 (`Buffer.from(imgBuffer).toString('base64')`).
  3. **Resilient Parsing & Execution Mode in `Procesar Resultado Visión`**:
     - Configured `"mode": "runOnceForAllItems"` to prevent n8n item execution mismatch errors.
     - Implemented robust regex JSON extraction `/\{[\s\S]*\}/` to parse structured vision responses reliably even if Anthropic outputs markdown fences or conversational preambles.
     - Verified strict brand boundaries for Zelle destinations (`pagos@totaltvlatina.com` for TVTotal24 Latina; `acalimanr@gmail.com` for TotalTv USA) and Pago Móvil verification (Phone `04246861135` / RIF `J405259221`).
  4. **Customer Language Detection & Receipt Confirmation in `Formatear Respuesta`**:
     - **Language Detection Fix**: Replaced the rigid `prepData.brand === 'totaltvusa'` check with keyword-based language detection matching the customer's incoming message (`esRegex` vs `enRegex`), ensuring bilingual TotalTv USA customers communicating in Spanish receive Spanish responses.
     - **Explicit Receipt Confirmation**: When a customer sends a payment receipt, `Formatear Respuesta` reads `visionData` from `Procesar Resultado Visión` and guarantees the customer receives an explicit confirmation mentioning the payment method, amount, and reference number (e.g. *"¡Muchas gracias por enviar tu comprobante de pago! Hemos recibido los datos de tu transacción vía ZELLE por $12.00 USD (Ref: COF2FWMXWLGP)..."*) before transferring the case to human administration.
     - **Technical Screenshot Confirmation**: For app/device error screenshots, ensures diagnostic details are included in the transfer and acknowledged to the customer without leaving the chat hanging.
     - **Auto-Guardrail Human Transfer**: Guarantees that any payment receipt automatically applies the `human` label and creates a comprehensive internal private note in Chatwoot with financial details even if the LLM tool execution had transient hiccups.

* **End-to-End Verification & Production Deployment**:
  - Tested end-to-end against real production payload (Conversation #1401 with Jose Parra, Zelle payment receipt of $12.00 USD).
  - Test execution 8943 succeeded with status `success`: Anthropic vision extracted transaction details, human transfer executed, and Chatwoot response was sent in Spanish acknowledging the receipt.
  - Published n8n workflow `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY` / active version `1fd937e9-92de-4a84-9b96-785c8b9a94ab`).
  - Synchronized repository with `export_workflows.py`.

---

## 37. Customer Evaluation Nodes: Removal of `$node.name` ExpressionError on New Leads

* **Objective & Problem Statement**:
  - The AI Agent was failing to attend incoming customer conversations in Chatwoot (e.g. Conversation #1406 with Mitchell Lovett, along with other non-customer leads).
  - Webhook executions in n8n (e.g. 9425, 9422, 9419, 9417, 9415, 9413, 9411, 9408, 9405) were crashing immediately after the Google Sheets lookup step without reaching the AI Agent or generating a response.

* **Root Cause**:
  - In recent updates, the `else` branch of customer evaluation nodes (`Evaluar Cliente Mega`, `Evaluar Cliente DnSpace`, `Evaluar DnSpace (Fallback)`, and `Evaluar Mega (Fallback)`) contained:
    ```javascript
    const isFallbackNode = typeof $node !== 'undefined' && ($node.name.includes('Fallback'));
    ```
  - In n8n's JavaScript sandbox, `$node` is a proxy object for accessing output data from upstream nodes by name (e.g. `$node["NodeName"].json`). Accessing `$node.name` caused n8n's expression engine to look for an upstream node literally named `"name"`.
  - When evaluating any lead NOT registered in Google Sheets, execution entered the `else` block and threw `ExpressionError: Referenced node doesn't exist` (`nodeCause: "name"`).
  - This unhandled fatal exception crashed the workflow prior to reaching `¿Qué Empresa?` and the AI Agent nodes.

* **Remediation & Technical Implementation**:
  - Removed all `$node.name` expressions across all 4 customer evaluation nodes in `workflows/router_chatwoot_ia.json`:
    1. **`Evaluar Cliente Mega` & `Evaluar Cliente DnSpace`**:
       - Replaced the `else` block with simple, clean `else { isLeadGanado = false; }`.
    2. **`Evaluar DnSpace (Fallback)`**:
       - `else` block sets `isLeadGanado = false;` and if the conversation lacks any `stage-*` label, appends `stage-incoming-leads` via Chatwoot API `POST /conversations/{id}/labels`.
    3. **`Evaluar Mega (Fallback)`**:
       - `else` block sets `isLeadGanado = false;` and if the conversation lacks any `stage-*` label, appends `stage-leads-entrantes` via Chatwoot API `POST /conversations/{id}/labels`.
  - Verified syntax of all JavaScript code nodes across the workflow (`Syntax OK`).

* **Production Deployment & Verification**:
  - Updated live n8n workflow `Chatwoot + IA Agent` (`n0zgnS1vlOGNcGNY`) via MCP tool `update_workflow` with 4 atomic operations.
  - Published active version `9ebe7752-2065-403f-9ae1-1f55c0845c19`.
  - Exported and synchronized `workflows/router_chatwoot_ia.json`.



