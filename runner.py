import sys
import os
import time
import requests
from playwright.sync_api import sync_playwright

# इनपुट्स रीड करना
TARGET_URL = sys.argv[1]
LOOP_COUNT = int(sys.argv[2])
CHAT_ID = sys.argv[3]
BOT_TOKEN = sys.argv[4]
MACHINE_ID = sys.argv[5]

def send_screenshot_to_telegram(page, text_msg):
    screenshot_path = f"ss_{MACHINE_ID}.png"
    try:
        page.screenshot(path=screenshot_path)
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        with open(screenshot_path, 'rb') as photo:
            files = {'photo': photo}
            data = {'chat_id': CHAT_ID, 'caption': text_msg}
            requests.post(url, files=files, data=data)
        os.remove(screenshot_path)
        print(f"📸 मशीन {MACHINE_ID}: स्क्रीनशॉट भेज दिया गया है।")
    except Exception as e:
        print(f"❌ स्क्रीनशॉट भेजने में एरर: {e}")

def run_machine():
    print(f"🎰 मशीन {MACHINE_ID} चालू हो रही है। कुल टारगेट: {LOOP_COUNT} लूप्स")
    
    with sync_playwright() as p:
        for i in range(1, LOOP_COUNT + 1):
            print(f"\n--- मशीन {MACHINE_ID} | लूप {i}/{LOOP_COUNT} ---")
            
            try:
                browser = p.chromium.launch(
                    headless=True,
                    args=["--mute-audio", "--no-sandbox", "--disable-setuid-sandbox"]
                )
                
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 720}
                )
                page = context.new_page()
                
                # बोट डिटेक्शन छुपाना
                page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """)
                
                start_time = time.time()
                
                print("🌐 वेबसाइट ओपन की जा रही है...")
                page.goto(TARGET_URL, wait_until="load")
                
                print("⏳ 10 सेकंड का इनिशियल वेट...")
                page.wait_for_timeout(10000)
                
                print("🔍 वीडियो खोजने और प्ले करने की कोशिश...")
                instagram_frame = page.frame_locator("iframe[src*='instagram.com']")
                try:
                    video_box = instagram_frame.locator("div.ClickShim, div.PlayButton, div[role='button']").first
                    video_box.hover()
                    video_box.click(timeout=5000)
                    print("▶️ प्ले बटन पर क्लिक कर दिया गया है!")
                except Exception:
                    instagram_frame.locator("body").click()
                    print("▶️ बैकअप बॉडी क्लिक का इस्तेमाल किया गया।")
                
                # 25वें सेकंड पर स्क्रीनशॉट (10s पहले + 15s अब = 25s)
                page.wait_for_timeout(15000) 
                print("📸 25 सेकंड हो गए! स्क्रीनशॉट कैप्चर हो रहा है...")
                send_screenshot_to_telegram(page, f"🤖 मशीन {MACHINE_ID}\n🔄 लूप: {i}/{LOOP_COUNT}\n✅ लाइव रनिंग स्टेटस!")
                
                # 31वें सेकंड तक का कुल वेट मैनेज करना
                remaining_wait = 31 - (time.time() - start_time)
                if remaining_wait > 0:
                    page.wait_for_timeout(remaining_wait * 1000)
                
                print("🔒 31 सेकंड पूरे हुए। पेज बंद किया जा रहा है।")
                
            except Exception as e:
                print(f"❌ इस लूप में एरर आया: {e}")
            finally:
                try:
                    context.close()
                    browser.close()
                except Exception:
                    pass
                
            time.sleep(1)

if __name__ == "__main__":
    run_machine()
