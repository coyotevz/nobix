"""Add new columns to articulos table.

Revision ID: 1841d29ae725
Revises: 37d96c94cf03
Create Date: 2014-11-07 13:26:58.646345

"""

# revision identifiers, used by Alembic.
revision = '1841d29ae725'
down_revision = '37d96c94cf03'

from alembic import op
import sqlalchemy as sa


# we build a quick link for the current connection of alembic
connection = op.get_bind()

# helper table
articulohelper = sa.Table(
    'articulos',
    sa.MetaData(),
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('tax_code', sa.Unicode(length=3)),
    sa.Column('status', sa.UnicodeText),
    sa.Column('product_type', sa.UnicodeText),
    sa.Column('es_activo', sa.Boolean),
)

statuses = {
    True: u'STATUS_AVAILABLE',
    False: u'STATUS_CLOSED'
}

def upgrade():
    # add new columns
    op.add_column('articulos',
        sa.Column('tax_code', sa.Unicode(length=3)))
    op.add_column('articulos',
        sa.Column('status', sa.UnicodeText))
    op.add_column('articulos',
        sa.Column('product_type', sa.UnicodeText))

    # migrate data
    for articulo in connection.execute(articulohelper.select()):
        active = articulo.es_activo
        connection.execute(
            articulohelper.update().where(
                articulohelper.c.id==articulo.id
            ).values(
                tax_code=u'V21',
                status=statuses[active],
                product_type=u'TYPE_PERMANENT',
            )
        )

    # make columns NOT NULL
    op.alter_column('articulos', 'tax_code', nullable=False)
    op.alter_column('articulos', 'status', nullable=False)
    op.alter_column('articulos', 'product_type', nullable=False)


def downgrade():
    op.drop_column('articulos', 'product_type')
    op.drop_column('articulos', 'status')
    op.drop_column('articulos', 'tax_code')
