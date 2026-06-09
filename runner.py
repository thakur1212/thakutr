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

# मौजूदा config फ़ाइलों की सूची (हम मानते हैं कि config_1.ovpn ... config_N.ovpn मौजूद हैं)
VPN_CONFIGS = sorted(
    [f for f in os.listdir() if f.startswith('config_') and f.endswith('.ovpn')],
    key=lambda x: int(x.split('_')[1].split('.')[0])
)

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
    # IP बदलने का इंतज़ार
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
    print("⚠️ IP नहीं बदला, फिर भी चलाते हैं।")
    return False

def human_touch(page):
    """पेज पर माउस हिलाएँ, स्क्रॉल करें"""
    try:
        page.mouse.move(random.randint(100, 900), random.randint(100, 500))
        time.sleep(random.uniform(0.3, 0.8))
        page.mouse.wheel(0, random.randint(100, 300))
        time.sleep(random.uniform(0.2, 0.5))
    except:
        pass

def run_machine():
    print(f"🎰 मशीन {MACHINE_ID} (Per‑Loop VPN + Anti‑Detect) | लूप्स: {LOOP_COUNT}")

    if not VPN_CONFIGS:
        print("❌ कोई VPN config फ़ाइल नहीं मिली!")
        return

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False, args=["--no-sandbox"])

        for i in range(1, LOOP_COUNT + 1):
            print(f"\n--- मशीन {MACHINE_ID} | लूप {i}/{LOOP_COUNT} ---")

            # हर लूप से पहले VPN बदलें
            disconnect_vpn()
            config_file = VPN_CONFIGS[(i-1) % len(VPN_CONFIGS)]
            connect_vpn(config_file)

            # नया कॉन्टेक्स्ट (पिछली कुकीज़/स्टोरेज साफ़)
            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
                ignore_https_errors=True
            )
            page = context.new_page()

            try:
                start_time = time.time()

                # 1. साइट खोलें
                print("🌐 पेज लोड...")
                page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)
                human_touch(page)

                # 2. 10 सेकंड रुकें (वीडियो प्लेयर तैयार होने के लिए)
                print("⏳ 10 सेकंड इंतज़ार...")
                page.wait_for_timeout(10000)
                human_touch(page)

                # 3. प्ले बटन क्लिक
                print("🔍 प्ले बटन ढूँढ रहा हूँ...")
                youtube_frame = page.frame_locator("iframe[src*='youtube.com/embed']")
                play_btn = youtube_frame.locator("button.ytp-large-play-button, .ytp-cued-thumbnail-overlay")
                clicked = False
                if play_btn.count() > 0:
                    play_btn.first.hover()
                    page.wait_for_timeout(random.randint(200, 500))
                    play_btn.first.click(timeout=5000)
                    print("▶️ बटन क्लिक किया!")
                    clicked = True
                else:
                    youtube_frame.locator("body").click()

                # 4. वीडियो चल रही है या नहीं, चेक करें, न चल रही हो तो JS से प्ले कराएँ
                time.sleep(2)  # क्लिक के बाद थोड़ा इंतज़ार
                playing = page.evaluate("""() => {
                    const iframes = document.querySelectorAll('iframe[src*="youtube.com/embed"]');
                    for (let iframe of iframes) {
                        try {
                            const video = iframe.contentWindow.document.querySelector('video');
                            if (video && video.currentTime > 0 && !video.paused) return true;
                        } catch(e) {}
                    }
                    return false;
                }""")
                
                if not playing:
                    print("⚠️ वीडियो नहीं चली, फोर्स प्ले कर रहा हूँ...")
                    try:
                        page.evaluate("""
                            () => {
                                const iframes = document.querySelectorAll('iframe[src*="youtube.com/embed"]');
                                for (let iframe of iframes) {
                                    try {
                                        const video = iframe.contentWindow.document.querySelector('video');
                                        if (video) video.play();
                                    } catch(e) {
                                        iframe.contentWindow.postMessage('{"event":"command","func":"playVideo","args":""}', '*');
                                    }
                                }
                            }
                        """)
                    except:
                        pass

                # 5. 25 सेकंड पर स्क्रीनशॉट
                elapsed = time.time() - start_time
                if elapsed < 25:
                    time.sleep(25 - elapsed)
                send_screenshot_to_telegram(page,
                    f"🤖 मशीन {MACHINE_ID}\n🔄 लूप: {i}/{LOOP_COUNT}\n🌐 नया IP हर बार")

                # 6. 31 सेकंड पूरे करें
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
                time.sleep(0.5)

        browser.close()
        disconnect_vpn()

if __name__ == "__main__":
    run_machine()
