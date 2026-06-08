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
    """पूरा पेज स्क्रीनशॉट लेकर टेलीग्राम पर भेजें"""
    screenshot_path = f"ss_{MACHINE_ID}.png"
    try:
        # full_page=True से पूरा स्क्रॉल किया हुआ पेज कैप्चर होगा
        page.screenshot(path=screenshot_path, full_page=True)
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        with open(screenshot_path, 'rb') as photo:
            files = {'photo': photo}
            data = {'chat_id': CHAT_ID, 'caption': text_msg}
            requests.post(url, files=files, data=data)
        os.remove(screenshot_path)
        print(f"📸 मशीन {MACHINE_ID}: पूरा पेज स्क्रीनशॉट टेलीग्राम पर भेज दिया गया।")
    except Exception as e:
        print(f"❌ स्क्रीनशॉट भेजने में एरर: {e}")

def run_machine():
    print(f"🎰 मशीन {MACHINE_ID} चालू (Tor Browser Mode) | कुल टारगेट: {LOOP_COUNT} लूप्स")
    
    # Tor SOCKS proxy – मान लिया कि tor service पहले से चल रही है (पोर्ट 9050)
    proxy_config = {
        "server": "socks5://127.0.0.1:9050"
    }
    
    with sync_playwright() as p:
        # Firefox launch करना (Tor Browser जैसा अनुभव)
        browser = p.firefox.launch(
            headless=False,
            args=["--no-sandbox"]
        )
        
        for i in range(1, LOOP_COUNT + 1):
            print(f"\n--- मशीन {MACHINE_ID} | लूप {i}/{LOOP_COUNT} ---")
            
            try:
                # Tor identity user-agent और सेटिंग्स के साथ context बनाएँ
                context = browser.new_context(
                    proxy=proxy_config,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0",  # Tor Browser जैसा UA
                    viewport={"width": 1280, "height": 720},
                    ignore_https_errors=True,  # कुछ साइट्स के लिए
                    extra_http_headers={
                        "Accept-Language": "en-US,en;q=0.5"
                    }
                )
                page = context.new_page()
                
                # WebDriver डिटेक्शन छुपाना (फ़ायरफ़ॉक्स के लिए)
                page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """)
                
                start_time = time.time()
                
                # 1. ब्लॉगस्पॉट वेबसाइट पर जाना (Tor के द्वारा)
                print("🌐 Tor नेटवर्क से वेबसाइट ओपन की जा रही है...")
                page.goto(TARGET_URL, wait_until="load", timeout=60000)
                
                # 2. 10 सेकंड का इंतज़ार (यूट्यूब प्लेयर लोड होने के लिए)
                print("⏳ 10 सेकंड का इंतजार...")
                page.wait_for_timeout(10000)
                
                # 3. यूट्यूब iframe ढूँढना और प्ले बटन पर क्लिक करना
                print("🔍 यूट्यूब वीडियो बॉक्स (iframe) ढूँढा जा रहा है...")
                youtube_frame = page.frame_locator("iframe[src*='youtube.com/embed']")
                
                print("⚡ यूट्यूब प्ले बटन पर क्लिक करने की कोशिश...")
                try:
                    play_button = youtube_frame.locator("button.ytp-large-play-button")
                    if play_button.count() > 0:
                        play_button.first.hover()
                        page.wait_for_timeout(500)
                        play_button.first.click(timeout=5000)
                        print("▶️ यूट्यूब वीडियो प्ले हो गया!")
                    else:
                        youtube_frame.locator("body").click()
                        print("▶️ बॉडी क्लिक से वीडियो चालू करने की कोशिश की गई।")
                except Exception as click_err:
                    print(f"⚠️ क्लिक में दिक्कत (शायद ऑटोप्ले): {click_err}")
                
                # 4. 25वें सेकंड पर स्क्रीनशॉट (10 + 15 = 25)
                page.wait_for_timeout(15000)
                print("📸 25 सेकंड हो गए! पूरा पेज स्क्रीनशॉट लिया जा रहा है...")
                send_screenshot_to_telegram(page, f"🤖 मशीन {MACHINE_ID}\n🔄 लूप: {i}/{LOOP_COUNT}\n✅ Tor + YouTube रनिंग!")
                
                # 5. बचे हुए 6 सेकंड (कुल 31 सेकंड)
                page.wait_for_timeout(6000)
                print("🔒 31 सेकंड पूरे हुए। पेज बंद किया जा रहा है।")
                
            except Exception as e:
                print(f"❌ लूप में एरर: {e}")
                try:
                    send_screenshot_to_telegram(page, f"❌ मशीन {MACHINE_ID} पर एरर: {str(e)[:100]}")
                except:
                    pass
            finally:
                try:
                    context.close()
                except:
                    pass
        browser.close()

if __name__ == "__main__":
    # पहले जाँचें कि Tor चल रहा है या नहीं
    import socket
    s = socket.socket()
    try:
        s.connect(("127.0.0.1", 9050))
        s.close()
        print("✅ Tor SOCKS proxy मिल गया, बॉट चालू कर रहे हैं...")
        run_machine()
    except:
        print("❌ Tor सेवा चालू नहीं है! पहले 'tor' शुरू करें।")
        sys.exit(1)
