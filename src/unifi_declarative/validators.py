"""
Configuration validators for unifi-declarative-network.

Enforces schema correctness, hardware constraints, and idempotency guarantees
before any API calls reach the UniFi controller.
"""

from typing import Any, Dict, List, Optional
from ipaddress import ip_network, ip_address


class ValidationError(Exception):
    """Raised when configuration validation fails."""
    pass


def validate_vlan_count(vlans: dict[str, Any], hardware_profile: str) -> None:
    """
    Enforce hardware-specific VLAN limits.
    
    The USG-3P supports a maximum of 4 VLANs (including VLAN 1).
    Exceeding this limit causes silent provisioning failures or performance
    degradation due to CPU-based routing instead of hardware offload.
    
    Args:
        vlans: Parsed VLAN configuration from vlans.yaml (keyed by VLAN ID)
        hardware_profile: Hardware identifier ('usg3p', 'uxg-pro', 'udm-se', etc.)
    
    Raises:
        ValidationError: If VLAN count exceeds hardware limit for the given profile
    
    Example:
        >>> vlans = {"1": {...}, "10": {...}, "30": {...}, "40": {...}, "90": {...}}
        >>> validate_vlan_count(vlans, "usg3p")
        ValidationError: USG-3P supports max 4 VLANs. Found 5.
    """
    vlan_count = len(vlans)
    
    # Hardware-specific limits
    limits = {
        "usg3p": 4,      # UniFi Security Gateway 3P (EdgeOS-based)
        "uxg-pro": 32,   # Next-gen gateway (full Linux network stack)
        "udm-se": 32,    # Dream Machine Special Edition
        "udm-pro": 32,   # Dream Machine Pro
    }
    
    max_vlans = limits.get(hardware_profile.lower())
    
    if max_vlans is None:
        raise ValidationError(
            f"Unknown hardware profile: '{hardware_profile}'. "
            f"Supported: {', '.join(limits.keys())}"
        )
    
    if vlan_count > max_vlans:
        raise ValidationError(
            f"{hardware_profile.upper()} supports max {max_vlans} VLANs. "
            f"Found {vlan_count} in config/vlans.yaml. "
            f"See docs/hardware-constraints.md for migration guidance."
        )


def validate_vlan_schema(vlan_config: dict[str, Any]) -> None:
    """
    Validate VLAN configuration schema.
    
    Ensures all required fields are present and types are correct.
    
    Args:
        vlan_config: Single VLAN configuration block
    
    Raises:
        ValidationError: If required fields are missing or invalid
    """
    required_fields = [
        "name", "subnet", "gateway", "vlan_id", 
        "dhcp_enabled", "enabled"
    ]
    
    for field in required_fields:
        if field not in vlan_config:
            raise ValidationError(
                f"Missing required field '{field}' in VLAN configuration"
            )
    
    # Type validation
    if not isinstance(vlan_config["vlan_id"], int):
        raise ValidationError(
            f"VLAN ID must be an integer, got {type(vlan_config['vlan_id'])}"
        )
    
    if not (1 <= vlan_config["vlan_id"] <= 4094):
        raise ValidationError(
            f"VLAN ID must be between 1 and 4094, got {vlan_config['vlan_id']}"
        )


def validate_subnet_overlap(vlans: dict[str, Any]) -> None:
    """
    Ensure no VLAN subnets overlap.
    
    Args:
        vlans: All VLAN configurations
    
    Raises:
        ValidationError: If any subnets overlap
    """
    # TODO: Implement IP subnet overlap detection
    # Will use ipaddress.ip_network() to check for conflicts
    pass


def load_hardware_profile(hardware: Dict[str, Any]) -> Dict[str, Any]:
    """Lightweight extractor for hardware.yaml fields used by validators."""
    return {
        "gateway": hardware.get("gateway", {}),
        "switches": hardware.get("switches", []),
        "controller": hardware.get("controller", {}),
    }


def validate_uplink_trunk_config(hardware: Dict[str, Any], vlans: Dict[str, Any]) -> None:
    """
    Ensure the US-8-60W uplink port to the gateway is a trunk with VLAN 1 native
    and tags for VLANs present in config (10, 30, 40 as per v3.0).
    """
    hw = load_hardware_profile(hardware)
    switches: List[Dict[str, Any]] = hw.get("switches", [])
    target_switch = next((s for s in switches if s.get("model") == "US-8-60W"), None)
    if not target_switch:
        raise ValidationError("US-8-60W switch definition missing in hardware.yaml")

    uplink_port = target_switch.get("uplink_port")
    ports: Dict[str, Any] = target_switch.get("port_assignments", {})
    uplink = ports.get(str(uplink_port)) or ports.get(uplink_port)
    if not uplink:
        raise ValidationError(f"Uplink port '{uplink_port}' assignment not found on US-8-60W")

    if uplink.get("type") != "trunk":
        raise ValidationError("US-8-60W uplink must be 'trunk'")

    if uplink.get("native_vlan") != 1:
        raise ValidationError("Native VLAN on uplink trunk must be 1 for management/adoption")

    # Expected tagged VLANs from config
    required_tags = sorted([int(v) for v in vlans.keys() if int(v) != 1])
    actual_tags = sorted(list(uplink.get("tagged_vlans", [])))
    if actual_tags != required_tags:
        raise ValidationError(
            f"Uplink trunk tagged VLANs mismatch. Expected {required_tags}, found {actual_tags}"
        )


def validate_controller_ip_migration(hardware: Dict[str, Any], vlans: Dict[str, Any]) -> None:
    """
    Verify controller target IP belongs to VLAN 10 subnet and differs from current.
    Also ensure VLAN 10 gateway aligns with hardware target network semantics.
    """
    hw = load_hardware_profile(hardware)
    controller = hw.get("controller", {})
    current_ip = controller.get("current_ip")
    target_ip = controller.get("target_ip")

    if not (current_ip and target_ip):
        raise ValidationError("Controller current_ip/target_ip must be specified in hardware.yaml")

    if current_ip == target_ip:
        raise ValidationError("Controller target_ip must differ from current_ip for migration")

    vlan10 = vlans.get("10")
    if not vlan10:
        raise ValidationError("VLAN 10 not found in vlans.yaml for controller placement")

    subnet10 = ip_network(vlan10["subnet"])  # e.g., 10.0.10.0/24
    if ip_address(target_ip) not in subnet10:
        raise ValidationError(
            f"Controller target_ip {target_ip} must be within VLAN 10 subnet {subnet10}"
        )

    # Gateway alignment
    gateway10 = vlan10.get("gateway")
    if not gateway10:
        raise ValidationError("VLAN 10 gateway missing in vlans.yaml")

    if ip_address(gateway10) not in subnet10:
        raise ValidationError("VLAN 10 gateway must reside within VLAN 10 subnet")


def validate_hardware_inventory(hardware: Dict[str, Any]) -> None:
    """Ensure hardware.yaml has no TBD placeholders and critical MACs are present."""
    hw = load_hardware_profile(hardware)
    switches: List[Dict[str, Any]] = hw.get("switches", [])
    errors: List[str] = []

    for sw in switches:
        pa = sw.get("port_assignments", {})
        if isinstance(pa, dict):
            for port_num, cfg in pa.items():
                text = str(cfg)
                if "TBD" in text:
                    errors.append(f"Switch {sw.get('model')} port {port_num} has TBD entries")
                mac = cfg.get("mac")
                device = cfg.get("device", "")
                # If a device is specified and it's not 'empty', prefer having a MAC
                if device and device != "empty" and not mac:
                    errors.append(f"Switch {sw.get('model')} port {port_num} missing device MAC")

    if errors:
        raise ValidationError("\n".join(errors))
