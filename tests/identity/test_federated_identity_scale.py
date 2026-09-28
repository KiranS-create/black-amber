"""
Tests for FederatedIdentityDirectory and Four-State Cache Lifecycle.

Validates:
- Provider adapter registration and routing
- Cache state transitions: FRESH -> CACHED -> STALE -> UNAVAILABLE
- Fail-soft PENDING resolution during external provider outages
- Stable identity_id across email and human metadata updates
- Strict multi-tenant isolation
"""

import pytest
import time

from core.identity.federated import (
    FederatedIdentityDirectory,
    EntraIdAdapter,
    OktaAdapter,
    IdentityCacheState
)
from core.identity.models import Identity, IdentityStatus


def test_federated_cache_lifecycle_states():
    # Configure short TTLs for deterministic testing: fresh=1.0s, stale=3.0s
    directory = FederatedIdentityDirectory(fresh_ttl_seconds=1.0, stale_threshold_seconds=3.0)
    tenant = "tenant_test"

    ident = Identity(
        identity_id="usr_001",
        provider="entra_id",
        provider_subject="sub_001",
        display_name="Alice Smith",
        email="alice@company.com",
        organization_id=tenant,
        department="Security",
        status=IdentityStatus.ACTIVE
    )
    directory.cache_identity(ident, tenant_id=tenant)
    directory.bind_recipient("rec_alice", "usr_001", tenant_id=tenant)

    # 1. Immediate resolution -> FRESH
    summary, status = directory.resolve_recipient("rec_alice", tenant_id=tenant)
    assert summary is not None
    assert status == "RESOLVED"
    assert summary.source == "CACHE_FRESH"

    # 2. Wait for fresh_ttl expiry -> CACHED
    time.sleep(1.2)
    summary2, status2 = directory.resolve_recipient("rec_alice", tenant_id=tenant)
    assert summary2 is not None
    assert status2 == "CACHED"
    assert summary2.source == "FALLBACK_CACHED"

    # 3. Wait for stale_threshold expiry -> STALE
    time.sleep(2.0)
    summary3, status3 = directory.resolve_recipient("rec_alice", tenant_id=tenant)
    assert summary3 is not None
    assert status3 == "CACHED"  # Still resolves for forensic auditability
    assert summary3.source == "FALLBACK_STALE"


def test_provider_outage_fail_soft_pending():
    """Verify that provider outage without cache returns PENDING without throwing."""
    directory = FederatedIdentityDirectory()
    tenant = "tenant_outage"

    entra = EntraIdAdapter(tenant_id=tenant, provider_id="entra_pri")
    entra.is_healthy = False  # Simulate cloud IdP outage
    directory.register_provider(entra)
    directory.bind_recipient("rec_bob", "usr_bob_missing", tenant_id=tenant)

    summary, status = directory.resolve_recipient("rec_bob", tenant_id=tenant)
    assert summary is None
    assert status == "PENDING"


def test_stable_identity_id_across_name_and_email_changes():
    """Verify identity_id remains immutable when IdP human attributes change."""
    directory = FederatedIdentityDirectory()
    tenant = "tenant_enterprise"

    # Initial identity
    ident_v1 = Identity(
        identity_id="usr_immutable_123",
        provider="okta",
        provider_subject="sub_okta_456",
        display_name="Carol Danvers",
        email="carol.danvers@company.com",
        organization_id=tenant,
        status=IdentityStatus.ACTIVE
    )
    directory.cache_identity(ident_v1, tenant_id=tenant)
    directory.bind_recipient("rec_carol", "usr_immutable_123", tenant_id=tenant)

    s1, _ = directory.resolve_recipient("rec_carol", tenant_id=tenant)
    assert s1.identity_id == "usr_immutable_123"
    assert s1.email == "carol.danvers@company.com"

    # Human gets married, updates name and email in IdP
    ident_v2 = Identity(
        identity_id="usr_immutable_123",  # Opaque ID preserved
        provider="okta",
        provider_subject="sub_okta_456",
        display_name="Carol Danvers-Rambeau",
        email="carol.rambeau@company.com",
        organization_id=tenant,
        status=IdentityStatus.ACTIVE
    )
    directory.cache_identity(ident_v2, tenant_id=tenant)

    s2, _ = directory.resolve_recipient("rec_carol", tenant_id=tenant)
    assert s2.identity_id == "usr_immutable_123"
    assert s2.display_name == "Carol Danvers-Rambeau"
    assert s2.email == "carol.rambeau@company.com"


def test_tenant_isolation_in_directory():
    directory = FederatedIdentityDirectory()
    tenant_a = "tenant_alpha"
    tenant_b = "tenant_beta"

    ident_a = Identity(
        identity_id="usr_a",
        provider="local",
        provider_subject="sub_a",
        display_name="User Alpha",
        email="user@alpha.com",
        organization_id=tenant_a,
        status=IdentityStatus.ACTIVE
    )
    directory.cache_identity(ident_a, tenant_id=tenant_a)
    directory.bind_recipient("rec_a", "usr_a", tenant_id=tenant_a)

    # Tenant B query for Tenant A recipient must return NOT_FOUND
    summary, status = directory.resolve_recipient("rec_a", tenant_id=tenant_b)
    assert summary is None
    assert status == "NOT_FOUND"
