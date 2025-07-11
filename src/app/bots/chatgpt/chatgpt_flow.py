from DrissionPage import ChromiumOptions, ChromiumPage
import shutil
import socket
import os
import platform
import tempfile
import subprocess
import time

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def free_port(start=9222):
    with socket.socket() as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def start_xvfb():
    if not os.environ.get("DISPLAY"):
        # Check if Xvfb is already running
        try:
            output = subprocess.check_output(["pgrep", "Xvfb"])
            print(":large_green_circle: Xvfb is already running.")
        except subprocess.CalledProcessError:
            print(":large_blue_circle: Starting Xvfb virtual display...")
            subprocess.Popen(["Xvfb", ":99", "-screen", "0", "1280x1024x24"])
            time.sleep(2)
        os.environ["DISPLAY"] = ":99"
    else:
        print(f":large_green_circle: DISPLAY already set to {os.environ['DISPLAY']}.")

def launch_chatgpt_browser():
    start_xvfb()
    port = 9222
    print(f"DEBUG: Using port {port} for Edge remote debugging")
    browser_path = "/usr/bin/microsoft-edge"
    if not os.path.exists(browser_path):
        print("DEBUG: Microsoft Edge not found at /usr/bin/microsoft-edge!")
        raise RuntimeError("Microsoft Edge binary not found at /usr/bin/microsoft-edge. Please install Edge for Linux via the official Microsoft repository.")
    print(f"DEBUG: Using Edge browser path: {browser_path}")
    co = ChromiumOptions()
    co.set_browser_path(browser_path)
    import tempfile
    temp_dir = tempfile.gettempdir()
    user_data_dir = os.path.join(temp_dir, f"edge_profile_{port}")
    co.set_argument("--no-sandbox")
    co.set_argument("--disable-gpu")
    co.set_argument("--disable-dev-shm-usage")
    co.set_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    co.set_argument("--disable-blink-features=AutomationControlled")
    co.set_argument("--disable-infobars")
    # Remove headless mode, only use Xvfb
    # co.set_argument("--headless=new")  # Removed
    co.set_argument(f"--remote-debugging-port={port}")
    co.set_argument(f"--user-data-dir={user_data_dir}")
    co.set_argument("--incognito")  # Always use incognito mode
    print(f"[DEBUG] Using Edge browser path: {browser_path}")
    print(f"[DEBUG] Using user data dir: {user_data_dir}")
    driver = ChromiumPage(co)
    # Clear all cookies before navigating to ChatGPT
    try:
        driver.cookies.clear()  # type: ignore[attr-defined]
        print("[DEBUG] Cleared all cookies before navigation.")
    except Exception as e:
        print(f"[WARN] Could not clear cookies: {e}")
    print(f"[SUCCESS] Launched new Edge browser on port {port}.")
    return driver 