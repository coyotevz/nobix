"""Add tax_code and product_type to articulo

Revision ID: 556ff4575155
Revises: 1841d29ae725
Create Date: 2014-11-09 02:08:53.573187

"""

# revision identifiers, used by Alembic.
revision = '556ff4575155'
down_revision = '1841d29ae725'

from alembic import op
import sqlalchemy as sa

# helper table
articulohelper = sa.Table(
    'articulos',
    sa.MetaData(),
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('tax_code', sa.Unicode(3)),
    sa.Column('product_type', sa.UnicodeText),
)

def upgrade():
    op.add_column('articulos',
        sa.Column('tax_code', sa.Unicode(length=3)))
    op.add_column('articulos',
        sa.Column('product_type', sa.UnicodeText))

    connection = op.get_bind()

    # populate with data
    connection.execute(
        articulohelper.update().values(
            tax_code=u'V21',
            product_type=u'TYPE_PERMANENT',
        )
    )

    # make columns NOT NULL
    op.alter_column('articulos', 'tax_code', nullable=False)
    op.alter_column('articulos', 'product_type', nullable=False)


def downgrade():
    op.drop_column('articulos', 'product_type')
    op.drop_column('articulos', 'tax_code')
