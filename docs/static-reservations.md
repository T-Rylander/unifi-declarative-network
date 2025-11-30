# Static DHCP Reservations

## Reserved IP Addresses

| IP            | Device              | VLAN | Purpose                        |
|---------------|---------------------|------|--------------------------------|
| 10.0.1.1      | USG-3P (auto)       | 1    | Gateway                        |
| 10.0.1.20     | rylan-dc            | 1    | UniFi Controller               |
| 10.0.10.10    | Samba/DC            | 10   | Domain Controller              |
| 10.0.10.60    | AI Workstation      | 10   | Ollama / n8n                   |
| 10.0.30.40    | Pi5 osTicket        | 30   | Helpdesk                       |
| 10.0.40.30    | FreePBX (macvlan)   | 40   | VoIP server                    |
