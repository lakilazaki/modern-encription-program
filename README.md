An advanced, cross-platform file encryption utility written in Python. It provides authenticated AES-GCM encryption, hardware-bound USB keycard support, secure multi-pass file purging, and active anti-tamper brute-force protection.

​👨‍💻 About The Author
​Hi! I am Lazar, an aspiring Cybersecurity & Digital Forensics specialist.
​I built this tool to demonstrate practical concepts in modern cryptography, low-level OS hardware interaction, and anti-forensic security controls. I am actively preparing my portfolio to apply for specialized higher education degrees in High Tech / Cybersecurity / Digital Forensics Engineering (VTK / High ICT studies).

​🔥 Key Features
​Authenticated Encryption: Uses AES-256-GCM (Galois/Counter Mode) via standard cryptography libraries, ensuring both confidentiality and data integrity.
​Hardware-Bound Keycards: Option to bind encryption keycards to the physical hardware serial number (ID_SERIAL_SHORT / VolumeSerialNumber) of a plugged-in USB removable drive.
​Robust Key Derivation: Uses PBKDF2-HMAC-SHA256 with 100,000 iterations and cryptographic salting to defeat pre-computed dictionary attacks.
​Secure Wipe & Auto-Purge: Implements urandom memory overwriting on original files before deletion to prevent forensic data recovery.
​FOXDIE Protocol (Anti-Tamper & Brute-Force Shield): Monitors failed decryption/keycard attempts. If a brute-force threshold is reached (e.g., >100 attempts/min), it automatically triggers asset purging, locks the operating system, and initiates emergency power-off.
​Cross-Platform: Supports Linux and Windows natively for hardware queries and system commands.

​🚀 Installation & Prerequisites
clone the repo

install requierments
pip install cryptography psutil

and run it
python3 sol_enc.py

Menu Options:
​Encrypt:
​Choose between Passphrase or USB Hardware Keycard mode.
​Drag and drop files/folders directly into the terminal.
​Optional secure purge of original raw files after encryption.
​Decrypt:
​Provide the passcode or insert the hardware-bound USB Keycard.
​Drag and drop .sole encrypted files/folders.
​Self-Destruct:
​Securely overwrites and purges all .sole encrypted assets within the working directory.
​🛡️ Disclaimer
​This project is created strictly for educational and portfolio demonstration purposes. It was developed as part of hands-on practical training in applied cryptography and digital forensics engineering.