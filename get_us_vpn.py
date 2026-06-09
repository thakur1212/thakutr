import base64
import requests
import sys
import os

def try_vpngate():
    """VPNGate API से US या कोई भी सर्वर निकालें"""
    print("🔍 VPNGate API से सर्वर ढूँढ रहे हैं...")
    url = "https://www.vpngate.net/api/iphone/"
    try:
        resp = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        resp.encoding = 'utf-8'
        lines = resp.text.strip().split('\n')

        # * और # वाली लाइनें हटाओ (ये headers/comments हैं)
        data_lines = [l for l in lines if l.strip() and not l.startswith('*') and not l.startswith('#')]

        if not data_lines:
            print("⚠️ VPNGate से कोई डेटा नहीं मिला।")
            return None

        # VPNGate CSV columns:
        # 0:HostName, 1:IP, 2:Score, 3:Ping, 4:Speed,
        # 5:CountryLong, 6:CountryShort, 7:NumVpnSessions,
        # 8:Uptime, 9:TotalUsers, 10:TotalTraffic,
        # 11:LogType, 12:Operator, 13:Message,
        # 14:OpenVPN_ConfigData_Base64

        us_configs = []
        all_configs = []

        for line in data_lines:
            parts = line.split(',')
            if len(parts) < 15:
                continue

            country_long = parts[5].strip()
            country_short = parts[6].strip()
            config_b64 = parts[14].strip()

            if not config_b64 or len(config_b64) < 100:
                continue

            try:
                config = base64.b64decode(config_b64).decode('utf-8')
                config = config.replace('\r\n', '\n')
            except:
                continue

            # चेक करें कि config असली है (auth, remote, etc. होना चाहिए)
            if 'remote' not in config:
                continue

            entry = {
                "country": country_long,
                "code": country_short,
                "config": config
            }

            # US चेक (कई नाम हो सकते हैं)
            if any(x in country_long.lower() for x in ['united states', 'us', 'america']):
                us_configs.append(entry)
            
            all_configs.append(entry)

        # पहले US सर्वर दो
        if us_configs:
            print(f"✅ {len(us_configs)} US सर्वर मिले! पहला चुन रहे हैं...")
            return us_configs[0]["config"], us_configs[0]["country"]

        # US नहीं मिला तो कोई भी सर्वर दो
        if all_configs:
            print(f"⚠️ US सर्वर नहीं मिला। {len(all_configs)} कुल सर्वर में से पहला चुन रहे हैं...")
            chosen = all_configs[0]
            print(f"📍 देश: {chosen['country']} ({chosen['code']})")
            return chosen["config"], chosen["country"]

        print("⚠️ VPNGate पर कोई काम करने वाला सर्वर नहीं मिला।")
        return None

    except Exception as e:
        print(f"❌ VPNGate एरर: {e}")
        return None


def try_github_fallback():
    """GitHub से फ्री OpenVPN config download करें"""
    print("🔍 GitHub से फ्री VPN config ढूँढ रहे हैं...")
    
    # कई स्रोत आज़माएँ
    sources = [
        "https://raw.githubusercontent.com/haugene/vpn-configs-contrib/main/openvpn/us.ovpn",
        "https://raw.githubusercontent.com/haugene/vpn-configs-contrib/main/openvpn/US.ovpn",
    ]

    for src in sources:
        try:
            resp = requests.get(src, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200 and 'remote' in resp.text:
                print(f"✅ GitHub से config मिल गई: {src}")
                return resp.text.replace('\r\n', '\n'), "GitHub-US"
        except:
            continue

    print("⚠️ GitHub से भी config नहीं मिली।")
    return None


def main():
    result = None

    # लेयर 1: VPNGate
    result = try_vpngate()

    # लेयर 2: GitHub fallback
    if not result:
        result = try_github_fallback()

    # अगर कुछ भी न मिले
    if not result:
        print("❌ कोई भी VPN config नहीं मिली! कृपया मैन्युअली us.ovpn फ़ाइल रिपो में डालें।")
        sys.exit(1)

    config, country = result
    with open("us.ovpn", "w") as f:
        f.write(config)
    
    print(f"✅ VPN config सेव हो गई! देश: {country}")
    print(f"📄 फ़ाइल साइज़: {len(config)} bytes")


if __name__ == "__main__":
    main()
