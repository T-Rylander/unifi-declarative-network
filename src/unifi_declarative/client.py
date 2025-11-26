import os
import json
import time
import requests
from requests.exceptions import Timeout, ConnectionError, HTTPError
from typing import Any, Dict, Optional
from dotenv import load_dotenv

class UniFiClient:
    def __init__(self, base_url: str, username: str, password: str, site: str = "default", verify_ssl: bool = True):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.site = site
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self._token = None

    def login(self) -> None:
        url = f"{self.base_url}/api/login"
        payload = {"username": self.username, "password": self.password}
        resp = self.session.post(url, json=payload, verify=self.verify_ssl)
        resp.raise_for_status()
        data = resp.json()
        self._token = data.get('data', [{}])[0].get('token')
        if not self._token:
            # Some controller versions rely on session cookies without explicit token
            self._token = 'cookie-auth'

    def get(self, path: str) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        resp = self.session.get(url, verify=self.verify_ssl, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            resp = self.session.post(url, json=payload, verify=self.verify_ssl, timeout=30)
            if resp.status_code == 401:
                # try re-login once
                self.login()
                resp = self.session.post(url, json=payload, verify=self.verify_ssl, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Timeout:
            raise RuntimeError("Controller timeout after 30s")
        except ConnectionError as e:
            raise RuntimeError(f"Cannot reach controller: {e}")
        except HTTPError as e:
            raise RuntimeError(f"API error {resp.status_code}: {resp.text}")

    def export_backup(self) -> bytes:
        # Controller export endpoint varies by version; using legacy path
        path = f"/api/s/{self.site}/cmd/backup"
        resp = self.session.post(f"{self.base_url}{path}", json={"cmd": "backup"}, verify=self.verify_ssl)
        resp.raise_for_status()
        return resp.content

    # ---- Networks (VLANs) ----
    def list_networks(self) -> Dict[str, Any]:
        """List network configurations (includes VLANs)."""
        return self.get(f"/api/s/{self.site}/rest/networkconf")

    def upsert_vlan(self, vlan: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update a VLAN network configuration."""
        payload = {
            "name": vlan["name"],
            "vlan": vlan["vlan_id"],
            "subnet": vlan["subnet"],
            "gateway": vlan["gateway"],
            "dhcp_enabled": vlan.get("dhcp_enabled", True),
            "domain_name": vlan.get("domain_name"),
            "dns1": (vlan.get("dhcp_dns") or [None])[0],
            "dns2": (vlan.get("dhcp_dns") or [None, None])[1] if len(vlan.get("dhcp_dns", [])) > 1 else None,
            "purpose": vlan.get("purpose"),
            "enabled": vlan.get("enabled", True),
        }
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}
        return self.post(f"/api/s/{self.site}/rest/networkconf", payload)

    @classmethod
    def from_env(cls) -> "UniFiClient":
        load_dotenv()
        return cls(
            base_url=os.getenv("UNIFI_CONTROLLER_URL", "http://localhost:8443"),
            username=os.getenv("UNIFI_USERNAME", ""),
            password=os.getenv("UNIFI_PASSWORD", ""),
            site=os.getenv("UNIFI_SITE", "default"),
            verify_ssl=os.getenv("UNIFI_VERIFY_SSL", "true").lower() == "true",
        )
