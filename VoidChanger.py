import os
import sys
import time
import subprocess

BANNER = r"""
 //    //  ///////   ///  ///////    /////////  ///////   ///////
 //    //  //   //   ///  //    //      ///     //   //   //    //
 //    //  //   //   ///  //    //      ///     //   //   ///////
  //  //   //   //   ///  //    //      ///     //   //   //   //
   ////    ///////   ///  ///////       ///     ///////   //    //
"""

TORRC = "/etc/tor/torrc"
TOR_SOCKS_PORT = 9050
TOR_CONTROL_PORT = 9051


def run_command(command):
    """Run a command and return True if successful."""
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return result.returncode == 0
    except Exception:
        return False


def command_output(command):
    """Run a command and return stdout."""
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout.strip()
    except Exception:
        return ""


def require_sudo():
    """Make sure the script has sudo privileges available."""
    if os.geteuid() == 0:
        return True

    print("[!] This program needs sudo privileges.")
    print("[*] Requesting sudo access...")

    return run_command(["sudo", "-v"])


def install_packages():
    """Install Tor and the Python SOCKS dependencies."""
    print("[*] Checking Tor installation...")

    tor_exists = command_output(["which", "tor"])

    if not tor_exists:
        print("[*] Tor is not installed.")
        print("[*] Installing Tor...")

        if not run_command(["sudo", "apt", "update"]):
            print("[!] Failed to run apt update.")
            return False

        if not run_command(["sudo", "apt", "install", "-y", "tor"]):
            print("[!] Failed to install Tor.")
            return False

    print("[+] Tor is installed.")

    try:
        import requests
    except ImportError:
        print("[*] Installing Python requests with SOCKS support...")

        if not run_command(
            [sys.executable, "-m", "pip", "install", "requests[socks]"]
        ):
            print("[!] Failed to install requests[socks].")
            return False

    return True


def configure_tor():
    """Configure Tor SOCKS and control ports."""
    print("[*] Configuring Tor...")

    required_settings = [
        f"SOCKSPort 127.0.0.1:{TOR_SOCKS_PORT}",
        f"ControlPort 127.0.0.1:{TOR_CONTROL_PORT}",
        "CookieAuthentication 0",
    ]

    try:
        existing = command_output(["sudo", "cat", TORRC])

        if not existing:
            existing = ""

        lines_to_add = []

        for setting in required_settings:
            key = setting.split()[0]

            found = False

            for line in existing.splitlines():
                stripped = line.strip()

                if stripped.startswith(key + " "):
                    found = True
                    break

            if not found:
                lines_to_add.append(setting)

        if lines_to_add:
            addition = "\n" + "\n".join(lines_to_add) + "\n"

            process = subprocess.run(
                ["sudo", "tee", "-a", TORRC],
                input=addition,
                text=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            if process.returncode != 0:
                print("[!] Failed to modify torrc.")
                return False

            print("[+] Tor configuration updated.")
        else:
            print("[+] Tor configuration already configured.")

        return True

    except Exception as error:
        print(f"[!] Configuration error: {error}")
        return False


def start_tor():
    """Start/restart Tor."""
    print("[*] Starting Tor...")

    run_command(["sudo", "systemctl", "enable", "tor"])

    if not run_command(["sudo", "systemctl", "restart", "tor"]):
        # Fallback for systems using the old service command.
        if not run_command(["sudo", "service", "tor", "restart"]):
            print("[!] Failed to start Tor.")
            return False

    print("[*] Waiting for Tor...")
    time.sleep(5)

    return True


def get_public_ip():
    """Get the public IP through Tor."""
    try:
        import requests

        proxies = {
            "http": f"socks5h://127.0.0.1:{TOR_SOCKS_PORT}",
            "https": f"socks5h://127.0.0.1:{TOR_SOCKS_PORT}",
        }

        response = requests.get(
            "https://checkip.amazonaws.com",
            proxies=proxies,
            timeout=20
        )

        response.raise_for_status()

        return response.text.strip()

    except Exception as error:
        return f"error: {error}"


def change_ip():
    """
    Request a new Tor circuit using the Tor control port.
    """
    try:
        from stem import Signal
        from stem.control import Controller

    except ImportError:
        print("[!] Python Stem is not installed.")
        print("[*] Installing python3-stem...")

        if not run_command(["sudo", "apt", "install", "-y", "python3-stem"]):
            return None

        try:
            from stem import Signal
            from stem.control import Controller
        except ImportError:
            print("[!] Could not load Stem.")
            return None

    try:
        with Controller.from_port(
            address="127.0.0.1",
            port=TOR_CONTROL_PORT
        ) as controller:

            controller.authenticate()
            controller.signal(Signal.NEWNYM)

        # Give Tor a moment to build the new circuit.
        time.sleep(5)

        return get_public_ip()

    except Exception as error:
        print(f"[!] Could not request a new Tor circuit: {error}")
        return None


def check_tor():
    """Check whether Tor is usable."""
    print("[*] Testing Tor connection...")

    ip = get_public_ip()

    if ip.startswith("error:"):
        print(f"[!] Tor connection failed: {ip}")
        return False

    print(f"[+] Tor is working.")
    print(f"[+] Current Tor exit IP: {ip}")

    return True


def ask_interval():
    while True:
        raw = input(
            "Enter interval in seconds between IP changes: "
        ).strip()

        try:
            value = int(raw)

            if value > 0:
                return value

        except ValueError:
            pass

        print("[!] Enter a valid positive number.")


def ask_duration():
    print(
        "Leave blank to rotate indefinitely, "
        "or enter a duration in seconds."
    )

    raw = input(
        "Enter total duration in seconds: "
    ).strip()

    if raw == "":
        return None

    try:
        value = int(raw)

        if value > 0:
            return value

    except ValueError:
        pass

    print("[!] Invalid duration. Using infinite mode.")
    return None


def rotate_loop(interval, duration):
    """Continuously request new Tor circuits."""
    start_time = time.time()

    previous_ip = get_public_ip()

    if previous_ip.startswith("error:"):
        print(f"[!] Initial IP check failed: {previous_ip}")
        return

    print(f"[+] Initial Tor IP: {previous_ip}")
    print("[*] Starting IP rotation...")
    print("[*] Press Ctrl+C to stop.\n")

    try:
        while True:

            if duration is not None:
                elapsed = time.time() - start_time

                if elapsed >= duration:
                    print("\n[*] Duration completed.")
                    break

            time.sleep(interval)

            new_ip = change_ip()

            if new_ip is None:
                print("[!] Failed to change Tor circuit.")
                continue

            if new_ip.startswith("error:"):
                print(f"[!] IP check failed: {new_ip}")
                continue

            if new_ip == previous_ip:
                print(f"[-] IP unchanged: {new_ip}")
            else:
                print(f"[+] IP changed: {previous_ip} -> {new_ip}")

            previous_ip = new_ip

    except KeyboardInterrupt:
        print("\n[*] Stopped by user.")


def main():
    print(BANNER)

    if os.name != "posix":
        print("[!] This program is intended for Linux.")
        sys.exit(1)

    if not require_sudo():
        print("[!] Sudo authentication failed.")
        sys.exit(1)

    if not install_packages():
        print("[!] Dependency installation failed.")
        sys.exit(1)

    if not configure_tor():
        sys.exit(1)

    if not start_tor():
        sys.exit(1)

    if not check_tor():
        print("\n[!] Tor is not working correctly.")
        print("[!] Check the Tor service and port 9050.")
        sys.exit(1)

    interval = ask_interval()
    duration = ask_duration()

    rotate_loop(interval, duration)


if __name__ == "__main__":
    main()
