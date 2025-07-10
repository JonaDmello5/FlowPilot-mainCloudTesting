from DrissionPage import ChromiumOptions, ChromiumPage
import shutil
import socket
import os
import platform
import tempfile

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def free_port(start=9222):
    with socket.socket() as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def launch_chatgpt_browser():
    port = 9222
    print(f"DEBUG: Using port {port} for Chromium remote debugging")
    browser_path = "/snap/bin/chromium"
    print(f"DEBUG: Checking Chromium path at {browser_path}")
    if not os.path.exists(browser_path):
        print("DEBUG: Chromium not found!")
        raise RuntimeError(f"Chromium binary not found at {browser_path}. Please install Chromium via snap.")
    co = ChromiumOptions()
    co.set_browser_path(browser_path)
    import tempfile
    temp_dir = tempfile.gettempdir()
    user_data_dir = os.path.join(temp_dir, f"chromium_profile_{port}")
    co.set_argument("--no-sandbox")
    co.set_argument("--disable-gpu")
    co.set_argument("--disable-dev-shm-usage")
    co.set_argument(f"--remote-debugging-port={port}")
    co.set_argument(f"--user-data-dir={user_data_dir}")
    print(f"[DEBUG] Using Chromium browser path: {browser_path}")
    print(f"[DEBUG] Using user data dir: {user_data_dir}")
    driver = ChromiumPage(co)
    print(f"[SUCCESS] Launched new Chromium browser on port {port}.")
    return driver 