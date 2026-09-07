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
  * Pay ID: `22628239`. Super discount pricing: 1 Month , 3 Months , 12 Months .

---

## 3. Workflow Catalog

| Workflow ID | Name | Role / Status |
| :--- | :--- | :--- |
| `n0zgnS1vlOGNcGNY` | `Chatwoot + IA Agent` | **Active / Main Gateway** (Claude Haiku 4.5, 0-temp, 3s debounce, multi-brand router, Google Sheets Customer DB check) |
| `kh10aaenUURvi7Ji` | `Tool - Create MVPlay Trial` | **Active Subworkflow / Tool** (Automated MVPlay Xtream-Masters trial generator for TVTotal24) |
| `4AYo7CX3Ou1K2yXH` | `Tool - Calcular Pago Movil` | **Active Subworkflow / Tool** (Pago Móvil rate scraping & Bs calculation for TVTotal24) |
| `e1R7zQorWBaaqgou` | `Create Mega OTT Trial Tool` | **Active Subworkflow / Tool** (Mega OTT Trial generator for TotalTv USA) |
| `3dBu0SNABE2pKCqU` | `getpaymentlink` | **Active Subworkflow / Tool** (Payment link generator for TotalTv USA) |
| `xam0WV65gvTbXcIx` | `Transfer to Human Tool` | **Active Subworkflow / Tool** (Human agent escalation - dual Telegram & WhatsApp Evolution API `TTvAlertsMovistar` to `584146130135`) |
| `XC1jY6Vkbgdu5iIz` | `Cron - Followup Stage Fase de Pruebas to Que Te Parecio` | **Active Cron** (Executes every 2 hours on even hours: `0 */2 * * *`) |
| `KRwjH3njrF4qRdph` | `Cron - Followup Stage Trials to Want to Join` | **Active Cron** (Executes every 2 hours on even hours: `0 */2 * * *`) |
| `1IlXjaNv0rc9laJy` | `Cron - Followup Stage Incoming Leads to Contacted` | **Active Cron** (Executes every 2 hours on even hours: `0 */2 * * *`) |
| `TfILC2hXao6SLQfE` | `Latin vence hoy y vence4` | **Active Outbound Notifier** (Daily 9 AM expiration WhatsApp templates via Meta Cloud API + Chatwoot Contact/Conversation/Private Note Sync) |
| `943Yu3CZMD4dzRCI` | `Mega expires TODAY (Vence HOY)` | **Active Outbound Notifier** (Mega OTT Daily 9 AM expiration notifier) |
| `F7M6sLe1lo4zUObT` | `Mega expires SOON (Vence 4 días)` | **Active Outbound Notifier** (Mega OTT 4-day expiration notifier) |
| `p8dS1jx73xvpbrkj` | `Telegram to N8N` | Active |
| `OrUMncnYf5wezbpU` | `AmoCRM Webhook` | Active |
| `uD5sM2ruGXYSlpY3` | `Chatwoot Webhook` | Active |
| `OQzmQUISGM6ShdKT` | `AmoCRM Contact Update` | Active |
| `asQhO3WgzQW4gR5P` | `Cron - Autoclose Inactive Conversations (48h)` | **Active Cron** (Executes at 0, 6, 12, 18h `0 0,6,12,18 * * *`; resolves conversations after 48h customer inactivity, strips `human` tag, applies `autoclosed`) |
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

