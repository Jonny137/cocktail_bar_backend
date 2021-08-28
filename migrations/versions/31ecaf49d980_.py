"""empty message

Revision ID: 31ecaf49d980
Revises: b18ef9b9b92b
Create Date: 2021-08-20 22:20:51.324112

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '31ecaf49d980'
down_revision = 'b18ef9b9b92b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=True)
    op.drop_index('ix_user_username_1', table_name='user')
    op.create_unique_constraint(None, 'user', ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'user', type_='unique')
    op.create_index('ix_user_username_1', 'user', ['username'], unique=True)
    op.drop_index(op.f('ix_user_username'), table_name='user')
    # ### end Alembic commands ###
