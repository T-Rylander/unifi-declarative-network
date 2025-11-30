# IP ACL Policies (Inter-VLAN Traffic Control)

Settings → Security → Access Control → Create Policy

L3 Network Isolation blocks all inter-VLAN traffic by default. These ACL policies explicitly allow required communication:

## Policy 1: Trusted → Servers
- **Type:** IP
- **Protocol:** All
- **Source:** trusted-devices (10.0.30.0/24)
- **Action:** Allow
- **Destination:** servers (10.0.10.0/26)
- **Purpose:** Workstations access infrastructure services

## Policy 2: Trusted → VoIP
- **Type:** IP
- **Protocol:** All
- **Source:** trusted-devices (10.0.30.0/24)
- **Action:** Allow
- **Destination:** voip (10.0.40.0/27)
- **Purpose:** Workstations manage phones and access FreePBX

## Policy 3: VoIP Internal Communication
- **Type:** IP
- **Protocol:** UDP
- **Source:** voip (10.0.40.0/27)
- **Action:** Allow
- **Destination:** voip (10.0.40.0/27)
- **Destination Port:** 5060-5061,10000-20000
- **Purpose:** SIP/RTP traffic between phones and FreePBX

## Notes

### Gateway Communication (No ACL Required)
All VLANs can communicate with the USG gateway (10.0.1.1) without ACL policies:
- DNS (port 53), NTP (port 123), DHCP work automatically
- L3 isolation only blocks inter-VLAN routing, not traffic to the gateway itself

### Guest/IoT Internet Access (No ACL Required)
Guest/IoT VLAN has internet access by default when L3 isolation is enabled:
- L3 isolation blocks RFC1918 private networks only
- Public internet destinations are allowed automatically
- No explicit "Guest → Internet" ACL policy needed (tested and verified)
