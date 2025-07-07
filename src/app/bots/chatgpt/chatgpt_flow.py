from DrissionPage import ChromiumOptions, ChromiumPage
import shutil
import socket

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def launch_chatgpt_browser(port=9222):
    if is_port_in_use(port):
        print(f"[ERROR] Port {port} is already in use. Please close any running Chrome/Chromium instances using --remote-debugging-port={port} before starting the bot.\nIf you want to use an existing browser, make sure it is started with --remote-debugging-port={port} and no other process is using this port.")
        exit(1)
    co = ChromiumOptions()
    for _path in (
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/lib/chromium-browser/chromium-browser",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
    ):
        if shutil.which(_path):
            co.set_browser_path(_path)
            break
    else:
        raise RuntimeError("No Chrome/Chromium binary found")

    co.set_argument("--headless=new")
    co.set_argument("--no-sandbox")
    co.set_argument("--disable-gpu")
    co.set_argument("--disable-dev-shm-usage")
    co.set_argument(f"--remote-debugging-port={port}")
    co.set_argument(f"--user-data-dir=/tmp/chrome_profile_{port}")

    driver = ChromiumPage(co)
    print(f"[SUCCESS] Launched new browser on port {port}.")
    return driver 