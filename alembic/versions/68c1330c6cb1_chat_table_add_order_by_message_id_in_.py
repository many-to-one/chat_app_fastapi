"""Chat table: add order_by Message.id in messages relationship

Revision ID: 68c1330c6cb1
Revises: 25aa78ada681
Create Date: 2024-12-22 17:01:57.026095

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '68c1330c6cb1'
down_revision: Union[str, None] = '25aa78ada681'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
