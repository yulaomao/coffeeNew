import socket
import time
import psutil
from typing import Optional, Dict, Any
import httpx
from loguru import logger

def check_internet_connection(host: str = "8.8.8.8", port: int = 53, timeout: int = 3) -> bool:
    """Check if internet connection is available"""
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False
    finally:
        socket.setdefaulttimeout(None)

def get_network_info() -> Dict[str, Any]:
    """Get current network information"""
    info = {
        "ip": None,
        "wifi_ssid": None,
        "wifi_signal": None,
        "connected": False
    }
    
    try:
        # Get IP address
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            info["ip"] = s.getsockname()[0]
        
        # Check connection
        info["connected"] = check_internet_connection()
        
        # Get WiFi info (mock for now, would need platform-specific implementation)
        info["wifi_ssid"] = "CoffeeMachine_WiFi"
        info["wifi_signal"] = -45  # dBm
        
    except Exception as e:
        logger.error(f"Failed to get network info: {e}")
    
    return info

def measure_bandwidth(url: str = "https://httpbin.org/bytes/1024", timeout: int = 10) -> Optional[float]:
    """Measure download bandwidth in bytes per second"""
    try:
        start_time = time.time()
        with httpx.Client(timeout=timeout) as client:
            response = client.get(url)
            response.raise_for_status()
            
        end_time = time.time()
        duration = end_time - start_time
        bytes_downloaded = len(response.content)
        
        return bytes_downloaded / duration if duration > 0 else None
    except Exception as e:
        logger.error(f"Failed to measure bandwidth: {e}")
        return None

def get_network_interfaces() -> Dict[str, Dict[str, Any]]:
    """Get information about network interfaces"""
    interfaces = {}
    
    try:
        for interface, addrs in psutil.net_if_addrs().items():
            interface_info = {
                "addresses": [],
                "is_up": False
            }
            
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    interface_info["addresses"].append({
                        "type": "IPv4",
                        "address": addr.address,
                        "netmask": addr.netmask,
                        "broadcast": addr.broadcast
                    })
                elif addr.family == socket.AF_INET6:
                    interface_info["addresses"].append({
                        "type": "IPv6", 
                        "address": addr.address,
                        "netmask": addr.netmask
                    })
            
            # Check if interface is up
            stats = psutil.net_if_stats().get(interface)
            if stats:
                interface_info["is_up"] = stats.isup
            
            interfaces[interface] = interface_info
    
    except Exception as e:
        logger.error(f"Failed to get network interfaces: {e}")
    
    return interfaces

def ping_host(host: str, timeout: int = 5) -> Optional[float]:
    """Ping a host and return round-trip time in milliseconds"""
    try:
        start_time = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, 80))
        end_time = time.time()
        sock.close()
        
        if result == 0:
            return (end_time - start_time) * 1000  # Convert to milliseconds
        return None
    except Exception:
        return None