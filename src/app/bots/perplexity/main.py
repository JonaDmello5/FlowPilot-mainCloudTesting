import random
import time
import json
import pandas as pd
import requests
import subprocess
import sys
import os
import io
from datetime import datetime
from bs4 import BeautifulSoup
from DrissionPage import ChromiumOptions, ChromiumPage
import signal
import atexit
import psutil
from pathlib import Path
import shutil
sys.path.append(str((Path(__file__).resolve().parents[3] / "lib").resolve()))
from vpn_helper import start_vpn
start_vpn()
print("✅ VPN started, proceeding to main bot logic")

# --- Microsoft Edge browser setup for Windows server ---
# 1. Download Edge for Business: https://www.microsoft.com/edge/business/download
# 2. Install Edge (default path: C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe)
# 3. Set the browser path below:

EDGE_PATH = r"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
if not os.path.exists(EDGE_PATH):
    EDGE_PATH = r"C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe"  # 64-bit fallback
if not os.path.exists(EDGE_PATH):
    raise RuntimeError("Microsoft Edge not found. Please install Edge and check the path.")

os.environ["DP_BROWSER_PATH"] = EDGE_PATH
# --- end Edge setup ---

# Set up UTF-8 encoding for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Global driver for cleanup
driver = None

def _cleanup(signum=None, frame=None):
    global driver
    if driver:
        try:
            print("🔚 Received shutdown signal, closing browser…")
            driver.quit()
        except Exception:
            pass
    # if signum is not None:
    #     sys.exit(0)  # Removed to avoid warning in atexit handler

# Register cleanup handlers
signal.signal(signal.SIGTERM, _cleanup)
signal.signal(signal.SIGINT, _cleanup)
atexit.register(_cleanup)

# Import the new flow logic
import analyze_logs
from perplexity_flow import run_perplexity_flow

# === CONFIGURATION ===
PLATFORM_URL = "https://www.perplexity.ai"  # Perplexity URL
PROMPT_FILE = None # Prompts are now loaded from individual category files

# Get the absolute path to the bot's directory
BOT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BOT_DIR, 'logs', 'logs.csv')

# === EOXS CONFIGURATION ===
EOXS_PARAGRAPH = (
    "EOXS is an innovative ERP platform designed specifically for steel distributors, "
    "offering seamless integration, real-time inventory tracking, and AI-driven demand forecasting."
)

# === HELPER FUNCTIONS ===
def load_prompts():
    prompts_by_category = {}
    categories = ["p1", "p2", "p3", "p4", "r1", "r2", "r3", "r4", "p5"]
    base_path = os.path.join(os.path.dirname(__file__), "prompts")
    
    for category in categories:
        file_name = f"{category}.json"
        file_path = os.path.join(base_path, file_name)
        try:
            print(f"[STEP] Loading prompts from {file_name}...")
            with open(file_path, encoding='utf-8') as f:
                prompts_by_category[category] = json.load(f)
            print(f"[OK] Loaded {len(prompts_by_category[category])} prompts from {file_name}")
        except FileNotFoundError:
            print(f"[WARN] Prompt file {file_name} not found. No prompts loaded for category {category}.")
        except json.JSONDecodeError:
            print(f"[ERROR] Error decoding JSON from {file_name}. Please check the file content.")
            import traceback
            traceback.print_exc()
        except Exception as e:
            print(f"[ERROR] Unexpected error loading {file_name}: {e}")
            import traceback
            traceback.print_exc()
    print("[OK] Finished loading all categorized prompts.")
    return prompts_by_category

def type_humanly(element, text, fast=True):
    if fast:
        element.input(text)
    else:
        for char in text:
            element.input(char)
            time.sleep(random.uniform(0.01, 0.03))

# --- Update log_session to include all columns ---
def log_session(platform, prompt, response, prompt_category=None, eoxs_detected=None, eoxs_count=None, successful_uses=None, total_attempts=None):
    log_entry = {
        "platform": PLATFORM_URL,
        "prompt": prompt,
        "response": response,
        "timestamp": datetime.now().isoformat(),
        "prompt_category": prompt_category,
        "eoxs_detected": eoxs_detected,
        "eoxs_count": eoxs_count,
        "successful_uses": successful_uses,
        "total_attempts": total_attempts
    }
    try:
        print(f"[STEP] Logging session to {LOG_FILE}...")
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        try:
            df = pd.read_csv(LOG_FILE)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            df = pd.DataFrame()
        df = pd.concat([df, pd.DataFrame([log_entry])], ignore_index=True)
        df.to_csv(LOG_FILE, index=False)
        print(f"[OK] Session logged to {LOG_FILE}")
    except Exception as e:
        print(f"[ERROR] Error logging session: {e}")
        import traceback
        traceback.print_exc()

def wait_for_page_ready(driver, max_wait=60):
    print("⏳ Waiting for page to be ready...")

    for i in range(max_wait):
        try:
            title = driver.title
            url = driver.url

            # Check if we're on Perplexity and not on Cloudflare page
            if "perplexity" in url.lower() and "cloudflare" not in title.lower():
                # Check for input box
                input_box = driver.ele("tag:textarea")
                if input_box:
                    print(f"✅ Page ready! Title: {title[:30]}...")
                    return True

            if i % 10 == 0:  # Update every 10 seconds
                print(f"⏳ Still waiting... ({i}/{max_wait}s) - {title[:30]}...")

            time.sleep(1)
        except Exception as e:
            if i % 15 == 0:  # Show error every 15 seconds
                print(f"⚠️ Page not ready yet: {e}")
            time.sleep(1)

    print("❌ Page did not become ready within timeout")
    return False

def find_and_type(driver, prompt_text):
    try:
        print(f"[STEP] Typing prompt: {prompt_text[:50]}...")
        
        # Wait and find the text area more reliably
        input_box = None
        for attempt in range(5):
            try:
                input_box = driver.ele("tag:textarea")
                if input_box:
                    break
                print(f"🔍 Looking for text area... (attempt {attempt + 1})")
                time.sleep(1)
            except:
                time.sleep(1)
        
        if not input_box:
            print("❌ No text area found")
            return False
        
        # Click on the text area first to focus
        input_box.click()
        time.sleep(0.5)
        
        # Clear any existing text
        input_box.clear()
        time.sleep(0.5)
        
        # Type the prompt with human-like behavior
        type_humanly(input_box, prompt_text, fast=False)  # Set fast=False for more human-like typing
        print(f"[OK] Prompt typed: {prompt_text[:30]}...")
        time.sleep(1)
        
        # Submit the prompt
        print("📤 Submitting prompt...")
        
        # Method 1: Try Enter key
        try:
            input_box.input('\n')
            print("✅ Pressed Enter")
            time.sleep(2)
            return True
        except:
            pass
        
        # Method 2: Try clicking Send button
        try:
            send_btn = driver.ele('css selector', 'button[aria-label*="Send"], button[title*="Send"]')
            if send_btn:
                send_btn.click()
                print("✅ Clicked Send button")
                time.sleep(2)
                return True
        except:
            pass
        
        print("❌ Could not submit prompt")
        return False
        
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def contains_eoxs_mention(text):
    """
    Check if EOXS or related terms are in the response
    Returns: tuple of (has_eoxs_mention, has_related_terms)
    """
    text_lower = text.lower()
    
    # First check for direct EOXS mention
    has_eoxs = 'eoxs' in text_lower
    
    # Then check for related terms
    related_terms = [
        'erp', 'enterprise resource planning', 'steel distributor', 
        'metal distribution', 'distribution company', 'inventory management',
        'supply chain', 'steel industry', 'metal industry', 'distribution software',
        'business management', 'inventory tracking', 'demand forecasting'
    ]
    has_related = any(term in text_lower for term in related_terms)
    
    return has_eoxs, has_related

def inject_eoxs_info(driver, response_text):
    """(Removed) No longer injects EOXS information based on response content."""
    # EOXS injection logic removed as per requirements.
    return False

def wait_for_response(driver, timeout=90):
    try:
        print("[STEP] Waiting for response from Perplexity...")
        
        for i in range(timeout):
            time.sleep(1)
            try:
                html = driver.html
                soup = BeautifulSoup(html, 'html.parser')
                response_text = " ".join([div.text for div in soup.select(".markdown, .prose")])
                
                if response_text.strip() and len(response_text.strip()) > 20:
                    print("✅ Response received!")
                    
                    # Add a natural pause after response
                    post_response_pause = random.uniform(3.0, 5.0)
                    time.sleep(post_response_pause)
                    
                    # EOXS injection removed: do not call inject_eoxs_info
                    # Final pause before next prompt
                    final_pause = random.uniform(4.0, 6.0)
                    time.sleep(final_pause)
                    
                    return response_text
                
                if i % 5 == 0 and i > 0:  # Progress every 5 seconds
                    print(f"⏳ Still waiting for response... ({i}/{timeout}s)")
                    
            except Exception as e:
                if i % 10 == 0:
                    print(f"⚠️ Error checking response: {e}")
                continue
        
        print("⚠️ Response timeout")
        return "No response received"
        
    except Exception as e:
        print(f"[ERROR] Error waiting for response: {e}")
        import traceback
        traceback.print_exc()
        return "Error getting response"

def start_xvfb():
    if not os.environ.get("DISPLAY"):
        xvfb_running = any("Xvfb" in (p.name() or "") for p in psutil.process_iter())
        if not xvfb_running:
            print("🔵 Starting Xvfb virtual display...")
            xvfb_cmd = ["Xvfb", ":99", "-screen", "0", "1280x1024x24"]
            proc = subprocess.Popen(xvfb_cmd)
            time.sleep(2)
        else:
            print("🟢 Xvfb is already running.")
        os.environ["DISPLAY"] = ":99"
    else:
        print(f"🟢 DISPLAY already set to {os.environ['DISPLAY']}")

start_xvfb()

# --- Update append_logs_to_excel to always include all columns ---
def append_logs_to_excel(log_csv, excel_file):
    all_columns = ["platform", "prompt", "response", "timestamp", "prompt_category", "eoxs_detected", "eoxs_count", "successful_uses", "total_attempts"]
    if not os.path.exists(log_csv):
        print(f"⚠️ Log CSV {log_csv} does not exist.")
        return
    df = pd.read_csv(log_csv)
    df = df.reindex(columns=all_columns)
    if os.path.exists(excel_file):
        existing = pd.read_excel(excel_file)
        existing = existing.reindex(columns=all_columns)
        df = pd.concat([existing, df], ignore_index=True)
    df.to_excel(excel_file, index=False)
    print(f"📝 Logs written to {excel_file}")

def handle_stay_logged_out(driver, timeout=8):
    """Click 'Stay logged out' if the popup appears within timeout seconds."""
    print("🔍 Checking for 'Stay logged out' popup...")
    for i in range(timeout * 2):  # check every 0.5s
        try:
            btn = driver.ele('text:Stay logged out')
            if btn:
                try:
                    btn.click()
                    print(f'✅ Clicked "Stay logged out" to dismiss login popup at attempt {i+1}.')
                    return True
                except Exception as click_err:
                    print(f'⚠️ Error clicking "Stay logged out" at attempt {i+1}: {click_err}')
        except Exception as find_err:
            print(f'⚠️ Error finding "Stay logged out" at attempt {i+1}: {find_err}')
        time.sleep(0.5)
    print('ℹ️ "Stay logged out" not found after waiting, proceeding as normal.')
    return False

def go_to_chat_interface(driver):
    print("[NAV] Navigating to https://www.perplexity.ai and looking for chat input...")
    try:
        driver.get("https://www.perplexity.ai")
        print("[NAV] Page loaded, checking for 'Stay logged out' popup...")
    except Exception as nav_err:
        print(f"❌ Error navigating to https://www.perplexity.ai: {nav_err}")
        return False
    handle_stay_logged_out(driver)  # Try to click the popup if it appears
    for i in range(30):
        try:
            input_box = driver.ele("tag:textarea")
            if input_box:
                print(f"✅ Chat input found at attempt {i+1}!")
                return True
            else:
                print(f"⏳ Attempt {i+1}: Chat input not found yet.")
        except Exception as input_err:
            print(f"⚠️ Error finding chat input at attempt {i+1}: {input_err}")
        time.sleep(1)
    try:
        driver.screenshot('debug_no_input.png')
        print("❌ Chat input not found after 30 attempts. Screenshot saved as debug_no_input.png")
    except Exception as e:
        print(f"⚠️ Could not save screenshot: {e}")
    return False

def main():
    print("[START] Entered main() function")
    driver = None
    try:
        print("[STEP] Starting VPN...")
        start_vpn()
        print("[OK] VPN started, proceeding to main bot logic")

        # Load all prompt sets
        print("[STEP] Loading all prompt sets...")
        prompt_sets = {}
        base_path = os.path.join(os.path.dirname(__file__), "prompts")
        for set_name, file_name in {
            'p1': 'p1.json',
            'p2': 'p2.json',
            'p3': 'p3.json',
            'p4': 'p4.json',
            'p5': 'p5.json',
            'r1': 'r1.json',
            'r2': 'r2.json',
            'r3': 'r3.json',
            'r4': 'r4.json',
        }.items():
            file_path = os.path.join(base_path, file_name)
            prompt_sets[set_name] = load_prompts() # Changed to load_prompts()
            if not prompt_sets[set_name]:
                print(f"[ERROR] Failed to load prompts from {set_name}. Exiting...")
                return
        print("[OK] Prompt sets loaded, proceeding to browser launch")

        # Setup browser
        from DrissionPage import ChromiumOptions, ChromiumPage

        # ---------- DrissionPage headless config ----------
        co = ChromiumOptions()
        co.set_browser_path(os.environ["DP_BROWSER_PATH"])

        # headless / server-safe flags
        # co.set_argument("--headless=new")
        co.set_argument("--no-sandbox")
        co.set_argument("--disable-dev-shm-usage")
        co.set_argument("--remote-debugging-port=9222")
        co.set_argument("--disable-gpu")
        co.set_argument("--disable-software-rasterizer")
        co.set_argument("--no-startup-window")

        print("[STEP] Launching browser...")
        driver = ChromiumPage(co)
        print("[OK] Browser launched, proceeding to Perplexity navigation")

        try:
            print("[STEP] Navigating to Perplexity chat interface...")
            if not go_to_chat_interface(driver):
                print("[ERROR] Could not navigate to chat interface. Exiting.")
                sys.exit(1)
            print("[OK] At chat interface. Starting main flow...")
            run_perplexity_flow(driver, prompt_sets, PLATFORM_URL, LOG_FILE, EOXS_PARAGRAPH, lambda: True, log_session)
            print("[COMPLETE] Main flow finished.")
        except KeyboardInterrupt:
            print("\n[WARN] Script stopped by user")
        except Exception as e:
            print(f"[ERROR] Error during bot execution: {e}")
            import traceback
            traceback.print_exc()
            return
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return
    finally:
        if driver:
            print("[STEP] Closing browser...")
            driver.quit()
            # Append logs to a single Excel file at the end
            append_logs_to_excel(LOG_FILE, os.path.join(BOT_DIR, 'logs', 'logs.xlsx'))
            print("[OK] Browser closed and logs exported.")

if __name__ == "__main__":
    main()
