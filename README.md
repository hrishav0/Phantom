# Phantom
Phantom is a powerful, user-friendly Python-based toolkit for performing a variety of Wi-Fi DoS (Denial of Service) attacks using the aircrack-ng suite and other Linux networking tools. Designed with both GUI and CLI support, Phantom lets you automate attacks like deauthentication, beacon flood, probe flood, RTS/CTS abuse


# ⚠️ Legal Disclaimer
This tool is intended strictly for educational purposes and authorized testing only. Do not use it on networks that you do not own or have explicit permission to test. Unauthorized use of this tool on someone else’s Wi-Fi network is illegal and can result in serious criminal charges, including jail time. Always act responsibly and within the boundaries of the law.


# What's a Deauth attack (DOS-Denial of Service)?
Wi-Fi uses something called 802.11 management frames to control connections. One of those is the deauth frame, which tells a device to disconnect. Problem is…
🔓 These frames aren't encrypted or authenticated.

A deauth (deauthentication) attack is a type of Denial of Service (DoS) attack used against Wi-Fi networks. It works by sending fake deauthentication packets to the devices connected to a specific WiFi network. This forces the client to disconnect from the network, even if they have the correct password.


# Pre-Requisites
1. An external wireless interface or an internal network card that supports monitor mode and packet injection.

2. A Linux system. (Termux won't work with the script unless you use an external WiFi adapter with monitor mode).

3. Make sure you have ```python``` and ```git``` installed on your system.


# What it does?
The script scans the network using ```aircrack-ng``` suite and then it exceutes a deauth attack on the selected WiFi Network.
It uses ```macchanger``` to spoof a ```MAC Address``` to make it harder to trace back. It also automatically changes ```monitor``` mode to ```managed``` mode on your interface upon exit.


# Usage 

```bash
git clone https://github.com/Hrishavvv/Phantom.git/
```

```bash
cd Phantom
```

```bash
python3 phantom.py
```

# Dev Note 
There are two more scripts ```phantom2.py``` (a v2 script which is still under development and has 2 more extra attacks) and a GUI interface for ```phantom.py``` called ```gphantom.py```.
