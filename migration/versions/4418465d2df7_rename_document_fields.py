"""Rename document fields

Revision ID: 4418465d2df7
Revises: 0bf5e14685c3
Create Date: 2018-05-27 13:23:48.864445

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4418465d2df7'
down_revision = '0bf5e14685c3'
branch_labels = None
depends_on = None

def rename_column(batch_op, old_name, new_name):
    batch_op.alter_column(old_name, new_column_name=new_name)


def upgrade():
    with op.batch_alter_table('documentos') as doc:
        rename_column(doc, 'cliente_direccion', 'customer_address')
        rename_column(doc, 'cliente_cuit', 'customer_cuit')
        rename_column(doc, 'cliente_id', 'customer_id')
        rename_column(doc, 'cliente_nombre', 'customer_name')
        rename_column(doc, 'descuento', 'discount')
        rename_column(doc, 'tipo', 'doc_type')
        rename_column(doc, 'periodo_iva', 'fiscal_period')
        rename_column(doc, 'fecha', 'issue_date')
        rename_column(doc, 'hora', 'issue_time')
        rename_column(doc, 'neto', 'net')
        rename_column(doc, 'numero', 'number')
        rename_column(doc, 'vendedor', 'salesman')

        doc.create_index(op.f('ix_documentos_customer_id'), ['customer_id'])
        doc.drop_index('ix_documentos_cliente_id')

        doc.create_unique_constraint('documentos_type_key',
                                     ['doc_type', 'issue_date', 'number'])
        doc.drop_constraint('documentos_tipo_key', type_='unique')

        doc.drop_constraint('documentos_cliente_id_fkey', type_='foreignkey')
        doc.create_foreign_key('documentos_customer_id_fkey', 'clientes',
                               ['customer_id'], ['id'])


def downgrade():

    with op.batch_alter_table('documentos') as doc:
        rename_column(doc, 'customer_address', 'cliente_direccion')
        rename_column(doc, 'customer_cuit', 'cliente_cuit')
        rename_column(doc, 'customer_id', 'cliente_id')
        rename_column(doc, 'customer_name', 'cliente_nombre')
        rename_column(doc, 'discount', 'descuento')
        rename_column(doc, 'doc_type', 'tipo')
        rename_column(doc, 'fiscal_period', 'periodo_iva')
        rename_column(doc, 'issue_date', 'fecha')
        rename_column(doc, 'issue_time', 'hora')
        rename_column(doc, 'net', 'neto')
        rename_column(doc, 'number', 'numero')
        rename_column(doc, 'salesman', 'vendedor')

        doc.drop_constraint('documentos_customer_id_fkey', type_='foreignkey')
        doc.create_foreign_key('documentos_cliente_id_fkey', 'clientes',
                               ['cliente_id'], ['id'])

        doc.create_index('ix_documentos_cliente_id', ['cliente_id'],
                         unique=False)
        doc.drop_index(op.f('ix_documentos_customer_id'))

        doc.drop_constraint('documentos_type_key',
                            type_='unique')
        doc.create_unique_constraint('documentos_tipo_key',
                                     ['tipo', 'fecha', 'numero'])
