"""Rename product table

Revision ID: 87b01a87c6da
Revises: b271077dc0a3
Create Date: 2018-05-30 02:23:39.699664

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '87b01a87c6da'
down_revision = 'b271077dc0a3'
branch_labels = None
depends_on = None


def rename_column(batch_op, old_name, new_name):
    batch_op.alter_column(old_name, new_column_name=new_name)


def upgrade():
    op.rename_table('articulos', 'product')

    with op.batch_alter_table('product') as p:
        rename_column(p, 'codigo', 'sku')
        rename_column(p, 'descripcion', 'description')
        rename_column(p, 'proveedor', 'supplier')
        rename_column(p, 'agrupacion', 'group')
        rename_column(p, 'vigencia', 'validity')
        rename_column(p, 'precio', 'price')
        rename_column(p, 'existencia', 'stock')
        rename_column(p, 'es_activo', 'is_active')

    op.execute('ALTER SEQUENCE articulos_id_seq RENAME TO product_id_seq')
    op.execute('ALTER INDEX articulos_pkey RENAME TO product_pkey')
    op.execute('ALTER TABLE product RENAME CONSTRAINT articulos_codigo_key TO product_sku_key')


def downgrade():
    op.rename_table('product', 'articulos')

    with op.batch_alter_table('articulos') as p:
        rename_column(p, 'sku', 'codigo')
        rename_column(p, 'description', 'descripcion')
        rename_column(p, 'supplier', 'proveedor')
        rename_column(p, 'group', 'agrupacion')
        rename_column(p, 'validity', 'vigencia')
        rename_column(p, 'price', 'precio')
        rename_column(p, 'stock', 'existencia')
        rename_column(p, 'is_active', 'es_activo')

    op.execute('ALTER SEQUENCE product_id_seq RENAME TO articulos_id_seq')
    op.execute('ALTER INDEX product_pkey RENAME TO articulos_pkey')
    op.execute('ALTER TABLE articulos RENAME CONSTRAINT product_sku_key TO articulos_codigo_key')
