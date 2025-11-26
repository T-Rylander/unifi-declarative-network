import sys
import time
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
    parser.add_argument("--check-mode", action="store_true", help="Validate configs without connecting to controller")
    parser.add_argument("--migrate", action="store_true", help="Allow changes to VLAN 1 and controller migration")
    parser.add_argument("--i-understand-vlan1-risks", action="store_true", help="Explicit acknowledgement of VLAN 1 modification risks")
    parser.add_argument("--force", action="store_true", help="Skip interactive confirmation and safety checks")
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

        if args.check_mode:
            print(f"Check-mode: {len(vlans)} VLANs validated successfully. No controller connection.")
            return 0

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

        # Pre-apply safety: backup
        try:
            backup_bytes = client.export_backup()
            backups_dir = repo_root / "backups"
            backups_dir.mkdir(parents=True, exist_ok=True)
            (backups_dir / "pre-apply.unf").write_bytes(backup_bytes)
            print(f"Backup saved: {backups_dir / 'pre-apply.unf'}")
        except Exception as e:
            if not args.force:
                print(f"Backup failed: {e}. Aborting (use --force to skip)")
                return 1
            else:
                print(f"Backup failed: {e}. Continuing due to --force")

        # Confirmation unless forced
        if not args.force:
            print("About to apply VLAN changes to controller. Type 'yes' to proceed:", end=" ")
            try:
                if input().strip().lower() != "yes":
                    print("Aborted.")
                    return 1
            except EOFError:
                print("No input available. Aborting.")
                return 1

        # Upsert each desired VLAN (ID-aware)
        for key, vlan in vlans.items():
            # Skip touching VLAN 1 unless explicitly acknowledged
            if int(vlan.get("vlan_id", 0)) == 1:
                if not args.migrate or not args.i_understand_vlan1_risks:
                    print("\n⚠️  WARNING: VLAN 1 is the default management network.")
                    print("Modifying VLAN 1 can break device adoption and controller access.")
                    print("Use --migrate --i-understand-vlan1-risks to proceed.\n")
                    continue
            existing = client.find_existing_vlan(live_networks, vlan)
            client.upsert_vlan(vlan, existing=existing)
            existing = client.find_existing_vlan(live_networks, vlan)
            client.upsert_vlan(vlan, existing=existing)
            # Community recommendation: delay between operations to avoid controller deadlock
            time.sleep(2)
        print(f"Applied {len(vlans)} VLAN(s) to controller.")

        # Provisioning wait with polling
        print("Triggering provision and waiting for devices to settle...")
        client.provision_gateway()
        if client.wait_for_provisioning(timeout=90):
            print("Provisioning complete.")
        else:
            print("⚠️  Provisioning timeout (devices may still be settling). Check controller UI.")

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
