# CONTEXT ANCHOR – unifi-declarative-network  
**Version 1.0** | 25 November 2025 | Travis + Grok (with Leo’s precision seasoning)

## Why This Repository Exists
The bootstrap repo (`rylan-home-bootstrap`) is frozen, proven, and portfolio-perfect.  
This repository is its adult form: the same network, now expressed declaratively, tested, multi-arch, secrets-aware, and auditable.  
We are not re-building the network.  
We are teaching the network to rebuild itself — exactly — from source of truth.

## Non-Negotiable Design Principles (enforced in CI, reviewed in every PR)
1. **Declarative First** – YAML describes desired state. Code is the reconciliation engine, never the source.
2. **Idempotency Guarantee** – Running `apply` 1× or 100× must yield identical outcome with zero side effects.
3. **Fail-Fast + Human-Readable Errors** – Validation runs before authentication. A single malformed VLAN aborts everything with a clear message.
4. **Single Source of Truth** – The `config/` directory is law. The controller is the cache.
5. **Zero Trust Between VLANs** – Explicit allow rules only. “Default deny” is not a suggestion; it is physics.
6. **Multi-Architecture from Day 1** – CI matrix runs on amd64 and arm64 because the UDM Pro is ARM and my desktop is not.
7. **Secrets Never Committed** – `.env` is gitignored; `.env.example` is the contract.

## Architectural Decisions (Locked In – see /docs/adr)
| ADR | Decision | Rationale | Status |
|-----|----------|---------|--------|
| 001 | Python 3.12 + type hints | Superior ecosystem for REST automation, testability, and future Terraform provider interop | Accepted |
| 002 | Pure REST client (no official SDK) | Official UniFi SDK is abandoned; community `unifi-api-client` is lightweight and battle-tested | Accepted |
| 003 | YAML over JSON for human configs | Eye-friendly, comments allowed, ruamel.yaml preserves order & comments | Accepted |
| 004 | No Bash in core logic | Bash stays in CI wrappers only. Core logic must be unit-testable | Accepted |
| 005 | Validation → Dry-Run → Apply pipeline | Mirrors GitOps reconciliation loops; prevents “surprise provisioning” | Accepted |

## Exact Scope of This Repository
| In Scope | Out of Scope (intentionally) |
|----|----|
| VLANs, subnets, DHCP scopes & options | UniFi device adoption (handled in bootstrap) |
| Firewall rules (LAN IN, LAN LOCAL, WAN IN) | Dynamic DNS, VPN tunnels (future repo) |
| QoS policy (smart queues + DSCP EF for VLAN 40) | Wi-Fi SSID scheduling, captive portal |
| Network groups & port groups | Controller high-availability |
| Full diff + audit trail of every apply | Physical cabling diagrams (lives in bootstrap) |

## Success Metrics (how we know we've won)
- `make apply` on a factory-reset USG-3P + fresh controller restores the entire Version 4.2 topology in <4 minutes with zero manual clicks.
- `make apply` on factory-reset USG-3P restores full v3.0 topology in <3 minutes.
- `make test` passes on both amd64 and arm64 runners in <90 seconds.
- An outsider can read `config/` and reconstruct the entire security posture without launching the controller.
- Every firewall rule change creates a git commit that is reviewer-friendly ("Allow Telegraf → InfluxDB" is a one-line diff).

## The “Academic Slant” We Are Quietly Proud Of
- Every major decision is an ADR with problem statement, considered alternatives, and consequences.
- Unit tests cover schema validation and idempotency edge cases.
- Type hints are exhaustive (`UnifiNetworkConf`, `FirewallRule`, `VlanId`, etc.).
- CI fails if `config/` and live controller drift >0 objects.

## Future Evolution Path (explicitly planned, not accidental)
1. Phase 2 – Terraform provider `ubiquiti/unifi` (already in beta) replaces custom Python client
2. Phase 3 – GitOps operator (ArgoCD-style) watching this repo, auto-applying on merge to main
3. Phase 4 – Vault integration + short-lived controller credentials

We are building Phase 1 so cleanly that Phase 4 will feel inevitable instead of painful.

---

This repository is not a collection of scripts.  
It is a formal description of a network that happens to be able to enforce itself.

Let’s go make something future-proof.