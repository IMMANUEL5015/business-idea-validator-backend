"""baseline — initial schema managed by SQLAlchemy create_all

Revision ID: 93709219fd4d
Revises:
Create Date: 2026-04-03 22:10:24.281805

This is a baseline migration. All tables were created by SQLAlchemy's
create_all() during early development. Alembic takes over from here
for any future incremental schema changes.
"""
from typing import Sequence, Union

revision: str = '93709219fd4d'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass