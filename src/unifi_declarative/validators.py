"""
Configuration validators for unifi-declarative-network.

Enforces schema correctness, hardware constraints, and idempotency guarantees
before any API calls reach the UniFi controller.
"""

import logging
from typing import Any, Dict, List, Optional
from ipaddress import ip_network, ip_address, AddressValueError

logger = logging.getLogger(__name__)


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
        >>> vlans = {"10": {...}, "30": {...}, "40": {...}, "90": {...}, "100": {...}, "110": {...}, "120": {...}, "130": {...}, "140": {...}}
        >>> validate_vlan_count(vlans, "usg3p")
        ValidationError: USG-3P supports max 8 VLANs. Found 9.
    """
    # Check for VLAN 1 in dictionary keys (forbidden in declarative config)
    if "1" in vlans:
        raise ValidationError(
            "VLAN key '1' found in vlans.yaml. VLAN 1 (Default LAN) must be managed "
            "manually via the controller UI, not in declarative config. Remove VLAN 1 "
            "from vlans.yaml and change it to 10.0.1.0/27 in the UI after adopting USG. "
            "See docs/9.5.21-NOTES.md for details."
        )
    
    vlan_count = len(vlans)
    
    # Hardware-specific limits
    limits = {
        "usg3p": 8,      # UniFi Security Gateway 3P (EdgeOS-based)
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
    Validate VLAN configuration schema and enforce UniFi-specific constraints.
    
    Ensures all required fields are present, types are correct, and UniFi best practices
    are followed (DHCP pool doesn't overlap gateway, VLAN ID within 802.1Q range).
    
    Args:
        vlan_config: Single VLAN configuration block from vlans.yaml
    
    Raises:
        ValidationError: If required fields are missing, types invalid, or constraints violated
        
    Example:
        >>> config = {"name": "Servers", "vlan_id": 10, "subnet": "10.0.1.0/26", 
        ...           "gateway": "10.0.1.1", "dhcp_enabled": True, "enabled": True,
        ...           "dhcp_start": "10.0.1.10", "dhcp_stop": "10.0.1.62"}
        >>> validate_vlan_schema(config)  # Passes validation
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
    
    # VLAN 1 is FORBIDDEN in declarative config (UniFi 9.5.21 requirement)
    # VLAN 1 must be managed manually via controller UI to prevent adoption failures
    if vlan_config["vlan_id"] == 1:
        raise ValidationError(
            "VLAN 1 (Default LAN) MUST NOT be in vlans.yaml. "
            "UniFi 9.5.21 requires VLAN 1 to be changed manually in the UI BEFORE "
            "adopting devices or creating VLANs. Attempting to manage VLAN 1 via API "
            "causes 'api.err.VlanUsed' errors and breaks device adoption. "
            "See docs/9.5.21-NOTES.md for the mandatory bootstrap procedure."
        )
    
    # VLAN range per 802.1Q (4095 reserved)
    if not (1 <= vlan_config["vlan_id"] <= 4094):
        raise ValidationError(
            f"VLAN ID must be between 1 and 4094, got {vlan_config['vlan_id']}"
        )
    
    if vlan_config["vlan_id"] == 4095:
        raise ValidationError("VLAN 4095 is reserved per 802.1Q")
    
    # DHCP pool validation
    if vlan_config.get("dhcp_enabled"):
        subnet_str = str(vlan_config.get("subnet", ""))
        gateway = vlan_config.get("gateway")
        dhcp_start = vlan_config.get("dhcp_start")
        dhcp_stop = vlan_config.get("dhcp_stop")
        
        if dhcp_start and dhcp_stop and gateway:
            try:
                from ipaddress import ip_address, ip_network
                subnet = ip_network(subnet_str, strict=False)
                gw = ip_address(gateway)
                start = ip_address(dhcp_start)
                stop = ip_address(dhcp_stop)
                
                if int(gw) >= int(start) and int(gw) <= int(stop):
                    raise ValidationError(
                        f"DHCP pool {dhcp_start}-{dhcp_stop} overlaps gateway {gateway}"
                    )
            except Exception as e:
                if "DHCP pool" in str(e):
                    raise
    
    # IGMP snooping warning (UniFi-specific)
    if vlan_config.get("igmp_snooping") and vlan_config["vlan_id"] in [1, 2]:
        import warnings
        warnings.warn(
            f"IGMP snooping on VLAN {vlan_config['vlan_id']} may affect UniFi device discovery"
        )


def validate_subnet_overlap(vlans: dict[str, Any]) -> None:
    """
    Ensure no VLAN subnets overlap (prevents routing conflicts).
    
    Checks all VLAN subnet definitions to detect overlapping IP ranges that would
    cause ambiguous routing table entries on the gateway.
    
    Args:
        vlans: Dictionary of VLAN configurations keyed by VLAN ID
    
    Raises:
        ValidationError: If any two subnets overlap or are identical
        
    Example:
        >>> vlans = {"10": {"subnet": "10.0.1.0/26"}, "30": {"subnet": "10.0.2.0/24"}}
        >>> validate_subnet_overlap(vlans)  # No overlap, passes
        
        >>> bad_vlans = {"10": {"subnet": "10.0.0.0/16"}, "30": {"subnet": "10.0.1.0/24"}}
        >>> validate_subnet_overlap(bad_vlans)  # Raises ValidationError
    """
    # TODO: Implement IP subnet overlap detection using ipaddress.ip_network().overlaps()
    pass


def load_hardware_profile(hardware: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract hardware configuration fields needed for validation.
    
    Provides normalized access to gateway, switch, and controller definitions
    from hardware.yaml without exposing full config structure.
    
    Args:
        hardware: Parsed hardware.yaml configuration
        
    Returns:
        Dictionary with 'gateway', 'switches', and 'controller' keys
        
    Example:
        >>> hw_yaml = {"gateway": {...}, "switches": [...], "controller": {...}}
        >>> profile = load_hardware_profile(hw_yaml)
        >>> profile["gateway"]["model"]  # Access gateway details
    """
    return {
        "gateway": hardware.get("gateway", {}),
        "switches": hardware.get("switches", []),
        "controller": hardware.get("controller", {}),
    }


def validate_uplink_trunk_config(hardware: Dict[str, Any], vlans: Dict[str, Any]) -> None:
    """
    Validate switch uplink trunk configuration for gateway connectivity.
    
    Ensures the US-8-60W uplink port to the gateway is configured as a trunk with:
    - VLAN 1 as native (for management/adoption)
    - All configured VLAN IDs (except 1) as tagged VLANs
    
    This prevents silent provisioning failures from missing trunk tags.
    
    Args:
        hardware: Parsed hardware.yaml configuration
        vlans: Dictionary of VLAN configurations keyed by VLAN ID
        
    Raises:
        ValidationError: If uplink is not a trunk, native VLAN != 1, or tagged VLANs mismatch
        
    Example:
        >>> hardware = {"switches": [{"model": "US-8-60W", "uplink_port": 1, 
        ...             "port_assignments": {"1": {"type": "trunk", "native_vlan": 1, 
        ...             "tagged_vlans": [10, 30, 40]}}}]}
        >>> vlans = {"10": {...}, "30": {...}, "40": {...}}
        >>> validate_uplink_trunk_config(hardware, vlans)  # Passes
    """
    hw = load_hardware_profile(hardware)
    switches: List[Dict[str, Any]] = hw.get("switches", [])
    target_switch = next((s for s in switches if s.get("model") == "US-8-60W"), None)
    if not target_switch:
        raise ValidationError("US-8-60W switch definition missing in hardware.yaml")

    uplink_port = target_switch.get("uplink_port")
    if uplink_port is None:
        raise ValidationError("US-8-60W uplink_port not specified in hardware.yaml")
    
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
    Validate controller IP migration parameters for safe network transition.
    
    Ensures:
    - Target IP differs from current IP (migration is actually happening)
    - Target IP falls within VLAN 10 subnet (servers network per design)
    - VLAN 10 gateway is correctly configured within subnet
    
    This prevents controller isolation after migration.
    
    Args:
        hardware: Parsed hardware.yaml with controller.current_ip and controller.target_ip
        vlans: Dictionary of VLAN configurations (must include VLAN 10)
        
    Raises:
        ValidationError: If target IP == current IP, target IP outside VLAN 10, or gateway misconfigured
        
    Example:
        >>> hardware = {"controller": {"current_ip": "10.0.1.1", "target_ip": "10.0.1.10"}}
        >>> vlans = {"10": {"subnet": "10.0.1.0/26", "gateway": "10.0.1.1"}}
        >>> validate_controller_ip_migration(hardware, vlans)  # Passes
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
    """
    Validate hardware inventory completeness and flag missing configuration.
    
    Checks for:
    - TBD placeholders that indicate incomplete configuration
    - Missing MAC addresses for non-empty port assignments
    
    This prevents deployment of incomplete hardware definitions.
    
    Args:
        hardware: Parsed hardware.yaml configuration
        
    Raises:
        ValidationError: If TBD placeholders found or device MACs missing
        
    Example:
        >>> hw = {"switches": [{"model": "US-8-60W", "port_assignments": {
        ...     "1": {"device": "controller", "mac": "aa:bb:cc:dd:ee:ff"}}}]}
        >>> validate_hardware_inventory(hw)  # Passes
    """
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
