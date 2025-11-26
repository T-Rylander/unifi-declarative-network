import sys
from pathlib import Path
import yaml
from dotenv import load_dotenv

from .validators import validate_vlan_count, validate_vlan_schema, ValidationError


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Apply UniFi configuration (dry-run by default)")
    parser.add_argument("--dry-run", action="store_true", help="Do not perform any API calls")
    args = parser.parse_args()

    load_dotenv()

    repo_root = Path(__file__).resolve().parents[2]
    vlans_path = repo_root / "config" / "vlans.yaml"

    if not vlans_path.exists():
        print(f"Error: VLAN config not found at {vlans_path}")
        return 1

    try:
        with vlans_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        vlans = data.get("vlans", {})

        # Basic validation
        validate_vlan_count(vlans, hardware_profile="usg3p")
        for key, vlan in vlans.items():
            validate_vlan_schema(vlan)

        if args.dry_run:
            print(f"Dry-run: would reconcile {len(vlans)} VLAN(s). No changes made.")
            return 0

        # TODO: Implement actual apply logic via REST client
        print("Apply not yet implemented. Use --dry-run for now.")
        return 0

    except ValidationError as e:
        print(f"ValidationError: {e}")
        return 2
    except Exception as e:
        print(f"Unexpected error during apply: {e}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
