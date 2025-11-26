"""
Configuration validators for unifi-declarative-network.

Enforces schema correctness, hardware constraints, and idempotency guarantees
before any API calls reach the UniFi controller.
"""

from typing import Any


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
