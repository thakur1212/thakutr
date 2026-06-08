import sys
import os
import time
import random
import requests
from playwright.sync_api import sync_playwright

# इनपुट्स
TARGET_URL = sys.argv[1]
LOOP_COUNT = int(sys.argv[2])
CHAT_ID = sys.argv[3]
BOT_TOKEN = sys.argv[4]
MACHINE_ID = sys.argv[5]

def get_tor_ip():
    """Tor नेटवर्क के ज़रिए करेंट IP पता करने का फंक्शन"""
    proxies = {
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    }
    for url in ["https://api.ipify.org", "https://icanhazip.com", "https://ident.me"]:
        try:
            ip = requests.get(url, proxies=proxies, timeout=10).text.strip()
            return ip
        except:
            continue
    return "Unknown IP"

def send_telegram_msg(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={'chat_id': CHAT_ID, 'text': text})
    except:
        pass

def send_screenshot_to_telegram(page, text_msg):
    screenshot_path = f"ss_{MACHINE_ID}.png"
    try:
        page.screenshot(path=screenshot_path, full_page=True)
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        with open(screenshot_path, 'rb') as photo:
            requests.post(url, files={'photo': photo}, data={'chat_id': CHAT_ID, 'caption': text_msg})
        os.remove(screenshot_path)
    except Exception as e:
        print(f"❌ स्क्रीनशॉट एरर: {e}")

def run_machine():
    print(f"🎰 मशीन {MACHINE_ID} चालू हो रही है...")
    send_telegram_msg(f"🚀 मशीन {MACHINE_ID} चालू! Firefox को Tor Browser बनाया जा रहा है...")
    
    with sync_playwright() as p:
        for i in range(1, LOOP_COUNT + 1):
            browser = None
            context = None
            
            try:
                # 🟢 Playwright Firefox को Tor Proxy के साथ लॉन्च करना
                browser = p.firefox.launch(
                    headless=False,
                    proxy={"server": "socks5://127.0.0.1:9050"},
                    args=["--mute-audio"]
                )
                
                # 🟢 MAGIC: Firefox को असली Tor Browser की पहचान देना
                context = browser.new_context(
                    viewport={"width": 1280, "height": 720},
                    # 1. असली Tor Browser 13.5 का User-Agent
                    user_agent="Mozilla/5.0 (Windows NT 10.0; rv:115.0) Gecko/20100101 Firefox/115.0",
                    # 2. Tor Browser हमेशा UTC टाइम यूज़ करता है (ट्रैकिंग से बचने के लिए)
                    timezone_id="UTC",
                    locale="en-US",
                    ignore_https_errors=True
                )
                
                page = context.new_page()
                
                # 3. Webdriver (Bot) की पहचान मिटाना
                page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """)
                
                print("🌐 वेबसाइट ओपन की जा रही है...")
                page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=90000)
                
                print("⏳ इंसान जैसी एक्टिविटी (Scrolling)...")
                page.wait_for_timeout(3000)
                page.mouse.wheel(0, 500)
                page.wait_for_timeout(2000)
                page.mouse.wheel(0, -300)
                page.wait_for_timeout(5000)
                
                print("🔍 यूट्यूब वीडियो बॉक्स (iframe) ढूँढा जा रहा है...")
                youtube_frame = page.frame_locator("iframe[src*='youtube.com/embed']")
                
                try:
                    play_button = youtube_frame.locator("button.ytp-large-play-button, .ytp-cued-thumbnail-overlay")
                    if play_button.count() > 0:
                        play_button.first.hover()
                        page.wait_for_timeout(random.randint(800, 1500))
                        play_button.first.click(timeout=5000)
                        print("▶️ यूट्यूब वीडियो प्ले हो गया!")
                    else:
                        youtube_frame.locator("body").click()
                        print("▶️ बॉडी क्लिक से प्ले किया गया।")
                except Exception as click_err:
                    print(f"⚠️ प्ले बटन क्लिक एरर: {click_err}")
                
                # 25वें सेकंड पर स्क्रीनशॉट और IP चेक
                page.wait_for_timeout(15000) 
                
                print("🔍 Tor IP चेक की जा रही है...")
                current_ip = get_tor_ip() 
                
                print("📸 स्क्रीनशॉट लिया जा रहा है...")
                # IP एड्रेस के साथ स्क्रीनशॉट भेजना
                caption = f"🧅 मशीन {MACHINE_ID} (True Tor Mode)\n🌍 Tor IP: {current_ip}\n🔄 लूप: {i}/{LOOP_COUNT}\n✅ सक्सेस!"
                send_screenshot_to_telegram(page, caption)
                
                page.wait_for_timeout(6000)
                
            except Exception as e:
                error_msg = str(e)
                print(f"❌ इस लूप में क्रैश हुआ: {error_msg}")
                send_telegram_msg(f"❌ मशीन {MACHINE_ID} में एरर:\n{error_msg[:100]}")
                
            finally:
                if context:
                    try:
                        context.close()
                        browser.close()
                    except:
                        pass
                
            time.sleep(2)

if __name__ == "__main__":
    run_machine()
