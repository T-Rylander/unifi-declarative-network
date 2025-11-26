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
