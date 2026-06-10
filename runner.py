import sys
import os
import time
import random
import requests
import re
from playwright.sync_api import sync_playwright

TARGET_URL = sys.argv[1]          # YouTube वीडियो या Shorts का सीधा URL
TOTAL_VIEWS = int(sys.argv[2])    # प्रति मशीन कुल व्यू
CHAT_ID = sys.argv[3]
BOT_TOKEN = sys.argv[4]
MACHINE_ID = int(sys.argv[5])

TABS_PER_LOOP = 20                # हर लूप में 20 टैब

VPN_CONFIGS = sorted(
    [f for f in os.listdir() if f.startswith('config_') and f.endswith('.ovpn')],
    key=lambda x: int(x.split('_')[1].split('.')[0])
)
BLACKLIST_FILE = f"bad_ips_{MACHINE_ID}.txt"

# पहचानें कि क्या यह Shorts लिंक है
IS_SHORTS = "/shorts/" in TARGET_URL

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
    screenshot_path = f"ss_{MACHINE_ID}_{random.randint(1000,9999)}.png"
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
    # ✅ 30 बार कोशिश (पहले 20 था) → ज़्यादा समय लेकिन भरोसेमंद
    for i in range(30):
        time.sleep(2)
        try:
            new_ip = requests.get("https://ifconfig.me", timeout=5).text.strip()
            if new_ip and new_ip != old_ip:
                print(f"✅ IP बदला: {new_ip}")
                return new_ip
        except:
            pass
    print("⚠️ IP नहीं बदला, फिर भी आगे बढ़ेंगे।")
    return "Unknown"

def page_has_bot_message(page):
    try:
        text = page.text_content("*")
        if re.search(r"not a robot|are you a robot|sign in to confirm|you are a bot|robot check", text, re.IGNORECASE):
            return True
    except:
        pass
    return False

def only_scroll_and_move(page):
    """बिना क्लिक के माउस हिलाएँ और स्क्रॉल करें"""
    try:
        if IS_SHORTS:
            # Shorts पेज पर हल्का स्वाइप जैसा मूवमेंट
            page.mouse.move(random.randint(200, 600), random.randint(400, 800))
            time.sleep(random.uniform(0.2, 0.4))
            page.mouse.wheel(0, random.randint(30, 80))
            time.sleep(random.uniform(0.1, 0.3))
            page.mouse.wheel(0, -random.randint(20, 50))
        else:
            page.mouse.move(random.randint(100, 700), random.randint(200, 800))
            time.sleep(random.uniform(0.2, 0.5))
            page.mouse.wheel(0, random.randint(200, 500))
            time.sleep(random.uniform(0.2, 0.5))
            page.mouse.wheel(0, -random.randint(100, 300))
    except:
        pass

def perform_engagement_actions(page):
    try:
        if IS_SHORTS:
            if random.random() < 0.4:
                try:
                    page.evaluate("""
                        () => {
                            const video = document.querySelector('video');
                            if (video) video.volume = 0.7;
                        }
                    """)
                except:
                    pass
            page.mouse.move(random.randint(200, 600), random.randint(600, 800))
            time.sleep(random.uniform(0.1, 0.3))
        else:
            if random.random() < 0.2:
                seek_time = random.randint(10, 40)
                page.evaluate(f"""
                    () => {{
                        const video = document.querySelector('video');
                        if (video) {{ video.currentTime = {seek_time}; video.play(); }}
                    }}
                """)
                time.sleep(random.uniform(1, 2))
            if random.random() < 0.3:
                new_vol = random.randint(30, 100)
                page.evaluate(f"""
                    () => {{
                        const video = document.querySelector('video');
                        if (video) video.volume = {new_vol/100};
                    }}
                """)
            if random.random() < 0.25:
                page.evaluate("""
                    () => {
                        const video = document.querySelector('video');
                        if (video) video.pause();
                    }
                """)
                time.sleep(random.uniform(2, 4))
                page.evaluate("""
                    () => {
                        const video = document.querySelector('video');
                        if (video) video.play();
                    }
                """)
            if random.random() < 0.15:
                page.keyboard.press("f")
                time.sleep(random.uniform(3, 5))
                page.keyboard.press("f")
            page.mouse.wheel(0, 600)
            time.sleep(random.uniform(1, 2))
            page.mouse.wheel(0, -400)
    except Exception as e:
        print(f"⚠️ इंगेजमेंट एरर: {e}")

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

    total_tabs = TOTAL_VIEWS
    completed_tabs = 0
    video_type = "Shorts" if IS_SHORTS else "Normal"
    print(f"🎰 मशीन {MACHINE_ID} | {video_type} | कुल व्यू: {total_tabs} | प्रति लूप {TABS_PER_LOOP} टैब")

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False, args=["--no-sandbox"])

        while completed_tabs < total_tabs:
            tabs_this_loop = min(TABS_PER_LOOP, total_tabs - completed_tabs)

            for _ in range(tabs_this_loop):
                if not available_configs:
                    print("❌ IP खत्म।")
                    break

                config_file = available_configs.pop(0)
                disconnect_vpn()
                current_ip = connect_vpn(config_file)
                if current_ip == "Unknown":
                    blacklist.add(config_file)
                    save_blacklist(blacklist)
                    continue

                context = browser.new_context(
                    viewport={"width": 820, "height": 1180},
                    user_agent="Mozilla/5.0 (iPad; CPU OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
                    ignore_https_errors=True
                )
                page = context.new_page()

                try:
                    start_time = time.time()
                    # ✅ टाइमआउट 60 सेकंड (पहले 30 था)
                    page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)
                    only_scroll_and_move(page)
                    page.wait_for_timeout(19000)
                    only_scroll_and_move(page)

                    if page_has_bot_message(page):
                        print(f"🚫 Bot पेज! IP: {current_ip} ब्लैकलिस्ट।")
                        blacklist.add(config_file)
                        save_blacklist(blacklist)
                        continue

                    if IS_SHORTS:
                        page.mouse.click(410, 600)
                        print("▶️ Shorts पर क्लिक")
                    else:
                        page.mouse.click(410, 300)
                        print("▶️ 19 सेकंड पर क्लिक (सामान्य वीडियो)")

                    time.sleep(2)
                    perform_engagement_actions(page)

                    if not IS_SHORTS:
                        time.sleep(30 - 2)
                        perform_engagement_actions(page)

                    # 55 सेकंड पर स्क्रीनशॉट
                    wait_55 = 55 - (time.time() - start_time)
                    if wait_55 > 0:
                        time.sleep(wait_55)
                    caption = (
                        f"🤖 मशीन {MACHINE_ID}\n"
                        f"📊 व्यू: {completed_tabs+1}/{total_tabs}\n"
                        f"🌐 IP: {current_ip}\n"
                        f"📟 {video_type} • रीच बूस्ट"
                    )
                    send_screenshot_to_telegram(page, caption)

                    # 60 सेकंड पूरे करें
                    elapsed = time.time() - start_time
                    if elapsed < 60:
                        time.sleep(60 - elapsed)

                    completed_tabs += 1
                    print(f"✅ व्यू {completed_tabs} सफल (IP: {current_ip})")
                    available_configs.append(config_file)

                except Exception as e:
                    print(f"❌ एरर: {e}")
                    try:
                        send_screenshot_to_telegram(page, f"❌ मशीन {MACHINE_ID} एरर: {str(e)[:80]}")
                    except:
                        pass
                    blacklist.add(config_file)
                    save_blacklist(blacklist)
                finally:
                    context.close()
                    time.sleep(2)

            # एक लूप के बाद 5 सेकंड गैप
            time.sleep(5)

        browser.close()
        disconnect_vpn()

if __name__ == "__main__":
    run_machine()
