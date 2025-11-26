# Network Migration Runbook

This guide documents a safe, manual migration of the UniFi Controller to `10.0.10.10` and the management plane to VLAN 10 without scripting OS-level changes. Follow in order. Do not automate OS netplan changes.

## Prerequisites
- Console/KVM access to `rylan-dc` (no SSH-only maintenance)
- Maintenance window scheduled (10–20 minutes)
- Latest controller backup downloaded (see Backup section)
- `.env` configured for current controller IP
- Out-of-band path to switch UI (in case controller moves)

## Phase 0: Prepare Network Path (critical)
1. Ensure VLAN 10 exists on the gateway:
   - Run from your workstation:
     - PowerShell:
       - `python -m src.unifi_declarative.cli apply --dry-run`
       - `python -m src.unifi_declarative.cli apply`
         - Safe: tool will create VLANs 10/30/40 and skip VLAN 1 unless `--migrate` is set.
2. Pre-stage the switch port for `rylan-dc`:
   - Change that port to Access VLAN 10 (recommended) or a Trunk that untagged=10 and tags include [10,30,40].
   - Verify a laptop on that port obtains a 10.0.10.0/24 lease and can ping `10.0.10.1`.

Notes:
- This ensures that when `rylan-dc` moves to `10.0.10.10`, L2/L3 connectivity already exists.
- If this step is skipped, the server may become unreachable after netplan change.

## Phase 1: Pre-migration validation (5 min)
- Validate configs (offline):
  - `python -m src.unifi_declarative.cli validate`
  - `python -m src.unifi_declarative.cli apply --check-mode`
- Export a controller backup:
  - `python -m src.unifi_declarative.cli backup`
  - Confirm file in `backups/controller-backup.unf`
- Optional: Manual backup via UI → Settings → Backup/Restore.

## Phase 2: Controller IP migration on rylan-dc (console/KVM only)
1. Identify the correct interface name on rylan-dc:
   - `ip -br a` (look for the cabled interface, e.g., `enp4s0`)
2. Backup current netplan:
   - `sudo cp /etc/netplan/00-installer-config.yaml /etc/netplan/00-installer-config.yaml.backup`
3. Create or replace netplan with VLAN 10 address (adjust interface name if needed):
```
network:
  version: 2
  ethernets:
    enp4s0:
      addresses:
        - 10.0.10.10/24
      routes:
        - to: default
          via: 10.0.10.1
      nameservers:
        addresses: [10.0.10.10, 1.1.1.1]
```
   - Apply safely:
     - `sudo netplan try --timeout 120`
     - Press ENTER to confirm if connectivity is good; otherwise it will auto-rollback.
4. Firewall/UFW check (if UFW is enabled):
   - `sudo ufw status`
   - If necessary: `sudo ufw allow 8443/tcp`
5. Time sync (TLS/session sanity): `timedatectl status` should show NTP synchronized: yes

## Phase 3: Update local tooling to new controller IP
- Update `.env` on your workstation:
  - PowerShell:
```
(Get-Content .env) -replace 'UNIFI_HOST=\d+\.\d+\.\d+\.\d+','UNIFI_HOST=10.0.10.10' | Set-Content .env
```
  - Bash:
```
sed -i 's/UNIFI_HOST=.*/UNIFI_HOST=10.0.10.10/' .env
```
- Verify controller reachability:
  - From a browser: https://10.0.10.10:8443
  - Or from Bash: `curl -k https://10.0.10.10:8443/status`

DNS (recommended):
- Update the internal DNS A record for the controller hostname to `10.0.10.10`.
- In UniFi UI → Settings → System → Application Configuration, verify the "Controller Hostname/IP" reflects the new value.

## Phase 4: Apply and verify from the tool
- Final dry-run:
  - `python -m src.unifi_declarative.cli apply --dry-run`
- Apply (no VLAN 1 changes unless explicitly migrating it):
  - `python -m src.unifi_declarative.cli apply`
- Post-apply checks:
  - `python -m src.unifi_declarative.cli status`
  - Verify devices show Connected and Provisioned.

## Rollback (summary)
If anything fails:
- Restore netplan:
  - `sudo cp /etc/netplan/00-installer-config.yaml.backup /etc/netplan/00-installer-config.yaml`
  - `sudo netplan apply`
- Restore controller config via UI using `backups/controller-backup.unf`.
- Revert `.env` to previous `UNIFI_HOST`.

For detailed recovery steps, see `docs/ROLLBACK_PROCEDURES.md`.

## Notes and rationale
- OS network changes are intentionally manual to avoid lockouts.
- The tool’s `--check-mode` and safe apply will never modify VLAN 1 unless `--migrate` and `--i-understand-vlan1-risks` are used.
- Switch port changes for `rylan-dc` are manual until port APIs are wired in a future phase.
