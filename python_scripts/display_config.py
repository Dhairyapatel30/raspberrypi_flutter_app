# ---------------------------------------------------------------------------------------------------
# Raspberry Pi Mass Parallel Deployment Script (250 Devices + Dual Logging + Auto Cleanup)
# ---------------------------------------------------------------------------------------------------
# Purpose:
# - Pings all devices on subnet
# - Excludes self, gateway, and listed IPs
# - Copies files & runs shell script on all active devices simultaneously
# - Logs detailed and error logs separately
# - Deletes transferred files after successful script execution
#
# Safe for isolated networks with up to 250 Raspberry Pis.
# ---------------------------------------------------------------------------------------------------

import os
import socket
import platform
import ipaddress
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import paramiko
from scp import SCPClient

# ---------------------------
# USER CONFIGURATION
# ---------------------------

REMOTE_USER = 'prod'
REMOTE_PASSWORD = 'phason'
REMOTE_DIR = '/home/prod/'
LOCAL_DIR = '/home/phason/auto sort ilitek-rev2-scripts calibration/Files'
TARGET_FILE_TO_RUN = 'update-ilitek'
USE_SSH_KEY = False
SSH_KEY_PATH = '/home/pi/.ssh/id_rsa'

EXCLUDE_IPS = []

MAX_PARALLEL_TASKS = 250
LOG_DIR = "/home/phason/Logs"
DETAILED_LOG = os.path.join(LOG_DIR, "detailed_log.txt")
ERROR_LOG = os.path.join(LOG_DIR, "error_log.txt")

# ---------------------------
# LOGGING UTILITIES
# ---------------------------

# 🧩 Print diagnostics
print("Running Python script from:", __file__)
print("Current working directory:", os.getcwd())

# Ensure Logs directory exists (relative to this script's location)
script_dir = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(script_dir, '..', 'Logs')
os.makedirs(log_dir, exist_ok=True)

print("Ensured log directory at:", os.path.abspath(log_dir))

# Example of logging
log_path = os.path.join(log_dir, 'Detailed_Log.txt')
with open(log_path, 'a') as f:
    f.write('Script started successfully.\n')

print("✅ Log file written to:", log_path)

def ensure_log_dir():
    """Ensure log directory exists."""
    os.makedirs(LOG_DIR, exist_ok=True)

def log_message(msg, error=False):
    """Append a message to the appropriate log file."""
    ensure_log_dir()
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    target_file = ERROR_LOG if error else DETAILED_LOG
    with open(target_file, "a") as f:
        f.write(f"{timestamp} {msg}\n")

# ---------------------------
# NETWORK FUNCTIONS
# ---------------------------

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()

def get_gateway_ip():
    try:
        output = subprocess.check_output("ip route", shell=True).decode()
        for line in output.splitlines():
            if line.startswith("default"):
                return line.split()[2]
    except:
        return None
    return None

def ping_ip(ip):
    param = "-n" if platform.system().lower() == "windows" else "-c"
    timeout = "-w" if platform.system().lower() == "windows" else "-W"
    try:
        result = subprocess.run(
            ["ping", param, "1", timeout, "1", ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if result.returncode == 0:
            return ip
    except:
        pass
    return None

# ---------------------------
# SSH / SCP FUNCTIONS
# ---------------------------

def create_ssh_client(host, user, password=None, key_path=None):
    """Create SSH client with timeouts tuned for mass parallel connections."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if key_path:
        key = paramiko.RSAKey.from_private_key_file(key_path)
        client.connect(
            hostname=host, username=user, pkey=key,
            timeout=10, banner_timeout=10, auth_timeout=10
        )
    else:
        client.connect(
            hostname=host, username=user, password=password,
            timeout=10, banner_timeout=10, auth_timeout=10
        )
    return client

def send_files_and_execute(ip):
    """Copy files, execute script, and clean up after success."""
    try:
        print(f"[→] {ip}: Connecting...")
        ssh_client = create_ssh_client(
            ip, REMOTE_USER,
            key_path=SSH_KEY_PATH if USE_SSH_KEY else None,
            password=None if USE_SSH_KEY else REMOTE_PASSWORD
        )

        if not os.path.isdir(LOCAL_DIR):
            msg = f"{ip}: ❌ Local directory '{LOCAL_DIR}' missing. Skipping."
            print(msg); log_message(msg, error=True)
            ssh_client.close()
            return

        # Transfer files
        transferred_files = []
        with SCPClient(ssh_client.get_transport()) as scp:
            for filename in os.listdir(LOCAL_DIR):
                full_path = os.path.join(LOCAL_DIR, filename)
                if os.path.isfile(full_path):
                    scp.put(full_path, remote_path=REMOTE_DIR)
                    transferred_files.append(filename)
                    log_message(f"{ip}: Copied {filename}")

        # Ensure script executable
        ssh_client.exec_command(f"chmod +x {REMOTE_DIR}{TARGET_FILE_TO_RUN}")

        # Execute the shell script
        stdin, stdout, stderr = ssh_client.exec_command(f"bash {REMOTE_DIR}{TARGET_FILE_TO_RUN}")
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        if error:
            msg = f"{ip}: ⚠ Script error: {error}"
            print(msg); log_message(msg, error=True)
        else:
            msg = f"{ip}: ✅ Script executed successfully."
            print(msg); log_message(msg)

            # 🧹 Cleanup: Delete the transferred files on the remote device
            for filename in transferred_files:
                cleanup_cmd = f"rm -f {REMOTE_DIR}{filename}"
                ssh_client.exec_command(cleanup_cmd)
                log_message(f"{ip}: Deleted {filename} after successful execution.")
            print(f"[🧹] {ip}: Cleaned up {len(transferred_files)} transferred files.")

        if output:
            log_message(f"{ip}: OUTPUT → {output}")

        ssh_client.close()

    except Exception as e:
        msg = f"{ip}: ❌ {e}"
        print(msg); log_message(msg, error=True)

# ---------------------------
# MAIN EXECUTION
# ---------------------------

def main():
    ensure_log_dir()
    start_time = time.time()
    local_ip = get_local_ip()
    gateway_ip = get_gateway_ip()

    print("------------------------------------------------------------")
    print("🔥 Raspberry Pi Mass Deployment (Dual Logging + Auto Cleanup)")
    print("------------------------------------------------------------")
    print(f"Local IP:    {local_ip}")
    print(f"Gateway IP:  {gateway_ip}")
    print(f"Threads:     {MAX_PARALLEL_TASKS}")
    print(f"Logs Folder: {LOG_DIR}")
    print("------------------------------------------------------------")

    log_message(f"\n==== Deployment Started at {time.ctime()} ====")
    log_message(f"Local IP: {local_ip}, Gateway: {gateway_ip}")

    network = ipaddress.ip_interface(f"{local_ip}/24").network
    ip_list = [str(ip) for ip in network.hosts()]

    print("[*] Scanning network for active devices...")

    with ThreadPoolExecutor(max_workers=250) as executor:
        ping_results = list(executor.map(ping_ip, ip_list))

    active_ips = [
        ip for ip in ping_results
        if ip and ip != local_ip and ip != gateway_ip and ip not in EXCLUDE_IPS
    ]

    print(f"[+] Found {len(active_ips)} active devices.")
    for ip in active_ips:
        print(f" - {ip}")

    if not active_ips:
        print("❌ No active devices found.")
        log_message("No active devices found.", error=True)
        return

    print("\n[>] Starting full parallel deployment...\n")

    with ThreadPoolExecutor(max_workers=MAX_PARALLEL_TASKS) as executor:
        futures = {executor.submit(send_files_and_execute, ip): ip for ip in active_ips}
        for future in as_completed(futures):
            ip = futures[future]
            try:
                future.result()
            except Exception as e:
                msg = f"❌ Uncaught error on {ip}: {e}"
                print(msg); log_message(msg, error=True)

    total_time = round(time.time() - start_time, 2)
    print(f"\n✅ Deployment completed for {len(active_ips)} devices in {total_time}s.")
    log_message(f"==== Deployment Finished ({total_time}s) ====")

# ---------------------------
# ENTRY POINT
# ---------------------------

if __name__ == "__main__":
    main()
