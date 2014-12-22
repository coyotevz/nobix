"""Add allow_frac to articulos table.

Revision ID: 39fbc55acf71
Revises: 289e42e64c5c
Create Date: 2014-12-22 01:12:28.958340

"""

# revision identifiers, used by Alembic.
revision = '39fbc55acf71'
down_revision = '289e42e64c5c'

from alembic import op
import sqlalchemy as sa


articulohelper = sa.Table(
    'articulos',
    sa.MetaData(),
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('allow_frac', sa.Boolean()),
)


def upgrade():
    op.add_column('articulos', sa.Column('allow_frac', sa.Boolean(), nullable=True))

    # migrate data
    op.execute(
        articulohelper.update().values(
            allow_frac=False
        )
    )

    op.alter_column('articulos', 'allow_frac', nullable=False)


def downgrade():
    op.drop_column('articulos', 'allow_frac')
