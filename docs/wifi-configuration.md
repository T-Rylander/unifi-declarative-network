# Wi-Fi SSID Configuration

## Rylan-Home (Primary Network)
- **Network:** VLAN 30 (Trusted Devices)
- **Security:** WPA2/WPA3 Personal
- **Client Isolation:** Disabled
- **Purpose:** Laptops, workstations, phones (data VLAN)

## Rylan-IoT (Smart Devices)
- **Network:** VLAN 90 (Guest + IoT)
- **Security:** WPA2/WPA3 Personal
- **Client Isolation:** Enabled (Block LAN to WLAN Multicast/Broadcast)
- **mDNS:** Still works within VLAN 90
- **Purpose:** Bulbs, Denon receiver, printers

## Rylan-Guest (Optional)
- **Network:** VLAN 90 (Guest + IoT)
- **Security:** WPA2 Personal or Open + Captive Portal
- **Client Isolation:** Enabled
- **Purpose:** Visitor devices
