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
- UniFi Network Application 9.5.21+ (cookie-based authentication required)
- USG-3P or compatible gateway
- **Local admin account WITHOUT 2FA** (mandatory for automation - see `docs/LESSONS_LEARNED.md`)
- **Session cookie authentication** (token auth is deprecated in 9.5.21)

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

> 🚨 **CRITICAL: You MUST follow this exact sequence or the script will fail with `api.err.VlanUsed` errors**

The **only** reliable bootstrap sequence for UniFi 9.5.21 with USG-3P:

1. **Factory reset** all devices (default network 192.168.1.0/24).
2. **Start a fresh controller**; complete the wizard with a **local admin** (skip Ubiquiti cloud login → avoids 2FA).
3. **Adopt the USG-3P first**.
4. 🔴 **IMMEDIATELY change the Default LAN** to `10.0.1.0/27` in the controller UI:
   - Navigate to: **Settings → Networks → Default LAN**
   - Change subnet from `192.168.1.0/24` to `10.0.1.0/27`
   - Save and provision the USG
   - **This step is NON-NEGOTIABLE**: UniFi 9.5.21 will reject any API attempts to manage VLAN 1 until you manually change the Default LAN first
5. **Adopt switches and APs** (they will now use the 10.0.1.0/27 management network).
6. **Run the script** from this repo to apply VLANs and firewall rules.

### 🛑 Critical Requirements (Battle-Tested)

| Requirement | Why It Matters |
|-------------|----------------|
| **VLAN 1 MUST be changed in UI first** | UniFi 9.5.21 rejects API changes to Default LAN. Attempting to manage VLAN 1 via script causes `api.err.VlanUsed` and breaks device adoption. |
| **VLAN 1 MUST NOT be in `vlans.yaml`** | Script will fail validation if it finds `vlan_id: 1` or key `"1"` in config. VLAN 1 is UI-managed only. |
| **Cookie-based auth required** | 9.5.21 uses session cookies (`POST /api/login`). Token auth is deprecated. Script handles cookie lifecycle automatically. |
| **Local admin without 2FA** | 2FA breaks automation. Create a dedicated local admin for API access (see `docs/LESSONS_LEARNED.md`). |

**If you skip step 4**, the script will fail with:
```
api.err.VlanUsed: Cannot modify VLAN 1 (Default network in use)
```

See `docs/9.5.21-KNOWN-ISSUES.md` for detailed troubleshooting.

## Architecture
See `docs/hardware-constraints.md` for USG-3P design decisions.

## Documentation
- **Setup & Operations**:
  - `docs/9.5.21-NOTES.md` — Version-specific bootstrap requirements
  - `docs/9.5.21-KNOWN-ISSUES.md` — **Battle-tested solutions to every UniFi 9.5.21 + USG-3P issue we survived**
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
