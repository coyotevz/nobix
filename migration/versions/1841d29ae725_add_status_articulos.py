"""Add status column to articulos table.

Revision ID: 1841d29ae725
Revises: 37d96c94cf03
Create Date: 2014-11-07 13:26:58.646345

"""

# revision identifiers, used by Alembic.
revision = '1841d29ae725'
down_revision = '37d96c94cf03'

from alembic import op
import sqlalchemy as sa


# helper table
articulohelper = sa.Table(
    'articulos',
    sa.MetaData(),
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('status', sa.UnicodeText),
    sa.Column('es_activo', sa.Boolean),
)

T_statuses = [u'STATUS_AVAILABLE']
F_statuses = [u'STATUS_CLOSED', u'STATUS_SUSPENDED']

def upgrade():
    # add new columns
    op.add_column('articulos',
        sa.Column('status', sa.UnicodeText))

    connection = op.get_bind()

    # migrate data
    connection.execute(
        articulohelper.update().where(
            articulohelper.c.es_activo==True
        ).values(
            status=u'STATUS_AVAILABLE',
        )
    )

    connection.execute(
        articulohelper.update().where(
            articulohelper.c.es_activo==False
        ).values(
            status=u'STATUS_CLOSED',
        )
    )

    # make columns NOT NULL
    op.alter_column('articulos', 'status', nullable=False)
    op.drop_column('articulos', 'es_activo')


def downgrade():
    op.add_column('articulos',
        sa.Column('es_activo', sa.Boolean, default=True))

    connection = op.get_bind()

    # migrate data
    connection.execute(
        articulohelper.update().where(
            articulohelper.c.status.in_(T_statuses)
        ).values(
            es_activo=True
        )
    )

    connection.execute(
        articulohelper.update().where(
            articulohelper.c.status.in_(F_statuses)
        ).values(
            es_activo=False
        )
    )

    op.drop_column('articulos', 'status')
