import sys
import os
import time
import random
import subprocess
import requests
from playwright.sync_api import sync_playwright

TARGET_URL = sys.argv[1]
LOOP_COUNT = int(sys.argv[2])
CHAT_ID = sys.argv[3]
BOT_TOKEN = sys.argv[4]
MACHINE_ID = sys.argv[5]

# हमारी सेव की गई config फ़ाइलों की संख्या (get_vpn_configs.py में 10 सेट की है)
TOTAL_VPN_CONFIGS = 10

def send_screenshot_to_telegram(page, text_msg):
    screenshot_path = f"ss_{MACHINE_ID}.png"
    try:
        page.screenshot(path=screenshot_path, full_page=True)
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        with open(screenshot_path, 'rb') as photo:
            files = {'photo': photo}
            data = {'chat_id': CHAT_ID, 'caption': text_msg}
            requests.post(url, files=files, data=data)
        os.remove(screenshot_path)
        print(f"📸 स्क्रीनशॉट भेजा")
    except Exception as e:
        print(f"❌ स्क्रीनशॉट एरर: {e}")

def disconnect_vpn():
    """पुरानी OpenVPN प्रक्रिया को मारें"""
    os.system("sudo killall openvpn 2>/dev/null")
    time.sleep(2)

def connect_vpn(config_file):
    """नई OpenVPN कॉन्फ़िग से कनेक्ट करें और IP चेंज होने का इंतज़ार करें"""
    print(f"🔌 VPN कनेक्ट कर रहे हैं: {config_file}")
    cmd = f"sudo openvpn --config {config_file} --daemon --log /tmp/vpn.log"
    os.system(cmd)
    # इंतज़ार करें कि IP बदल जाए
    original_ip = ""
    try:
        original_ip = requests.get("https://ifconfig.me", timeout=5).text.strip()
    except:
        pass
    for i in range(20):
        time.sleep(2)
        try:
            current_ip = requests.get("https://ifconfig.me", timeout=5).text.strip()
            if current_ip != original_ip and current_ip:
                print(f"✅ VPN कनेक्ट! New IP: {current_ip}")
                return True
        except:
            pass
    print("⚠️ IP बदल नहीं पाया, फिर भी जारी रखते हैं।")
    return False

def run_machine():
    print(f"🎰 मशीन {MACHINE_ID} (Dynamic VPN) | लूप्स: {LOOP_COUNT}")

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False, args=["--no-sandbox"])

        for i in range(1, LOOP_COUNT + 1):
            print(f"\n--- मशीन {MACHINE_ID} | लूप {i}/{LOOP_COUNT} ---")

            # VPN कनेक्शन बदलें (हर 3 लूप में, या जब लूप नंबर 1 हो)
            if i == 1 or i % 3 == 0:
                disconnect_vpn()
                # config फ़ाइल साइकल करें (1 से 10)
                config_num = ((i-1) % TOTAL_VPN_CONFIGS) + 1
                config_file = f"config_{config_num}.ovpn"
                if not os.path.exists(config_file):
                    # फ़ॉलबैक: कोई भी config लें
                    existing = [f for f in os.listdir() if f.startswith('config_') and f.endswith('.ovpn')]
                    if existing:
                        config_file = existing[0]
                    else:
                        print("❌ कोई VPN config नहीं मिली!")
                        break
                connect_vpn(config_file)

            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
                ignore_https_errors=True
            )
            page = context.new_page()

            try:
                start_time = time.time()
                print("🌐 पेज लोड...")
                page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)

                print("⏳ 10 सेकंड इंतज़ार...")
                page.wait_for_timeout(10000)

                print("🔍 प्ले बटन ढूँढ रहा हूँ...")
                youtube_frame = page.frame_locator("iframe[src*='youtube.com/embed']")
                play_btn = youtube_frame.locator("button.ytp-large-play-button, .ytp-cued-thumbnail-overlay")
                if play_btn.count() > 0:
                    play_btn.first.hover()
                    page.wait_for_timeout(500)
                    play_btn.first.click(timeout=5000)
                    print("▶️ क्लिक किया!")
                else:
                    youtube_frame.locator("body").click()

                # 25 सेकंड पर स्क्रीनशॉट
                elapsed = time.time() - start_time
                if elapsed < 25:
                    time.sleep(25 - elapsed)
                send_screenshot_to_telegram(page, f"🤖 मशीन {MACHINE_ID}\n🔄 लूप: {i}/{LOOP_COUNT}\n🌐 Dynamic VPN")

                # 31 सेकंड पूरे करें
                elapsed = time.time() - start_time
                if elapsed < 31:
                    time.sleep(31 - elapsed)
                print("🔒 लूप समाप्त")

            except Exception as e:
                print(f"❌ एरर: {e}")
                try:
                    send_screenshot_to_telegram(page, f"❌ मशीन {MACHINE_ID} एरर: {str(e)[:80]}")
                except:
                    pass
            finally:
                context.close()
                time.sleep(1)

        browser.close()
        disconnect_vpn()

if __name__ == "__main__":
    # VPN config फ़ाइलों की मौजूदगी चेक करें
    if not any(f.startswith('config_') for f in os.listdir('.')):
        print("❌ कोई VPN config फ़ाइल नहीं! पहले get_vpn_configs.py चलाएँ।")
        sys.exit(1)
    run_machine()
