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
MACHINE_ID = int(sys.argv[5])   # integer

# सभी मौजूद config फ़ाइलें (config_1.ovpn, ... config_N.ovpn)
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
    """चेक करें कि पेज पर 'not a robot' जैसा कुछ तो नहीं है"""
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

    total_configs = len(VPN_CONFIGS)
    print(f"🎰 मशीन {MACHINE_ID} | Total VPNs: {total_configs} | लूप्स: {LOOP_COUNT}")

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False, args=["--no-sandbox"])

        completed_loops = 0
        attempts = 0
        while completed_loops < LOOP_COUNT:
            # हर लूप की शुरुआत से पहले VPN बदलें
            disconnect_vpn()
            # मशीन के हिसाब से config इंडेक्स: (MACHINE_ID * 100 + completed_loops) % total_configs
            config_idx = (MACHINE_ID * 100 + completed_loops) % total_configs
            config_file = VPN_CONFIGS[config_idx]
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

                # 10 सेकंड इंतज़ार (वीडियो प्लेयर तैयार)
                page.wait_for_timeout(10000)

                # बॉट डिटेक्शन चेक करें
                if page_has_bot_message(page):
                    print("🚫 'You are a robot' पेज मिला! लूप स्किप कर रहे हैं और नया IP लेंगे।")
                    context.close()
                    continue   # retry नहीं, skipped loop (अगले attempt में नया IP होगा)

                # प्ले बटन खोजें और क्लिक करें
                youtube_frame = page.frame_locator("iframe[src*='youtube.com/embed']")
                play_btn = youtube_frame.locator("button.ytp-large-play-button, .ytp-cued-thumbnail-overlay")
                if play_btn.count() > 0:
                    play_btn.first.hover()
                    page.wait_for_timeout(random.randint(200, 500))
                    play_btn.first.click(timeout=5000)
                    print("▶️ प्ले बटन क्लिक किया")
                else:
                    youtube_frame.locator("body").click()

                # वीडियो चल रही है यह सुनिश्चित करें (JS से check/play)
                time.sleep(2)
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
                    page.evaluate("""() => {
                        const iframes = document.querySelectorAll('iframe[src*="youtube.com/embed"]');
                        for (let iframe of iframes) {
                            try {
                                const video = iframe.contentWindow.document.querySelector('video');
                                if (video) video.play();
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
                    f"🤖 मशीन {MACHINE_ID}\n🔄 लूप: {completed_loops+1}/{LOOP_COUNT}\n🌐 IP: fresh")

                # 31 सेकंड पूरे करें
                elapsed = time.time() - start_time
                if elapsed < 31:
                    time.sleep(31 - elapsed)

                completed_loops += 1
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
