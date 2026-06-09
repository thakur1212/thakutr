import csv
import io
import base64
import requests
import sys
import os
import random

def fetch_configs(max_configs=10):
    """
    VPNGate API से कई देशों के (US priority) OpenVPN कॉन्फ़िग निकालता है,
    और उन्हें config_1.ovpn, config_2.ovpn ... के रूप में सेव करता है।
    """
    url = "https://www.vpngate.net/api/iphone/"
    try:
        resp = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        resp.encoding = 'utf-8'
        lines = resp.text.strip().split('\n')
        # * और # वाली लाइनें हटाओ
        data_lines = [l for l in lines if l.strip() and not l.startswith('*') and not l.startswith('#')]
        if not data_lines:
            print("⚠️ VPNGate से कोई डेटा नहीं मिला।")
            return 0

        us_configs = []
        other_configs = []

        for line in data_lines:
            parts = line.split(',')
            if len(parts) < 15:
                continue
            country_long = parts[5].strip()
            config_b64 = parts[14].strip()
            if not config_b64 or len(config_b64) < 100:
                continue
            try:
                config = base64.b64decode(config_b64).decode('utf-8')
                config = config.replace('\r\n', '\n')
            except:
                continue
            if 'remote' not in config:
                continue

            entry = config
            if any(x in country_long.lower() for x in ['united states', 'us', 'america']):
                us_configs.append(entry)
            else:
                other_configs.append(entry)

        # US को प्राथमिकता, फिर बाकी
        all_configs = us_configs + other_configs
        random.shuffle(all_configs)

        count = 0
        for i, config in enumerate(all_configs):
            if count >= max_configs:
                break
            filename = f"config_{count+1}.ovpn"
            with open(filename, "w") as f:
                f.write(config)
            print(f"✅ सेव: {filename}")
            count += 1

        return count

    except Exception as e:
        print(f"❌ VPNGate API error: {e}")
        return 0

if __name__ == "__main__":
    count = fetch_configs(10)
    if count == 0:
        print("❌ कोई कॉन्फ़िग नहीं मिली।")
        sys.exit(1)
    print(f"कुल {count} कॉन्फ़िग सेव हुईं।")
