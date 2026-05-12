"""add username phone avatar to user

Revision ID: 002
Revises: 001
Create Date: 2026-05-12

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, Sequence[str], None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'user',
        sa.Column('username', sqlmodel.sql.sqltypes.AutoString(), nullable=True)
    )

    op.add_column(
        'user',
        sa.Column('phone', sqlmodel.sql.sqltypes.AutoString(), nullable=True)
    )

    op.add_column(
        'user',
        sa.Column('avatar_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True)
    )

    # Fill usernames for existing rows
    op.execute("""
        UPDATE user
        SET username = CONCAT('user_', id)
        WHERE username IS NULL
    """)

    op.create_index(
        op.f('ix_user_username'),
        'user',
        ['username'],
        unique=True
    )

    op.alter_column(
        'user',
        'username',
        existing_type=sqlmodel.sql.sqltypes.AutoString(),
        nullable=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_column('user', 'avatar_url')
    op.drop_column('user', 'phone')
    op.drop_column('user', 'username')