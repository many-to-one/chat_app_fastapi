"""Message and User: some table correction

Revision ID: 599c8467c870
Revises: ce3ff1a5d66d
Create Date: 2024-12-12 19:50:52.574643

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '599c8467c870'
down_revision: Union[str, None] = 'ce3ff1a5d66d'
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
