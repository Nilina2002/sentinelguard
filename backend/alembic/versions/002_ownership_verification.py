"""ownership verification schema

Revision ID: 002
Revises: 001
Create Date: 2026-05-02 23:35:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, Sequence[str], None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("report", sa.Column("target_image_id", sa.Integer(), nullable=True))
    op.add_column("report", sa.Column("face_presence_passed", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("report", sa.Column("selfie_verified", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("report", sa.Column("supporting_verified", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("report", sa.Column("final_decision", sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column("report", sa.Column("selfie_similarity", sa.Float(), nullable=True))
    op.add_column("report", sa.Column("support_similarity", sa.Float(), nullable=True))
    op.add_column("report", sa.Column("db_consistency_score", sa.Float(), nullable=True))
    op.create_foreign_key("fk_report_target_image_id", "report", "image", ["target_image_id"], ["id"])

    op.create_table(
        "report_evidence",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("report_id", sa.Integer(), nullable=False),
        sa.Column("evidence_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("file_path", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("vector_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["report_id"], ["report.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "report_verification_attempt",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("report_id", sa.Integer(), nullable=False),
        sa.Column("step", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("reason_code", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("scores_json", sa.JSON(), nullable=True),
        sa.Column("ip_hash", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("user_agent", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["report_id"], ["report.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("report_verification_attempt")
    op.drop_table("report_evidence")
    op.drop_constraint("fk_report_target_image_id", "report", type_="foreignkey")
    op.drop_column("report", "db_consistency_score")
    op.drop_column("report", "support_similarity")
    op.drop_column("report", "selfie_similarity")
    op.drop_column("report", "final_decision")
    op.drop_column("report", "supporting_verified")
    op.drop_column("report", "selfie_verified")
    op.drop_column("report", "face_presence_passed")
    op.drop_column("report", "target_image_id")
