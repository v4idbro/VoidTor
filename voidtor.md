```
 //    //  ///////   ///  ///////    /////////  ///////   /////// 
 //    //  //   //   ///  //    //      ///     //   //   //    //
 //    //  //   //   ///  //    //      ///     //   //   /////// 
  //  //   //   //   ///  //    //      ///     //   //   //   // 
   ////    ///////   ///  ///////       ///     ///////   //    //
```

VoidTor installs Mullvad VPN and Tor on Linux and rotates your Tor exit-node IP on demand.

## Requirements

- Linux with apt
- Python 3
- Tor with ControlPort enabled

## Setup

```
sudo apt install tor
```

Edit `/etc/tor/torrc` and add:

```
ControlPort 9051
CookieAuthentication 1
```

Restart Tor:

```
sudo systemctl restart tor
```

The script authenticates using Tor's cookie file at `/run/tor/control.authcookie`, so your user needs read access to it (usually via the `debian-tor` group).

## Usage

Install Mullvad and Tor Browser:

```
python3 voidtor.py --install
```

Rotate IP automatically:

```
python3 voidtor.py
```

You will be asked for the interval between rotations, then for a total duration. Leave the duration blank for infinite rotation, or set a number of seconds to stop automatically. The script then rotates continuously, printing each new IP, until the duration ends or you press Ctrl+C.

## Notes

Mullvad requires a paid account to connect; there is no free tier.
This tool does not change your ISP-assigned IPv4 or IPv6 address, only the exit-node IP visible over Tor.
