"""Adjust uniqueness constraints for user.

Revision ID: ae4feefbe47f
Revises: c4f45ee0fea2
Create Date: 2024-07-06 05:59:51.725766

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ae4feefbe47f'
down_revision = 'c4f45ee0fea2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint('user_email_key', type_='unique')
        batch_op.drop_constraint('user_username_key', type_='unique')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.create_unique_constraint('user_username_key', ['username'])
        batch_op.create_unique_constraint('user_email_key', ['email'])

    # ### end Alembic commands ###
