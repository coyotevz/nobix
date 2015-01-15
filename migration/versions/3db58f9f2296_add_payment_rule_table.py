"""Add payment rule table

Revision ID: 3db58f9f2296
Revises: 39fbc55acf71
Create Date: 2015-01-15 04:11:43.387240

"""

# revision identifiers, used by Alembic.
revision = '3db58f9f2296'
down_revision = '39fbc55acf71'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('payment_rule',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('method_id', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['method_id'], ['payment_method.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('payment_rule')
