import os
import sys
import ssl
import time
import json
import urllib.request
import re

def load_dotenv():
    env_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'),
        '.env'
    ]
    for path in env_paths:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        k = k.strip()
                        v = v.strip().strip("'").strip('"')
                        if k and k not in os.environ:
                            os.environ[k] = v
            break

load_dotenv()

token = os.environ.get('N8N_MCP_TOKEN', '').strip()
url = os.environ.get('N8N_MCP_URL', 'https://n8n.ac4.club/mcp-server/http').strip()

if not token:
    print("Error: N8N_MCP_TOKEN not found in environment or .env file.")
    print("Please copy .env.example to .env and set your N8N_MCP_TOKEN.")
    sys.exit(1)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def call_mcp(method_name, args):
    body = {'jsonrpc': '2.0', 'id': int(time.time()), 'method': 'tools/call', 'params': {'name': method_name, 'arguments': args}}
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/event-stream',
            'User-Agent': 'Mozilla/5.0'
        },
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=20, context=ctx) as resp:
        raw = resp.read().decode('utf-8')
        for line in raw.split('\n'):
            if line.startswith('data: '):
                return json.loads(line[6:])
    return None

wfs = {
    'router_chatwoot_ia': 'n0zgnS1vlOGNcGNY',
    'cron_followup_incoming_leads': '1IlXjaNv0rc9laJy',
    'cron_followup_fase_pruebas': 'XC1jY6Vkbgdu5iIz',
    'cron_followup_trials': 'KRwjH3njrF4qRdph',
    'tool_calcular_pago_movil': '4AYo7CX3Ou1K2yXH',
    'tool_create_mvplay_trial': 'kh10aaenUURvi7Ji',
    'tool_create_mega_ott_trial': 'e1R7zQorWBaaqgou',
    'tool_get_mvplay_credentials': 'gyTc5A6r5TNRgJCs',
    'tool_transfer_to_human': 'xam0WV65gvTbXcIx',
    'latin_vence_hoy_y_vence4': 'TfILC2hXao6SLQfE',
    'cron_autoclose_inactive_conversations': 'asQhO3WgzQW4gR5P',
    'ecwid_to_client_and_me_2': 'hAHmBsRVDc4Hyt6g',
    'proxy_chatwoot_evolution': 'ecfTEElylV4snTHG',
    'sync_mega_to_megadata': 'Lcyro95g4yg39bdD',
    'card2crypto_link': 'p8dS1jx73xvpbrkj',
    'telegram_to_n8n': 'TS2CADjNNn05jXBW',
    'tool_card2crypto_tvtotal24': 'OCrN0N77qR9Gqppx'
}

base_dir = os.path.dirname(os.path.abspath(__file__))

def sanitize_secrets(data_str):
    # Mask tokens that trigger GitHub push protection
    data_str = re.sub(r'KEY01[A-Za-z0-9_]+', 'KEY_TELNYX_REDACTED', data_str)
    data_str = re.sub(r'KEY[A-Za-z0-9_]{25,}', 'KEY_TELNYX_REDACTED', data_str)
    data_str = re.sub(r'apik_[A-Za-z0-9_]+', 'APIK_WHOP_REDACTED', data_str)
    data_str = re.sub(r'sk_[A-Za-z0-9_]{20,}', 'SK_REDACTED', data_str)
    data_str = re.sub(r'pk_[A-Za-z0-9_]{20,}', 'PK_REDACTED', data_str)
    return data_str

def main():
    for name, wid in wfs.items():
        try:
            res = call_mcp('get_workflow_details', {'workflowId': wid})
            if res:
                wf_data = json.loads(res.get('result', {}).get('content', [{}])[0].get('text', '{}')).get('workflow', {})
                filepath = os.path.join(base_dir, f'{name}.json')
                raw_json = json.dumps(wf_data, indent=2, ensure_ascii=False)
                sanitized_json = sanitize_secrets(raw_json)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(sanitized_json)
                print(f'Exported {name} -> {filepath}')
        except Exception as e:
            print(f'Error exporting {name}: {e}')

if __name__ == '__main__':
    main()

