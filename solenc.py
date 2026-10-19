import os
import sys
import time
import glob
import shlex
import psutil
import subprocess
from collections import deque
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

HEADER = r"""
  ____     ___    _     
 / ___|   / _ \  | |    
 \___ \  | | | | | |    
  ___) | | |_| | | |___ 
 |____/   \___/  |_____|

 Sons of Liberty Encryption System
 Made by Lazar
"""

SALT_SIZE = 16
NONCE_SIZE = 12
KEY_LEN = 32
PBKDF2_ITERATIONS = 100000

# FOXDIE Trigger Parameters
MAX_ATTEMPTS = 100
TIME_WINDOW_SECONDS = 60
FAILED_ATTEMPTS = deque()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    clear_screen()
    print(HEADER)
    print("=" * 50)

def register_failed_attempt():
    """Tracks failed password attempts and triggers FOXDIE if limit is breached."""
    now = time.time()
    FAILED_ATTEMPTS.append(now)

    while FAILED_ATTEMPTS and FAILED_ATTEMPTS[0] < now - TIME_WINDOW_SECONDS:
        FAILED_ATTEMPTS.popleft()

    if len(FAILED_ATTEMPTS) >= MAX_ATTEMPTS:
        trigger_foxdie()

def trigger_foxdie():
    """FOXDIE Protocol: Permanent asset purging, workstation lock, and emergency shutdown."""
    print("\n" + "!" * 50)
    print(" [!] CRITICAL WARNING: FOXDIE PROTOCOL ACTIVATED [!]")
    print("     BRUTE-FORCE ANOMALY DETECTED (>100 ATTEMPTS/MIN)")
    print("!" * 50 + "\n")
    time.sleep(1)

    print("[🔥] FOXDIE: Overwriting and purging all .sole files...")
    sole_files = glob.glob("**/*.sole", recursive=True) + glob.glob("*.sole")
    for fpath in set(sole_files):
        try:
            size = os.path.getsize(fpath)
            with open(fpath, 'wb') as f:
                f.write(os.urandom(size))
            os.remove(fpath)
            print(f"     [-] Purged: {fpath}")
        except Exception:
            pass

    print("[🔒] FOXDIE: Locking system access...")
    if os.name == 'nt':
        os.system("rundll32.exe user32.dll,LockWorkStation")
    else:
        os.system("gnome-screensaver-command -l || loginctl lock-session || xscreensaver-command -lock")

    time.sleep(1)

    print("[☠️] FOXDIE: Initiating emergency system power off...")
    if os.name == 'nt':
        os.system("shutdown /s /f /t 0")
    else:
        os.system("shutdown -h now")

    sys.exit(1)

def get_usb_serial(mount_path: str) -> bytes:
    """Retrieves the physical hardware serial number of the USB drive (Linux/Windows)."""
    try:
        if os.name == 'posix':
            # Query udevadm on Linux to pull ID_SERIAL_SHORT
            res = subprocess.run(
                ["df", "--output=source", mount_path],
                capture_output=True, text=True, check=True
            )
            device_node = res.stdout.strip().split('\n')[-1]
            udev_res = subprocess.run(
                ["udevadm", "info", "--query=property", "--name=" + device_node],
                capture_output=True, text=True, check=True
            )
            for line in udev_res.stdout.splitlines():
                if "ID_SERIAL_SHORT=" in line or "ID_SERIAL=" in line:
                    return line.split('=')[1].strip().encode('utf-8')
        elif os.name == 'nt':
            # Query wmic on Windows for VolumeSerialNumber
            drive_letter = os.path.splitdrive(mount_path)[0]
            res = subprocess.run(
                ["wmic", "logicaldisk", "where", f"DeviceID='{drive_letter}'", "get", "VolumeSerialNumber"],
                capture_output=True, text=True, check=True
            )
            lines = [l.strip() for l in res.stdout.splitlines() if l.strip()]
            if len(lines) > 1:
                return lines[1].encode('utf-8')
    except Exception as e:
        print(f"[!] Warning: Hardware serial check fallback ({e})")
    
    # Fallback to mount path string if raw serial extraction fails
    return mount_path.encode('utf-8')

def derive_key(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LEN,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(passphrase.encode('utf-8'))

def derive_hardware_key(raw_keycard_bytes: bytes, usb_path: str, salt: bytes) -> bytes:
    """Mixes raw keycard bytes with the physical USB hardware serial number."""
    serial = get_usb_serial(usb_path)
    combined_seed = raw_keycard_bytes + serial
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LEN,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(combined_seed)

def list_usb_drives():
    drives = []
    for p in psutil.disk_partitions(all=False):
        if 'removable' in p.opts.lower() or 'usb' in p.opts.lower() or p.mountpoint.startswith('/media') or p.mountpoint.startswith('/run/media'):
            drives.append(p.mountpoint)
    return drives

def select_usb_drive():
    drives = list_usb_drives()
    if not drives:
        print("[!] No USB removable drives detected.")
        manual = parse_drag_drop_paths(input("Drag and drop USB folder or enter path manually (or Enter to cancel): "))
        return manual[0] if manual else None
    
    print("\n[+] Detected USB Devices:")
    for idx, drive in enumerate(drives, 1):
        print(f"  [{idx}] {drive}")
    
    choice = input("\nSelect USB device number: ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(drives):
        return drives[int(choice) - 1]
    return None

def parse_drag_drop_paths(input_str: str) -> list:
    if not input_str.strip():
        return []
    try:
        paths = shlex.split(input_str, posix=False)
        cleaned = [p.strip('"\'') for p in paths]
    except Exception:
        cleaned = [p.strip('"\'') for p in input_str.split()]
    return [p for p in cleaned if os.path.exists(p)]

def get_target_files(paths: list, extension_filter: str = None) -> list:
    file_list = []
    for p in paths:
        if os.path.isfile(p):
            if not extension_filter or p.endswith(extension_filter):
                file_list.append(p)
        elif os.path.isdir(p):
            for root, _, files in os.walk(p):
                for f in files:
                    full_p = os.path.join(root, f)
                    if not extension_filter or full_p.endswith(extension_filter):
                        file_list.append(full_p)
    return list(set(file_list))

def wipe_and_remove(file_path: str):
    """Securely overwrites original file prior to deletion."""
    try:
        size = os.path.getsize(file_path)
        with open(file_path, 'wb') as f:
            f.write(os.urandom(size))
        os.remove(file_path)
        print(f"  [🔥] Auto-purged: {os.path.basename(file_path)}")
    except Exception as e:
        print(f"  [!] Failed to purge {file_path}: {e}")

def encrypt_file(file_path: str, keycard_path: str = None, passphrase: str = None, wipe_original: bool = False):
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)

    if keycard_path:
        raw_key = os.urandom(KEY_LEN)
        keycard_file = os.path.join(keycard_path, f"{os.path.basename(file_path)}.keycard")
        with open(keycard_file, 'wb') as f:
            f.write(raw_key)
        
        # Key is cryptographically bound to raw keycard + physical USB serial
        key = derive_hardware_key(raw_key, keycard_path, salt)
        print(f"  [+] Hardware-Bound Keycard created: {os.path.basename(keycard_file)}")
    else:
        key = derive_key(passphrase, salt)

    aesgcm = AESGCM(key)
    with open(file_path, 'rb') as f:
        data = f.read()

    ciphertext = aesgcm.encrypt(nonce, data, None)
    out_path = file_path + ".sole"

    with open(out_path, 'wb') as f:
        f.write(salt + nonce + ciphertext)

    print(f"  [✔] Encrypted: {os.path.basename(file_path)} -> {os.path.basename(out_path)}")

    if wipe_original:
        wipe_and_remove(file_path)

def decrypt_file(file_path: str, keycard_path: str = None, passphrase: str = None):
    with open(file_path, 'rb') as f:
        content = f.read()

    salt = content[:SALT_SIZE]
    nonce = content[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
    ciphertext = content[SALT_SIZE + NONCE_SIZE:]

    if keycard_path:
        orig_filename = os.path.basename(file_path).replace(".sole", "")
        keycard_file = os.path.join(keycard_path, f"{orig_filename}.keycard")
        if not os.path.exists(keycard_file):
            print(f"  [!] Keycard not found for: {os.path.basename(file_path)}")
            register_failed_attempt()
            return
        with open(keycard_file, 'rb') as f:
            raw_key = f.read()
            
        key = derive_hardware_key(raw_key, keycard_path, salt)
    else:
        key = derive_key(passphrase, salt)

    try:
        aesgcm = AESGCM(key)
        decrypted_data = aesgcm.decrypt(nonce, ciphertext, None)
        out_path = file_path[:-5] if file_path.endswith(".sole") else file_path + ".decrypted"
        with open(out_path, 'wb') as f:
            f.write(decrypted_data)
        print(f"  [✔] Decrypted: {os.path.basename(file_path)} -> {os.path.basename(out_path)}")
        
        # AUTOMATIC CLEANUP: Purge and remove the .sole file upon successful decryption
        wipe_and_remove(file_path)

    except Exception:
        print(f"  [!] Decryption failed for: {os.path.basename(file_path)} (Wrong key / hardware serial mismatch)")
        register_failed_attempt()

def self_destruct():
    sole_files = glob.glob("**/*.sole", recursive=True) + glob.glob("*.sole")
    sole_files = list(set(sole_files))
    
    if not sole_files:
        print("[!] No .sole files found to destruct.")
        return

    print(f"[!] Found {len(sole_files)} file(s) ending with .sole.")
    confirm = input("Are you sure you want to PERMANENTLY DESTROY all .sole files? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("[*] Aborted self-destruct operation.")
        return

    for fpath in sole_files:
        wipe_and_remove(fpath)

def main():
    if len(sys.argv) > 1 and sys.argv[1] in ['--foxdie', '-f']:
        trigger_foxdie()

    print_banner()
    print("1. Encrypt (Drag and Drop files/folders)")
    print("2. Decrypt (Drag and Drop .sole files/folders)")
    print("3. Self-Destruct (.sole purge)")
    
    choice = input("\nSelect option (1-3): ").strip()

    if choice == '1':
        print_banner()
        use_keycard = input("Encrypt using USB keycard mode? (yes/no): ").strip().lower() in ['y', 'yes']
        keycard_path = None
        passphrase = None

        if use_keycard:
            keycard_path = select_usb_drive()
            if not keycard_path:
                print("[!] USB selection failed.")
                return
        else:
            passphrase = input("Enter encryption passcode: ").strip()
            if not passphrase:
                print("[!] Passcode cannot be empty.")
                return

        raw_files = input("\nDRAG & DROP file(s) or folder(s) here, then press Enter: ")
        parsed_paths = parse_drag_drop_paths(raw_files)
        files = get_target_files(parsed_paths)

        if not files:
            print("[!] No valid files found.")
            return

        wipe_orig = input("\nDelete/wipe original files after encryption? (yes/no): ").strip().lower() in ['y', 'yes']

        print(f"\n[+] Encrypting {len(files)} file(s)...")
        for f in files:
            encrypt_file(f, keycard_path=keycard_path, passphrase=passphrase, wipe_original=wipe_orig)
        print("\n[✔] Operation Complete.")

    elif choice == '2':
        print_banner()
        use_keycard = input("Decrypt using USB keycard mode? (yes/no): ").strip().lower() in ['y', 'yes']
        keycard_path = None
        passphrase = None

        if use_keycard:
            keycard_path = select_usb_drive()
            if not keycard_path:
                print("[!] USB selection failed.")
                return
        else:
            passphrase = input("Enter decryption passcode: ").strip()

        raw_files = input("\nDRAG & DROP .sole file(s) or folder(s) here, then press Enter: ")
        parsed_paths = parse_drag_drop_paths(raw_files)
        files = get_target_files(parsed_paths, extension_filter=".sole")

        if not files:
            print("[!] No .sole files found.")
            return

        print(f"\n[+] Decrypting {len(files)} file(s)...")
        for f in files:
            decrypt_file(f, keycard_path=keycard_path, passphrase=passphrase)
        print("\n[✔] Operation Complete.")

    elif choice == '3':
        print_banner()
        self_destruct()

    else:
        print("[!] Invalid option selected.")

if __name__ == "__main__":
    main()
