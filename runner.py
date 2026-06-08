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
        # 🟢 full_page=True लगाने से पूरे पेज (ऊपर से नीचे तक) का स्क्रीनशॉट आएगा
        page.screenshot(path=screenshot_path, full_page=True)
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        with open(screenshot_path, 'rb') as photo:
            files = {'photo': photo}
            data = {'chat_id': CHAT_ID, 'caption': text_msg}
            requests.post(url, files=files, data=data)
        os.remove(screenshot_path)
        print(f"📸 मशीन {MACHINE_ID}: फुल-स्क्रीन स्क्रीनशॉट टेलीग्राम पर भेज दिया गया है।")
    except Exception as e:
        print(f"❌ स्क्रीनशॉट भेजने में एरर: {e}")

def run_machine():
    print(f"🎰 मशीन {MACHINE_ID} चालू हो रही है। असली 'Tor Browser' इस्तेमाल हो रहा है।")
    
    # Tor Browser की लोकेशन जो GitHub Actions में डाउनलोड होगी
    tor_executable = os.path.abspath("./tor-browser/Browser/firefox")
    tor_profile = os.path.abspath("./tor-browser/Browser/TorBrowser/Data/Browser/profile.default")
    
    with sync_playwright() as p:
        for i in range(1, LOOP_COUNT + 1):
            print(f"\n--- मशीन {MACHINE_ID} | लूप {i}/{LOOP_COUNT} ---")
            
            try:
                # 🟢 Playwright अब सीधे असली Tor Browser को ही खोलेगा
                context = p.firefox.launch_persistent_context(
                    user_data_dir=tor_profile,
                    executable_path=tor_executable,
                    headless=False,
                    viewport={"width": 1280, "height": 720},
                    args=["--mute-audio"]
                )
                
                # पहला पेज जो अपने आप खुलेगा
                page = context.pages[0] if context.pages else context.new_page()
                
                # Tor को नेटवर्क से कनेक्ट होने में थोड़ा समय लगता है (30 सेकंड)
                print("⏳ Tor नेटवर्क से कनेक्ट हो रहा है (30 सेकंड इंतज़ार)...")
                page.wait_for_timeout(30000)
                
                # 1. ब्लॉगस्पॉट वेबसाइट पर जाना
                print("🌐 वेबसाइट ओपन की जा रही है...")
                page.goto(TARGET_URL, wait_until="load", timeout=90000)
                
                # 2. 10 सेकंड का इनिशियल वेट
                print("⏳ पेज लोड होने का इंतज़ार...")
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
                    print(f"⚠️ क्लिक करने में समस्या आई: {click_err}")
                
                # 5. 25वें सेकंड पर फुल स्क्रीन स्क्रीनशॉट
                page.wait_for_timeout(15000) 
                print("📸 फुल-स्क्रीन स्क्रीनशॉट लिया जा रहा है...")
                send_screenshot_to_telegram(page, f"🧅 मशीन {MACHINE_ID} (Original Tor Browser)\n🔄 लूप: {i}/{LOOP_COUNT}\n✅ रनिंग स्टेटस!")
                
                # 6. पेज बंद करना
                page.wait_for_timeout(6000)
                print("🔒 लूप पूरा हुआ। पेज बंद किया जा रहा है।")
                
            except Exception as e:
                print(f"❌ इस लूप में एरर आया: {e}")
                try:
                    send_screenshot_to_telegram(page, f"❌ मशीन {MACHINE_ID} पर एरर आया: {str(e)[:100]}")
                except Exception:
                    pass
            finally:
                try:
                    context.close()
                except Exception:
                    pass
                
            time.sleep(2)

if __name__ == "__main__":
    run_machine()
