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
    print("⚠️ IP नहीं बदला, फिर भी आगे बढ़ेंगे।")
    return False

def page_has_bot_message(page):
    try:
        text = page.text_content("*")
        if re.search(r"not a robot|are you a robot|sign in to confirm|you are a bot|robot check", text, re.IGNORECASE):
            return True
    except:
        pass
    try:
        frames = page.frames
        for frame in frames:
            if frame.url != page.url:
                ftext = frame.text_content("*")
                if re.search(r"not a robot|are you a robot|sign in to confirm|you are a bot|robot check", ftext, re.IGNORECASE):
                    return True
    except:
        pass
    return False

def human_like_interaction(page):
    """मोबाइल यूज़र जैसी माउस हरकतें (टच की जगह)"""
    try:
        # पेज पर कहीं हल्का क्लिक (जैसे स्क्रीन टच)
        page.mouse.move(random.randint(50, 350), random.randint(300, 500))
        time.sleep(random.uniform(0.2, 0.5))
        page.mouse.click(random.randint(100, 300), random.randint(400, 600))
        time.sleep(random.uniform(0.2, 0.5))
        # स्क्रॉल (नीचे फिर ऊपर)
        page.mouse.wheel(0, random.randint(200, 400))
        time.sleep(random.uniform(0.2, 0.5))
        page.mouse.wheel(0, -random.randint(50, 150))
        time.sleep(random.uniform(0.1, 0.3))
    except:
        pass

def force_mobile_video_interaction(page):
    """
    YouTube player के अंदर इंसानी हरकतें:
    - अनम्यूट करना
    - क्वालिटी बदलने का नाटक
    """
    try:
        # वीडियो अनम्यूट और क्वालिटी
        page.evaluate("""
            () => {
                const iframes = document.querySelectorAll('iframe[src*="youtube.com/embed"], iframe[src*="youtube-nocookie.com/embed"]');
                for (let iframe of iframes) {
                    try {
                        iframe.contentWindow.postMessage('{"event":"command","func":"unMute","args":""}','*');
                        setTimeout(() => {
                            iframe.contentWindow.postMessage('{"event":"command","func":"setPlaybackQuality","args":"hd720"}','*');
                        }, 3000);
                    } catch(e) {}
                }
            }
        """)
        if random.random() < 0.4:
            time.sleep(5)
            page.evaluate("""
                () => {
                    const iframes = document.querySelectorAll('iframe[src*="youtube.com/embed"], iframe[src*="youtube-nocookie.com/embed"]');
                    for (let iframe of iframes) {
                        try {
                            iframe.contentWindow.postMessage('{"event":"command","func":"setPlaybackQuality","args":"large"}','*');
                        } catch(e) {}
                    }
                }
            """)
    except:
        pass

def run_machine():
    if not VPN_CONFIGS:
        print("❌ कोई VPN config फ़ाइल नहीं!")
        return

    blacklist = load_blacklist()
    available_configs = [cfg for cfg in VPN_CONFIGS if cfg not in blacklist]
    if not available_configs:
        print("❌ सभी configs ब्लैकलिस्ट हो चुकी हैं।")
        return

    random.seed(MACHINE_ID * 1000 + int(time.time()))
    random.shuffle(available_configs)

    print(f"🎰 मशीन {MACHINE_ID} | उपलब्ध IP: {len(available_configs)} | लक्ष्य लूप: {LOOP_COUNT}")

    with sync_playwright() as p:
        # Firefox ब्राउज़र लॉन्च
        browser = p.firefox.launch(headless=False, args=["--no-sandbox"])

        completed_loops = 0
        while completed_loops < LOOP_COUNT:
            if not available_configs:
                print("❌ कोई और usable IP नहीं।")
                break

            config_file = available_configs[0]
            disconnect_vpn()
            if not connect_vpn(config_file):
                blacklist.add(config_file)
                save_blacklist(blacklist)
                available_configs.remove(config_file)
                continue

            # --- महत्वपूर्ण बदलाव: मोबाइल एमुलेशन Firefox में बिना isMobile के ---
            context = browser.new_context(
                viewport={"width": 390, "height": 844},                     # iPhone 14 Pro
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
                ignore_https_errors=True
            )
            page = context.new_page()

            try:
                start_time = time.time()
                page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)
                human_like_interaction(page)
                page.wait_for_timeout(10000)  # वीडियो लोड

                if page_has_bot_message(page):
                    print(f"🚫 Bot पेज मिला! IP: {config_file} ब्लैकलिस्ट कर रहे हैं।")
                    blacklist.add(config_file)
                    save_blacklist(blacklist)
                    available_configs.remove(config_file)
                    continue

                # --- प्ले बटन पर क्लिक (टच की जगह माउस क्लिक) ---
                youtube_frame = page.frame_locator("iframe[src*='youtube.com/embed'], iframe[src*='youtube-nocookie.com/embed']")
                play_btn = youtube_frame.locator("button.ytp-large-play-button, .ytp-cued-thumbnail-overlay")
                if play_btn.count() > 0:
                    play_btn.first.click(timeout=5000)   # .click() सही है
                    print("▶️ प्ले बटन क्लिक किया")
                else:
                    print("▶️ वीडियो शायद ऑटोप्ले हो गई")

                time.sleep(2)
                force_mobile_video_interaction(page)
                human_like_interaction(page)

                # 50 सेकंड पर स्क्रीनशॉट (कुल 60 सेकंड का व्यू)
                wait = 50 - (time.time() - start_time)
                if wait > 0:
                    time.sleep(wait)
                send_screenshot_to_telegram(page,
                    f"🤖 मशीन {MACHINE_ID}\n🔄 लूप: {completed_loops+1}/{LOOP_COUNT}\n📱 मोबाइल UA")

                # 60 सेकंड पूरे करें
                elapsed = time.time() - start_time
                if elapsed < 60:
                    time.sleep(60 - elapsed)

                # अच्छे IP को रीसायकल करें
                available_configs.remove(config_file)
                available_configs.append(config_file)
                completed_loops += 1
                print(f"✅ लूप {completed_loops} सफल (IP: {config_file})")

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
