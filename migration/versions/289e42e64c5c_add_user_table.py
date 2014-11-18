"""Add user table

Revision ID: 289e42e64c5c
Revises: 360cddbebd21
Create Date: 2014-11-17 20:54:05.690739

"""

# revision identifiers, used by Alembic.
revision = '289e42e64c5c'
down_revision = '360cddbebd21'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('user',
        sa.Column('created', sa.DateTime, nullable=True),
        sa.Column('modified', sa.DateTime, nullable=True),
        sa.Column('id', sa.Integer, nullable=False),
        sa.Column('first_name', sa.UnicodeText, nullable=False),
        sa.Column('last_name', sa.UnicodeText, nullable=True),
        sa.Column('username', sa.Unicode(60), nullable=False),
        sa.Column('pw_hash', sa.Unicode(80), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
    )


def downgrade():
    op.drop_table('user')
