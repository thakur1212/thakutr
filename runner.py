import sys
import os
import time
import requests
from playwright.sync_api import sync_playwright

# इनपुट्स रीड करना (टेलीग्राम बॉट से आने वाला डेटा)
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
        print(f"📸 मशीन {MACHINE_ID}: स्क्रीनशॉट टेलीग्राम पर भेज दिया गया है।")
    except Exception as e:
        print(f"❌ स्क्रीनशॉट भेजने में एरर: {e}")

def run_machine():
    print(f"🎰 मशीन {MACHINE_ID} चालू हो रही है। यूट्यूब मोड एक्टिव है [Firefox]। कुल टारगेट: {LOOP_COUNT} लूप्स")
    
    with sync_playwright() as p:
        for i in range(1, LOOP_COUNT + 1):
            print(f"\n--- मशीन {MACHINE_ID} | लूप {i}/{LOOP_COUNT} ---")
            
            try:
                # 🛠️ यहाँ बदलाव किया गया है: Chromium की जगह Firefox लॉन्च हो रहा है
                browser = p.firefox.launch(
                    headless=False,
                    args=["--mute-audio"]  # Firefox के लिए सैंडबॉक्स आर्ग्युमेंट्स की जरूरत नहीं होती
                )
                
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
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
                
                # 1. ब्लॉगस्पॉट वेबसाइट पर जाना
                print("🌐 वेबसाइट ओपन की जा रही है...")
                page.goto(TARGET_URL, wait_until="load")
                
                # 2. 10 सेकंड का इनिशियल वेट
                print("⏳ 10 सेकंड का इंतजार...")
                page.wait_for_timeout(10000)
                
                # 3. यूट्यूब वीडियो फ्रेम (iframe) ढूँढना
                print("🔍 यूट्यूब वीडियो बॉक्स (iframe) ढूँढा जा रहा है...")
                youtube_frame = page.frame_locator("iframe[src*='youtube.com/embed']")
                
                # 4. यूट्यूब के बड़े प्ले बटन पर क्लिक करना
                print("⚡ यूट्यूब प्ले बटन पर क्लिक करने की कोशिश...")
                try:
                    play_button = youtube_frame.locator("button.ytp-large-play-button, .ytp-cued-thumbnail-overlay")
                    
                    if play_button.count() > 0:
                        play_button.first.hover()
                        page.wait_for_timeout(500)
                        play_button.first.click(timeout=5000)
                        print("▶️ यूट्यूब वीडियो प्ले हो गया है!")
                    else:
                        youtube_frame.locator("body").click()
                        print("▶️ बॉडी क्लिक से वीडियो चालू करने की कोशिश की गई।")
                except Exception as click_err:
                    print(f"⚠️ क्लिक करने में समस्या आई (शायद वीडियो ऑटोप्ले हो गया हो): {click_err}")
                
                # 5. 25वें सेकंड पर स्क्रीनशॉट
                page.wait_for_timeout(15000) 
                print("📸 25 सेकंड हो गए! स्क्रीनशॉट लिया जा रहा है...")
                send_screenshot_to_telegram(page, f"🤖 मशीन {MACHINE_ID}\n🔄 लूप: {i}/{LOOP_COUNT}\n✅ यूट्यूब रनिंग स्टेटस [Firefox]!")
                
                # 6. 31वें सेकंड तक का पूरा वेट मैनेज करना
                page.wait_for_timeout(6000)
                print("🔒 31 सेकंड पूरे हुए। पेज बंद किया जा रहा है।")
                
            except Exception as e:
                print(f"❌ इस लूप में एरर आया: {e}")
                try:
                    send_screenshot_to_telegram(page, f"❌ मशीन {MACHINE_ID} पर एरर आया: {str(e)[:100]}")
                except Exception:
                    pass
            finally:
                try:
                    context.close()
                    browser.close()
                except Exception:
                    pass
                
            # लूप्स के बीच 1 सेकंड का गैप
            time.sleep(1)

if __name__ == "__main__":
    run_machine()
