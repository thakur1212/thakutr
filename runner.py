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
    for i in range(20):  # थोड़ा और इंतज़ार
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
    """पूरे पेज का टेक्स्ट चेक करें कि कहीं 'not a robot' जैसा कुछ तो नहीं"""
    try:
        text = page.text_content("*")  # सारा टेक्स्ट निकालें
        if re.search(r"not a robot|are you a robot|sign in to confirm|you are a bot|robot check", text, re.IGNORECASE):
            return True
    except:
        pass
    # कभी-कभी iframe के अंदर हो सकता है
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

def human_behavior(page):
    """पेज पर असली इंसान जैसी हरकतें"""
    try:
        # माउस को कुछ जगहों पर ले जाएँ
        for _ in range(random.randint(1, 3)):
            page.mouse.move(random.randint(100, 1100), random.randint(100, 600))
            time.sleep(random.uniform(0.2, 0.6))
        # थोड़ा स्क्रॉल
        page.mouse.wheel(0, random.randint(100, 400))
        time.sleep(random.uniform(0.2, 0.5))
        page.mouse.wheel(0, -random.randint(50, 200))
        time.sleep(random.uniform(0.1, 0.3))
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

    # हर मशीन के लिए अलग शफ़ल
    random.seed(MACHINE_ID * 1000 + int(time.time()))
    random.shuffle(available_configs)

    print(f"🎰 मशीन {MACHINE_ID} | उपलब्ध IP: {len(available_configs)} | लक्ष्य लूप: {LOOP_COUNT}")

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False, args=["--no-sandbox"])

        completed_loops = 0
        while completed_loops < LOOP_COUNT:
            if not available_configs:
                print("❌ कोई और usable IP नहीं।")
                break

            # अगला IP चुनें (हर बार अलग)
            config_file = available_configs[0]
            disconnect_vpn()
            if not connect_vpn(config_file):
                # VPN नहीं जुड़ा तो इस config को ब्लैकलिस्ट करके अगली बार चुनें
                blacklist.add(config_file)
                save_blacklist(blacklist)
                available_configs.remove(config_file)
                continue

            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
                ignore_https_errors=True
            )
            page = context.new_page()

            try:
                start_time = time.time()
                page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)
                # इंसानी हरकतें
                human_behavior(page)
                # 10 सेकंड इंतज़ार (वीडियो प्लेयर के लिए)
                page.wait_for_timeout(10000)
                human_behavior(page)

                # ----- बॉट डिटेक्शन चेक -----
                if page_has_bot_message(page):
                    print(f"🚫 Bot पेज मिला! IP: {config_file} ब्लैकलिस्ट कर रहे हैं।")
                    blacklist.add(config_file)
                    save_blacklist(blacklist)
                    available_configs.remove(config_file)
                    # दोबारा कोशिश करने के लिए continue (लूप काउंट न बढ़े)
                    continue

                # यूट्यूब प्ले बटन क्लिक
                youtube_frame = page.frame_locator("iframe[src*='youtube.com/embed']")
                play_btn = youtube_frame.locator("button.ytp-large-play-button, .ytp-cued-thumbnail-overlay")
                if play_btn.count() > 0:
                    play_btn.first.hover()
                    page.wait_for_timeout(random.randint(200, 600))
                    play_btn.first.click(timeout=5000)
                    print("▶️ प्ले बटन क्लिक")
                else:
                    youtube_frame.locator("body").click()

                # वीडियो चलाने की पुख्ता कोशिश (JS)
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

                # 25 सेकंड पर स्क्रीनशॉट
                elapsed = time.time() - start_time
                if elapsed < 25:
                    time.sleep(25 - elapsed)
                send_screenshot_to_telegram(page,
                    f"🤖 मशीन {MACHINE_ID}\n🔄 लूप: {completed_loops+1}/{LOOP_COUNT}\nIP: clean")

                # 31 सेकंड पूरे करें
                elapsed = time.time() - start_time
                if elapsed < 31:
                    time.sleep(31 - elapsed)

                # इस IP ने अच्छा काम किया, इसे लिस्ट से हटाकर अंत में डाल दें (ताकि दोबारा इस्तेमाल हो सके)
                available_configs.remove(config_file)
                available_configs.append(config_file)  # अच्छे IP को रिपीट करने के लिए
                completed_loops += 1
                print(f"✅ लूप {completed_loops} सफल")

            except Exception as e:
                print(f"❌ एरर: {e}")
                try:
                    send_screenshot_to_telegram(page, f"❌ मशीन {MACHINE_ID} एरर: {str(e)[:80]}")
                except:
                    pass
                # एरर आने पर भी IP बदलेंगे
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
