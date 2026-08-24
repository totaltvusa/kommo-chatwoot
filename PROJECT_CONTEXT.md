# 🧠 PROJECT CONTEXT & PERSISTENCE DOCUMENT
> **Ecosistema de Automatización Omnicanal: Chatwoot + n8n + OpenAI + APIs**
> **Baseline Estable:** Versión restaurada al 19 de Agosto de 2026

---

## 📌 1. Propósito y Filosofía del Proyecto
Este archivo es el **documento único de persistencia y contexto de trabajo**. Debe ser leído al iniciar cualquier sesión de desarrollo o asistencia (con Google Antigravity o cualquier otro entorno) para garantizar continuidad total, uniformidad y evitar regresiones.

### Protocolo Diario de Trabajo (Check-in / Check-out)
1. **Al iniciar la jornada o cambiar de equipo:**
   ```bash
   git pull origin main
   ```
   *Leer obligatoriamente este archivo (`PROJECT_CONTEXT.md`) para cargar el contexto actualizado.*
2. **Durante el desarrollo:**
   * Respetar las reglas de negocio y los prompts maestros sin alterar el contexto informativo existente.
   * Probar flujos end-to-end antes de dar por completado un cambio.
3. **Al finalizar o realizar cambios:**
   * Actualizar este archivo con cualquier nuevo nodo, webhook, ID o ajuste realizado.
   * Sincronizar inmediatamente con GitHub:
     ```bash
     git add .
     git commit -m "Descripción clara del cambio"
     git push origin main
     ```

---

## 🏗️ 2. Arquitectura General del Sistema

```mermaid
graph TD
    User([Cliente: WhatsApp / Telegram]) -->|Mensaje| Chatwoot[Chatwoot Hub]
    Chatwoot -->|Webhook: message_created| Router[n8n: Chatwoot + IA Agent (n0zgnS1vlOGNcGNY)]
    
    subgraph n8n Workflow Autocontenido
        Router --> IncomingFilter{¿Es mensaje entrante?}
        IncomingFilter -->|Sí| Agent[LangChain AI Agent]
        Agent --> Model[OpenAI Chat Model: gpt-4o-mini]
        Agent --> Memory[Simple Memory: Buffer Window]
        Agent -.-> ToolPay[Call: getpaymentlink (3dBu0SNABE2pKCqU)]
        Agent --> Switch[Switch Response Router]
        Switch --> Code[Code: Formatear Enlaces / Texto]
    end
    
    Switch --> Responder[Responder en Chatwoot]
    Code --> Responder
    Responder -->|POST /messages| Chatwoot
    Chatwoot -->|Salida Nativa| User
```

---

## 📱 3. Mapeo de Canales e Inboxes en Chatwoot (Account ID: 1)

| Inbox ID | Nombre del Inbox | Tipo de Canal | Manejo / Rol |
| :---: | :--- | :--- | :--- |
| **`4`** | `TTvAlertsMovistar` | `Channel::Api` (WhatsApp) | Atendido por `Chatwoot + IA Agent` |
| **`6`** | `TvTotalUSAbot` | `Channel::Telegram` | Atendido por `Chatwoot + IA Agent` |
| **`7`** | `AlvezClawBot` | `Channel::Telegram` | Atendido por `Chatwoot + IA Agent` |
| **`10`** | `Telegram - TvTotal24` | `Channel::Telegram` | Canal Telegram TvTotal24 |
| **`8`** | `migracion` | `Channel::Api` | Soporte / Migración |

---

## ⚙️ 4. Catálogo de Workflows Activos en n8n

| ID del Workflow | Nombre en n8n | Rol / Función | Estado |
| :--- | :--- | :--- | :--- |
| **`n0zgnS1vlOGNcGNY`** | `Chatwoot + IA Agent` | **Workflow Principal:** Recibe el webhook de Chatwoot, procesa la intención con OpenAI LangChain Agent, genera enlaces de pago y responde directamente en Chatwoot. | **Activo** |
| **`xam0WV65gvTbXcIx`** | `Transfer to Human Tool` | **Herramienta de Traspaso:** Agrega etiqueta `human` y genera notificación interna. | **Activo** |
| **`3dBu0SNABE2pKCqU`** | `getpaymentlink` | **Herramienta Pagos:** Genera links dinámicos para Crypto (NowPayments), CashApp (PD.cash) y Tarjeta/PayPal (Card2Crypto). | **Activo** |
| **`p8dS1jx73xvpbrkj`** | `Card2CryptoLink` | Generación de enlaces Card2Crypto. | **Activo** |
| **`uD5sM2ruGXYSlpY3`** | `NowPayments to me` | Notificación de pagos NowPayments. | **Activo** |
| **`asQhO3WgzQW4gR5P`** | `Agent - TotalTv USA` | Subagente USA (creado el 20-ago). | *Inactivo / Despublicado* |
| **`Vfweu0rjoTT3FUl1`** | `Agent - TVTotal24 (Latina)` | Subagente Latina (creado el 20-ago). | *Inactivo / Despublicado* |
| **`4AYo7CX3Ou1K2yXH`** | `Tool - Calcular Pago Movil` | Herramienta Pago Móvil (creada el 21-ago). | *Inactivo / Despublicado* |
| **`e1R7zQorWBaaqgou`** | `Create Mega OTT Trial Tool` | Herramienta Demos Mega OTT (creada el 20-ago). | *Inactivo / Despublicado* |

---

## 🤖 5. Configuración de IA y Reglas de Negocio

### Configuración del LLM
* **Modelo:** `gpt-4o-mini` (OpenAI)
* **Temperature:** `0`
* **Top P:** `0.1`
* **Memoria:** `Simple Memory` con clave de sesión `{{$json.body.conversation.id}}` (50 turnos de ventana de contexto).

### Reglas Críticas
1. **Regla 2.1 (Saludos y Cortesía):**
   * Saludos casuales (*"hola"*, *"buenas noches"*, *"hello"*, etc.) son **IN-SCOPE**. El agente responde cordialmente sin rechazar el contexto.
2. **Transferencia a Humano:**
   * Al transferir a un agente humano, se preservan las etiquetas de la conversación y se marca con `human`, pausando la respuesta automática de la IA mientras mantenga dicha etiqueta.

---

## 📁 6. Estructura del Repositorio Local

```text
/mnt/Data/Projects for Antigravity/kommo-chatwoot/
├── PROJECT_CONTEXT.md          # 🧠 Documento maestro de persistencia
├── .gitignore                  # Exclusiones de Git (seguridad y temporales)
├── requirements.txt            # Dependencias de Python
├── config.py                   # Configuraciones base
├── prompts/
│   ├── agent_prompt.md         # Prompt maestro TotalTv USA
│   └── tvtotal24_prompt.md     # Prompt maestro TVTotal24 Latina
├── workflows/                  # Backups JSON versionados de n8n
│   ├── router_chatwoot_ia.json
│   ├── tool_transfer_to_human.json
│   └── ...
└── core/                       # Módulos Python para Kommo y Chatwoot API
```
