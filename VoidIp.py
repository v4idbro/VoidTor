import time
import sys
import subprocess
import urllib.request

BANNER = r"""
 //    //  ///////   ///  ///////    /////////  ///////   /////// 
 //    //  //   //   ///  //    //      ///     //   //   //    //
 //    //  //   //   ///  //    //      ///     //   //   /////// 
  //  //   //   //   ///  //    //      ///     //   //   //   // 
   ////    ///////   ///  ///////       ///     ///////   //    //
"""


def run(cmd):
    return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def install_tor():
    check = subprocess.run("which tor", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if check.returncode != 0:
        subprocess.run("sudo apt update", shell=True)
        subprocess.run("sudo apt install -y tor", shell=True)


def get_public_ip():
    proxy_handler = urllib.request.ProxyHandler({
        "http": "socks5h://127.0.0.1:9050",
        "https": "socks5h://127.0.0.1:9050",
    })
    opener = urllib.request.build_opener(proxy_handler)
    try:
        with opener.open("http://checkip.amazonaws.com", timeout=15) as resp:
            return resp.read().decode().strip()
    except Exception as e:
        return f"error: {e}"


def change_ip():
    subprocess.run(["sudo", "service", "tor", "reload"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return get_public_ip()


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
    previous_ip = get_public_ip()

    try:
        while True:
            if duration is not None and (time.time() - start) >= duration:
                break

            time.sleep(interval)
            new_ip = change_ip()

            if new_ip == previous_ip:
                print(f"IP unchanged {new_ip}")
            else:
                print(f"IP changed to {new_ip}")

            previous_ip = new_ip
    except KeyboardInterrupt:
        print("stopped")


def main():
    install_tor()
    print(BANNER)

    subprocess.run(["sudo", "service", "tor", "start"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3)

    interval = ask_interval()
    duration = ask_duration()
    rotate_loop(interval, duration)


if __name__ == "__main__":
    main()
