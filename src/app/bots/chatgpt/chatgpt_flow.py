from DrissionPage import ChromiumOptions, ChromiumPage
import shutil
import socket
import os
import platform
import tempfile

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def launch_chatgpt_browser(port=9222):
    # Only allow Chromium via snap
    browser_path = "/snap/bin/chromium"
    if not os.path.exists(browser_path):
        raise RuntimeError(f"Chromium binary not found at {browser_path}. Please install Chromium via snap.")
    co = ChromiumOptions()
    co.set_browser_path(browser_path)
    # Use cross-platform temp directory for user data dir
    import tempfile
    temp_dir = tempfile.gettempdir()
    user_data_dir = os.path.join(temp_dir, f"chromium_profile_{port}")
    co.set_argument("--no-sandbox")
    co.set_argument("--disable-gpu")
    co.set_argument("--disable-dev-shm-usage")
    co.set_argument(f"--remote-debugging-port=9222")
    co.set_argument(f"--user-data-dir={user_data_dir}")
    print(f"[DEBUG] Using Chromium browser path: {browser_path}")
    print(f"[DEBUG] Using user data dir: {user_data_dir}")
    driver = ChromiumPage(co)
    print(f"[SUCCESS] Launched new Chromium browser on port 9222.")
    return driver 