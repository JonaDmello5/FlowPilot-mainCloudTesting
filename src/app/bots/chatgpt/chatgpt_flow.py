from DrissionPage import ChromiumOptions, ChromiumPage
import shutil

def launch_chatgpt_browser(port=9222):
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

    driver = ChromiumPage(co)
    return driver 