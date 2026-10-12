"""change review id to uuid

Revision ID: ca8ebc28730f
Revises: 8b63052585b1
Create Date: 2026-10-12 07:30:46.689682

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'ca8ebc28730f'
down_revision: Union[str, Sequence[str], None] = '8b63052585b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("pull_request_reviews")

    op.create_table(
        "pull_request_reviews",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("github_owner", sa.String(length=100), nullable=False),
        sa.Column("repository_name", sa.String(length=100), nullable=False),
        sa.Column("pull_request_number", sa.Integer(), nullable=False),
        sa.Column("pull_request_title", sa.String(length=500), nullable=True),
        sa.Column(
            "status",
            sa.String(length=30),
            server_default="pending",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("pull_request_reviews")

    op.create_table(
        "pull_request_reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("github_owner", sa.String(length=100), nullable=False),
        sa.Column("repository_name", sa.String(length=100), nullable=False),
        sa.Column("pull_request_number", sa.Integer(), nullable=False),
        sa.Column("pull_request_title", sa.String(length=500), nullable=True),
        sa.Column(
            "status",
            sa.String(length=30),
            server_default="pending",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###
