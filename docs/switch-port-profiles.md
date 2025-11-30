# Switch Port Profiles & Assignments

## Port Profiles

| Profile Name       | Native VLAN | Tagged VLANs     | Used For                              |
|--------------------|-------------|------------------|---------------------------------------|
| All VLANs Trunk    | None        | 10,30,40,90     | USG ↔ Switch, Switch ↔ Switch, AP uplinks |
| Management Gear    | 1           | None             | USG, Switches, APs, rylan-dc controller |
| Servers            | 10          | None             | Infrastructure servers                |
| Trusted Devices    | 30          | None             | Workstations, laptops                 |
| VoIP              | 40          | None             | Grandstream phones                    |
| Guest/IoT         | 90          | None             | Smart devices, guest devices          |

## Current Port Assignments (US-8-60W)

- **Port 1** → USG              → All VLANs Trunk
- **Port 8** → rylan-dc         → Management Gear
- **Ports 2-3** → APs           → All VLANs Trunk
- **Remaining ports** as needed → appropriate profile above
