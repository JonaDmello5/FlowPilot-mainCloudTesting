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
    if is_port_in_use(port):
        print(f"[ERROR] Port {port} is already in use. Please close any running Chrome/Chromium instances using --remote-debugging-port={port} before starting the bot.\nIf you want to use an existing browser, make sure it is started with --remote-debugging-port={port} and no other process is using this port.")
        exit(1)
    co = ChromiumOptions()
    system = platform.system()
    browser_path = None
    if system == "Windows":
        possible_paths = [
            r"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
            r"C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
            shutil.which("msedge.exe"),
            r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            r"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
            shutil.which("chrome.exe"),
            shutil.which("chromium.exe"),
        ]
    else:
        possible_paths = [
            "/usr/bin/microsoft-edge",
            shutil.which("microsoft-edge"),
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/lib/chromium-browser/chromium-browser",
            "/usr/bin/chromium-browser",
            shutil.which("google-chrome"),
            shutil.which("chromium-browser"),
        ]
    for _path in possible_paths:
        if _path and os.path.exists(_path):
            browser_path = _path
            co.set_browser_path(_path)
            break
    if not browser_path:
        raise RuntimeError(f"No Chrome/Chromium binary found. Tried: {possible_paths}")

    # Use cross-platform temp directory for user data dir
    temp_dir = tempfile.gettempdir()
    user_data_dir = os.path.join(temp_dir, f"chrome_profile_{port}")

    co.set_argument("--headless=new")
    co.set_argument("--no-sandbox")
    co.set_argument("--disable-gpu")
    co.set_argument("--disable-dev-shm-usage")
    co.set_argument(f"--remote-debugging-port={port}")
    co.set_argument(f"--user-data-dir={user_data_dir}")

    print(f"[DEBUG] Using browser path: {browser_path}")
    print(f"[DEBUG] Using user data dir: {user_data_dir}")

    driver = ChromiumPage(co)
    print(f"[SUCCESS] Launched new browser on port {port}.")
    return driver 