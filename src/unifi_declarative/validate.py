"""
Validation entry point for unifi-declarative-network configuration.

Runs comprehensive checks on VLAN schemas, hardware constraints, and topology.
"""

import sys
import logging
from pathlib import Path
import os
import yaml
from dotenv import load_dotenv

from .validators import (
    validate_vlan_count,
    validate_vlan_schema,
    validate_uplink_trunk_config,
    validate_controller_ip_migration,
    ValidationError,
)
from .logging_config import setup_logging

logger = logging.getLogger(__name__)


def main() -> int:
    """
    Validate UniFi network configuration files.
    
    Returns:
        0 on success, 1 on file not found, 2 on validation errors, 3 on unexpected errors
    """
    setup_logging()
    load_dotenv()
    hardware = os.getenv("HARDWARE_PROFILE", "usg3p")

    repo_root = Path(__file__).resolve().parents[2]
    vlans_path = repo_root / "config" / "vlans.yaml"
    hardware_path = repo_root / "config" / "hardware.yaml"

    if not vlans_path.exists():
        logger.error("VLAN config not found at %s", vlans_path)
        return 1

    try:
        with vlans_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        vlans = data.get("vlans", {})

        if not hardware_path.exists():
            raise ValidationError("Missing config/hardware.yaml — required for topology checks")
        with hardware_path.open("r", encoding="utf-8") as hf:
            hardware = yaml.safe_load(hf) or {}

        # Hardware limit validation
        validate_vlan_count(vlans, hardware_profile=hardware)

        # Per-VLAN schema validation
        for key, vlan in vlans.items():
            validate_vlan_schema(vlan)

        # Topology validations using hardware.yaml
        validate_uplink_trunk_config(hardware, vlans)
        validate_controller_ip_migration(hardware, vlans)

        logger.info(
            "Validation successful: %d VLANs compliant; uplink trunk and controller migration validated.",
            len(vlans)
        )
        return 0

    except ValidationError as e:
        logger.error("ValidationError: %s", e)
        return 2
    except Exception as e:
        logger.exception("Unexpected error during validation: %s", e)
        return 3


if __name__ == "__main__":
    sys.exit(main())
