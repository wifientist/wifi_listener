"""
MAC address vendor lookup utility

Uses a minimal OUI database for common WiFi vendors
"""

# Minimal OUI database for common WiFi AP vendors
# Format: OUI prefix -> Vendor name
OUI_DATABASE = {
    # Ruckus Wireless
    '24:79:2a': 'Ruckus Wireless',
    '2c:30:33': 'Ruckus Wireless',
    '54:3d:37': 'Ruckus Wireless',
    '88:dc:96': 'Ruckus Wireless',
    'c4:10:8a': 'Ruckus Wireless',

    # Ubiquiti
    '24:a4:3c': 'Ubiquiti Networks',
    '44:d9:e7': 'Ubiquiti Networks',
    '68:72:51': 'Ubiquiti Networks',
    '74:83:c2': 'Ubiquiti Networks',
    '78:8a:20': 'Ubiquiti Networks',
    '80:2a:a8': 'Ubiquiti Networks',
    'b4:fb:e4': 'Ubiquiti Networks',
    'dc:9f:db': 'Ubiquiti Networks',
    'e0:63:da': 'Ubiquiti Networks',
    'f0:9f:c2': 'Ubiquiti Networks',
    'fc:ec:da': 'Ubiquiti Networks',

    # Cisco
    '00:0d:bc': 'Cisco',
    '00:1d:7e': 'Cisco',
    '00:1f:ca': 'Cisco',
    '00:24:13': 'Cisco',
    '00:62:ec': 'Cisco',
    '70:ea:1a': 'Cisco',
    'a0:e0:af': 'Cisco',
    'f8:7b:20': 'Cisco',

    # Aruba Networks
    '00:1a:1e': 'Aruba Networks',
    '00:24:6c': 'Aruba Networks',
    '20:4c:03': 'Aruba Networks',
    '6c:f3:7f': 'Aruba Networks',
    '94:b4:0f': 'Aruba Networks',

    # Meraki
    '00:18:0a': 'Cisco Meraki',
    '88:15:44': 'Cisco Meraki',
    'e0:55:3d': 'Cisco Meraki',
    'e0:cb:bc': 'Cisco Meraki',

    # TP-Link
    '14:cc:20': 'TP-Link',
    '50:c7:bf': 'TP-Link',
    '60:32:b1': 'TP-Link',
    'a4:2b:8c': 'TP-Link',
    'c0:4a:00': 'TP-Link',
    'f4:ec:38': 'TP-Link',

    # Netgear
    '20:e5:2a': 'Netgear',
    '28:c6:8e': 'Netgear',
    'a0:63:91': 'Netgear',
    'c4:04:15': 'Netgear',

    # Apple
    '00:03:93': 'Apple',
    '00:1b:63': 'Apple',
    '00:1e:52': 'Apple',
    '00:25:00': 'Apple',
    '28:cf:e9': 'Apple',
    '98:01:a7': 'Apple',
    'f0:99:bf': 'Apple',
}


def lookup_vendor(mac_address: str) -> str:
    """
    Look up vendor name from MAC address

    Args:
        mac_address: MAC address in format "aa:bb:cc:dd:ee:ff" or "AA-BB-CC-DD-EE-FF"

    Returns:
        str: Vendor name or "Unknown" if not found
    """
    if not mac_address:
        return "Unknown"

    # Normalize MAC address to lowercase with colons
    mac = mac_address.lower().replace('-', ':')

    # Extract OUI (first 3 octets)
    parts = mac.split(':')
    if len(parts) < 3:
        return "Unknown"

    oui = ':'.join(parts[:3])

    return OUI_DATABASE.get(oui, "Unknown")


def get_oui(mac_address: str) -> str:
    """
    Extract OUI (first 3 octets) from MAC address

    Args:
        mac_address: MAC address in any common format

    Returns:
        str: OUI in format "aa:bb:cc" or empty string if invalid
    """
    if not mac_address:
        return ""

    # Normalize MAC address
    mac = mac_address.lower().replace('-', ':')
    parts = mac.split(':')

    if len(parts) < 3:
        return ""

    return ':'.join(parts[:3])
