"""Rename customer table and fields

Revision ID: e7211c188fee
Revises: 4418465d2df7
Create Date: 2018-05-29 01:12:07.730238

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e7211c188fee'
down_revision = '4418465d2df7'
branch_labels = None
depends_on = None


def rename_column(batch_op, old_name, new_name):
    batch_op.alter_column(old_name, new_column_name=new_name)


def upgrade():
    op.rename_table('clientes', 'customer')

    with op.batch_alter_table('customer') as cli:
        rename_column(cli, 'domicilio', 'address')
        rename_column(cli, 'codigo', 'code')
        rename_column(cli, 'responsabilidad_iva', 'fiscal_type')
        rename_column(cli, 'nombre', 'name')
        rename_column(cli, 'relacion', 'role')
        rename_column(cli, 'localidad', 'city')
        rename_column(cli, 'codigo_postal', 'zip_code')

    op.execute('ALTER SEQUENCE clientes_id_seq RENAME TO customer_id_seq')
    op.execute('ALTER INDEX clientes_pkey RENAME TO customer_pkey')
    op.execute('ALTER TABLE customer RENAME CONSTRAINT clientes_codigo_key TO customer_code_key')

def downgrade():
    op.rename_table('customer', 'clientes')

    with op.batch_alter_table('clientes') as cli:
        rename_column(cli, 'address', 'domicilio')
        rename_column(cli, 'code', 'codigo')
        rename_column(cli, 'fiscal_type', 'responsabilidad_iva')
        rename_column(cli, 'name', 'nombre')
        rename_column(cli, 'role', 'relacion')
        rename_column(cli, 'city', 'localidad')
        rename_column(cli, 'zip_code', 'codigo_postal')

    op.execute('ALTER SEQUENCE customer_id_seq RENAME TO clientes_id_seq')
    op.execute('ALTER INDEX customer_pkey RENAME TO clientes_pkey')
    op.execute('ALTER TABLE clientes RENAME CONSTRAINT customer_code_key TO clientes_codigo_key')
