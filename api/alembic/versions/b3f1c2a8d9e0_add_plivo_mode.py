"""add plivo mode

Revision ID: b3f1c2a8d9e0
Revises: e54ddb048535
Create Date: 2026-04-02 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b3f1c2a8d9e0"
down_revision: Union[str, None] = "e54ddb048535"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE workflow_run_mode ADD VALUE IF NOT EXISTS 'plivo'")


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed safely in-place.
    pass
