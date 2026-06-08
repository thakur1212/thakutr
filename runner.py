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

def send_telegram_msg(text):
    """सिर्फ टेक्स्ट मैसेज भेजने के लिए फंक्शन"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={'chat_id': CHAT_ID, 'text': text})
    except:
        pass

def send_screenshot_to_telegram(page, text_msg):
    """स्क्रीनशॉट भेजने के लिए फंक्शन"""
    screenshot_path = f"ss_{MACHINE_ID}.png"
    try:
        page.screenshot(path=screenshot_path, full_page=True)
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        with open(screenshot_path, 'rb') as photo:
            requests.post(url, files={'photo': photo}, data={'chat_id': CHAT_ID, 'caption': text_msg})
        os.remove(screenshot_path)
        print(f"📸 मशीन {MACHINE_ID}: स्क्रीनशॉट भेज दिया गया है।")
    except Exception as e:
        print(f"❌ स्क्रीनशॉट एरर: {e}")
        send_telegram_msg(f"⚠️ मशीन {MACHINE_ID}: स्क्रीनशॉट नहीं लिया जा सका। एरर: {str(e)[:100]}")

def run_machine():
    print(f"🎰 मशीन {MACHINE_ID} चालू हो रही है...")
    
    # मशीन चालू होते ही आपको टेलीग्राम पर अलर्ट आएगा
    send_telegram_msg(f"🚀 मशीन {MACHINE_ID} चालू हो गई है! Tor Browser लोड किया जा रहा है...")
    
    tor_executable = os.path.abspath("./tor-browser/Browser/firefox")
    tor_profile = os.path.abspath("./tor-browser/Browser/TorBrowser/Data/Browser/profile.default")
    
    with sync_playwright() as p:
        for i in range(1, LOOP_COUNT + 1):
            print(f"\n--- मशीन {MACHINE_ID} | लूप {i}/{LOOP_COUNT} ---")
            
            context = None
            page = None
            
            try:
                # Tor Browser लॉन्च करना
                print("Tor Browser को Launch किया जा रहा है...")
                context = p.firefox.launch_persistent_context(
                    user_data_dir=tor_profile,
                    executable_path=tor_executable,
                    headless=False,
                    viewport={"width": 1280, "height": 720},
                    args=["--mute-audio"]
                )
                
                page = context.pages[0] if context.pages else context.new_page()
                
                print("⏳ Tor नेटवर्क से कनेक्ट हो रहा है (30 सेकंड इंतज़ार)...")
                page.wait_for_timeout(30000)
                
                print("🌐 वेबसाइट ओपन की जा रही है...")
                page.goto(TARGET_URL, wait_until="load", timeout=90000)
                
                print("⏳ पेज लोड होने का इंतज़ार...")
                page.wait_for_timeout(10000)
                
                print("🔍 यूट्यूब वीडियो बॉक्स (iframe) ढूँढा जा रहा है...")
                youtube_frame = page.frame_locator("iframe[src*='youtube.com/embed']")
                
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
                    print(f"⚠️ प्ले बटन क्लिक एरर: {click_err}")
                
                # 25वें सेकंड पर स्क्रीनशॉट
                page.wait_for_timeout(15000) 
                print("📸 फुल-स्क्रीन स्क्रीनशॉट लिया जा रहा है...")
                send_screenshot_to_telegram(page, f"🧅 मशीन {MACHINE_ID} (Tor Browser)\n🔄 लूप: {i}/{LOOP_COUNT}\n✅ सक्सेस!")
                
                page.wait_for_timeout(6000)
                
            except Exception as e:
                error_msg = str(e)
                print(f"❌ इस लूप में क्रैश हुआ: {error_msg}")
                # 🟢 अगर कोई एरर आता है, तो अब बॉट आपको टेलीग्राम पर लिखकर बताएगा!
                send_telegram_msg(f"❌ मशीन {MACHINE_ID} में एरर आ गया:\n{error_msg[:200]}")
                
            finally:
                if context:
                    try:
                        context.close()
                    except:
                        pass
                
            time.sleep(2)

if __name__ == "__main__":
    run_machine()
