# unifi-declarative-network

Infrastructure-as-Code for UniFi networks | Python + Pydantic + GitOps

## Overview
Production-grade network automation built for the Rylan-Home Bootstrap foundation. Declarative YAML configs with hardware-aware validation for USG-3P deployments.

## Features
- ✅ Type-safe VLAN/firewall management (Pydantic v2)
- ✅ Deep-diff state reconciliation
- ✅ Hardware constraint validation (USG-3P 4-VLAN limit)
- ✅ Idempotent apply operations
- ✅ Comprehensive testing suite

## Security Best Practices

⚠️ **Critical Security Notes**:
- **Never commit `.env`** to version control (already in `.gitignore`)
- **Use strong, unique passwords** for the `api-declarative` controller admin
- **SSL verification** is enabled by default; only disable for internal testing
- **Rotate credentials** after any suspected compromise
- **Backup before apply**: Script auto-backs up, but verify `backups/` directory
- **Limit API account scope**: Use local-only admin, not owner/super-admin

If you disable SSL verification:
```bash
UNIFI_VERIFY_SSL=false  # Only for self-signed certs in isolated networks
```
You will see a warning on every run. Re-enable for production use.

## Prerequisites
- Python 3.12+
- UniFi Controller 8.1+ (9.5.21 tested)
- USG-3P or compatible gateway
- Local admin account without 2FA (see `docs/LESSONS_LEARNED.md`)

## Quick Start
```bash
# Clone and setup
git clone <your-repo-url>
cd unifi-declarative-network
python -m venv venv
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Configure
copy .env.example .env
# Edit .env with your credentials

# Validate config
python -m src.unifi_declarative.validate

# Dry run
python -m src.unifi_declarative.apply --dry-run
```

## Bootstrap & Migration (UniFi 9.5.21 + USG-3P)
The only reliable sequence for 9.5.21 with USG-3P:

1. Factory reset all devices (default network 192.168.1.0/24).
2. Start a fresh controller; complete the wizard with a local admin (skip Ubiquiti cloud login → no 2FA).
3. Adopt the USG-3P first.
4. Immediately change the Default LAN to `10.0.1.0/27` in the UI. This manual change is mandatory before creating any VLANs.
5. Adopt switches and APs.
6. Run the script from this repo to apply VLANs and firewall.

Notes:
- VLAN 1 is managed manually in the UI and must not appear in `config/vlans.yaml`.
- Legacy bootstrap network (192.168.1.0/24) must not use `vlan_id: 1` in config.
- Ensure controller authentication uses a local admin without 2FA for automation.

## Architecture
See `docs/hardware-constraints.md` for USG-3P design decisions.

## Documentation
- **Setup & Operations**:
  - `docs/9.5.21-NOTES.md` — Version-specific bootstrap requirements
  - `docs/TROUBLESHOOTING.md` — Common issues and solutions
  - `docs/LESSONS_LEARNED.md` — 2FA workarounds and gotchas
- **Migration & Recovery**:
  - `docs/MIGRATION_GUIDE.md` — Step-by-step migration runbook
  - `docs/ROLLBACK_PROCEDURES.md` — Emergency recovery procedures
  - `docs/MANUAL_TASKS.md` — OS tasks kept manual (netplan, DNS, UFW)
- **Architecture & Decisions**:
  - `docs/hardware-constraints.md` — USG-3P VLAN limits and design rationale
  - `docs/adr/001-python-over-bash.md` — Technology choices and validation strategy

## License
MIT
