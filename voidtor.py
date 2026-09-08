import subprocess
import time
import sys
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


def run(cmd):
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode == 0


def install_mullvad():
    run(["sudo", "apt", "update"])
    ok = run(["sudo", "apt", "install", "-y", "mullvad-vpn"])
    if not ok:
        print("https://mullvad.net/en/download/vpn/linux")


def install_tor():
    run(["sudo", "apt", "update"])
    run(["sudo", "apt", "install", "-y", "torbrowser-launcher", "tor"])
    run(["sudo", "systemctl", "enable", "--now", "tor"])


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


def new_tor_circuit():
    try:
        s = socket.create_connection(("127.0.0.1", TOR_CONTROL_PORT), timeout=5)
    except Exception as e:
        print(f"error: {e}")
        return False

    cookie_hex = read_auth_cookie()
    if cookie_hex:
        auth_cmd = f"AUTHENTICATE {cookie_hex}\r\n"
    else:
        auth_cmd = "AUTHENTICATE\r\n"

    s.sendall(auth_cmd.encode())
    resp = s.recv(1024).decode()
    if "250" not in resp:
        s.close()
        return False

    s.sendall(b"SIGNAL NEWNYM\r\n")
    resp = s.recv(1024).decode()
    s.close()
    return "250" in resp


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

    if "--install" in sys.argv:
        install_mullvad()
        install_tor()

    interval = ask_interval()
    duration = ask_duration()
    rotate_loop(interval, duration)


if __name__ == "__main__":
    main()
