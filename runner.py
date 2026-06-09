import sys
import os
import time
import random
import requests
from playwright.sync_api import sync_playwright

# इनपुट
TARGET_URL = sys.argv[1]
LOOP_COUNT = int(sys.argv[2])
CHAT_ID = sys.argv[3]
BOT_TOKEN = sys.argv[4]
MACHINE_ID = sys.argv[5]

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
        print(f"📸 मशीन {MACHINE_ID} का स्क्रीनशॉट भेजा")
    except Exception as e:
        print(f"❌ स्क्रीनशॉट एरर: {e}")

def run_machine():
    print(f"🎰 मशीन {MACHINE_ID} (VPN + प्ले बटन क्लिक) | लूप्स: {LOOP_COUNT}")

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False, args=["--no-sandbox"])

        for i in range(1, LOOP_COUNT + 1):
            print(f"\n--- मशीन {MACHINE_ID} | लूप {i}/{LOOP_COUNT} ---")
            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
                ignore_https_errors=True
            )
            page = context.new_page()

            try:
                start_time = time.time()

                # 1. वेबसाइट खोलें
                print("🌐 पेज लोड हो रहा है...")
                page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)

                # 2. ठीक 10 सेकंड इंतज़ार (जैसा आपने कहा)
                print("⏳ 10 सेकंड का इंतज़ार...")
                page.wait_for_timeout(10000)

                # 3. यूट्यूब iframe में जाकर बड़े प्ले बटन पर क्लिक करें
                print("🔍 यूट्यूब प्ले बटन ढूँढ रहा हूँ...")
                youtube_frame = page.frame_locator("iframe[src*='youtube.com/embed']")
                
                # बड़ा प्ले बटन (लाल/काला तीर वाला)
                play_button = youtube_frame.locator("button.ytp-large-play-button, .ytp-cued-thumbnail-overlay")
                
                if play_button.count() > 0:
                    play_button.first.hover()
                    page.wait_for_timeout(500)  # hover effect के लिए
                    play_button.first.click(timeout=5000)
                    print("▶️ प्ले बटन पर क्लिक किया!")
                else:
                    # अगर बटन न मिले तो बॉडी पर क्लिक (कभी-कभी यूट्यूब ऑटोप्ले नहीं होता)
                    print("⚠️ बटन नहीं मिला, बॉडी पर क्लिक कर रहा हूँ...")
                    youtube_frame.locator("body").click()

                # 4. अब 25वें सेकंड तक इंतज़ार (10 सेकंड पहले हो चुके हैं, 15 और रुकें)
                wait_until_25 = max(0, 25 - (time.time() - start_time))
                time.sleep(wait_until_25)
                send_screenshot_to_telegram(
                    page,
                    f"🤖 मशीन {MACHINE_ID}\n🔄 लूप: {i}/{LOOP_COUNT}\n▶️ प्ले बटन क्लिक किया"
                )

                # 5. 31 सेकंड पूरे करें
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

if __name__ == "__main__":
    run_machine()
