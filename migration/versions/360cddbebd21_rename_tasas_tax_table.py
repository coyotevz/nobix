"""Rename tasas->tax table

Revision ID: 360cddbebd21
Revises: 1eab6f4b7663
Create Date: 2014-11-17 13:16:52.184512

"""

from decimal import Decimal

# revision identifiers, used by Alembic.
revision = '360cddbebd21'
down_revision = '1eab6f4b7663'

from alembic import op
import sqlalchemy as sa

# helper table
taxhelper = sa.Table(
    'tax',
    sa.MetaData(),
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('taxable', sa.Numeric(10, 2)),
)

def upgrade():
    op.rename_table('tasas', 'tax')
    op.alter_column('tax', 'nombre',
                    new_column_name='tax_code', type_=sa.Unicode(3))
    op.alter_column('tax', 'monto', new_column_name='amount')
    op.alter_column('tax', 'documento_id', new_column_name='document_id')
    op.add_column('tax', sa.Column('taxable', sa.Numeric(10, 2)))
    op.drop_constraint('tasas_pkey', 'tax')
    op.create_primary_key('tax_pkey', 'tax', ['id'])
    op.drop_constraint('tasas_documento_id_fkey', 'tax')
    op.create_foreign_key('tax_documento_id_fkey', 'tax', 'documentos',
                          ['document_id'], ['id'])

    op.execute(
        taxhelper.update().\
            values({'taxable': Decimal(0)})
        )

    op.alter_column('tax', 'taxable', nullable=False)
    op.create_index(op.f('ix_tax_document_id'), 'tax', ['document_id'],
                    unique=False)
    op.drop_index('ix_tasas_documento_id', table_name='tax')


def downgrade():
    op.create_index('ix_tasas_documento_id', 'tax', ['document_id'],
                    unique=False)
    op.drop_index(op.f('ix_tax_document_id'), table_name='tax')
    op.drop_constraint('tax_pkey', 'tax')
    op.create_primary_key('tasas_pkey', 'tax', ['id'])
    op.drop_constraint('tax_documento_id_fkey', 'tax')
    op.create_foreign_key('tasas_documento_id_fkey', 'tax', 'documentos',
                          ['document_id'], ['id'])

    op.drop_column('tax', 'taxable')
    op.alter_column('tax', 'document_id', new_column_name='documento_id')
    op.alter_column('tax', 'amount', new_column_name='monto')
    op.alter_column('tax', 'tax_code', new_column_name='nombre',
                    type_=sa.UnicodeText)
    op.rename_table('tax', 'tasas')
