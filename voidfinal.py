import subprocess
import time
import sys
import os
import socket
import binascii
import urllib.request

BANNER = r"""
 //    //  ///////   ///  ///////    /////////  ///////   /////// 
 //    //  //   //   ///  //    //      ///     //   //   //    //
 //    //  //   //   ///  //    //      ///     //   //   /////// 
  //  //   //   //   ///  //    //      ///     //   //   //   // 
   ////    ///////   ///  ///////       ///     ///////   //    //
"""

TOR_CONTROL_PORT = 9051
TOR_COOKIE_PATH = "/run/tor/control.authcookie"
TORRC_PATH = "/etc/tor/torrc"


def run(cmd):
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode == 0


def line_exists(line):
    result = subprocess.run(
        ["grep", "-qxF", line, TORRC_PATH],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def append_line(line):
    subprocess.run(f"echo '{line}' | sudo tee -a {TORRC_PATH}", shell=True, stdout=subprocess.DEVNULL)


def install_tor():
    run(["sudo", "apt", "update"])
    run(["sudo", "apt", "install", "-y", "torbrowser-launcher", "tor"])


def setup_tor_control():
    changed = False

    if not line_exists("ControlPort 9051"):
        append_line("ControlPort 9051")
        changed = True

    if not line_exists("CookieAuthentication 1"):
        append_line("CookieAuthentication 1")
        changed = True

    user = os.environ.get("USER") or os.environ.get("LOGNAME") or ""
    if user:
        subprocess.run(["sudo", "usermod", "-aG", "debian-tor", user],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if changed:
        run(["sudo", "systemctl", "restart", "tor"])
        time.sleep(3)
    else:
        run(["sudo", "systemctl", "start", "tor"])
        time.sleep(1)


def get_public_ip_via_tor():
    proxy_handler = urllib.request.ProxyHandler({
        "http": "socks5h://127.0.0.1:9050",
        "https": "socks5h://127.0.0.1:9050",
    })
    opener = urllib.request.build_opener(proxy_handler)
    try:
        with opener.open("https://api.ipify.org", timeout=15) as resp:
            return resp.read().decode().strip()
    except Exception as e:
        return f"error: {e}"


def read_auth_cookie():
    try:
        with open(TOR_COOKIE_PATH, "rb") as f:
            return binascii.hexlify(f.read()).decode()
    except Exception:
        return None


def authenticate(sock):
    cookie_hex = read_auth_cookie()
    if cookie_hex:
        sock.sendall(f"AUTHENTICATE {cookie_hex}\r\n".encode())
        resp = sock.recv(1024).decode()
        if "250" in resp:
            return True

    sock.sendall(b"AUTHENTICATE\r\n")
    resp = sock.recv(1024).decode()
    return "250" in resp


def new_tor_circuit():
    try:
        s = socket.create_connection(("127.0.0.1", TOR_CONTROL_PORT), timeout=5)
    except Exception:
        return False

    try:
        if not authenticate(s):
            return False

        s.sendall(b"SIGNAL NEWNYM\r\n")
        resp = s.recv(1024).decode()
        return "250" in resp
    finally:
        s.close()


def ask_interval():
    while True:
        raw = input("Enter interval in seconds between IP changes: ").strip()
        try:
            value = int(raw)
            if value > 0:
                return value
        except ValueError:
            pass
        print("Enter a valid positive number.")


def ask_duration():
    print("Tap on blank to make it infinite or set a specific time.")
    raw = input("Enter total duration in seconds: ").strip()
    if raw == "":
        return None
    try:
        value = int(raw)
        if value > 0:
            return value
    except ValueError:
        pass
    return None


def rotate_loop(interval, duration):
    start = time.time()
    previous_ip = get_public_ip_via_tor()

    try:
        while True:
            if duration is not None and (time.time() - start) >= duration:
                break

            ok = new_tor_circuit()
            if not ok:
                time.sleep(interval)
                continue

            time.sleep(3)
            new_ip = get_public_ip_via_tor()

            if new_ip == previous_ip:
                print(f"IP unchanged {new_ip}")
            else:
                print(f"IP changed to {new_ip}")

            previous_ip = new_ip
            time.sleep(interval)
    except KeyboardInterrupt:
        print("stopped")


def main():
    print(BANNER)

    install_tor()
    setup_tor_control()

    interval = ask_interval()
    duration = ask_duration()
    rotate_loop(interval, duration)


if __name__ == "__main__":
    main()
