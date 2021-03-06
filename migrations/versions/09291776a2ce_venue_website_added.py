"""venue website added

Revision ID: 09291776a2ce
Revises: c7cfd3ea4e33
Create Date: 2020-08-22 20:34:22.647886

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '09291776a2ce'
down_revision = 'c7cfd3ea4e33'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('venue', sa.Column('website', sa.String(length=120), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('venue', 'website')
    # ### end Alembic commands ###
