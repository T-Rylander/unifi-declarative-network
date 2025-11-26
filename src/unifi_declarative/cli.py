import sys
import json
from pathlib import Path
import yaml

from .client import UniFiClient
from .validators import (
    validate_vlan_count,
    validate_vlan_schema,
    validate_uplink_trunk_config,
    validate_controller_ip_migration,
    validate_hardware_inventory,
    ValidationError,
)
from .differ import diff_configs

STATE_DIR = Path("config/.state")
STATE_FILE = STATE_DIR / "last-applied.yaml"


def cmd_validate(repo_root: Path) -> int:
    vlans_path = repo_root / "config" / "vlans.yaml"
    hardware_path = repo_root / "config" / "hardware.yaml"
    with vlans_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    vlans = data.get("vlans", {})
    with hardware_path.open("r", encoding="utf-8") as hf:
        hardware = yaml.safe_load(hf) or {}

    validate_vlan_count(vlans, hardware_profile="usg3p")
    for _, v in vlans.items():
        validate_vlan_schema(v)
    validate_uplink_trunk_config(hardware, vlans)
    validate_controller_ip_migration(hardware, vlans)
    validate_hardware_inventory(hardware)
    print("Validation OK: VLANs, uplink trunk, controller migration.")
    return 0


def cmd_status(client: UniFiClient) -> int:
    # Minimal status check: controller version endpoint; varies by API version
    try:
        data = client.get(f"/api/self")
        print(json.dumps(data, indent=2))
        return 0
    except Exception as e:
        print(f"Error getting status: {e}")
        return 1


def cmd_backup(client: UniFiClient, repo_root: Path) -> int:
    try:
        content = client.export_backup()
        backup_dir = repo_root / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        out = backup_dir / "controller-backup.unf"
        out.write_bytes(content)
        print(f"Backup saved: {out}")
        return 0
    except Exception as e:
        print(f"Backup failed: {e}")
        return 2


def cmd_apply(repo_root: Path, dry_run: bool) -> int:
    # Load desired state
    with (repo_root / "config" / "vlans.yaml").open("r", encoding="utf-8") as f:
        desired = yaml.safe_load(f) or {}

    # TODO: Pull live state via UniFiClient (placeholder)
    live = {"vlans": {}}  # placeholder until REST wiring

    # Diff
    dd = diff_configs(desired, live)
    print("Diff:", json.dumps(dd, indent=2))

    if dry_run:
        print("Dry-run: no changes applied.")
        return 0

    # TODO: Perform REST apply operations
    # On success, write state
    # sanitize state before writing
    def sanitize_state_for_storage(state: dict) -> dict:
        sanitized = json.loads(json.dumps(state))  # deep copy
        for section in ("controller", "wan"):
            if section in sanitized:
                for key in ("password", "secret", "community", "radius_key"):
                    sanitized[section].pop(key, None)
        return sanitized

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with STATE_FILE.open("w", encoding="utf-8") as sf:
        yaml.safe_dump(sanitize_state_for_storage(desired), sf, sort_keys=False)
    print(f"State saved to {STATE_FILE}")
    return 0


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="UniFi Declarative Network CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("validate")
    sub.add_parser("status")
    sub.add_parser("backup")
    sub.add_parser("rollback")

    p_apply = sub.add_parser("apply")
    p_apply.add_argument("--dry-run", action="store_true")
    p_apply.add_argument("--check-mode", action="store_true")
    p_apply.add_argument("--migrate", action="store_true")
    p_apply.add_argument("--i-understand-vlan1-risks", action="store_true")
    p_apply.add_argument("--force", action="store_true")

    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]

    if args.cmd == "validate":
        return cmd_validate(repo_root)

    client = UniFiClient.from_env()
    client.login()

    if args.cmd == "status":
        return cmd_status(client)
    if args.cmd == "backup":
        return cmd_backup(client, repo_root)
    if args.cmd == "rollback":
        # minimal rollback placeholder: print last state path
        if STATE_FILE.exists():
            print(f"Would rollback using {STATE_FILE}")
            return 0
        else:
            print("No state file found for rollback")
            return 1
    if args.cmd == "apply":
        # Reuse apply entry in apply.py to avoid duplicate logic
        from .apply import main as apply_main
        # Build args for apply_main via sys.argv handoff
        sys.argv = [sys.argv[0]]
        if args.dry_run:
            sys.argv.append("--dry-run")
        if args.check_mode:
            sys.argv.append("--check-mode")
        if args.migrate:
            sys.argv.append("--migrate")
        if hasattr(args, 'i_understand_vlan1_risks') and args.i_understand_vlan1_risks:
            sys.argv.append("--i-understand-vlan1-risks")
        if args.force:
            sys.argv.append("--force")
        return apply_main()

    print("Unknown command")
    return 1


if __name__ == "__main__":
    sys.exit(main())
