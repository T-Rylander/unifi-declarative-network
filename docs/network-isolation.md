# Network Isolation and ACL Policies (UniFi 9.5.21 + USG-3P)

This document captures the production configuration for L3 Network Isolation and IP ACL policies that enforce inter-VLAN segmentation.

## L3 Network Isolation Settings

Settings → Networks → [Network Name] → Advanced → Network Isolation

| Network | L3 Isolation Enabled | Purpose |
|---------|---------------------|---------|
| Management (VLAN 1) | ❌ No | Full access required for adoption and controller operation |
| Servers (VLAN 10) | ✅ Yes | Protected infrastructure |
| Trusted Devices (VLAN 30) | ✅ Yes | Workstation isolation |
| VoIP (VLAN 40) | ✅ Yes | Voice network isolation |
| Guest/IoT (VLAN 90) | ✅ Yes | Untrusted device isolation |

Note: L3 Network Isolation creates default-deny ACLs between VLANs. Explicit ACL policies (below) override these blocks for required traffic flows.

## IP ACL Policies (Inter-VLAN Traffic Control)

Settings → Security → Access Control → Create Policy

L3 Network Isolation blocks all inter-VLAN traffic by default. These ACL policies explicitly allow required communication:

### Policy 1: Trusted → Servers
- Type: IP
- Protocol: All
- Source: trusted-devices (10.0.30.0/24)
- Action: Allow
- Destination: servers (10.0.10.0/26)

### Policy 2: Trusted → VoIP
- Type: IP
- Protocol: All
- Source: trusted-devices (10.0.30.0/24)
- Action: Allow
- Destination: voip (10.0.40.0/27)

### Policy 3: VoIP Internal Communication
- Type: IP
- Protocol: UDP
- Source: voip (10.0.40.0/27)
- Action: Allow
- Destination: voip (10.0.40.0/27)
- Destination Port: 5060-5061,10000-20000

Note: Gateway communication (10.0.1.1) does not require ACL policies — all VLANs can reach the USG for DNS/NTP by default.

## Hardware Offload Configuration

Settings → System → Advanced → Routing & Firewall → Advanced

| Setting | Configuration | Reason |
|---------|--------------|--------|
| Hardware Offload | ✅ Enabled | Maintains WAN performance |
| Offload Scheduler | ✅ Enabled | QoS hardware acceleration |
| Offload Layer 2 Blocking | ❌ Disabled | Ensures ACL/firewall rules are enforced for inter-VLAN traffic |

Critical: Layer 2 offloading can bypass firewall rules and ACL policies, breaking VLAN segmentation. Must be disabled.
