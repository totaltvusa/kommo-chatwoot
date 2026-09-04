import urllib.request
import json
import os
import time

token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyY2E4ZWVmMi1hOWVjLTRiYTktOWVmMy02MDA1OTJlYzY1ZWYiLCJpc3MiOiJuOG4iLCJhdWQiOiJtY3Atc2VydmVyLWFwaSIsImp0aSI6ImUzZmZlNjkwLWNmYTMtNDNkNC05YTM0LThjNGViMjA1NjM4YSIsImlhdCI6MTc4NzA5NDk3Mn0.1C2sTahMnvbG6_H6Q4s2Fhq_cgKR8KlqGlmkG5s34bE'
url = 'https://n8n.ac4.club/mcp-server/http'

import ssl

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
    with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
        for _ in range(50):
            line = resp.readline().decode('utf-8')
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
    'tool_transfer_to_human': 'xam0WV65gvTbXcIx',
    'latin_vence_hoy_y_vence4': 'TfILC2hXao6SLQfE',
    'cron_autoclose_inactive_conversations': 'asQhO3WgzQW4gR5P'
}

base_dir = os.path.dirname(os.path.abspath(__file__))

for name, wid in wfs.items():
    try:
        res = call_mcp('get_workflow_details', {'workflowId': wid})
        if res:
            wf_data = json.loads(res.get('result', {}).get('content', [{}])[0].get('text', '{}')).get('workflow', {})
            filepath = os.path.join(base_dir, f'{name}.json')
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(wf_data, f, indent=2, ensure_ascii=False)
            print(f'Exported {name} -> {filepath}')
    except Exception as e:
        print(f'Error exporting {name}: {e}')
