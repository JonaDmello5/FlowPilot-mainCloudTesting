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
    print(f"DEBUG: Using port {port} for Edge remote debugging")
    # Try Linux Edge path first
    browser_path = "/usr/bin/microsoft-edge"
    if not os.path.exists(browser_path):
        # Try Windows Edge path as fallback
        browser_path = r"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
        if not os.path.exists(browser_path):
            browser_path = r"C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe"
            if not os.path.exists(browser_path):
                print("DEBUG: Microsoft Edge not found!")
                raise RuntimeError("Microsoft Edge binary not found. Please install Edge and check the path.")
    print(f"DEBUG: Using Edge browser path: {browser_path}")
    co = ChromiumOptions()
    co.set_browser_path(browser_path)
    import tempfile
    temp_dir = tempfile.gettempdir()
    user_data_dir = os.path.join(temp_dir, f"edge_profile_{port}")
    co.set_argument("--no-sandbox")
    co.set_argument("--disable-gpu")
    co.set_argument("--disable-dev-shm-usage")
    co.set_argument(f"--remote-debugging-port={port}")
    co.set_argument(f"--user-data-dir={user_data_dir}")
    print(f"[DEBUG] Using Edge browser path: {browser_path}")
    print(f"[DEBUG] Using user data dir: {user_data_dir}")
    driver = ChromiumPage(co)
    print(f"[SUCCESS] Launched new Edge browser on port {port}.")
    return driver 