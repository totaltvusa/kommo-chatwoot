# Xtream-Masters (MVPlay) Reseller API Documentation

Source: https://ottpanel.tv/xm_reseller_api_doc.html / http://panel.mvpl.uk:2086/xm_api

## Authentication
All API requests require the `api_key` parameter. Include it as a query parameter (or POST body) on every request.

## Base URL Format
```http
http://{server-dns}:{stream-port}/{api-access-code}/reseller/index.php
```
* **Server DNS / Port:** E.g. `http://wk.mvpl.uk:2082` or `http://panel.mvpl.uk:2086`
* **API Access Code:** Unique code for the reseller account (found in panel under API Settings).
* **API Key:** `ace3cacdfd48afdec756ec214ec0793f` (User: `TtvLat2025`).

---

## Global Parameters

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `api_key` | string | **Required** | Your unique API key for authentication |
| `action` | string | **Required** | The API action to perform |
| `dry_run` | int | Optional | `1` = validate, price and return record without writing/charging. |
| `request_id` | string | Optional | Unique ID for idempotency (prevents duplicate creates on retry within 24h). |

---

## 1. General Endpoints

### `user_info` — Get Reseller Account Info
Returns reseller account details including credits, status, and account settings.

**Request:**
```bash
curl -X GET "http://{dns}:{port}/{access_code}/reseller/index.php?api_key={api_key}&action=user_info"
```

**Response:**
```json
{
  "status": "STATUS_SUCCESS",
  "data": {
    "id": 152,
    "username": "TtvLat2025",
    "email": "...",
    "credits": 485.00,
    "status": 1,
    "reseller_dns": "...",
    "created_at": "...",
    "member_group_id": 3
  }
}
```

### `packages` — Get Available Packages
Returns the list of packages available with IDs, pricing, duration, and whether it is a trial (`is_trial: 1`).

**Request:**
```bash
curl -X GET "http://{dns}:{port}/{access_code}/reseller/index.php?api_key={api_key}&action=packages"
```

**Response:**
```json
{
  "status": "STATUS_SUCCESS",
  "data": [
    {
      "id": 1,
      "package_name": "1 Month",
      "credits": 1.00,
      "duration_months": 1,
      "is_trial": 0
    },
    {
      "id": 2,
      "package_name": "4 Hours Trial",
      "credits": 0.00,
      "duration_months": 0,
      "is_trial": 1
    }
  ]
}
```

---

## 2. Line Management (M3U)

### `create_line` — Create New Line / Trial
Creates a new line. Username and password are auto-generated if omitted.

**Request:**
```bash
curl -X POST "http://{dns}:{port}/{access_code}/reseller/index.php"   -d "api_key={api_key}"   -d "action=create_line"   -d "package={package_id}"   -d "trial=1"   -d "username={username}"   -d "password={password}"   -d "reseller_notes={customer_name_and_phone}"
```

**Parameters:**
* `package` (int, required): Package ID from `packages` endpoint.
* `trial` (int, required): `1` for trial / demo, `0` for paid.
* `username` (string, optional): Custom username.
* `password` (string, optional): Custom password.
* `reseller_notes` (string, optional): Notes (customer name, WhatsApp, email).
* `max_connections` (int, optional): Max simultaneous screens (default 1).

**Response:**
```json
{
  "status": "STATUS_SUCCESS",
  "data": {
    "id": 4521,
    "username": "demo12345",
    "password": "passXYZ",
    "package_id": 2,
    "exp_date": 1740000000,
    "is_trial": 1,
    "status": 1,
    "reseller_notes": "John Doe - 58412...",
    "created_at": "2026-08-28 12:00:00"
  }
}
```

### `get_line` — Get Specific Line Info
```bash
curl -X GET "http://{dns}:{port}/{access_code}/reseller/index.php?api_key={api_key}&action=get_line&id={line_id}"
```

### `get_lines` — List Lines
```bash
curl -X GET "http://{dns}:{port}/{access_code}/reseller/index.php?api_key={api_key}&action=get_lines"
```

### `extend_line` / `edit_line` — Extend or Edit Line
```bash
curl -X POST "http://{dns}:{port}/{access_code}/reseller/index.php"   -d "api_key={api_key}"   -d "action=edit_line"   -d "id={line_id}"   -d "package={package_id}"
```

---

## 3. Server DNS & Application Connection

### Stream / Line DNS URLs:
* `http://wk.mvpl.uk:2082`
* `http://dt.nexr.cc:2095`
* `http://wk.wxn.ch:2095`
* `http://vd.cooteg.cc:2082`
* `http://vd.cooteg.ch:2095`

### Smart TV (Samsung / LG IPTV Smarters) DNS URLs:
* `http://cdn01link.uk:2095`
* `http://node01hub.uk:2082`
* `http://mundosmarters.uk:2082`
