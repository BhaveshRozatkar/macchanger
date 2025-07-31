import ctypes
import sys
import subprocess
import re
import time
import winreg
import random
import tkinter as tk
from tkinter import ttk

# Hide subprocess windows
CREATE_NO_WINDOW = 0x08000000
startupinfo = subprocess.STARTUPINFO()
startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

# --- Helper Functions ---

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def relaunch_as_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit(0)


def get_adapters():
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
           "-Command", "Get-NetAdapter | Select-Object -Property Name,MacAddress | ConvertTo-Json"]
    out = subprocess.check_output(cmd, text=True, startupinfo=startupinfo)
    import json
    entries = json.loads(out)
    if isinstance(entries, dict):
        entries = [entries]
    return [(e['Name'], e['MacAddress']) for e in entries]


def generate_random_mac():
    first = random.randint(0x00, 0xff) & 0xfe | 0x02
    mac = [first] + [random.randint(0x00, 0xff) for _ in range(5)]
    return ":".join(f"{octet:02X}" for octet in mac)


def set_mac(adapter_name, new_mac, status_var):
    status_var.set("Changing MAC...")
    root.update()
    get_guid_cmd = [
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-Command",
        f"(Get-NetAdapter -Name '{adapter_name}').InterfaceGuid"
    ]
    guid = subprocess.check_output(get_guid_cmd, text=True, startupinfo=startupinfo).strip().strip('{}')

    base_key = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}"
    target = None
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base_key) as cls:
        for i in range(winreg.QueryInfoKey(cls)[0]):
            subkey = winreg.EnumKey(cls, i)
            try:
                with winreg.OpenKey(cls, subkey) as sub:
                    cfg_id, _ = winreg.QueryValueEx(sub, "NetCfgInstanceId")
                    if cfg_id.strip('{}').upper() == guid.upper():
                        target = subkey
                        break
            except:
                continue
        if not target:
            status_var.set("Error: Adapter not found in registry.")
            return False
    full_path = f"{base_key}\\{target}"
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, full_path, 0, winreg.KEY_WRITE) as key:
        winreg.SetValueEx(key, "NetworkAddress", 0, winreg.REG_SZ, new_mac.replace(':', ''))

    # Disable & Enable
    subprocess.run([
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-Command", f"Disable-NetAdapter -Name '{adapter_name}' -Confirm:$false"
    ], check=True, startupinfo=startupinfo)
    time.sleep(2)
    subprocess.run([
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-Command", f"Enable-NetAdapter -Name '{adapter_name}' -Confirm:$false"
    ], check=True, startupinfo=startupinfo)

    status_var.set(f"Success: {adapter_name} → {new_mac}")
    return True


def validate_mac(mac):
    return re.fullmatch(r"([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}", mac) is not None

# --- Relaunch with Admin Rights ---
if not is_admin():
    relaunch_as_admin()

# --- GUI Setup ---
root = tk.Tk()
root.title("MAC Changer")
root.resizable(False, False)
root.configure(bg="#FFE4EC")  # pastel pink background

# Style Configuration for pastel pink theme
style = ttk.Style(root)
style.theme_use('default')
style.configure('TFrame', background='#FFE4EC')
style.configure('TLabel', background='#FFE4EC', foreground='#5D1451', font=('Helvetica', 10, 'bold'))
style.configure('TButton', background='#FFC1E3', foreground='#5D1451', font=('Helvetica', 10), padding=6)
style.map('TButton', background=[('active', '#FFB6C1')])
style.configure('TRadiobutton', background='#FFE4EC', foreground='#5D1451', font=('Helvetica', 10))
style.configure('TEntry', fieldbackground='#FFDDEE', background='#FFDDEE', foreground='#5D1451', font=('Helvetica', 10))
style.configure('TCombobox', fieldbackground='#FFDDEE', background='#FFDDEE', foreground='#5D1451', font=('Helvetica', 10))

main = ttk.Frame(root, padding=15)
main.grid()

# Adapter list with current MACs
adapters = get_adapters()
displays = [f"{name} ({mac})" for name, mac in adapters]
adapter_var = tk.StringVar()

ttk.Label(main, text="Select Interface:").grid(row=0, column=0, sticky='w', pady=5)
adapter_menu = ttk.Combobox(main, textvariable=adapter_var, values=displays, state='readonly', width=35)
adapter_menu.grid(row=0, column=1, pady=5)

# Mode
mode_var = tk.StringVar(value='Random')
random_rb = ttk.Radiobutton(main, text='Random MAC', variable=mode_var, value='Random',
                            command=lambda: manual_entry.config(state='disabled'))
manual_rb = ttk.Radiobutton(main, text='Manual MAC', variable=mode_var, value='Manual',
                            command=lambda: manual_entry.config(state='normal'))
random_rb.grid(row=1, column=0, columnspan=2, sticky='w', pady=5)
manual_rb.grid(row=2, column=0, columnspan=2, sticky='w', pady=5)

# Manual entry
ttk.Label(main, text="MAC Address:").grid(row=3, column=0, sticky='w', pady=5)
manual_entry = ttk.Entry(main, width=35)
manual_entry.grid(row=3, column=1, pady=5)
manual_entry.config(state='disabled')

# Apply & Status
apply_btn = ttk.Button(main, text="Apply", command=lambda: apply_action())
apply_btn.grid(row=4, column=0, columnspan=2, pady=15)

status_var = tk.StringVar(value='')
status_label = ttk.Label(main, textvariable=status_var, wraplength=350)
status_label.grid(row=5, column=0, columnspan=2)

# Action

def apply_action():
    sel = adapter_var.get()
    if not sel:
        status_var.set("Select an interface first.")
        return
    idx = displays.index(sel)
    adapter_name = adapters[idx][0]
    if mode_var.get() == 'Manual':
        mac = manual_entry.get().strip()
        if not validate_mac(mac):
            status_var.set("Invalid MAC format. Use XX:XX:XX:XX:XX:XX.")
            return
    else:
        mac = generate_random_mac()
        manual_entry.config(state='normal')
        manual_entry.delete(0, tk.END)
        manual_entry.insert(0, mac)
        manual_entry.config(state='disabled')
    set_mac(adapter_name, mac, status_var)

# Start
root.mainloop()
