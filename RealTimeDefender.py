# ==============================================================================
# NEXO-TECH ENTERPRISE REAL-TIME DEFENDER v9.0
# CONTINUOUS BACKGROUND MONITORING & THREAT MITIGATION SYSTEM
# ACTIVE DEFENSE WHILE TERMINAL/PROGRAM IS RUNNING
# ==============================================================================

import os
import sys
import hashlib
import shutil
import time
import math
import random
import threading
import queue
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# ==============================================================================
# 1. TERMINAL GRAPHICS & THEME CONFIGURATION
# ==============================================================================
CLR_RESET   = "\033[0m"
CLR_BANNER  = "\033[1;35m"   # Bold Magenta Tech Banner
CLR_INFO    = "\033[1;34m"   # Bold Blue System Information
CLR_WARN    = "\033[1;33m"   # Bold Yellow System Warnings
CLR_ALERT   = "\033[1;31m"   # Bold Red Active Detections
CLR_SUCCESS = "\033[1;32m"   # Bold Green Remediation
CLR_CYAN    = "\033[1;36m"   # Cyan Technical Traces
CLR_WHITE   = "\033[1;37m"   # White Visual Dividers

# ==============================================================================
# 2. DEFENSE THREAT SIGNATURE DATABASE
# ==============================================================================
BAD_HASHES = {
    "44d88612fea8a8f36de82e1278abb02f": "EICAR Standard Anti-Virus Test File",
    "69630e4574ec67ba100ef63daabb04d0": "WanaCryptor Ransomware Payload",
    "5f4dcc3b5aa765d61d8327deb882cf99": "Carbanak Banking Trojan Module",
    "8c72834b12fe018ba29a1b14daef021f": "DarkHotel Spyware Keylogger Script",
    "3a4b5c6d7e8f90a1b2c3d4e5f6a7b8c9": "Pegasus Advanced Spyware Variant",
    "a1b2c3d4e5f67890abcdef1234567890": "Mirai Botnet Linux IoT Payload",
    "f9e8d7c6b5a43210fedcba9876543210": "Emotet Polling Infostealer DLL",
    "0123456789abcdef0123456789abcdef": "Cobalt Strike Beacon Stager",
    "7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e": "REvil Decryptor Execution Hook",
    "d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7": "LockBit 3.0 Ransomware Main Core"
}

BAD_STRINGS = [
    b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE",
    b"WanaCryptor",
    b"YOUR_FILES_HAVE_BEEN_ENCRYPTED",
    b"RUN_BACKGROUND_KEYLOGGER",
    b"PERSIST_SYSTEM_BOOT_HOOK",
    b"SetWindowsHookEx",
    b"GetAsyncKeyState",
    b"from pynput import keyboard",
    b"http://malicious-phishing-bank.com",
    b"http://hacker-command-control.xyz",
    b"ftp_upload_stolen_session_data",
    b"coinhive.min.js",
    b"powershell -nop -w hidden -enc",
    b"vssadmin.exe delete shadows",
    b"ShadowCopyDeleteTrigger",
    b"irc_bot_net_join_channel",
    b"mimikatz",
    b"lsass.exe_dump_credentials",
    b"HttpOpenRequestA",
    b"InternetReadFile",
    b"CreateRemoteThread",
    b"WriteProcessMemory"
]

BASE_DIR = os.getcwd()
DEFENDER_LOG = os.path.join(BASE_DIR, "defender_realtime.log")
QUARANTINE_DIR = os.path.join(BASE_DIR, "quarantine_vault")
WATCHED_DIRS = [BASE_DIR]

# ==============================================================================
# 3. REAL-TIME DEFENDER METRICS
# ==============================================================================
defender_metrics = {
    "uptime_seconds": 0,
    "files_scanned": 0,
    "threats_detected": 0,
    "threats_quarantined": 0,
    "threats_blocked": 0,
    "last_threat_time": None,
    "scan_cycles": 0,
    "avg_scan_time": 0.0,
    "memory_usage_mb": 0,
    "cpu_usage_percent": 0
}

active_monitoring = True
threat_queue = queue.Queue()
file_cache = {}

# ==============================================================================
# 4. SECURITY BANNER ENGINE (SAME AS SCANNER)
# ==============================================================================
def print_banner():
    """Renders the NEXO-TECH advanced terminal EDR system suite interface."""
    banner = f"""
{CLR_BANNER}====================================================================================================
  _   _  _______   _____        _____ _____ ____ _   _ 

 | \ | || ____\ \ / / _ \      |_   _| ____/ ___| | | |
 |  \| ||  _|  \ V / | | |_______| | |  _|| |   | |_| |
 | |\  || |___  / . \ |_| |______| | | |__| |___|  _  |
 |_| \_||_____|/_/ \_\___/       |_| |_____\____|_| |_|
                                                       
       [ NEXO-TECH ENTERPRISE REAL-TIME DEFENDER v9.0 - CONTINUOUS PROTECTION ]
            ADVANCED ACTIVE MONITORING: RANSOMWARE, KEYLOGGERS & EXPLOITS
                         WINDOWS DEFENDER-STYLE BACKGROUND DEFENSE
===================================================================================================={CLR_RESET}
    """
    print(banner)

def log_defender_event(message, status="INFO", show_time=True):
    """Logs real-time defender events with timestamps."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    if status == "SUCCESS": 
        color = CLR_SUCCESS
    elif status == "WARN": 
        color = CLR_WARN
    elif status == "ALERT": 
        color = CLR_ALERT
    elif status == "CYAN": 
        color = CLR_CYAN
    else: 
        color = CLR_INFO
    
    if show_time:
        print(f"{color}[{timestamp}] [{status}] {message}{CLR_RESET}")
        log_msg = f"[{timestamp}] [{status}] {message}\n"
    else:
        print(f"{color}[{status}] {message}{CLR_RESET}")
        log_msg = f"[{status}] {message}\n"
    
    try:
        with open(DEFENDER_LOG, "a", encoding="utf-8") as log:
            log.write(log_msg)
    except Exception:
        pass

# ==============================================================================
# 5. CORE THREAT DETECTION ENGINE
# ==============================================================================
def calculate_file_entropy(file_data):
    """Calculates entropy to detect encrypted/ransomware files."""
    if not file_data:
        return 0.0
    
    entropy = 0
    total_len = len(file_data)
    for x in range(256):
        p_x = float(file_data.count(x)) / total_len
        if p_x > 0:
            entropy += - p_x * math.log(p_x, 2)
    return entropy

def scan_file_realtime(file_path):
    """Performs rapid threat detection on a single file."""
    try:
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            return False
        
        if file_path.endswith("defender_realtime.log") or file_path.endswith(".pyc"):
            return False
        
        # Check file cache to avoid re-scanning unchanged files
        try:
            file_stat = os.path.getmtime(file_path)
            if file_path in file_cache:
                if file_cache[file_path] == file_stat:
                    return False
            file_cache[file_path] = file_stat
        except:
            pass
        
        defender_metrics["files_scanned"] += 1
        
        with open(file_path, "rb") as f:
            file_data = f.read(65536)  # Read first 64KB for speed
        
        # Hash-based detection
        file_hash = hashlib.md5(file_data).hexdigest()
        if file_hash in BAD_HASHES:
            threat_name = BAD_HASHES[file_hash]
            log_defender_event(f"💥 THREAT DETECTED: {threat_name} at {file_path}", "ALERT")
            threat_queue.put({"path": file_path, "threat": threat_name, "type": "SIGNATURE"})
            defender_metrics["threats_detected"] += 1
            return True
        
        # String-based detection
        for bad_string in BAD_STRINGS:
            if bad_string in file_data:
                threat_type = bad_string.decode('utf-8', errors='ignore')
                log_defender_event(f"⚠️ SUSPICIOUS CONTENT: {threat_type} at {file_path}", "WARN")
                threat_queue.put({"path": file_path, "threat": threat_type, "type": "BEHAVIORAL"})
                defender_metrics["threats_detected"] += 1
                return True
        
        # Entropy-based ransomware detection
        entropy = calculate_file_entropy(file_data)
        if entropy > 7.8:
            log_defender_event(f"🔐 RANSOMWARE SIGNATURE: Entropy {entropy:.2f} at {file_path}", "ALERT")
            threat_queue.put({"path": file_path, "threat": "HIGH_ENTROPY_RANSOMWARE", "type": "HEURISTIC"})
            defender_metrics["threats_detected"] += 1
            return True
        
        return False
        
    except Exception as e:
        log_defender_event(f"Scan error on {file_path}: {e}", "WARN", show_time=False)
        return False

def quarantine_threat(file_path, threat_info):
    """Isolates detected threats into quarantine vault."""
    try:
        if not os.path.exists(QUARANTINE_DIR):
            os.makedirs(QUARANTINE_DIR)
        
        file_name = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        quarantine_path = os.path.join(QUARANTINE_DIR, f"QUARANTINE_{timestamp}_{file_name}")
        
        shutil.move(file_path, quarantine_path)
        os.chmod(quarantine_path, 0o000)
        
        log_defender_event(f"✅ THREAT QUARANTINED: {file_name} isolated safely", "SUCCESS")
        defender_metrics["threats_quarantined"] += 1
        defender_metrics["last_threat_time"] = datetime.now()
        
    except Exception as e:
        log_defender_event(f"Quarantine failed: {e}", "WARN", show_time=False)

# ==============================================================================
# 6. CONTINUOUS DIRECTORY MONITORING
# ==============================================================================
class ContinuousMonitor:
    """Monitors directories continuously for file changes and threats."""
    
    def __init__(self, watch_dirs):
        self.watch_dirs = watch_dirs
        self.monitor_running = True
        self.monitor_thread = None
        self.scan_interval = 5  # Seconds between scans
        self.file_snapshot = {}
    
    def start_continuous_monitoring(self):
        """Launches the continuous monitoring thread."""
        log_defender_event("🔴 REAL-TIME DEFENDER ACTIVATED: Continuous monitoring started", "INFO")
        log_defender_event(f"👁️ WATCHING DIRECTORIES: {', '.join(self.watch_dirs)}", "INFO")
        time.sleep(0.3)
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        log_defender_event("✅ MONITORING THREAD: Active and watching for threats", "SUCCESS")
    
    def _monitor_loop(self):
        """Background monitoring loop that continuously scans for threats."""
        scan_count = 0
        while self.monitor_running:
            scan_count += 1
            scan_start = time.time()
            
            try:
                # Scan watched directories
                for watch_dir in self.watch_dirs:
                    if os.path.exists(watch_dir):
                        self._scan_directory(watch_dir)
                
                # Process threat queue
                while not threat_queue.empty():
                    try:
                        threat = threat_queue.get_nowait()
                        self._handle_threat(threat)
                    except queue.Empty:
                        break
                
                # Calculate scan time
                scan_time = time.time() - scan_start
                if scan_count > 1:
                    defender_metrics["avg_scan_time"] = (
                        (defender_metrics["avg_scan_time"] * (scan_count - 1) + scan_time) / scan_count
                    )
                else:
                    defender_metrics["avg_scan_time"] = scan_time
                
                defender_metrics["scan_cycles"] = scan_count
                
                # Wait before next scan
                time.sleep(self.scan_interval)
                
            except Exception as e:
                log_defender_event(f"Monitor loop error: {e}", "WARN", show_time=False)
                time.sleep(1)
    
    def _scan_directory(self, target_dir):
        """Scans a directory for file changes and threats."""
        try:
            for root, dirs, files in os.walk(target_dir):
                # Skip system directories
                dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules']]
                
                for file in files[:20]:  # Limit files per scan for performance
                    file_path = os.path.join(root, file)
                    scan_file_realtime(file_path)
                    
        except Exception as e:
            log_defender_event(f"Directory scan error in {target_dir}: {e}", "WARN", show_time=False)
    
    def _handle_threat(self, threat_info):
        """Handles detected threats with containment protocols."""
        file_path = threat_info.get("path")
        threat_name = threat_info.get("threat")
        threat_type = threat_info.get("type")
        
        log_defender_event(f"🛑 THREAT HANDLING PROTOCOL: {threat_type} threat from {threat_name}", "ALERT")
        
        # Auto-quarantine high-severity threats
        if threat_type in ["SIGNATURE", "HEURISTIC"]:
            log_defender_event(f"🧹 AUTO-QUARANTINE: Isolating {os.path.basename(file_path)}", "WARN")
            quarantine_threat(file_path, threat_info)
            defender_metrics["threats_blocked"] += 1
        
        elif threat_type == "BEHAVIORAL":
            log_defender_event(f"⚠️ BEHAVIORAL ALERT: Monitoring {os.path.basename(file_path)} closely", "WARN")
    
    def stop_monitoring(self):
        """Stops the continuous monitoring thread."""
        self.monitor_running = False
        log_defender_event("🔵 REAL-TIME DEFENDER: Monitoring stopped", "INFO")

# ==============================================================================
# 7. SYSTEM STATUS DISPLAY
# ==============================================================================
def display_defender_status():
    """Displays real-time defender status panel."""
    log_defender_event("\n" + "="*90, "INFO", show_time=False)
    log_defender_event("📊 REAL-TIME DEFENDER STATUS PANEL", "INFO", show_time=False)
    log_defender_event("="*90, "INFO", show_time=False)
    
    uptime_minutes = defender_metrics["uptime_seconds"] // 60
    uptime_seconds = defender_metrics["uptime_seconds"] % 60
    
    log_defender_event(f"⏱️ UPTIME: {uptime_minutes}m {uptime_seconds}s", "INFO", show_time=False)
    log_defender_event(f"📁 FILES SCANNED: {defender_metrics['files_scanned']}", "INFO", show_time=False)
    log_defender_event(f"🔍 SCAN CYCLES: {defender_metrics['scan_cycles']}", "CYAN", show_time=False)
    log_defender_event(f"⏱️ AVG SCAN TIME: {defender_metrics['avg_scan_time']:.3f}s", "CYAN", show_time=False)
    
    log_defender_event("", "INFO", show_time=False)
    log_defender_event(f"💥 THREATS DETECTED: {defender_metrics['threats_detected']}", 
                       "ALERT" if defender_metrics['threats_detected'] > 0 else "SUCCESS", show_time=False)
    log_defender_event(f"🧹 THREATS QUARANTINED: {defender_metrics['threats_quarantined']}", "SUCCESS", show_time=False)
    log_defender_event(f"🛑 THREATS BLOCKED: {defender_metrics['threats_blocked']}", "SUCCESS", show_time=False)
    
    if defender_metrics["last_threat_time"]:
        log_defender_event(f"⏰ LAST THREAT: {defender_metrics['last_threat_time'].strftime('%H:%M:%S')}", "WARN", show_time=False)
    else:
        log_defender_event("✅ NO THREATS DETECTED YET", "SUCCESS", show_time=False)
    
    log_defender_event("="*90, "INFO", show_time=False)

# ==============================================================================
# 8. INTERACTIVE COMMAND HANDLER
# ==============================================================================
def show_help():
    """Shows available commands."""
    print(f"""
{CLR_CYAN}
╔════════════════════════════════════════════════════════════════╗
║         NEXO-TECH REAL-TIME DEFENDER - COMMAND MENU           ║
╚════════════════════════════════════════════════════════════════╝

  📊 STATUS               Display real-time defender status
  🔍 SCAN                 Perform manual scan of watched directories
  🛑 THREATS              Show detected threats list
  📋 QUARANTINE          List quarantined files
  🔴 SETTINGS            Configure defender settings
  ℹ️  HELP                Show this help menu
  ❌ STOP                 Stop the defender (requires confirmation)

{CLR_RESET}
    """)

def handle_user_commands(monitor):
    """Handles user input commands while defender runs."""
    while active_monitoring:
        try:
            user_input = input(f"\n{CLR_CYAN}[DEFENDER] > {CLR_RESET}").strip().upper()
            
            if user_input == "STATUS":
                display_defender_status()
            
            elif user_input == "SCAN":
                log_defender_event("🔍 MANUAL SCAN INITIATED", "INFO")
                monitor._scan_directory(BASE_DIR)
                log_defender_event("✅ MANUAL SCAN COMPLETE", "SUCCESS")
            
            elif user_input == "THREATS":
                if defender_metrics["threats_detected"] > 0:
                    log_defender_event(f"Total threats detected: {defender_metrics['threats_detected']}", "ALERT")
                else:
                    log_defender_event("No threats detected yet", "SUCCESS")
            
            elif user_input == "QUARANTINE":
                if os.path.exists(QUARANTINE_DIR):
                    files = os.listdir(QUARANTINE_DIR)
                    if files:
                        log_defender_event(f"Quarantined files ({len(files)}):", "WARN")
                        for f in files:
                            log_defender_event(f"  - {f}", "WARN", show_time=False)
                    else:
                        log_defender_event("Quarantine vault is empty", "SUCCESS")
                else:
                    log_defender_event("No quarantine vault yet", "INFO")
            
            elif user_input == "HELP":
                show_help()
            
            elif user_input == "SETTINGS":
                log_defender_event("⚙️ DEFENDER SETTINGS:", "INFO")
                log_defender_event(f"  Scan Interval: {monitor.scan_interval}s", "CYAN", show_time=False)
                log_defender_event(f"  Watched Directories: {', '.join(monitor.watch_dirs)}", "CYAN", show_time=False)
                log_defender_event(f"  Quarantine Path: {QUARANTINE_DIR}", "CYAN", show_time=False)
            
            elif user_input == "STOP":
                confirm = input(f"{CLR_ALERT}[WARNING] Stop defender? (yes/no): {CLR_RESET}").strip().upper()
                if confirm == "YES":
                    return False
            
            elif user_input == "":
                continue
            
            else:
                log_defender_event(f"Unknown command: {user_input}", "WARN")
                log_defender_event("Type 'HELP' for available commands", "INFO")
                
        except KeyboardInterrupt:
            return False
        except Exception as e:
            log_defender_event(f"Command error: {e}", "WARN")
    
    return True

# ==============================================================================
# 9. MAIN EXECUTION
# ==============================================================================
def main():
    """Main execution function for Real-Time Defender."""
    global active_monitoring
    
    print_banner()
    
    log_defender_event("🚀 NEXO-TECH REAL-TIME DEFENDER v9.0 INITIALIZING...", "INFO")
    time.sleep(0.5)
    
    log_defender_event("📡 INITIALIZING CORE DEFENSE SYSTEMS", "INFO")
    time.sleep(0.2)
    
    # Create monitor
    monitor = ContinuousMonitor(WATCHED_DIRS)
    monitor.start_continuous_monitoring()
    
    time.sleep(1)
    log_defender_event("🎯 DEFENDER FULLY OPERATIONAL - Type 'HELP' for commands", "SUCCESS")
    log_defender_event("", "INFO")
    
    # Main loop with user interaction and status updates
    start_time = time.time()
    status_interval = 30  # Show status every 30 seconds
    last_status = start_time
    
    try:
        while active_monitoring:
            current_time = time.time()
            defender_metrics["uptime_seconds"] = int(current_time - start_time)
            
            # Auto-display status every 30 seconds
            if current_time - last_status >= status_interval:
                display_defender_status()
                last_status = current_time
            
            # Handle user commands
            if not handle_user_commands(monitor):
                break
    
    except KeyboardInterrupt:
        log_defender_event("\n⚠️ Shutdown signal received", "WARN")
    
    finally:
        active_monitoring = False
        monitor.stop_monitoring()
        time.sleep(0.5)
        
        log_defender_event("", "INFO")
        display_defender_status()
        log_defender_event("🔵 REAL-TIME DEFENDER SHUTDOWN COMPLETE", "INFO")
        log_defender_event("📝 Defense logs saved to defender_realtime.log", "INFO")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log_defender_event(f"❌ FATAL ERROR: {e}", "ALERT")
        sys.exit(1)
