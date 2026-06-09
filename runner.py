import sys
import os
import time
import random
import requests
import re
from playwright.sync_api import sync_playwright

TARGET_URL = sys.argv[1]
LOOP_COUNT = int(sys.argv[2])
CHAT_ID = sys.argv[3]
BOT_TOKEN = sys.argv[4]
MACHINE_ID = int(sys.argv[5])

VPN_CONFIGS = sorted(
    [f for f in os.listdir() if f.startswith('config_') and f.endswith('.ovpn')],
    key=lambda x: int(x.split('_')[1].split('.')[0])
)

BLACKLIST_FILE = f"bad_ips_{MACHINE_ID}.txt"   # हर मशीन की अपनी ब्लैकलिस्ट

def load_blacklist():
    if not os.path.exists(BLACKLIST_FILE):
        return set()
    with open(BLACKLIST_FILE) as f:
        return set(line.strip() for line in f if line.strip())

def save_blacklist(black_set):
    with open(BLACKLIST_FILE, "w") as f:
        for item in black_set:
            f.write(item + "\n")

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
    os.system("sudo killall openvpn 2>/dev/null")
    time.sleep(1)

def connect_vpn(config_file):
    print(f"🔌 VPN कनेक्ट: {config_file}")
    os.system(f"sudo openvpn --config {config_file} --daemon --log /tmp/vpn.log")
    old_ip = ""
    try:
        old_ip = requests.get("https://ifconfig.me", timeout=5).text.strip()
    except:
        pass
    for i in range(15):
        time.sleep(2)
        try:
            new_ip = requests.get("https://ifconfig.me", timeout=5).text.strip()
            if new_ip and new_ip != old_ip:
                print(f"✅ नया IP: {new_ip}")
                return True
        except:
            pass
    print("⚠️ IP बदला नहीं, फिर भी आगे बढ़ते हैं।")
    return False

def page_has_bot_message(page):
    try:
        text = page.content().lower()
        if any(x in text for x in ["not a robot", "are you a robot", "sign in to confirm", "you are a bot"]):
            return True
    except:
        pass
    return False

def run_machine():
    if not VPN_CONFIGS:
        print("❌ कोई VPN config फ़ाइल नहीं!")
        return

    blacklist = load_blacklist()
    available_configs = [cfg for cfg in VPN_CONFIGS if cfg not in blacklist]

    if not available_configs:
        print("❌ सभी configs ब्लैकलिस्ट हो चुकी हैं।")
        return

    # हर मशीन के लिए अलग शफ़ल (ताकि पूरी मशीनें एक साथ एक जैसा IP न लें)
    random.seed(MACHINE_ID * 100 + int(time.time()))
    random.shuffle(available_configs)

    total_available = len(available_configs)
    print(f"🎰 मशीन {MACHINE_ID} | उपलब्ध IPs: {total_available} | लक्ष्य लूप: {LOOP_COUNT}")

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False, args=["--no-sandbox"])

        completed_loops = 0
        attempt = 0
        while completed_loops < LOOP_COUNT:
            if not available_configs:
                print("❌ कोई और usable IP नहीं बचा।")
                break

            # हर बार available_configs में से कोशिश करें
            config_file = available_configs[attempt % len(available_configs)]
            disconnect_vpn()
            connect_vpn(config_file)

            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
                ignore_https_errors=True
            )
            page = context.new_page()

            try:
                start_time = time.time()
                page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(10000)

                if page_has_bot_message(page):
                    print(f"🚫 Bot detection! IP: {config_file} ब्लैकलिस्ट में डाल रहे हैं।")
                    blacklist.add(config_file)
                    save_blacklist(blacklist)
                    available_configs.remove(config_file)
                    attempt = 0  # अगली बार शुरू से खोजें
                    continue

                # प्ले बटन क्लिक और फोर्स प्ले (Same as before)
                youtube_frame = page.frame_locator("iframe[src*='youtube.com/embed']")
                play_btn = youtube_frame.locator("button.ytp-large-play-button, .ytp-cued-thumbnail-overlay")
                if play_btn.count() > 0:
                    play_btn.first.hover()
                    page.wait_for_timeout(random.randint(200, 500))
                    play_btn.first.click(timeout=5000)
                    print("▶️ प्ले बटन क्लिक किया")
                else:
                    youtube_frame.locator("body").click()

                time.sleep(2)
                # Force play via JS
                page.evaluate("""() => {
                    const iframes = document.querySelectorAll('iframe[src*="youtube.com/embed"]');
                    for (let iframe of iframes) {
                        try {
                            const video = iframe.contentWindow.document.querySelector('video');
                            if (video && video.paused) video.play();
                        } catch(e) {
                            iframe.contentWindow.postMessage('{"event":"command","func":"playVideo","args":""}','*');
                        }
                    }
                }""")

                elapsed = time.time() - start_time
                if elapsed < 25:
                    time.sleep(25 - elapsed)
                send_screenshot_to_telegram(page,
                    f"🤖 मशीन {MACHINE_ID}\n🔄 लूप: {completed_loops+1}/{LOOP_COUNT}\n🌐 Clean IP")

                elapsed = time.time() - start_time
                if elapsed < 31:
                    time.sleep(31 - elapsed)

                completed_loops += 1
                attempt += 1
                print(f"✅ लूप {completed_loops} पूरा")

            except Exception as e:
                print(f"❌ एरर: {e}")
                try:
                    send_screenshot_to_telegram(page, f"❌ मशीन {MACHINE_ID} एरर: {str(e)[:80]}")
                except:
                    pass
            finally:
                context.close()
                time.sleep(0.5)

        browser.close()
        disconnect_vpn()

if __name__ == "__main__":
    run_machine()
