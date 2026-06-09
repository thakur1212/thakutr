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
BLACKLIST_FILE = f"bad_ips_{MACHINE_ID}.txt"

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
        print("📸 स्क्रीनशॉट भेजा")
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
    for i in range(20):
        time.sleep(2)
        try:
            new_ip = requests.get("https://ifconfig.me", timeout=5).text.strip()
            if new_ip and new_ip != old_ip:
                print(f"✅ IP बदला: {new_ip}")
                return True
        except:
            pass
    print("⚠️ IP नहीं बदला, पर आगे बढ़ते हैं।")
    return False

def page_has_bot_message(page):
    try:
        text = page.text_content("*")
        if re.search(r"not a robot|are you a robot|sign in to confirm|you are a bot|robot check", text, re.IGNORECASE):
            return True
    except:
        pass
    try:
        for frame in page.frames:
            if frame.url != page.url:
                ftext = frame.text_content("*")
                if re.search(r"not a robot|are you a robot|sign in to confirm|you are a bot|robot check", ftext, re.IGNORECASE):
                    return True
    except:
        pass
    return False

def human_touch_mobile(page):
    """मोबाइल डिवाइस पर इंसानी हरकतें (टैप, स्क्रॉल, स्वाइप)"""
    try:
        # कुछ टैप
        for _ in range(random.randint(1, 3)):
            x = random.randint(50, 300)
            y = random.randint(100, 700)
            page.tap({"x": x, "y": y})
            time.sleep(random.uniform(0.2, 0.5))
        # स्क्रॉल
        for _ in range(random.randint(1, 4)):
            page.mouse.wheel(0, random.randint(200, 600))
            time.sleep(random.uniform(0.3, 0.8))
        # स्वाइप (टच ड्रैग)
        page.mouse.move(random.randint(100, 300), random.randint(400, 600))
        page.mouse.down()
        page.mouse.move(random.randint(100, 300), random.randint(100, 300), steps=10)
        page.mouse.up()
    except:
        pass

def run_machine():
    if not VPN_CONFIGS:
        print("❌ कोई VPN config नहीं!")
        return

    blacklist = load_blacklist()
    available_configs = [cfg for cfg in VPN_CONFIGS if cfg not in blacklist]
    if not available_configs:
        print("❌ सभी configs ब्लैकलिस्ट हो चुकी हैं।")
        return

    random.seed(MACHINE_ID * 1000 + int(time.time()))
    random.shuffle(available_configs)

    print(f"🎰 मशीन {MACHINE_ID} | लक्ष्य लूप: {LOOP_COUNT} | उपलब्ध IP: {len(available_configs)}")

    with sync_playwright() as p:
        # मोबाइल ब्राउज़र (iPhone 14 Pro)
        browser = p.firefox.launch(headless=False, args=["--no-sandbox"])

        completed_loops = 0
        while completed_loops < LOOP_COUNT:
            if not available_configs:
                print("❌ और कोई IP नहीं बचा।")
                break

            config_file = available_configs[0]
            disconnect_vpn()
            if not connect_vpn(config_file):
                blacklist.add(config_file)
                save_blacklist(blacklist)
                available_configs.remove(config_file)
                continue

            # मोबाइल कॉन्टेक्स्ट
            context = browser.new_context(
                viewport={"width": 390, "height": 844},
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
                is_mobile=True,
                has_touch=True,
                ignore_https_errors=True
            )
            page = context.new_page()

            try:
                start_time = time.time()
                page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)
                human_touch_mobile(page)

                # 10 सेकंड इंतज़ार (वीडियो प्लेयर)
                page.wait_for_timeout(10000)
                human_touch_mobile(page)

                # बॉट चेक
                if page_has_bot_message(page):
                    print(f"🚫 Bot पेज! IP ब्लैकलिस्ट: {config_file}")
                    blacklist.add(config_file)
                    save_blacklist(blacklist)
                    available_configs.remove(config_file)
                    continue

                # यूट्यूब प्ले बटन क्लिक
                youtube_frame = page.frame_locator("iframe[src*='youtube.com/embed']")
                play_btn = youtube_frame.locator("button.ytp-large-play-button, .ytp-cued-thumbnail-overlay")
                if play_btn.count() > 0:
                    play_btn.first.tap()  # टैप का उपयोग करें
                    print("▶️ प्ले बटन टैप किया")
                else:
                    youtube_frame.locator("body").tap()

                # वीडियो प्ले होना सुनिश्चित करें
                time.sleep(2)
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

                # 30 सेकंड पर स्क्रीनशॉट (ताकि वीडियो चलती दिखे)
                elapsed = time.time() - start_time
                if elapsed < 30:
                    time.sleep(30 - elapsed)
                send_screenshot_to_telegram(page,
                    f"🤖 मशीन {MACHINE_ID}\n🔄 लूप: {completed_loops+1}/{LOOP_COUNT}\n📱 मोबाइल व्यू")

                # कुल 60 सेकंड पूरे करें (यूट्यूब व्यू काउंट के लिए)
                elapsed = time.time() - start_time
                if elapsed < 60:
                    time.sleep(60 - elapsed)

                # अच्छे IP को फिर से उपयोग के लिए वापस डालें
                available_configs.remove(config_file)
                available_configs.append(config_file)
                completed_loops += 1
                print(f"✅ लूप {completed_loops} सफल (60s व्यू)")

            except Exception as e:
                print(f"❌ एरर: {e}")
                try:
                    send_screenshot_to_telegram(page, f"❌ मशीन {MACHINE_ID} एरर: {str(e)[:80]}")
                except:
                    pass
                blacklist.add(config_file)
                save_blacklist(blacklist)
                available_configs.remove(config_file)
            finally:
                context.close()
                time.sleep(0.5)

        browser.close()
        disconnect_vpn()

if __name__ == "__main__":
    run_machine()
