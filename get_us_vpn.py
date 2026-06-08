import csv
import io
import base64
import requests
import sys

def fetch_us_config():
    url = "https://www.vpngate.net/api/iphone/"
    try:
        resp = requests.get(url, timeout=30)
        resp.encoding = 'utf-8'
        data = resp.text
        # पहली लाइन में कभी-कभी "*vpn_servers" आदि होता है, उसे हटाएँ
        reader = csv.DictReader(io.StringIO(data))
        for row in reader:
            country = row.get("CountryLong", "")
            if "United States" not in country:
                continue
            # OpenVPN config Base64 encoded होती है
            config_b64 = row.get("OpenVPN_ConfigData_Base64", "")
            if config_b64:
                config = base64.b64decode(config_b64).decode('utf-8')
                # कभी-कभी config में Windows-style \r\n होते हैं, सामान्य करें
                return config.replace('\r\n', '\n')
        print("❌ कोई US सर्वर नहीं मिला।")
        return None
    except Exception as e:
        print(f"❌ VPNGate API error: {e}")
        return None

if __name__ == "__main__":
    config = fetch_us_config()
    if config:
        with open("us.ovpn", "w") as f:
            f.write(config)
        print("✅ US OpenVPN config us.ovpn में सेव हो गई।")
    else:
        sys.exit(1)
