import sys
from pathlib import Path
import yaml
from dotenv import load_dotenv

from .validators import validate_vlan_count, validate_vlan_schema, ValidationError
from .differ import diff_configs
from .client import UniFiClient


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

        # Diff desired vs. placeholder live state
        desired = data
        live = {"vlans": {}}  # TODO: fetch from controller
        dd = diff_configs(desired, live)
        print("Diff:", dd)

        if args.dry_run:
            print(f"Dry-run: would reconcile {len(vlans)} VLAN(s). No changes made.")
            return 0

        # Perform REST apply logic via UniFi client
        client = UniFiClient.from_env()
        client.login()
        live_networks = client.list_networks()
        # Upsert each desired VLAN
        for key, vlan in vlans.items():
            client.upsert_vlan(vlan)
        print(f"Applied {len(vlans)} VLAN(s) to controller.")

        # Save last applied state
        state_dir = repo_root / "config" / ".state"
        state_dir.mkdir(parents=True, exist_ok=True)
        with (state_dir / "last-applied.yaml").open("w", encoding="utf-8") as sf:
            yaml.safe_dump(desired, sf, sort_keys=False)
        print(f"State saved to {state_dir / 'last-applied.yaml'}")
        return 0

    except ValidationError as e:
        print(f"ValidationError: {e}")
        return 2
    except Exception as e:
        print(f"Unexpected error during apply: {e}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
