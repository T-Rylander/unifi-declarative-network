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

## Prerequisites
- Python 3.12+
- UniFi Controller 8.1+
- USG-3P or compatible gateway
- Completed bootstrap setup

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

## Migration & Operations 🛤️
- `docs/MIGRATION_GUIDE.md`: Step-by-step migration runbook (manual, safe OS changes; use `netplan try`).
- `docs/ROLLBACK_PROCEDURES.md`: Emergency recovery for netplan, controller restore, and switch port reversion.
- `docs/MANUAL_TASKS.md`: OS tasks intentionally kept manual (netplan, DNS, UFW, time sync, device re-inform).
- Script: `scripts/pre-migration-smoke-test.sh` — non-destructive checks (controller reachability, backup presence, offline validation).

## Architecture
See `docs/hardware-constraints.md` for USG-3P design decisions.

## Documentation
- `docs/adr/001-python-over-bash.md`
- `docs/hardware-constraints.md`
- `docs/MIGRATION_GUIDE.md` (step-by-step migration runbook)
- `docs/ROLLBACK_PROCEDURES.md` (emergency recovery)
- `docs/MANUAL_TASKS.md` (OS steps intentionally manual)
- Schema reference (coming soon)

## License
MIT
