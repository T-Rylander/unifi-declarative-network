# Troubleshooting Guide

## Common Issues and Solutions

### Authentication Failures

**Problem**: `Login failed: 401 Unauthorized`

**Solutions**:
1. Verify credentials in `.env` match controller admin account
2. Ensure account is **local admin** (not cloud account)
3. Check for typos in `UNIFI_CONTROLLER_URL` (include https:// and port)
4. Confirm 2FA is **disabled** for the API account (see `LESSONS_LEARNED.md`)

**Problem**: `400 Bad Request` on login

**Cause**: Controller rejecting login due to 2FA requirement

**Solution**: Create dedicated local-only admin without 2FA

---

### SSL/TLS Errors

**Problem**: `SSLError: certificate verify failed`

**Cause**: Self-signed certificate on controller

**Solution**:
```bash
# In .env:
UNIFI_VERIFY_SSL=false
```
⚠️ **Only use for internal testing**. You'll see a warning on every run.

**Problem**: `Connection refused` or `Name or service not known`

**Cause**: Controller URL incorrect or controller offline

**Solutions**:
1. Ping controller hostname: `ping unifi-controller.local`
2. Verify controller is running: check UI access
3. Check firewall rules allowing port 8443
4. Try IP address instead of hostname in `.env`

---

### Configuration Errors

**Problem**: `ValidationError: USG-3P supports max 8 VLANs`

**Cause**: Too many VLANs defined in `config/vlans.yaml`

**Solution**:
- Remove unused VLANs or migrate to UXG-Pro/UDM-SE
- Note: VLAN 1 managed manually in UI, not in config

**Problem**: `VLAN ID must be between 1 and 4094`

**Cause**: Invalid `vlan_id` field

**Solution**: Check `config/vlans.yaml` for typos in VLAN IDs

**Problem**: `Gateway X.X.X.X not in subnet Y.Y.Y.Y/Z`

**Cause**: Gateway IP outside subnet range

**Solution**: Adjust gateway or subnet in `config/vlans.yaml`

---

### Provisioning Issues

**Problem**: `Provisioning timeout (devices may still be settling)`

**Cause**: Controller or devices slow to apply changes

**Solutions**:
1. Wait 2-3 minutes and check controller UI
2. Manually trigger provision: Devices → [device] → Force Provision
3. Re-run script (idempotent, safe to retry)

**Problem**: Devices show "Adopting" forever

**Cause**: Network misconfiguration or adoption loop

**Solutions**:
1. SSH to device: `set-inform http://controller-ip:8080/inform`
2. Check VLAN 1 (management) is accessible from device
3. Factory reset device and re-adopt

---

### Dry-Run and Safety

**Problem**: Want to preview changes without applying

**Solution**:
```bash
python -m src.unifi_declarative.apply --dry-run
```

**Problem**: Need to validate config without controller access

**Solution**:
```bash
python -m src.unifi_declarative.validate
```

**Problem**: Script failed mid-apply, network inconsistent

**Solution**:
1. Check `backups/pre-apply.unf` exists
2. Restore via controller UI: Settings → Backup → Upload
3. See `docs/ROLLBACK_PROCEDURES.md`

---

### Performance and Rate Limiting

**Problem**: `429 Too Many Requests`

**Cause**: Controller rate limiting API calls

**Solution**: Script has built-in retry with exponential backoff. Wait and retry.

**Problem**: Script hangs on `wait_for_provisioning`

**Cause**: Devices not reporting state or controller overloaded

**Solutions**:
1. Ctrl+C to abort (safe, no partial state)
2. Check controller UI for device status
3. Increase timeout: edit `client.py` `wait_for_provisioning(timeout=120)`

---

### Python Environment Issues

**Problem**: `ModuleNotFoundError: No module named 'dotenv'`

**Cause**: Dependencies not installed

**Solution**:
```bash
pip install -r requirements.txt
```

**Problem**: `python: command not found`

**Cause**: Python not in PATH or wrong version

**Solution**:
```bash
python3 --version  # Should be 3.12+
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\Activate.ps1  # Windows
```

---

### Log Analysis

**Enable debug logging** (future enhancement):
```python
# In apply.py:
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Check controller logs**:
```bash
# On controller host:
tail -f /var/log/unifi/server.log
```

---

## Still Stuck?

1. Check `docs/9.5.21-NOTES.md` for version-specific quirks
2. Review `docs/LESSONS_LEARNED.md` for known gotchas
3. Open GitHub issue with:
   - Python version (`python --version`)
   - Controller version (from UI)
   - Full error message
   - Sanitized `.env` (remove credentials!)
   - Output of `python -m src.unifi_declarative.validate`
