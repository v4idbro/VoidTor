VoidChanger
 //    //  ///////   ///  ///////    /////////  ///////   ///////
 //    //  //   //   ///  //    //      ///     //   //   //    //
 //    //  //   //   ///  //    //      ///     //   //   ///////
  //  //   //   //   ///  //    //      ///     //   //   //   //
   ////    ///////   ///  ///////       ///     ///////   //    //


VoidChanger is a Linux tool that configures Tor, routes its IP-checking requests through Tor's SOCKS5 proxy, and automatically requests new Tor circuits.

The main program is:

VoidChanger.py

Requirements

Before installing VoidChanger, make sure you have:

Linux based on Debian, Kali Linux, or Ubuntu
Python 3
apt
sudo access
An active internet connection
Tor

The program can automatically install the required Tor components.

Installation
1. Enter the project directory

If the project is located in ~/VoidTor:

cd ~/VoidTor


Check the project files:

ls


You should have:

VoidChanger.py
VoidChanger.md

2. Make the Python file executable

This step is optional:

chmod +x VoidChanger.py

3. Run VoidChanger

Start the program with:

python3 VoidChanger.py


On the first run, VoidChanger checks the required dependencies and configures Tor automatically.

Manual Dependency Installation

If you prefer to install the dependencies before running the program:

sudo apt update
sudo apt install -y tor python3 python3-pip python3-stem


Then install Python SOCKS support:

python3 -m pip install requests[socks]


Run the program:

python3 VoidChanger.py

Automatic Tor Configuration

VoidChanger automatically configures the Tor service to use:

SOCKS Port:    127.0.0.1:9050
Control Port:  127.0.0.1:9051


You do not need to manually edit:

/etc/tor/torrc


The program also starts the Tor service automatically.

Using VoidChanger

When you run:

python3 VoidChanger.py


the program asks for the interval between circuit-change requests:

Enter interval in seconds between IP changes: 30


For example:

30


The program then asks for the total duration:

Enter total duration in seconds:


For example:

300


This runs the program for approximately five minutes.

Infinite Mode

To keep VoidChanger running indefinitely, leave the duration empty and press Enter:

Enter total duration in seconds:


You can stop the program at any time with:

Ctrl+C

How It Works

VoidChanger first checks the current public IP through the Tor SOCKS5 proxy.

At each configured interval, it sends a NEWNYM signal to the Tor control port, requesting a new Tor circuit.

After waiting for the new circuit, the program checks the public IP again through Tor.

If the exit node changes, you may see:

[+] IP changed: 185.xxx.xxx.xxx -> 51.xxx.xxx.xxx


If Tor uses the same exit node:

[-] IP unchanged: 185.xxx.xxx.xxx


This can be normal behavior.

Important: IP Changes Are Not Guaranteed

The NEWNYM command requests a new Tor circuit, but Tor does not guarantee that every request will result in a different exit-node IP address.

Tor may select the same exit node again.

Therefore, seeing:

IP unchanged


does not necessarily mean that VoidChanger is malfunctioning.

How to Confirm It Is Working

A successful startup should look similar to:

[+] Tor is installed.
[+] Tor configuration already configured.
[*] Starting Tor...
[*] Waiting for Tor...
[*] Testing Tor connection...
[+] Tor is working.
[+] Current Tor exit IP: xxx.xxx.xxx.xxx

Enter interval in seconds between IP changes: 30
Enter total duration in seconds: 300

[*] Starting IP rotation...
[*] Press Ctrl+C to stop.

[+] IP changed: xxx.xxx.xxx.xxx -> xxx.xxx.xxx.xxx
[+] IP changed: xxx.xxx.xxx.xxx -> xxx.xxx.xxx.xxx


The IP displayed by VoidChanger is the Tor exit-node IP, not the IP address assigned to your internet connection by your ISP.

Testing Tor Manually

You can test the Tor SOCKS5 connection without running VoidChanger:

curl --socks5-hostname 127.0.0.1:9050 https://check.torproject.org/api/ip


If Tor is working correctly, the command should return information containing an IP address.

You can also check whether the SOCKS port is listening:

ss -lntp | grep 9050


Check the Tor control port:

ss -lntp | grep 9051

Checking the Tor Service

Check the Tor service status:

sudo systemctl status tor


If Tor is running correctly, the service should be shown as active.

To restart Tor manually:

sudo systemctl restart tor


Then run VoidChanger again:

python3 VoidChanger.py

Project Structure
VoidTor/
├── VoidChanger.py
└── VoidChanger.md

VoidChanger.py

The main program responsible for:

Checking and installing dependencies
Installing Tor when necessary
Configuring the Tor SOCKS port
Configuring the Tor control port
Starting the Tor service
Connecting through the Tor SOCKS5 proxy
Checking the current Tor exit IP
Requesting new Tor circuits
Displaying IP changes
Running continuously or for a specified duration
VoidChanger.md

Project documentation containing:

Requirements
Installation instructions
Configuration
Usage
Tor testing
Troubleshooting
Project structure
Troubleshooting
unknown url type: socks5h

If you see:

unknown url type: socks5h


make sure you are using the current VoidChanger.py.

The program uses a SOCKS-capable HTTP client rather than Python's standard urllib.request, which does not natively handle socks5h:// proxies.

Install the required dependency:

python3 -m pip install requests[socks]

Tor Is Not Listening on Port 9050

Check:

ss -lntp | grep 9050


If nothing is returned, check the Tor service:

sudo systemctl status tor


Restart it if necessary:

sudo systemctl restart tor

Control Port 9051 Is Not Available

Check:

ss -lntp | grep 9051


If the port is not listening, verify the Tor configuration and restart the service:

sudo systemctl restart tor

Privacy and Network Behavior

VoidChanger does not change the IPv4 or IPv6 address assigned to your device by your ISP.

Instead, requests made through the Tor SOCKS5 proxy are routed through the Tor network, so websites and services receiving those requests normally see the Tor exit-node IP.

Applications that do not use the configured Tor proxy are not automatically routed through Tor.

Disclaimer

VoidChanger is intended for educational, privacy, and authorized testing purposes.

Tor does not guarantee a unique exit IP for every NEWNYM request, and VoidChanger cannot guarantee that the public IP will change after every rotation request.

Always comply with applicable laws, network policies, and the terms of service of the systems you access.

License

Distributed for educational and privacy-related purposes.
