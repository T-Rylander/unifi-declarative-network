# Lessons Learned

**Document Purpose:** Capture technical hurdles, non-obvious solutions, and "gotchas" encountered during development and deployment. These lessons preserve institutional knowledge and help future contributors avoid the same pitfalls.

---

## UniFi Controller 2FA vs Automation

UniFi Network Application with 2FA enabled blocks API logins from scripts (400 on `/api/login`, triggers 2FA email).

**Permanent fix:**  
Create a dedicated local-only admin account with 2FA disabled:
- Settings → Admins → Add Admin → Local Access Only
- Username: `api-declarative`
- Strong password
- Full admin rights
- Two-Factor Authentication **unchecked**

Update `.env`:
```
UNIFI_USERNAME=api-declarative
UNIFI_PASSWORD=super-long-random-password
UNIFI_VERIFY_SSL=false
```

This account is used only by automation — your personal account keeps 2FA for human logins.

---

## Additional Lessons

*(Future hurdles and solutions will be documented here as they arise)*
