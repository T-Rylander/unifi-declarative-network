from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field, IPvAnyNetwork, field_validator
from ipaddress import IPv4Network


class DHCPOption(BaseModel):
    option: int = Field(ge=1, le=255)
    value: str


class QoSConfig(BaseModel):
    uplink_priority: int = Field(ge=0, le=7)
    downlink_priority: int = Field(ge=0, le=7)
    dscp_marking: int = Field(ge=0, le=63)


class VLANConfig(BaseModel):
    name: str
    purpose: str
    subnet: IPv4Network
    gateway: str
    vlan_id: int = Field(ge=1, le=4094)
    dhcp_enabled: bool
    dhcp_start: Optional[str] = None
    dhcp_stop: Optional[str] = None
    dhcp_dns: List[str] = []
    dhcp_options: List[DHCPOption] = []
    qos: Optional[QoSConfig] = None
    enabled: bool = True

    @field_validator('gateway')
    def gateway_in_subnet(cls, v, info):
        subnet = info.data.get('subnet')
        if subnet and IPv4Network(f"{v}/32") not in subnet:
            raise ValueError(f"Gateway {v} not in {subnet}")
        return v


class NetworkConfig(BaseModel):
    vlans: Dict[str, VLANConfig]

    @field_validator('vlans')
    def max_four_vlans(cls, v):
        enabled = [x for x in v.values() if x.enabled]
        if len(enabled) > 4:
            raise ValueError(f"USG-3P supports max 4 VLANs, found {len(enabled)}")
        return v
