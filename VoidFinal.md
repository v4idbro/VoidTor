```
 //    //  ///////   ///  ///////    /////////  ///////   /////// 
 //    //  //   //   ///  //    //      ///     //   //   //    //
 //    //  //   //   ///  //    //      ///     //   //   /////// 
  //  //   //   //   ///  //    //      ///     //   //   //   // 
   ////    ///////   ///  ///////       ///     ///////   //    //
```

VoidFinal installs and configures Tor on Linux and rotates your Tor exit-node IP automatically.

## Requirements

- Linux with apt and sudo access
- Python 3

## Usage

```
python3 VoidFinal.py
```

On first run the script installs Tor, enables the control port, adds your user to the required group, and starts the Tor service automatically. No manual editing of torrc is needed.

You will be asked for the interval between rotations, then for a total duration. Leave the duration blank for infinite rotation, or set a number of seconds to stop automatically. The script then rotates continuously, printing each new IP, until the duration ends or you press Ctrl+C.

If group changes were just applied, you may need to open a new terminal session for them to take effect. The script falls back to unauthenticated control port access if the cookie is not readable yet.

## Notes

This tool does not change your ISP-assigned IPv4 or IPv6 address, only the exit-node IP visible over Tor.
