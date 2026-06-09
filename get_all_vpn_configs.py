import requests
import base64
import re
import random
import sys
import os
import csv
import io
from bs4 import BeautifulSoup

# ---------- VPNGate ----------
def fetch_vpngate():
    configs = []
    url = "https://www.vpngate.net/api/iphone/"
    try:
        resp = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        resp.encoding = 'utf-8'
        lines = resp.text.strip().split('\n')
        data_lines = [l for l in lines if l.strip() and not l.startswith('*') and not l.startswith('#')]
        for line in data_lines:
            parts = line.split(',')
            if len(parts) < 15:
                continue
            config_b64 = parts[14].strip()
            if not config_b64 or len(config_b64) < 100:
                continue
            try:
                config = base64.b64decode(config_b64).decode('utf-8')
                config = config.replace('\r\n', '\n')
                if 'remote' in config:
                    configs.append(config)
            except:
                continue
    except Exception as e:
        print(f"⚠️ VPNGate error: {e}")
    return configs

# ---------- VPNBook ----------
def fetch_vpnbook():
    configs = []
    url = "https://www.vpnbook.com/freevpn"
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, 'html.parser')
        # extract ovpn file links
        ovpn_links = [a['href'] for a in soup.find_all('a', href=True) if '.ovpn' in a['href']]
        for link in ovpn_links:
            if not link.startswith('http'):
                link = 'https://www.vpnbook.com' + link
            try:
                ovpn_resp = requests.get(link, timeout=10)
                config = ovpn_resp.text.replace('\r\n', '\n')
                if 'remote' in config:
                    configs.append(config)
            except:
                continue
    except Exception as e:
        print(f"⚠️ VPNBook error: {e}")
    return configs

# ---------- FreeVPN.se (US Servers) ----------
def fetch_freevpndb():
    configs = []
    urls = [
        "https://www.freevpn.se/english/openvpn/ovpn/freevpn_se_US.ovpn",
        "https://www.freevpn.se/english/openvpn/ovpn/freevpn_se_US-1.ovpn",
        "https://www.freevpn.se/english/openvpn/ovpn/freevpn_se_US-2.ovpn",
    ]
    for url in urls:
        try:
            resp = requests.get(url, timeout=10)
            config = resp.text.replace('\r\n', '\n')
            if 'remote' in config:
                configs.append(config)
        except:
            continue
    return configs

if __name__ == "__main__":
    all_configs = []
    print("📥 VPNGate से configs ला रहे हैं...")
    all_configs.extend(fetch_vpngate())
    print("📥 VPNBook से configs ला रहे हैं...")
    all_configs.extend(fetch_vpnbook())
    print("📥 FreeVPN.se से US configs ला रहे हैं...")
    all_configs.extend(fetch_freevpndb())

    # डुप्लीकेट हटाएँ (remote server के आधार पर)
    seen = set()
    unique = []
    for cfg in all_configs:
        try:
            remote = re.findall(r'remote\s+([^\s]+)', cfg)[0]
        except:
            continue
        if remote not in seen:
            seen.add(remote)
            unique.append(cfg)

    random.shuffle(unique)

    if len(unique) == 0:
        print("❌ कोई VPN config नहीं मिली।")
        sys.exit(1)

    # 100 configs तक सेव करें (जितने मिलें, फ़ाइलों में)
    max_save = min(len(unique), 100)
    for i in range(max_save):
        fname = f"config_{i+1}.ovpn"
        with open(fname, "w") as f:
            f.write(unique[i])
    print(f"✅ कुल {max_save} unique configs सेव हुईं।")
