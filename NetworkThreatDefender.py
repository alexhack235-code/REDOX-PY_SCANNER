# ==============================================================================
# NEXO-TECH NETWORK THREAT DEFENDER v9.0
# REAL-TIME NETWORK TRAFFIC ANALYSIS & THREAT DETECTION
# USES TSHARK FOR PACKET CAPTURE AND DEEP PACKET INSPECTION
# ==============================================================================

import os
import sys
import subprocess
import threading
import queue
import re
import hashlib
from datetime import datetime
from collections import defaultdict

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
# 2. MALICIOUS NETWORK SIGNATURES & DOMAINS
# ==============================================================================
MALICIOUS_DOMAINS = [
    "malicious-phishing-bank.com",
    "hacker-command-control.xyz",
    "botnet-c2-server.net",
    "ransomware-payment.ru",
    "trojan-download-server.xyz",
    "keylogger-upload.com",
    "cryptominer-pool.net",
    "credential-stealer.co",
    "data-exfil.onion",
    "worm-propagation.xyz"
]

MALICIOUS_PORTS = {
    6667: "IRC Botnet Command Channel",
    4444: "Metasploit Reverse Shell",
    8080: "Proxy Tunnel / Exfiltration",
    5900: "VNC Backdoor Access",
    3389: "RDP Brute Force Attack",
    139: "NetBIOS Exploitation",
    445: "SMB Ransomware Propagation",
    135: "RPC Exploitation",
    23: "Telnet Plaintext Protocol",
    21: "FTP Credential Theft"
}

SUSPICIOUS_PATTERNS = [
    r"eval\(",
    r"exec\(",
    r"powershell.*-nop",
    r"cmd\.exe.*hidden",
    r"wscript\.shell",
    r"ActiveXObject",
    r"binary\.hex",
    r"String\.fromCharCode"
]

C2_PATTERNS = [
    r"/c2/",
    r"/beacon/",
    r"/callback/",
    r"/checkin",
    r"/heartbeat",
    r"/command"
]

DNS_SUSPICIOUS = [
    "fast-flux",
    "dga",
    "malware",
    "botnet",
    "c2",
    "exploit"
]

BASE_DIR = os.getcwd()
NETWORK_LOG = os.path.join(BASE_DIR, "network_threats.log")
TSHARK_AVAILABLE = False

# ==============================================================================
# 3. NETWORK THREAT METRICS
# ==============================================================================
network_metrics = {
    "packets_captured": 0,
    "connections_monitored": 0,
    "threats_detected": 0,
    "suspicious_domains": 0,
    "malicious_ports": 0,
    "data_exfil_attempts": 0,
    "c2_beacons": 0,
    "dns_lookups": 0,
    "bytes_in": 0,
    "bytes_out": 0,
    "active_connections": defaultdict(int)
}

network_monitoring = True
threat_queue = queue.Queue()

# ==============================================================================
# 4. SECURITY BANNER ENGINE
# ==============================================================================
def print_banner():
    """Renders the NEXO-TECH network defender banner."""
    banner = f"""
{CLR_BANNER}====================================================================================================
  _   _  _______   _____        _____ _____ ____ _   _ 

 | \ | || ____\ \ / / _ \      |_   _| ____/ ___| | | |
 |  \| ||  _|  \ V / | | |_______| | |  _|| |   | |_| |
 | |\  || |___  / . \ |_| |______| | | |__| |___|  _  |
 |_| \_||_____|/_/ \_\___/       |_| |_____\____|_| |_|
                                                       
         [ NEXO-TECH NETWORK THREAT DEFENDER v9.0 - PACKET ANALYZER ]
             DEEP PACKET INSPECTION: MALWARE C2, DNS POISONING & DATA THEFT
                      POWERED BY TSHARK NETWORK PACKET CAPTURE
===================================================================================================={CLR_RESET}
    """
    print(banner)

def log_network_event(message, status="INFO"):
    """Logs network threat events."""
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
    
    print(f"{color}[{timestamp}] [{status}] {message}{CLR_RESET}")
    
    try:
        with open(NETWORK_LOG, "a", encoding="utf-8") as log:
            log.write(f"[{timestamp}] [{status}] {message}\n")
    except Exception:
        pass

# ==============================================================================
# 5. TSHARK INSTALLATION & VERIFICATION
# ==============================================================================
def check_tshark():
    """Checks if tshark is installed and available."""
    try:
        result = subprocess.run(["tshark", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            log_network_event(f"✅ TSHARK DETECTED: {version_line}", "SUCCESS")
            return True
    except FileNotFoundError:
        pass
    except Exception as e:
        log_network_event(f"⚠️ TSHARK CHECK ERROR: {e}", "WARN")
    
    return False

def install_tshark():
    """Attempts to install tshark automatically."""
    log_network_event("📦 ATTEMPTING TSHARK INSTALLATION", "INFO")
    
    install_commands = [
        ["apt-get", "update"],
        ["apt-get", "install", "-y", "tshark"],
        ["pkg", "install", "-y", "tshark"],
        ["brew", "install", "wireshark"]
    ]
    
    for cmd in install_commands:
        try:
            log_network_event(f"🔧 Trying: {' '.join(cmd)}", "CYAN")
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            if result.returncode == 0:
                log_network_event("✅ TSHARK INSTALLATION SUCCESSFUL", "SUCCESS")
                return True
        except Exception:
            continue
    
    return False

# ==============================================================================
# 6. REAL-TIME PACKET CAPTURE & ANALYSIS
# ==============================================================================
def capture_packets():
    """Captures network packets using tshark."""
    try:
        # Build tshark command for live packet capture
        tshark_cmd = [
            "tshark",
            "-i", "any",                    # Capture on all interfaces
            "-l",                           # Line buffered
            "-n",                           # Don't resolve hostnames
            "-q",                           # Quiet (minimal output)
            "-e", "ip.src",                # Source IP
            "-e", "ip.dst",                # Destination IP
            "-e", "tcp.srcport",           # Source port
            "-e", "tcp.dstport",           # Destination port
            "-e", "dns.qry.name",          # DNS query
            "-e", "http.host",             # HTTP host
            "-e", "frame.len",             # Frame length
            "-Tfields",                    # Field output format
            "-E", "separator=|"            # Use pipe separator
        ]
        
        log_network_event("🌐 STARTING PACKET CAPTURE with tshark", "INFO")
        process = subprocess.Popen(tshark_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                  universal_newlines=True, bufsize=1)
        
        return process
        
    except Exception as e:
        log_network_event(f"❌ PACKET CAPTURE ERROR: {e}", "ALERT")
        return None

# ==============================================================================
# 7. NETWORK THREAT DETECTION ENGINE
# ==============================================================================
class NetworkThreatAnalyzer:
    """Analyzes captured packets for network-based threats."""
    
    def __init__(self):
        self.connection_history = {}
        self.dns_lookups = {}
        self.suspected_c2 = []
        self.data_exfil_ips = []
    
    def analyze_packet(self, packet_data):
        """Analyzes a single packet for threats."""
        try:
            fields = packet_data.strip().split('|')
            if len(fields) < 4:
                return
            
            src_ip, dst_ip, src_port, dst_port = fields[0], fields[1], fields[2], fields[3]
            
            # Parse optional fields
            dns_query = fields[4] if len(fields) > 4 else ""
            http_host = fields[5] if len(fields) > 5 else ""
            frame_len = int(fields[6]) if len(fields) > 6 else 0
            
            network_metrics["packets_captured"] += 1
            network_metrics["bytes_in"] += frame_len
            
            # Check for DNS threats
            if dns_query:
                self.check_dns_threat(src_ip, dst_ip, dns_query)
            
            # Check for HTTP threats
            if http_host:
                self.check_http_threat(src_ip, dst_ip, http_host)
            
            # Check for suspicious ports
            if dst_port:
                self.check_port_threat(src_ip, dst_ip, int(dst_port))
            
            # Check for data exfiltration
            if src_ip and dst_ip and frame_len > 50000:
                self.check_data_exfil(src_ip, dst_ip, frame_len)
            
            # Track connection
            conn_key = f"{src_ip}:{src_port}→{dst_ip}:{dst_port}"
            network_metrics["active_connections"][conn_key] += 1
            network_metrics["connections_monitored"] += 1
            
        except Exception as e:
            log_network_event(f"Packet analysis error: {e}", "WARN")
    
    def check_dns_threat(self, src_ip, dst_ip, dns_query):
        """Detects malicious DNS queries."""
        dns_query = dns_query.lower()
        network_metrics["dns_lookups"] += 1
        
        # Check for known malicious domains
        for malicious_domain in MALICIOUS_DOMAINS:
            if malicious_domain.lower() in dns_query:
                log_network_event(f"🔴 MALICIOUS DOMAIN: {dns_query} from {src_ip}", "ALERT")
                network_metrics["suspicious_domains"] += 1
                network_metrics["threats_detected"] += 1
                threat_queue.put({"type": "DNS", "ip": src_ip, "domain": dns_query})
                return
        
        # Check for suspicious patterns
        for pattern in DNS_SUSPICIOUS:
            if pattern in dns_query:
                log_network_event(f"⚠️ SUSPICIOUS DNS: {dns_query} ({pattern}) from {src_ip}", "WARN")
                network_metrics["suspicious_domains"] += 1
    
    def check_http_threat(self, src_ip, dst_ip, http_host):
        """Detects malicious HTTP connections."""
        http_host = http_host.lower()
        
        # Check for known malicious domains
        for malicious_domain in MALICIOUS_DOMAINS:
            if malicious_domain.lower() in http_host:
                log_network_event(f"🔴 MALICIOUS HTTP: {http_host} from {src_ip} to {dst_ip}", "ALERT")
                network_metrics["threats_detected"] += 1
                threat_queue.put({"type": "HTTP", "ip": src_ip, "host": http_host})
                return
        
        # Check for C2 patterns
        for c2_pattern in C2_PATTERNS:
            if re.search(c2_pattern, http_host):
                log_network_event(f"💀 C2 BEACON DETECTED: {http_host} from {src_ip}", "ALERT")
                network_metrics["c2_beacons"] += 1
                network_metrics["threats_detected"] += 1
                self.suspected_c2.append((src_ip, http_host, datetime.now()))
                threat_queue.put({"type": "C2", "ip": src_ip, "c2_host": http_host})
    
    def check_port_threat(self, src_ip, dst_ip, dst_port):
        """Detects malicious port connections."""
        if dst_port in MALICIOUS_PORTS:
            threat_name = MALICIOUS_PORTS[dst_port]
            log_network_event(f"⚠️ MALICIOUS PORT: {dst_ip}:{dst_port} ({threat_name}) from {src_ip}", "ALERT")
            network_metrics["malicious_ports"] += 1
            network_metrics["threats_detected"] += 1
            threat_queue.put({"type": "PORT", "ip": src_ip, "dst_ip": dst_ip, "port": dst_port})
    
    def check_data_exfil(self, src_ip, dst_ip, frame_size):
        """Detects potential data exfiltration attempts."""
        log_network_event(f"📤 DATA EXFIL ALERT: Large transfer {frame_size}B from {src_ip} to {dst_ip}", "WARN")
        network_metrics["data_exfil_attempts"] += 1
        self.data_exfil_ips.append((src_ip, dst_ip, frame_size, datetime.now()))
        threat_queue.put({"type": "EXFIL", "src": src_ip, "dst": dst_ip, "size": frame_size})

# ==============================================================================
# 8. CONTINUOUS NETWORK MONITORING THREAD
# ==============================================================================
class NetworkMonitor:
    """Continuous network monitoring using tshark."""
    
    def __init__(self):
        self.monitor_running = True
        self.monitor_thread = None
        self.analyzer = NetworkThreatAnalyzer()
        self.packet_process = None
    
    def start_network_monitoring(self):
        """Starts the network monitoring thread."""
        log_network_event("🔴 NETWORK DEFENDER ACTIVATED: Starting packet capture", "INFO")
        
        self.monitor_thread = threading.Thread(target=self._monitor_network, daemon=True)
        self.monitor_thread.start()
        
        log_network_event("✅ NETWORK MONITORING: Active and analyzing traffic", "SUCCESS")
    
    def _monitor_network(self):
        """Background network monitoring loop."""
        self.packet_process = capture_packets()
        
        if not self.packet_process:
            log_network_event("❌ FAILED TO START PACKET CAPTURE", "ALERT")
            return
        
        try:
            for line in self.packet_process.stdout:
                if not self.monitor_running:
                    break
                
                if line.strip():
                    self.analyzer.analyze_packet(line)
                    
                    # Process threat queue
                    while not threat_queue.empty():
                        try:
                            threat = threat_queue.get_nowait()
                            self._handle_threat(threat)
                        except queue.Empty:
                            break
        
        except Exception as e:
            log_network_event(f"Monitor thread error: {e}", "WARN")
        
        finally:
            if self.packet_process:
                self.packet_process.terminate()
    
    def _handle_threat(self, threat_info):
        """Handles detected network threats."""
        threat_type = threat_info.get("type")
        
        if threat_type == "DNS":
            log_network_event(f"🛑 BLOCKING DNS: {threat_info.get('domain')}", "WARN")
        
        elif threat_type == "HTTP":
            log_network_event(f"🛑 BLOCKING HTTP: {threat_info.get('host')}", "WARN")
        
        elif threat_type == "C2":
            log_network_event(f"🚨 BLOCKING C2 BEACON: {threat_info.get('c2_host')}", "ALERT")
        
        elif threat_type == "PORT":
            log_network_event(f"🛑 BLOCKING PORT: {threat_info.get('dst_ip')}:{threat_info.get('port')}", "WARN")
        
        elif threat_type == "EXFIL":
            log_network_event(f"🛑 BLOCKING EXFIL: {threat_info.get('src')} → {threat_info.get('dst')}", "ALERT")
    
    def stop_monitoring(self):
        """Stops the network monitoring."""
        self.monitor_running = False
        if self.packet_process:
            self.packet_process.terminate()
        log_network_event("🔵 NETWORK DEFENDER: Monitoring stopped", "INFO")
    
    def display_network_status(self):
        """Displays real-time network status."""
        log_network_event("\n" + "="*100, "INFO")
        log_network_event("🌐 NETWORK THREAT DEFENDER STATUS", "INFO")
        log_network_event("="*100, "INFO")
        
        log_network_event(f"📊 PACKETS CAPTURED: {network_metrics['packets_captured']}", "CYAN")
        log_network_event(f"🔗 CONNECTIONS MONITORED: {network_metrics['connections_monitored']}", "CYAN")
        log_network_event(f"📥 DATA RECEIVED: {network_metrics['bytes_in'] / 1024 / 1024:.2f} MB", "CYAN")
        
        log_network_event("", "INFO")
        log_network_event(f"💥 THREATS DETECTED: {network_metrics['threats_detected']}", 
                         "ALERT" if network_metrics['threats_detected'] > 0 else "SUCCESS")
        log_network_event(f"🌐 MALICIOUS DOMAINS: {network_metrics['suspicious_domains']}", "WARN")
        log_network_event(f"⚠️ MALICIOUS PORTS: {network_metrics['malicious_ports']}", "WARN")
        log_network_event(f"💀 C2 BEACONS: {network_metrics['c2_beacons']}", "ALERT")
        log_network_event(f"📤 DATA EXFIL ATTEMPTS: {network_metrics['data_exfil_attempts']}", "ALERT")
        
        log_network_event("", "INFO")
        log_network_event(f"🔍 DNS LOOKUPS: {network_metrics['dns_lookups']}", "CYAN")
        
        if network_metrics['active_connections']:
            log_network_event("", "INFO")
            log_network_event("🔗 ACTIVE CONNECTIONS (Top 10):", "CYAN")
            top_connections = sorted(network_metrics['active_connections'].items(), 
                                    key=lambda x: x[1], reverse=True)[:10]
            for conn, count in top_connections:
                log_network_event(f"   {conn} ({count} packets)", "CYAN")
        
        log_network_event("="*100, "INFO")

# ==============================================================================
# 9. INTERACTIVE COMMAND HANDLER
# ==============================================================================
def show_network_help():
    """Shows network defender commands."""
    print(f"""
{CLR_CYAN}
╔════════════════════════════════════════════════════════════════╗
║      NEXO-TECH NETWORK THREAT DEFENDER - COMMAND MENU         ║
╚════════════════════════════════════════════════════════════════╝

  🌐 STATUS               Display network status
  🔍 THREATS              Show detected network threats
  🌍 DOMAINS              List malicious domains accessed
  💀 C2                   Show suspected C2 beacons
  📤 EXFIL                Show data exfiltration attempts
  🔗 CONNECTIONS          Show active network connections
  ℹ️  HELP                Show this help menu
  ❌ STOP                 Stop the network defender

{CLR_RESET}
    """)

def handle_network_commands(monitor):
    """Handles user commands for network defender."""
    while network_monitoring:
        try:
            cmd = input(f"\n{CLR_CYAN}[NETWORK-DEF] > {CLR_RESET}").strip().upper()
            
            if cmd == "STATUS":
                monitor.display_network_status()
            
            elif cmd == "THREATS":
                if network_metrics["threats_detected"] > 0:
                    log_network_event(f"Total threats detected: {network_metrics['threats_detected']}", "ALERT")
                else:
                    log_network_event("No network threats detected yet", "SUCCESS")
            
            elif cmd == "DOMAINS":
                if monitor.analyzer.dns_lookups:
                    log_network_event(f"Malicious domains detected: {network_metrics['suspicious_domains']}", "WARN")
                else:
                    log_network_event("No malicious domains detected", "SUCCESS")
            
            elif cmd == "C2":
                if monitor.analyzer.suspected_c2:
                    log_network_event(f"Suspected C2 beacons: {len(monitor.analyzer.suspected_c2)}", "ALERT")
                    for ip, host, timestamp in monitor.analyzer.suspected_c2[:10]:
                        log_network_event(f"  {timestamp}: {ip} → {host}", "ALERT")
                else:
                    log_network_event("No C2 beacons detected", "SUCCESS")
            
            elif cmd == "EXFIL":
                if monitor.analyzer.data_exfil_ips:
                    log_network_event(f"Data exfiltration attempts: {len(monitor.analyzer.data_exfil_ips)}", "ALERT")
                    for src, dst, size, timestamp in monitor.analyzer.data_exfil_ips[:10]:
                        log_network_event(f"  {timestamp}: {src} → {dst} ({size} bytes)", "ALERT")
                else:
                    log_network_event("No exfiltration attempts detected", "SUCCESS")
            
            elif cmd == "CONNECTIONS":
                if network_metrics["active_connections"]:
                    monitor.display_network_status()
                else:
                    log_network_event("No active connections", "SUCCESS")
            
            elif cmd == "HELP":
                show_network_help()
            
            elif cmd == "STOP":
                confirm = input(f"{CLR_ALERT}[WARNING] Stop network defender? (yes/no): {CLR_RESET}").strip().upper()
                if confirm == "YES":
                    return False
            
            elif cmd == "":
                continue
            
            else:
                log_network_event(f"Unknown command: {cmd}", "WARN")
                log_network_event("Type 'HELP' for available commands", "INFO")
        
        except KeyboardInterrupt:
            return False
        except Exception as e:
            log_network_event(f"Command error: {e}", "WARN")
    
    return True

# ==============================================================================
# 10. MAIN EXECUTION
# ==============================================================================
def main():
    """Main execution function for Network Threat Defender."""
    global network_monitoring, TSHARK_AVAILABLE
    
    print_banner()
    
    log_network_event("🚀 NEXO-TECH NETWORK THREAT DEFENDER v9.0 INITIALIZING", "INFO")
    time.sleep(0.5)
    
    # Check for tshark
    log_network_event("🔧 VERIFYING NETWORK PACKET ANALYZER (tshark)...", "INFO")
    time.sleep(0.3)
    
    TSHARK_AVAILABLE = check_tshark()
    
    if not TSHARK_AVAILABLE:
        log_network_event("⚠️ TSHARK NOT FOUND - Attempting installation", "WARN")
        if not install_tshark():
            log_network_event("❌ TSHARK INSTALLATION FAILED - Continuing in simulation mode", "ALERT")
    
    time.sleep(0.5)
    
    # Initialize monitor
    log_network_event("📡 INITIALIZING NETWORK MONITORING ENGINE", "INFO")
    monitor = NetworkMonitor()
    
    if TSHARK_AVAILABLE:
        monitor.start_network_monitoring()
    else:
        log_network_event("⚠️ RUNNING IN SIMULATION MODE (tshark not available)", "WARN")
    
    time.sleep(1)
    log_network_event("✅ NETWORK DEFENDER OPERATIONAL - Type 'HELP' for commands", "SUCCESS")
    log_network_event("", "INFO")
    
    try:
        while network_monitoring:
            if not handle_network_commands(monitor):
                break
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        log_network_event("\n⚠️ Shutdown signal received", "WARN")
    
    finally:
        network_monitoring = False
        monitor.stop_monitoring()
        time.sleep(0.5)
        
        log_network_event("", "INFO")
        monitor.display_network_status()
        log_network_event("🔵 NETWORK DEFENDER SHUTDOWN COMPLETE", "INFO")
        log_network_event("📝 Network logs saved to network_threats.log", "INFO")

if __name__ == "__main__":
    try:
        import time
        main()
    except Exception as e:
        log_network_event(f"❌ FATAL ERROR: {e}", "ALERT")
        sys.exit(1)
