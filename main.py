from flask import Flask, send_file
import os, requests, subprocess, sys, json, base64, io
from datetime import datetime

app = Flask(__name__)

#основная функция
@app.route('/WARP')
def warp():
    #генерируем ключики, важно иметь wireguard-tools в системе
    priv = run_command('wg genkey')
    pub = run_command(f'echo "{priv}" | wg pubkey')
    
    response = ins("POST", "reg", json={
        "install_id": "",
        "tos": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "key": pub,
        "fcm_token": "",
        "type": "ios",
        "locale": "en_US"
    })
    resultid = response['result']['id']
    token = response['result']['token']
    response = sec("PATCH", f"reg/{resultid}", token, json={"warp_enabled": True})
    peer_pub = response['result']['config']['peers'][0]['public_key']
    peer_endpoint = response['result']['config']['peers'][0]['endpoint']['host']
    client_ipv4 = response['result']['config']['interface']['addresses']['v4']
    client_ipv6 = response['result']['config']['interface']['addresses']['v6']
    conf = f"""[Interface]
PrivateKey = {priv}
S1 = 0
S2 = 0
Jc = 4
Jmin = 40
Jmax = 70
H1 = 1
H2 = 2
H3 = 3
H4 = 4
MTU = 1280
Address = {client_ipv4}, {client_ipv6}
DNS = 1.1.1.1, 2606:4700:4700::1111, 1.0.0.1, 2606:4700:4700::1001

[Peer]
PublicKey = {peer_pub}
AllowedIPs = 0.0.0.0/0, ::/0
Endpoint = {peer_endpoint}
"""
    file_buffer = io.BytesIO()
    file_buffer.write(conf.encode('utf-8'))
    file_buffer.seek(0)
    return send_file(
            file_buffer,
            mimetype='text/plain',
            as_attachment=True,
            download_name='WARP.conf'
    )

#функция, чтоб проще выполнять команды
def run_command(command):
    process = subprocess.run(command, shell=True, capture_output=True, text=True)
    return process.stdout.strip()

#первый запрос
def ins(method, endpoint, **kwargs):
    api = 'https://api.cloudflareclient.com/v0i1909051800'
    headers = {
        'user-agent': '',
        'content-type': 'application/json'
    }
    response = requests.request(method, f"{api}/{endpoint}", headers=headers, **kwargs)
    return response.json()

#второй запрос
def sec(method, endpoint, token, **kwargs):
    api = 'https://api.cloudflareclient.com/v0i1909051800'
    headers = {
        'authorization': f'Bearer {token}'
    }
    response = requests.request(method, f"{api}/{endpoint}", headers=headers, **kwargs)
    return response.json()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
