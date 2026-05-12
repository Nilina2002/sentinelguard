"""add username phone avatar to user

Revision ID: 002
Revises: 001
Create Date: 2026-05-12

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, Sequence[str], None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]
    return index_name in indexes


def table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if table_exists('user'):
        if not column_exists('user', 'username'):
            op.add_column(
                'user',
                sa.Column('username', sqlmodel.sql.sqltypes.AutoString(), nullable=True)
            )
        if not column_exists('user', 'phone'):
            op.add_column(
                'user',
                sa.Column('phone', sqlmodel.sql.sqltypes.AutoString(), nullable=True)
            )
        if not column_exists('user', 'avatar_url'):
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

        if not index_exists('user', 'ix_user_username'):
            op.create_index(
                op.f('ix_user_username'),
                'user',
                ['username'],
                unique=True
            )
        if column_exists('user', 'username'):
            op.alter_column(
                'user',
                'username',
                existing_type=sqlmodel.sql.sqltypes.AutoString(),
                nullable=False
            )

    if not table_exists('image_like'):
        op.create_table(
            'image_like',
            sa.Column(
                'id',
                sa.Integer(),
                nullable=False
            ),
            sa.Column(
                'image_id',
                sa.Integer(),
                nullable=False
            ),
            sa.Column(
                'user_id',
                sa.Integer(),
                nullable=False
            ),
            sa.Column(
                'created_at',
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now()
            ),
            sa.ForeignKeyConstraint(
                ['image_id'],
                ['image.id'],
                ondelete='CASCADE'
            ),
            sa.ForeignKeyConstraint(
                ['user_id'],
                ['user.id'],
                ondelete='CASCADE'
            ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint(
                'image_id',
                'user_id',
                name='uq_image_like'
            )
        )

        op.create_index(
            'ix_image_like_image_id',
            'image_like',
            ['image_id']
        )

        op.create_index(
            'ix_image_like_user_id',
            'image_like',
            ['user_id']
        )

    if not table_exists('image_comment'):
        op.create_table(
            'image_comment',
            sa.Column(
                'id',
                sa.Integer(),
                nullable=False
            ),
            sa.Column(
                'image_id',
                sa.Integer(),
                nullable=False
            ),
            sa.Column(
                'user_id',
                sa.Integer(),
                nullable=False
            ),
            sa.Column(
                'content',
                sa.Text(),
                nullable=False
            ),
            sa.Column(
                'created_at',
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now()
            ),
            sa.ForeignKeyConstraint(
                ['image_id'],
                ['image.id'],
                ondelete='CASCADE'
            ),
            sa.ForeignKeyConstraint(
                ['user_id'],
                ['user.id'],
                ondelete='CASCADE'
            ),
            sa.PrimaryKeyConstraint('id')
        )

        op.create_index(
            'ix_image_comment_image_id',
            'image_comment',
            ['image_id']
        )

        op.create_index(
            'ix_image_comment_user_id',
            'image_comment',
            ['user_id']
        )

def downgrade() -> None:
    if table_exists('image_comment'):
        op.drop_index('ix_image_comment_user_id', table_name='image_comment')
        op.drop_index('ix_image_comment_image_id', table_name='image_comment')
        op.drop_table('image_comment')
    
    if table_exists('image_like'):
        op.drop_index('ix_image_like_user_id', table_name='image_like')
        op.drop_index('ix_image_like_image_id', table_name='image_like')
        op.drop_table('image_like')
    
    if table_exists('user'):
        if index_exists('user', 'ix_user_username'):
            op.drop_index(op.f('ix_user_username'), table_name='user')
        if column_exists('user', 'username'):
            op.drop_column('user', 'username')
        if column_exists('user', 'avatar_url'):
            op.drop_column('user', 'avatar_url')
        if column_exists('user', 'phone'):
            op.drop_column('user', 'phone')
    