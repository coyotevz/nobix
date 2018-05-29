"""Rename customer table fields

Revision ID: e7211c188fee
Revises: d0f2d7126340
Create Date: 2018-05-29 01:12:07.730238

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e7211c188fee'
down_revision = 'd0f2d7126340'
branch_labels = None
depends_on = None


def rename_column(batch_op, old_name, new_name):
    batch_op.alter_column(old_name, new_column_name=new_name)


def upgrade():
    with op.batch_alter_table('clientes') as cli:
        rename_column(cli, 'domicilio', 'address')
        rename_column(cli, 'codigo', 'code')
        rename_column(cli, 'responsabilidad_iva', 'fiscal_type')
        rename_column(cli, 'nombre', 'name')
        rename_column(cli, 'relacion', 'relation')
        rename_column(cli, 'localidad', 'state')
        rename_column(cli, 'codigo_postal', 'zip_code')

    op.execute('''
        ALTER TABLE clientes RENAME CONSTRAINT 
            clientes_codigo_key TO customer_code_key
    ''')

def downgrade():
    with op.batch_alter_table('clientes') as cli:
        rename_column(cli, 'address', 'domicilio')
        rename_column(cli, 'code', 'codigo')
        rename_column(cli, 'fiscal_type', 'responsabilidad_iva')
        rename_column(cli, 'name', 'nombre')
        rename_column(cli, 'relation', 'relacion')
        rename_column(cli, 'state', 'localidad')
        rename_column(cli, 'zip_code', 'codigo_postal')

    op.execute('''
        ALTER TABLE clientes RENAME CONSTRAINT
            customer_code_key TO clientes_codigo_key
    ''')
