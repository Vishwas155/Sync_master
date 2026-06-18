import time
from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf
from config import get_device_name, get_port
from db import update_peer, get_all_peers

SERVICE_TYPE = "_obsync._tcp.local."
peers = {}

def on_service_state_change(zeroconf, service_type, name, state_change):
    if state_change == ServiceStateChange.Added:
        info = zeroconf.get_service_info(service_type, name)
        if info:
            device_name = info.properties.get(b"device", b"unknown").decode()
            ip = info.parsed_addresses()[0] if info.parsed_addresses() else None
            port = info.port

            if device_name != get_device_name() and ip:
                update_peer(device_name, ip, port, time.time())
                peers[device_name] = {"ip": ip, "port": port}
                print(f"✓ Discovered peer: {device_name} ({ip}:{port})")

    elif state_change == ServiceStateChange.Removed:
        device_name = name.split(".")[0].replace(f"_{SERVICE_TYPE}", "")
        if device_name in peers:
            del peers[device_name]
            print(f"✗ Peer offline: {device_name}")

def advertise_service():
    try:
        from zeroconf import ServiceInfo
        device_name = get_device_name()
        port = get_port()

        info = ServiceInfo(
            SERVICE_TYPE,
            f"{device_name}.{SERVICE_TYPE}",
            port=port,
            properties={"device": device_name},
        )

        zeroconf = Zeroconf()
        zeroconf.register_service(info)
        print(f"✓ Advertising service: {device_name}")
        return zeroconf
    except Exception as e:
        print(f"Failed to advertise service: {e}")
        return None

def discover_peers():
    try:
        zeroconf = Zeroconf()
        ServiceBrowser(zeroconf, SERVICE_TYPE, handlers=[on_service_state_change])
        print(f"✓ Listening for peers on {SERVICE_TYPE}")
        return zeroconf
    except Exception as e:
        print(f"Failed to start discovery: {e}")
        return None

def get_online_peers():
    return list(peers.values())
