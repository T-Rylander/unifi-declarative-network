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

## Architecture
See `docs/hardware-constraints.md` for USG-3P design decisions.

## Documentation
- `docs/adr/001-python-over-bash.md`
- `docs/hardware-constraints.md`
- Schema reference (coming soon)

## License
MIT
