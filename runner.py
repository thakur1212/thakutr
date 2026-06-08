import sys
import os
import time
import random
import requests
from playwright.sync_api import sync_playwright

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
    print(f"🎰 मशीन {MACHINE_ID} (VPN मोड) | लूप्स: {LOOP_COUNT}")

    with sync_playwright() as p:
        browser = p.firefox.launch(
            headless=False,
            args=["--no-sandbox"]
        )

        for i in range(1, LOOP_COUNT + 1):
            print(f"\n--- मशीन {MACHINE_ID} | लूप {i}/{LOOP_COUNT} ---")
            # सीधा सादा context, कोई प्रॉक्सी नहीं
            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
                ignore_https_errors=True
            )
            page = context.new_page()

            try:
                start_time = time.time()
                print("🌐 पेज लोड हो रहा है...")
                page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)
                time.sleep(random.uniform(2, 5))

                print("▶️ वीडियो प्ले कर रहा हूँ (JS)...")
                try:
                    page.evaluate("""
                        async () => {
                            const iframes = document.querySelectorAll('iframe[src*="youtube.com/embed"]');
                            for (let iframe of iframes) {
                                try {
                                    const video = iframe.contentWindow.document.querySelector('video');
                                    if (video) {
                                        await video.play();
                                        return 'played';
                                    }
                                } catch(e) {
                                    iframe.contentWindow.postMessage('{"event":"command","func":"playVideo","args":""}', '*');
                                }
                            }
                        }
                    """)
                except:
                    pass

                # 25 सेकंड पर स्क्रीनशॉट
                elapsed = time.time() - start_time
                if elapsed < 25:
                    time.sleep(25 - elapsed)
                send_screenshot_to_telegram(page, f"🤖 मशीन {MACHINE_ID}\n🔄 लूप: {i}/{LOOP_COUNT}\n🌐 VPN (OpenVPN)")

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

if __name__ == "__main__":
    run_machine()
