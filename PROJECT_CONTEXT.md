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
      * **Inbox 6**: Telegram (`@TotalTvUSAbot`).
      * **Inbox 14**: Instagram (`@tvtotalusa`) via Zernio API.
      * **Inbox 17**: Facebook Messenger (`Facebook - TotalTv USA`) via Zernio API.
      * **Inbox 4**: WhatsApp (`TTvAlertsMovistar`).
    * Service: Mega OTT panel.
    * Audience: USA & International (English / Spanish bilingual auto-detection).
    * Auto-Labeling: Automatically tagged with `funnel-totaltv-usa`, channel labels (`channel-facebook`, `channel-instagram`, `channel-telegram`, `channel-whatsapp`), and initial stage `stage-incoming-leads`.
    * Connected Tools:
      1. `Call 'getpaymentlink'` (`3dBu0SNABE2pKCqU`): Payment link generator.
      2. `Call 'create_trial_tool'` (`e1R7zQorWBaaqgou`): Mega OTT 24h trial generator (tracked via Chatwoot attributes `trial_1_id`, `trial_2_id`; uses `$fromAI` parameter mapping with Chatwoot regex fallback; dual Telegram & WhatsApp Evolution API notifications to `584146130135`).
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
  * **Stage Transition & Label Cleanup**: Upon trial generation, the conversation is automatically tagged with `stage-trials` (TotalTv USA) or `stage-fase-de-pruebas` (TVTotal24), and ANY previous `stage-*` label (e.g. `stage-incoming-leads`, `stage-lead-entrantes`, `stage-contacted`, `stage-contactado`) is strictly removed while preserving all other labels (`funnel-*`, `channel-*`, `human`).

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
    * TotalTv USA (Inboxes 1, 4, 6, 14, 17): automatically assigns `stage-incoming-leads` if no stage exists.
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












