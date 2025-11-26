from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DHCPOption(BaseModel):
    option: int
    value: str


class QoSConfig(BaseModel):
    uplink_priority: int
    downlink_priority: int
    dscp_marking: int


class VlanConfig(BaseModel):
    name: str
    purpose: Optional[str] = None
    subnet: str
    gateway: str
    vlan_id: int
    vlan_enabled: bool = True
    networkgroup: str = "LAN"
    domain_name: Optional[str] = None
    dhcp_enabled: bool = True
    dhcp_start: Optional[str] = None
    dhcp_stop: Optional[str] = None
    dhcp_lease: Optional[int] = None
    dhcp_dns: Optional[List[str]] = None
    dhcp_options: Optional[List[DHCPOption]] = None
    igmp_snooping: Optional[bool] = None
    multicast_dns: Optional[bool] = None
    lldp_med_enabled: Optional[bool] = None
    qos: Optional[QoSConfig] = None
    enabled: bool = True
    notes: Optional[str] = None


class NetworkConfig(BaseModel):
    vlans: Dict[str, VlanConfig] = Field(default_factory=dict)
