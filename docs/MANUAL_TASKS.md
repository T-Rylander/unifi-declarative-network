# Manual Tasks (Not Automated)

The following tasks are intentionally not automated to avoid lockouts and platform coupling.

- Server network migration (netplan changes)
  - High blast radius; requires console/KVM; use `netplan try` with auto-rollback.
- Switch port reassignment for `rylan-dc`
  - Must be staged in the controller UI: set to Access VLAN 10 (or trunk with untagged=10) before server IP change.
- DNS updates
  - Update the A record for the controller hostname to the new IP (`10.0.10.10`).
- UFW / host firewall rules
  - Verify `8443/tcp` is allowed if UFW is enabled.
- Controller Hostname/IP (Inform) setting
  - In UniFi UI → Settings → System → Application Configuration, confirm hostname/IP matches new address.
- Time sync validation
  - Ensure `timedatectl status` shows `NTP service: active` and `System clock synchronized: yes`.

Rationale: These steps depend on live environment context and should be executed by an operator with out-of-band access. Future phases may add opt-in automation behind explicit flags.

## Device Re-Inform (Controller IP change)
When the controller IP changes, some devices may not automatically reconnect. If devices remain Disconnected for more than ~5 minutes, perform a re-inform.

- Trigger condition: Devices show `Disconnected` > 5 minutes after controller IP migration.

### Option A: CLI on device (SSH)
On each device (USG/USW/UAP), SSH in and run:

```
set-inform http://10.0.10.10:8080/inform
```

Notes:
- UniFi 8.x typically uses `http://<controller>:8080/inform` for adoption inform URL.
- Repeat the command until the device reports `Adopting` or `Connected`.

### Option B: Controller UI
In the controller:
- Navigate to the device → Settings
- Locate “Manage” or “Connection” section → Use “Reconnect”/“Locate” then “Adopt” if needed
- Ensure the “Controller Hostname/IP” is correct under Settings → System → Application Configuration

### Bulk Re-Inform (example)
If multiple APs need re-inform, use a host with SSH key access:

```bash
#!/bin/bash
CONTROLLER_INFORM="http://10.0.10.10:8080/inform"
DEVICE_LIST=(
  "ap-upstairs.local"
  "ap-downstairs.local"
  "switch-closet.local"
)

for host in "${DEVICE_LIST[@]}"; do
  echo "Re-informing $host"
  ssh -o BatchMode=yes "$host" "sudo syswrapper.sh set-inform $CONTROLLER_INFORM" || {
    echo "Failed to re-inform $host";
  }
done
```

Replace hostnames with IPs/DNS entries reachable from your admin workstation.
