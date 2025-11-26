# Rollback Procedures

Use this guide to recover quickly if the migration fails.

## 1) Restore Server Network (rylan-dc)
1. Console/KVM into `rylan-dc`.
2. Restore previous netplan:
```
sudo cp /etc/netplan/00-installer-config.yaml.backup /etc/netplan/00-installer-config.yaml
sudo netplan apply
```
3. Verify connectivity to the old gateway and controller IP (as applicable).

## 2) Restore UniFi Controller Configuration
Preferred: Use the UniFi UI.
1. Browse to the controller (at the IP that is reachable) → Settings → Backup/Restore.
2. Upload and restore `backups/controller-backup.unf`.
3. Wait for the application to restart and devices to reconnect.

Notes:
- If the controller is unreachable, first complete the server network rollback above.
- Restoration may take several minutes as MongoDB/application restart.

## 3) Revert Local Tooling
- Revert `.env` to the prior host, e.g. `UNIFI_HOST=192.168.1.20`.
- Optionally commit a revert with context in Git.

## 4) Switch Port Configuration
- If the `rylan-dc` switch port was changed to Access VLAN 10, revert it to its previous state (typically Access VLAN 1) until the next maintenance window.

## 5) Troubleshooting
- Controller service status:
```
sudo systemctl status unifi
journalctl -u unifi --no-pager -n 200
```
- Network interface status:
```
ip -br a
ip route
```
- Firewall (if UFW is enabled):
```
sudo ufw status
```

## 6) Post-Rollback Validation
- Devices adopt and show Connected
- Controller UI accessible
- DHCP working on expected VLANs
- Document root cause in repo and plan a corrected next attempt
