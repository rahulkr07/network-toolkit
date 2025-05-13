import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import socket
import subprocess
import threading
import speedtest
import os
from datetime import datetime
import ttkbootstrap as tb
from ttkbootstrap.constants import *

# Log file path
LOG_PATH = "logs/output_logs.txt"
os.makedirs("logs", exist_ok=True)

# Utility Functions
def write_log(message):
    with open(LOG_PATH, "a") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")

def threaded(fn):
    def wrapper(*args, **kwargs):
        threading.Thread(target=fn, args=args, kwargs=kwargs, daemon=True).start()
    return wrapper

class NetworkToolkitApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Network Troubleshooting Toolkit")
        self.root.geometry("1024x600")
        self.root.minsize(800, 500)

        self.style = tb.Style("litera")
        self.dark_mode = False

        # Canvas Gradient Background
        self.background = tk.Canvas(self.root, bg="black", highlightthickness=0)
        self.background.pack(fill="both", expand=True)
        self.background.bind("<Configure>", self.draw_gradient)

        self.main_frame = ttk.Frame(self.background)
        self.background.create_window((0, 0), window=self.main_frame, anchor="nw", width=1024, height=600)

        # Tabs
        self.tabs = ttk.Notebook(self.main_frame)
        self.tab_tools = ttk.Frame(self.tabs)
        self.tab_logs = ttk.Frame(self.tabs)
        self.tab_settings = ttk.Frame(self.tabs)

        self.tabs.add(self.tab_tools, text="🛠 Tools")
        self.tabs.add(self.tab_logs, text="📄 Logs Viewer")
        self.tabs.add(self.tab_settings, text="⚙ Settings")
        self.tabs.pack(expand=1, fill="both", padx=10, pady=10)

        self.status_var = tk.StringVar(value="Checking...")
        self.setup_tools_tab()
        self.setup_logs_tab()
        self.setup_settings_tab()
        self.update_network_status()

    def draw_gradient(self, event=None):
        self.background.delete("gradient")
        w = self.background.winfo_width()
        h = self.background.winfo_height()

        r1, g1, b1 = (255, 90, 150)  # Pink
        r2, g2, b2 = (70, 130, 180)  # Blue

        steps = h
        for i in range(steps):
            r = int(r1 + (r2 - r1) * i / steps)
            g = int(g1 + (g2 - g1) * i / steps)
            b = int(b1 + (b2 - b1) * i / steps)
            color = f"#{r:02x}{g:02x}{b:02x}"
            self.background.create_line(0, i, w, i, tags="gradient", fill=color)

    def setup_tools_tab(self):
        f = self.tab_tools

        # Status Badge
        self.status_label = ttk.Label(f, textvariable=self.status_var, font=("Segoe UI", 12, "bold"))
        self.status_label.grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=(10, 0))

        ttk.Label(f, text="Ping Host:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.ping_entry = ttk.Entry(f)
        self.ping_entry.insert(0, "8.8.8.8")
        self.ping_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(f, text="Run Ping", command=self.run_ping).grid(row=1, column=2, padx=5)

        ttk.Label(f, text="DNS Lookup:").grid(row=2, column=0, sticky="e", padx=5)
        self.dns_entry = ttk.Entry(f)
        self.dns_entry.insert(0, "google.com")
        self.dns_entry.grid(row=2, column=1, padx=5)
        ttk.Button(f, text="Run DNS", command=self.run_dns).grid(row=2, column=2, padx=5)

        ttk.Label(f, text="Internet Speed Test (India):").grid(row=3, column=0, sticky="e", padx=5)
        ttk.Button(f, text="Run Speed Test", command=self.run_speed_test).grid(row=3, column=2, padx=5)

        ttk.Label(f, text="Host for Port Scan:").grid(row=4, column=0, sticky="e", padx=5)
        self.portscan_host = ttk.Entry(f)
        self.portscan_host.insert(0, "localhost")
        self.portscan_host.grid(row=4, column=1, padx=5)

        ttk.Label(f, text="Port Range:").grid(row=5, column=0, sticky="e", padx=5)
        self.port_start = ttk.Entry(f, width=6)
        self.port_end = ttk.Entry(f, width=6)
        self.port_start.insert(0, "20")
        self.port_end.insert(0, "80")
        self.port_start.grid(row=5, column=1, sticky="w", padx=5)
        self.port_end.grid(row=5, column=1, sticky="e", padx=5)
        ttk.Button(f, text="Run Port Scan", command=self.run_port_scan).grid(row=5, column=2, padx=5)

        self.output = tk.Text(f, height=15, wrap="word", bg="#f8f9fa")
        self.scroll = ttk.Scrollbar(f, command=self.output.yview)
        self.output.configure(yscrollcommand=self.scroll.set)
        self.output.grid(row=6, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        self.scroll.grid(row=6, column=3, sticky="ns")

        ttk.Button(f, text="Save Log", command=self.save_log).grid(row=7, column=2, pady=5)
        f.grid_columnconfigure(1, weight=1)
        f.grid_rowconfigure(6, weight=1)

    def setup_logs_tab(self):
        self.log_viewer = tk.Text(self.tab_logs, wrap="word")
        scroll = ttk.Scrollbar(self.tab_logs, command=self.log_viewer.yview)
        self.log_viewer.configure(yscrollcommand=scroll.set)
        self.log_viewer.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.refresh_logs()

    def setup_settings_tab(self):
        f = self.tab_settings
        ttk.Button(f, text="🌓 Toggle Dark Mode", command=self.toggle_dark_mode).pack(pady=10)
        ttk.Button(f, text="🖥 Fullscreen Mode", command=self.fullscreen_mode).pack(pady=10)
        ttk.Button(f, text="🗗 Half-Screen Mode", command=self.halfscreen_mode).pack(pady=10)

    def update_output(self, text):
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, text)
        write_log(text)
        self.refresh_logs()

    def update_network_status(self):
        def check():
            try:
                socket.create_connection(("8.8.8.8", 53), timeout=2)
                self.status_var.set("🟢 Online")
            except:
                self.status_var.set("🔴 Offline")
            self.root.after(3000, self.update_network_status)
        threading.Thread(target=check, daemon=True).start()

    @threaded
    def run_ping(self):
        host = self.ping_entry.get()
        try:
            result = subprocess.check_output(["ping", host, "-n", "4" if os.name == "nt" else "-c", "4"], text=True)
            self.update_output(result)
        except Exception as e:
            self.update_output(f"Ping failed: {e}")

    @threaded
    def run_dns(self):
        domain = self.dns_entry.get()
        try:
            ip = socket.gethostbyname(domain)
            self.update_output(f"{domain} resolves to {ip}")
        except Exception as e:
            self.update_output(f"DNS lookup failed: {e}")

    @threaded
    def run_speed_test(self):
        try:
            st = speedtest.Speedtest()
            st.get_best_server()
            dl = st.download() / 1_000_000
            ul = st.upload() / 1_000_000
            self.update_output(f"Download: {dl:.2f} Mbps\nUpload: {ul:.2f} Mbps")
        except Exception as e:
            self.update_output(f"Speed test failed: {e}")

    @threaded
    def run_port_scan(self):
        host = self.portscan_host.get()
        try:
            start = int(self.port_start.get())
            end = int(self.port_end.get())
            result = ""
            for port in range(start, end + 1):
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(0.5)
                        if s.connect_ex((host, port)) == 0:
                            result += f"Port {port} is open\n"
                except:
                    pass
            self.update_output(result or "No open ports found.")
        except Exception as e:
            self.update_output(f"Port scan failed: {e}")

    def save_log(self):
        with open(LOG_PATH, "a") as f:
            f.write(self.output.get("1.0", tk.END) + "\n")
        messagebox.showinfo("Saved", "Log saved to logs/output_logs.txt")
        self.refresh_logs()

    def refresh_logs(self):
        try:
            with open(LOG_PATH) as f:
                self.log_viewer.delete("1.0", tk.END)
                self.log_viewer.insert(tk.END, f.read())
        except:
            self.log_viewer.insert(tk.END, "No logs yet.")

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.style.theme_use("darkly" if self.dark_mode else "litera")

    def fullscreen_mode(self):
        self.root.attributes("-fullscreen", True)

    def halfscreen_mode(self):
        self.root.attributes("-fullscreen", False)
        w, h = 1024, 600
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

if __name__ == '__main__':
    root = tb.Window(themename="litera")
    app = NetworkToolkitApp(root)
    root.mainloop()
