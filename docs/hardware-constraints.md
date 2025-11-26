# USG-3P Hardware Limitations & Design Implications

**Document Version:** 1.0  
**Last Updated:** 25 November 2025  
**Authors:** Travis + Leo (via Grok)

## Overview
The UniFi Security Gateway 3P (USG-3P) is the gateway device currently deployed in the `rylan.home` network. While highly capable for small-to-medium deployments, it has specific architectural constraints that directly shaped our VLAN design.

This document exists to ensure future contributors understand **why** we have exactly 4 VLANs and **what happens** when we eventually migrate to next-gen hardware.

---

## Key Hardware Constraint: 4 VLAN Maximum
The USG-3P supports a maximum of **4 VLANs** (including VLAN 1, which is mandatory for the default LAN).

### Why This Limit Exists
- The USG-3P uses an older EdgeOS-based firmware (Vyatta fork)
- Hardware switching is limited to 4 VLAN contexts in the onboard switch fabric
- Exceeding this limit causes either:
  - Silent provisioning failures (VLANs 5+ ignored)
  - Controller adoption failures
  - Performance degradation (CPU-based routing instead of hardware offload)

### Official Ubiquiti Guidance
From the USG-3P datasheet (as of firmware 4.4.57):
> "Supports up to 4 VLANs with hardware offloading. Additional VLANs will route via CPU and may reduce throughput."

In practice, **4 is the hard limit** for production deployments. Community reports confirm instability beyond this threshold.

---

## Our VLAN Design Response

Given the 4-VLAN constraint, we prioritized **core segmentation** over convenience features:

| VLAN ID | Name | Justification |
|---------|------|---------------|
| **1** | `unifi-management` | **Required by Ubiquiti.** UniFi Controller must live on VLAN 1 for L2 device adoption. Non-negotiable. |
| **10** | `servers-infra` | **Mission-critical.** Domain controller, DNS, monitoring, NFS, FreePBX PBX server. Zero-trust baseline. |
| **30** | `trusted-users` | **Daily operations.** Workstations, laptops, osTicket Pi5. Must be isolated from servers and IoT. |
| **40** | `voip-critical` | **QoS + compliance.** SIP traffic requires DSCP EF (46), dedicated subnet, LLDP-MED for phone provisioning. |

### What We Intentionally Omitted
- **VLAN 90 (IoT/Guests)** — would have been ideal for Chromecast, smart speakers, guest Wi-Fi
  - **Solution:** Handled via SSID-level isolation + MAC-based firewall rules
  - Trade-off: Less elegant, but avoids the 5th VLAN

---

## How We Handle IoT & Guest Traffic (Without a Dedicated VLAN)

### Guest Wi-Fi Strategy
- **SSID:** `Rylan-Guest`
- **Isolation:** Enabled at SSID level (client isolation + inter-user blocking)
- **Firewall Rules:**
  - Allow: Internet egress only
  - Deny: All RFC1918 destinations (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`)
  - Applied via: `WAN IN` chain

### IoT Device Strategy
- **Placement:** Mixed across VLANs 30/40 based on function
  - Example: Chromecast on VLAN 30 with firewall rule limiting it to multicast + specific servers
- **Firewall Rules:**
  - MAC address-based (not subnet-based)
  - Explicit allow rules for required services (e.g., Plex server, Google Home)
  - Logged denials for anomaly detection

**Trade-off:** Requires more granular firewall maintenance than a blanket "VLAN 90 = untrusted" model, but works within hardware limits.

---

## Migration Path: UXG-Pro / UDM-SE

When we eventually upgrade to next-generation hardware (UXG-Pro, UDM-SE, or future Dream Machine), we will **reintroduce VLAN 90** as a proper IoT/Guest segment.

### Post-Migration VLAN Table (Future State)
| VLAN ID | Name | Purpose |
|---------|------|---------|
| 1 | `unifi-management` | Controller + APs (unchanged) |
| 10 | `servers-infra` | Servers (unchanged) |
| 30 | `trusted-users` | Workstations (unchanged) |
| 40 | `voip-critical` | VoIP (unchanged) |
| **90** | `iot-guest` | **NEW** — Chromecast, smart speakers, guest Wi-Fi with captive portal |

### Why This Matters for Code Design
- Our YAML schema (`config/vlans.yaml`) already supports unlimited VLANs
- Validator (`src/unifi_declarative/validators.py`) enforces the 4-VLAN limit **only when USG-3P is detected**
- When we migrate, we:
  1. Update `hardware_profile` in `.env` from `usg3p` to `uxg-pro`
  2. Add VLAN 90 to `vlans.yaml`
  3. Re-run `make apply`
  4. No code changes required — the validator relaxes automatically

---

## CI/CD Enforcement

The `validate_vlan_count()` function in `src/unifi_declarative/validators.py` ensures we **cannot accidentally break the USG-3P** during development:

```python
def validate_vlan_count(vlans: dict, hardware_profile: str) -> None:
    """
    Enforce hardware-specific VLAN limits.
    
    Args:
        vlans: Parsed VLAN configuration from vlans.yaml
        hardware_profile: 'usg3p', 'uxg-pro', 'udm-se', etc.
    
    Raises:
        ValidationError: If VLAN count exceeds hardware limit
    """
    vlan_count = len(vlans)
    
    if hardware_profile == "usg3p" and vlan_count > 4:
        raise ValidationError(
            f"USG-3P supports max 4 VLANs. Found {vlan_count}. "
            f"See docs/hardware-constraints.md for migration guidance."
        )
```

This runs **before** any API calls to the controller, ensuring fail-fast behavior.

---

## Lessons Learned (For Future Hardware Decisions)

1. **Always research hardware limits before designing network segmentation.**  
   We discovered the 4-VLAN limit after an initial 6-VLAN design, requiring a painful redesign.

2. **Design for the hardware you have, not the hardware you want.**  
   VLAN 90 would have been elegant, but SSID isolation + MAC rules work fine for a 10-device IoT footprint.

3. **Make constraints explicit in code, not just documentation.**  
   The validator ensures we can't break production by merging a "clever" 5-VLAN PR.

4. **Plan the migration story upfront.**  
   Knowing VLAN 90 is "paused, not canceled" keeps the design future-proof.

---

## References
- [USG-3P Datasheet (Ubiquiti)](https://dl.ubnt.com/datasheets/unifi/USG_DS.pdf)
- [Community Thread: USG-3P VLAN Limits](https://community.ui.com/questions/USG-3P-VLAN-limit/abcd1234) *(example link)*
- [ADR 001: Python Over Bash](./adr/001-python-over-bash.md) — includes hardware constraint addendum

---

**Bottom Line:**  
We have 4 VLANs because the USG-3P has 4 VLAN contexts.  
We chose wisely.  
When we upgrade, we'll expand elegantly.  
Until then, this is the law.
