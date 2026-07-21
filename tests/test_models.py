from src.db.base import Base
from src.models import ApprovalRequest, AuditLog, Policy


def test_sentry_models_are_registered_with_metadata() -> None:
    assert "audit_log" in Base.metadata.tables
    assert "policy" in Base.metadata.tables
    assert "approval_request" in Base.metadata.tables


def test_approval_request_links_to_audit_log() -> None:
    relationship = ApprovalRequest.audit_log.property

    assert relationship.mapper.class_ is AuditLog
    assert ApprovalRequest.__table__.c.audit_log_id.unique is True


def test_policy_links_to_audit_logs_by_violated_policy_code() -> None:
    relationship = Policy.audit_logs.property

    assert relationship.mapper.class_ is AuditLog
    assert AuditLog.__table__.c.violated_policy.foreign_keys

