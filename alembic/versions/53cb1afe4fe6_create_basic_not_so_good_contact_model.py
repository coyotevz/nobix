"""Create basic (not so good) contact model.

Revision ID: 53cb1afe4fe6
Revises: None
Create Date: 2014-11-06 02:44:05.923943

"""

# revision identifiers, used by Alembic.
revision = '53cb1afe4fe6'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'contacts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('contacts')
