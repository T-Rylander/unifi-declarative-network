#!/bin/bash
# Non-destructive pre-migration smoke test
set -euo pipefail

CONTROLLER_HOST=${UNIFI_HOST:-"$(grep -E '^UNIFI_HOST=' .env | cut -d'=' -f2)"}
NEW_GATEWAY=${NEW_GATEWAY:-"10.0.10.1"}
BACKUP_FILE="backups/controller-backup.unf"

exit_with() {
  echo "$2" >&2
  exit "$1"
}

echo "🛤️ Pre-Migration Smoke Test"

# 1) Controller connectivity
if curl -k -s "https://${CONTROLLER_HOST}:8443/status" >/dev/null; then
  echo "✅ Controller reachable at ${CONTROLLER_HOST}:8443"
else
  exit_with 10 "❌ Controller not reachable at ${CONTROLLER_HOST}:8443"
fi

# 2) VLAN 10 status (basic reachability to gateway)
if ping -c 1 -W 2 "${NEW_GATEWAY}" >/dev/null 2>&1; then
  echo "ℹ️ VLAN 10 gateway ${NEW_GATEWAY} is reachable (pre-staged)"
else
  echo "⚠️ VLAN 10 gateway ${NEW_GATEWAY} not reachable from this host"
fi

# 3) Backup exists
if [[ -f "${BACKUP_FILE}" ]]; then
  echo "✅ Backup present: ${BACKUP_FILE}"
else
  exit_with 20 "❌ Missing backup file: ${BACKUP_FILE}"
fi

# 4) Confirm new gateway not yet reachable (if running from VLAN 1 host)
# This check is informational; success either way is acceptable based on staging.
if ping -c 1 -W 2 "${NEW_GATEWAY}" >/dev/null 2>&1; then
  echo "ℹ️ New gateway reachable now (OK if staging complete)"
else
  echo "ℹ️ New gateway not reachable yet (expected before netplan change)"
fi

# 5) Validate configs offline
if python -m src.unifi_declarative.cli validate >/dev/null; then
  echo "✅ Config validation OK"
else
  exit_with 30 "❌ Config validation failed"
fi

if python -m src.unifi_declarative.cli apply --check-mode >/dev/null; then
  echo "✅ Check-mode OK (offline)"
else
  exit_with 31 "❌ Check-mode validation failed"
fi

echo "✅ Smoke test passed"
exit 0
