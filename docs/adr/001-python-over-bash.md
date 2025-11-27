# ADR 001: Python 3.12 Over Bash for Core Logic

**Status:** Accepted  
**Date:** 25 November 2025  
**Authors:** Travis + Grok + Leo  
**Deciders:** Travis (network owner), Leo (architecture review)

## Context and Problem Statement

The `rylan-home-bootstrap` repository successfully provisioned a UniFi network using shell scripts, but lacked testability, type safety, and idempotency guarantees. As we transition to a declarative, GitOps-ready architecture, we must choose a language and tooling strategy that supports:

1. **Unit testing** of validation logic, API interactions, and state reconciliation
2. **Type safety** to catch configuration errors at lint-time, not runtime
3. **Rich ecosystem** for REST APIs, YAML parsing, and future integrations (Terraform providers, Vault)
4. **Multi-architecture CI** (amd64 + arm64) without platform-specific hacks
5. **Auditability** via structured logging and clear error messages

## Decision Drivers

- **Idempotency requirement:** Running `apply` multiple times must be safe and deterministic
- **Fail-fast validation:** Schema errors should abort before authenticating to the controller
- **Community tooling:** UniFi REST API is better documented than official Python SDK (which is abandoned)
- **Future-proofing:** Likely migration to Terraform `ubiquiti/unifi` provider in Phase 2

## Considered Options

### Option 1: Continue with Bash + `curl` + `jq`
**Pros:**
- Already working in bootstrap repo
- Zero dependencies beyond coreutils
- Familiar to network engineers

**Cons:**
- No type checking (errors discovered at runtime)
- Difficult to unit test (requires mocking `curl` responses)
- JSON manipulation with `jq` is brittle for complex schemas
- Idempotency logic requires manual state tracking (file-based locks, etc.)
- Hard to enforce VLAN count limits or subnet overlap checks

### Option 2: Python 3.12 + Type Hints + `unifi-api-client`
**Pros:**
- Native REST client libraries (`httpx`, `requests`)
- Type hints enforce schema correctness at lint-time (`mypy` integration)
- Rich testing ecosystem (`pytest`, `pytest-mock`, `responses`)
- YAML parsing with comment preservation (`ruamel.yaml`)
- Easy CI matrix for amd64/arm64 (GitHub Actions, GitLab CI)
- Community package `unifi-api-client` wraps REST API cleanly
- Future Terraform provider likely has Python bindings

**Cons:**
- Requires Python 3.12+ (not a concern on modern CI runners or Docker)
- Slightly larger container image than Alpine + Bash

### Option 3: Go + Official UniFi SDK
**Pros:**
- Single static binary (no runtime dependencies)
- Native concurrency for parallel API calls

**Cons:**
- Official Ubiquiti Go SDK is **abandoned** (last commit 2019)
- Community alternatives are fragmented
- Less mature YAML parsing (no comment preservation)
- Steeper learning curve for network engineers

### Option 4: Terraform `ubiquiti/unifi` Provider Only
**Pros:**
- Declarative by design
- State file provides automatic drift detection

**Cons:**
- Provider is still in **beta** (breaking changes expected)
- No custom validation logic (VLAN count limits, subnet overlap)
- Harder to integrate secrets management (Vault requires enterprise features)
- Less flexibility for "pre-flight checks" or dry-run mode

## Decision Outcome

**Chosen option:** Python 3.12 + Type Hints + `unifi-api-client`

### Rationale
1. **Type safety:** Python's type hints + `mypy` catch schema errors before provisioning
2. **Testability:** `pytest` allows unit tests for validation logic, API mocking, and idempotency checks
3. **Ecosystem maturity:** `ruamel.yaml`, `pydantic`, `httpx` are production-grade tools
4. **Community support:** `unifi-api-client` is actively maintained and wraps the REST API cleanly
5. **Future compatibility:** Phase 2 migration to Terraform can use Python for pre-apply validation hooks

### Consequences

#### Positive
- Unit tests enforce VLAN count limits, subnet overlap checks, and schema correctness
- CI pipeline can run `pytest --cov` to ensure >90% code coverage
- Type hints make code self-documenting (less reliance on external docs)
- YAML comments preserved in `config/` (important for audit trail)
- Easy to integrate with Vault (Python `hvac` library)

#### Negative
- Requires Python 3.12+ in CI runners (mitigated by Docker)
- Slightly larger container image (~50MB vs ~10MB for Alpine + Bash)
- Network engineers unfamiliar with Python may need training (mitigated by clear examples)

#### Neutral
- Bash remains in CI wrappers (Makefile targets, Docker entrypoints) per ADR 004

---

## Validation and Testing Strategy

### Required Checks (enforced in CI)
1. **Type checking:** `mypy src/ --strict`
2. **Linting:** `ruff check src/`
3. **Unit tests:** `pytest tests/ --cov=src --cov-report=term-missing`
4. **Schema validation:** `python -m unifi_declarative.validators config/vlans.yaml`

### Example Test Case (from `tests/test_validators.py`)
```python
def test_usg3p_vlan_limit():
    """USG-3P should cap VLANs conservatively (e.g., 8)."""
    vlans = {str(i): {"vlan_id": i} for i in range(1, 10)}  # 9 VLANs
    
    with pytest.raises(ValidationError, match="USG-3P supports max 8 VLANs"):
        validate_vlan_count(vlans, hardware_profile="usg3p")
```

---

## References

- [UniFi REST API Documentation](https://ubntwiki.com/products/software/unifi-controller/api) (community-maintained)
- [`unifi-api-client` PyPI package](https://pypi.org/project/unifi-api-client/)
- [Terraform `ubiquiti/unifi` Provider](https://registry.terraform.io/providers/ubiquiti/unifi/latest) (beta)
- [PEP 484: Type Hints](https://peps.python.org/pep-0484/)

---

### Hardware Constraint Addendum (27 Nov 2025)

USG-3P officially supports up to 15 tagged VLANs; practical stability with full routing/QoS is best around 8–10. This deployment uses 6 (5 tagged + 1 untagged legacy during bootstrap). See `docs/hardware-constraints.md`.

**Validator enforcement:**  
`validate_vlan_count()` caps USG-3P at 8 VLANs for stability. On UXG-Pro/UDM-SE profiles, the limit increases accordingly.
