"""empty message

Revision ID: 9b71f2671668
Revises: d08c4af06555
Create Date: 2021-03-02 01:44:01.659529

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9b71f2671668'
down_revision = 'd08c4af06555'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('venue', sa.Column('genres', sa.ARRAY(sa.String()), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('venue', 'genres')
    # ### end Alembic commands ###
