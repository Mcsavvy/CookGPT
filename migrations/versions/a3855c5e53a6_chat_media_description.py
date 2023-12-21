"""hatmedia description

Revision ID: a3855c5e53a6
Revises: 3fea1acabb3a
Create Date: 2023-12-22 13:38:09.458137

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3855c5e53a6'
down_revision = '3fea1acabb3a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('chat_media', schema=None) as batch_op:
        batch_op.add_column(sa.Column('description', sa.Text(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('chat_media', schema=None) as batch_op:
        batch_op.drop_column('description')

    # ### end Alembic commands ###
