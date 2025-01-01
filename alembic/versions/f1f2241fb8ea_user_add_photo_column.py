"""User: add photo column

Revision ID: f1f2241fb8ea
Revises: 68c1330c6cb1
Create Date: 2024-12-24 13:09:10.206893

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1f2241fb8ea'
down_revision: Union[str, None] = '68c1330c6cb1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('photo', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'photo')
    # ### end Alembic commands ###