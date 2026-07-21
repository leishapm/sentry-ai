"""create sentry initial tables

Revision ID: 202607220001
Revises: None
Create Date: 2026-07-22 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "202607220001"
down_revision = None
branch_labels = None
depends_on = None

decision_enum = postgresql.ENUM("ALLOW", "BLOCK", "CONFIRM", name="sentry_decision", create_type=False)
policy_severity_enum = postgresql.ENUM(
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
    name="policy_severity",
    create_type=False,
)
approval_status_enum = postgresql.ENUM(
    "PENDING",
    "APPROVED",
    "REJECTED",
    name="approval_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    decision_enum.create(bind, checkfirst=True)
    policy_severity_enum.create(bind, checkfirst=True)
    approval_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "policy",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("policy_code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", policy_severity_enum, nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("policy_code"),
    )
    op.create_index(op.f("policy_severity_idx"), "policy", ["severity"], unique=False)
    op.create_index("policy_enabled_severity_idx", "policy", ["enabled", "severity"], unique=False)
    op.bulk_insert(
        sa.table(
            "policy",
            sa.column("id", sa.Uuid()),
            sa.column("policy_code", sa.String()),
            sa.column("name", sa.String()),
            sa.column("description", sa.Text()),
            sa.column("severity", policy_severity_enum),
            sa.column("enabled", sa.Boolean()),
        ),
        [
            {
                "id": "8d507479-b15f-4b73-9a8b-23ae32689dc0",
                "policy_code": "SCOPE_BOUNDARY",
                "name": "Scope Boundary",
                "description": "Prevents agents from executing actions outside their permitted scope.",
                "severity": "HIGH",
                "enabled": True,
            },
            {
                "id": "60d81201-2896-4cfc-81a9-8b3ed94a4e0c",
                "policy_code": "PARAMETER_SAFETY",
                "name": "Parameter Safety",
                "description": "Detects unsafe or sensitive-looking request parameters.",
                "severity": "MEDIUM",
                "enabled": True,
            },
            {
                "id": "4744475a-f276-40da-89e3-ef54a87bb956",
                "policy_code": "RATE_LIMIT",
                "name": "Rate Limit",
                "description": "Flags agents that exceed placeholder request volume thresholds.",
                "severity": "MEDIUM",
                "enabled": True,
            },
            {
                "id": "93127e93-b0af-4add-907e-238b4b3fed20",
                "policy_code": "COST_LIMIT",
                "name": "Cost Limit",
                "description": "Flags tool executions that exceed placeholder cost limits.",
                "severity": "HIGH",
                "enabled": True,
            },
            {
                "id": "d18024b4-03a8-447f-8be6-fc5b60ee66f0",
                "policy_code": "IRREVERSIBLE_ACTION",
                "name": "Irreversible Action",
                "description": "Requires confirmation for actions that may be difficult or impossible to undo.",
                "severity": "HIGH",
                "enabled": True,
            },
        ],
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("agent_name", sa.String(length=128), nullable=False),
        sa.Column("tool_name", sa.String(length=128), nullable=False),
        sa.Column("action", sa.String(length=256), nullable=False),
        sa.Column("decision", decision_enum, nullable=False),
        sa.Column("risk_score", sa.SmallInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("violated_policy", sa.String(length=64), nullable=True),
        sa.Column("suggested_fix", sa.Text(), nullable=True),
        sa.Column("execution_time_ms", sa.Integer(), nullable=True),
        sa.Column("request_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("response_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.CheckConstraint("execution_time_ms IS NULL OR execution_time_ms >= 0", name="execution_time_ms_non_negative"),
        sa.CheckConstraint("risk_score >= 0 AND risk_score <= 100", name="risk_score_range"),
        sa.ForeignKeyConstraint(["violated_policy"], ["policy.policy_code"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("audit_log_agent_name_idx"), "audit_log", ["agent_name"], unique=False)
    op.create_index(op.f("audit_log_decision_idx"), "audit_log", ["decision"], unique=False)
    op.create_index(op.f("audit_log_timestamp_idx"), "audit_log", ["timestamp"], unique=False)
    op.create_index(op.f("audit_log_tool_name_idx"), "audit_log", ["tool_name"], unique=False)
    op.create_index(op.f("audit_log_violated_policy_idx"), "audit_log", ["violated_policy"], unique=False)
    op.create_index("audit_log_agent_tool_timestamp_idx", "audit_log", ["agent_name", "tool_name", "timestamp"], unique=False)

    op.create_table(
        "approval_request",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("audit_log_id", sa.Uuid(), nullable=False),
        sa.Column("status", approval_status_enum, server_default=sa.text("'PENDING'"), nullable=False),
        sa.Column("approved_by", sa.String(length=128), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["audit_log_id"], ["audit_log.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("audit_log_id"),
    )
    op.create_index("approval_request_status_created_idx", "approval_request", ["status", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("approval_request_status_created_idx", table_name="approval_request")
    op.drop_table("approval_request")

    op.drop_index("audit_log_agent_tool_timestamp_idx", table_name="audit_log")
    op.drop_index(op.f("audit_log_violated_policy_idx"), table_name="audit_log")
    op.drop_index(op.f("audit_log_tool_name_idx"), table_name="audit_log")
    op.drop_index(op.f("audit_log_timestamp_idx"), table_name="audit_log")
    op.drop_index(op.f("audit_log_decision_idx"), table_name="audit_log")
    op.drop_index(op.f("audit_log_agent_name_idx"), table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_index("policy_enabled_severity_idx", table_name="policy")
    op.drop_index(op.f("policy_severity_idx"), table_name="policy")
    op.drop_table("policy")

    approval_status_enum.drop(op.get_bind(), checkfirst=True)
    policy_severity_enum.drop(op.get_bind(), checkfirst=True)
    decision_enum.drop(op.get_bind(), checkfirst=True)
