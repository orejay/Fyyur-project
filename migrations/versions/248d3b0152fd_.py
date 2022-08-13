"""empty message

Revision ID: 248d3b0152fd
Revises: 39e1979921aa
Create Date: 2022-08-13 05:50:54.200404

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '248d3b0152fd'
down_revision = '39e1979921aa'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('venue', sa.Column('genres', sa.String(length=120), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('venue', 'genres')
    # ### end Alembic commands ###