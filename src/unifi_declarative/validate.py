import sys
from pathlib import Path
import os
import yaml
from dotenv import load_dotenv

from .validators import validate_vlan_count, validate_vlan_schema, ValidationError


def main() -> int:
    load_dotenv()
    hardware = os.getenv("HARDWARE_PROFILE", "usg3p")

    repo_root = Path(__file__).resolve().parents[2]
    vlans_path = repo_root / "config" / "vlans.yaml"

    if not vlans_path.exists():
        print(f"Error: VLAN config not found at {vlans_path}")
        return 1

    try:
        with vlans_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        vlans = data.get("vlans", {})

        # Hardware limit validation
        validate_vlan_count(vlans, hardware_profile=hardware)

        # Per-VLAN schema validation
        for key, vlan in vlans.items():
            validate_vlan_schema(vlan)

        print(
            f"Validation successful: {len(vlans)} VLANs compliant with '{hardware}' hardware profile."
        )
        return 0

    except ValidationError as e:
        print(f"ValidationError: {e}")
        return 2
    except Exception as e:
        print(f"Unexpected error during validation: {e}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
