import os
import subprocess
import time
import requests

OVPN_CMD = [
    "sudo", "openvpn",
    "--config", "/etc/openvpn/client/us_california.ovpn",
    "--auth-user-pass", "/etc/openvpn/client/auth.txt",
    "--daemon",  # don't block – run in background
]

_IP_SOURCES = [
    "https://api.ipify.org",
    "https://ifconfig.me/ip",
    "https://icanhazip.com",
    "https://ipinfo.io/ip",
]

def current_ip():
    for url in _IP_SOURCES:
        try:
            return requests.get(url, timeout=3).text.strip()
        except Exception:
            pass
    return None  # all sources failed

def start_vpn(max_wait=20):
    # launch if no tun* yet
    if not any(x.startswith("tun") for x in os.listdir("/sys/class/net")):
        subprocess.check_call(OVPN_CMD)

    # wait for tun interface
    for _ in range(max_wait):
        if any(x.startswith("tun") for x in os.listdir("/sys/class/net")):
            break
        time.sleep(1)
    else:
        raise RuntimeError("tun device never appeared")

    # wait for outbound IP
    for _ in range(max_wait):
        ip = current_ip()
        if ip:
            print("\U0001F6E1  VPN up, public IP:", ip, flush=True)
            return
        time.sleep(1)
    raise RuntimeError("VPN up but no external IP") 