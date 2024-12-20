"""empty message

Revision ID: d157e7e0d512
Revises: fbff914b112f
Create Date: 2024-12-08 20:30:02.789548

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import func

# revision identifiers, used by Alembic.
revision: str = "d157e7e0d512"
down_revision: str | None = "fbff914b112f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "pr_requests",
        sa.Column("added", sa.DateTime(), nullable=False, server_default=func.now()),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("pr_requests", "added")
    # ### end Alembic commands ###
