# 🧠 PROJECT CONTEXT & PERSISTENCE DOCUMENT
> **Ecosistema de Automatización Omnicanal: Chatwoot + n8n + Anthropic Claude + APIs**
> **Marcas:** TotalTv USA & TVTotal24 (Latina)

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
    Chatwoot -->|Webhook: message_created| Router[n8n: Router Principal (n0zgnS1vlOGNcGNY)]
    
    subgraph Router n8n
        Router --> IncomingFilter{¿Es entrante y no humano?}
        IncomingFilter -->|Sí| Debounce[Wait 5s + Debounce Messages]
        Debounce --> BrandRouter{Determinar Marca}
    end
    
    BrandRouter -->|USA: Inboxes 4, 6, 7| AgentUSA[Agente TotalTv USA (asQhO3WgzQW4gR5P)]
    BrandRouter -->|Latina: Inbox 10| AgentLatina[Agente TVTotal24 (Vfweu0rjoTT3FUl1)]
    
    subgraph LLM Model
        AgentUSA --> ClaudeUSA[Anthropic Claude 3.5 Sonnet\ntemp: 0, topP: 0.001]
        AgentLatina --> ClaudeLat[Anthropic Claude 3.5 Sonnet\ntemp: 0, topP: 0.001]
    end
    
    subgraph Tools USA
        AgentUSA -.-> ToolTrial[Create Mega OTT Trial (e1R7zQorWBaaqgou)]
        AgentUSA -.-> ToolPayUSA[Get Payment Link (3dBu0SNABE2pKCqU)]
        AgentUSA -.-> ToolHumanUSA[Transfer to Human (xam0WV65gvTbXcIx)]
    end
    
    subgraph Tools Latina
        AgentLatina -.-> ToolPM[Calcular Pago Movil (4AYo7CX3Ou1K2yXH)\nParalelo vs Binance P2P]
        AgentLatina -.-> ToolHumanLat[Transfer to Human (xam0WV65gvTbXcIx)]
    end
    
    AgentUSA --> Responder[Responder en Chatwoot]
    AgentLatina --> Responder
    Responder -->|POST /messages| Chatwoot
    Chatwoot -->|Salida Nativa| User
```

---

## 📱 3. Mapeo de Canales e Inboxes en Chatwoot (Account ID: 1)

| Inbox ID | Nombre del Inbox | Tipo de Canal | Marca / Funnel | Agente Asignado |
| :---: | :--- | :--- | :--- | :--- |
| **`4`** | `TTvAlertsMovistar` | `Channel::Api` (WhatsApp) | `totaltvusa` / `funnel-totaltv-usa` | `Agent - TotalTv USA` (`asQhO3WgzQW4gR5P`) |
| **`6`** | `TvTotalUSAbot` | `Channel::Telegram` | `totaltvusa` / `funnel-totaltv-usa` | `Agent - TotalTv USA` (`asQhO3WgzQW4gR5P`) |
| **`7`** | `AlvezClawBot` | `Channel::Telegram` | `totaltvusa` / `funnel-totaltv-usa` | `Agent - TotalTv USA` (`asQhO3WgzQW4gR5P`) |
| **`10`** | `Telegram - TvTotal24` | `Channel::Telegram` | `tvtotal24` / `funnel-totaltv-latina` | `Agent - TVTotal24 (Latina)` (`Vfweu0rjoTT3FUl1`) |
| **`8`** | `migracion` | `Channel::Api` | Soporte / Migración | No automatizado |

### Reglas de Automatización en Chatwoot
* **Regla 1 (`LIC USA`):** Se dispara en inboxes `[4, 6, 7]` $\rightarrow$ Asigna etiqueta `funnel-totaltv-usa`.
* **Regla 5 (`LIC LAT`):** Se dispara en inbox `10` $\rightarrow$ Asigna etiqueta `funnel-totaltv-latina`.

---

## ⚙️ 4. Catálogo de Workflows en n8n

| ID del Workflow | Nombre en n8n | Rol / Función |
| :--- | :--- | :--- |
| **`n0zgnS1vlOGNcGNY`** | `Chatwoot + IA Agent` | **Router Principal:** Recibe webhook de Chatwoot, filtra mensajes no respondidos, ejecuta debounce de 5s, enruta por marca y envía respuesta de vuelta a Chatwoot. |
| **`asQhO3WgzQW4gR5P`** | `Agent - TotalTv USA` | **Agente USA:** LangChain Agent con Anthropic Claude 3.5 Sonnet y herramientas de Trial, Payment Link y Transfer to Human. |
| **`Vfweu0rjoTT3FUl1`** | `Agent - TVTotal24 (Latina)` | **Agente Latina:** LangChain Agent con Anthropic Claude 3.5 Sonnet y herramientas de Pago Móvil y Transfer to Human. |
| **`4AYo7CX3Ou1K2yXH`** | `Tool - Calcular Pago Movil` | **Herramienta Financiera:** Consulta tasa en tiempo real de DolarApi (Paralelo) y Binance P2P (VES), selecciona la más alta y calcula montos exactos en Bs. |
| **`xam0WV65gvTbXcIx`** | `Transfer to Human Tool` | **Herramienta de Traspaso:** Agrega etiqueta `human` sin borrar etiquetas previas y publica un mensaje privado interno en Chatwoot. |
| **`3dBu0SNABE2pKCqU`** | `getpaymentlink` | **Herramienta Pagos USA:** Genera links dinámicos para Crypto (NowPayments), CashApp (PD.cash) y Tarjeta/PayPal (Card2Crypto). |
| **`e1R7zQorWBaaqgou`** | `Create Mega OTT Trial Tool` | **Herramienta Pruebas:** Genera demos de 24h vía API de Mega OTT. |

---

## 🤖 5. Parámetros de Modelos y Reglas de IA

### Configuración del LLM (Anthropic)
* **Modelo:** `claude-3-5-sonnet-20241022`
* **Temperature:** `0` (Decodificación determinista pura para cero alucinaciones).
* **Top P:** `0.001` (Mínimo estricto permitido por la API de Anthropic).

### Reglas Críticas de Comportamiento de los Agentes
1. **Regla 2.1 (Saludos y Cortesía):**
   * Saludos casuales y de cortesía (*"hola"*, *"buenas noches"*, *"hello"*, etc.) son **IN-SCOPE**. El agente debe responder con un saludo cálido y presentarse brevemente como asistente de la marca.
   * **NUNCA** responder con el fallback *"No dispongo de información específica sobre ese tema"* ante un saludo.
2. **Regla de Pago Móvil (TVTotal24 Latina):**
   * Al mencionar métodos de pago generales, NO se envían imágenes ni datos extensos.
   * Al solicitar Pago Móvil específicamente, se consulta la herramienta `calcular_pago_movil` para dar el monto exacto en Bs (calculado con la tasa mayor entre Paralelo y Binance P2P) junto con los datos bancarios:
     * **Beneficiario:** `ArialStore C.A.`
     * **RIF:** `J405259221`
     * **Teléfono:** `04246861135`
     * **Banco:** `Bancamiga`
     * **QR:** `![Código QR Pago Móvil](https://raw.githubusercontent.com/totaltvusa/images/main/Arialstorepm.jpeg)`
   * **No se pasa a humano** para pagos con Pago Móvil a menos que el cliente lo pida expresamente o tenga un problema con el pago.
3. **Regla de Transferencia a Humano:**
   * Al transferir, la herramienta `xam0WV65gvTbXcIx` añade la etiqueta `human` preservando todas las demás etiquetas de la conversación (`funnel-totaltv-usa`, `channel-telegram`, etc.).
   * Se crea una nota privada (`private: true`) notificando a los agentes humanos.
   * El agente deja de responder automáticamente mientras la conversación mantenga la etiqueta `human`.

---

## 📁 6. Estructura del Repositorio Local

```text
/mnt/Data/Projects for Antigravity/kommo-chatwoot/
├── PROJECT_CONTEXT.md          # Este documento maestro de persistencia
├── .gitignore                  # Exclusiones de Git (seguridad y temporales)
├── requirements.txt            # Dependencias de Python
├── config.py                   # Configuraciones base
├── prompts/
│   ├── agent_prompt.md         # Prompt maestro Agente TotalTv USA
│   └── tvtotal24_prompt.md     # Prompt maestro Agente TVTotal24 Latina
├── core/                       # Módulos Python para Kommo y Chatwoot API
│   ├── chatwoot_api.py
│   ├── kommo_api.py
│   └── ...
├── migrate.py                  # Scripts de migración y sincronización
├── export_funnel.py
├── reapply_labels.py
└── repair_and_add_channels.py
```

---

## 🔒 7. Seguridad y Buenas Prácticas
* **Nunca versionar claves de API ni secretos en texto plano:** Usar `.env` y `.gitignore`.
* **Mantener backups periódicos de los workflows exportados de n8n** en formato JSON dentro de la carpeta del proyecto.
* **Probar siempre los cambios en una conversación de test antes de desplegar a producción.**
