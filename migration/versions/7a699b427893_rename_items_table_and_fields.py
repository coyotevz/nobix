"""Rename items table and fields

Revision ID: 7a699b427893
Revises: 87b01a87c6da
Create Date: 2018-05-31 02:17:31.492672

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a699b427893'
down_revision = '87b01a87c6da'
branch_labels = None
depends_on = None


def rename_column(batch_op, old_name, new_name):
    batch_op.alter_column(old_name, new_column_name=new_name)


def upgrade():
    op.rename_table('items_documento', 'item')

    with op.batch_alter_table('item') as it:
        rename_column(it, 'codigo', 'sku')
        rename_column(it, 'descripcion', 'description')
        rename_column(it, 'cantidad', 'quantity')
        rename_column(it, 'precio', 'unit_price')
        rename_column(it, 'articulo_id', 'product_id')
        rename_column(it, 'documento_id', 'document_id')

    op.execute('ALTER SEQUENCE items_documento_id_seq RENAME TO item_id_seq')
    op.execute('ALTER INDEX items_documento_pkey RENAME TO item_pkey')
    op.execute('ALTER INDEX ix_items_documento_articulo_id RENAME TO ix_item_product_id')
    op.execute('ALTER INDEX ix_items_documento_documento_id RENAME TO ix_item_document_id')
    op.execute('ALTER TABLE item RENAME CONSTRAINT items_documento_articulo_id_fkey TO item_product_id_fkey')
    op.execute('ALTER TABLE item RENAME CONSTRAINT items_documento_documento_id_fkey TO item_document_id_fkey')


def downgrade():
    op.rename_table('item', 'items_documento')

    with op.batch_alter_table('items_documento') as it:
        rename_column(it, 'sku', 'codigo')
        rename_column(it, 'description', 'descripcion')
        rename_column(it, 'quantity', 'cantidad')
        rename_column(it, 'unit_price', 'precio')
        rename_column(it, 'product_id', 'articulo_id')
        rename_column(it, 'document_id', 'documento_id')

    op.execute('ALTER SEQUENCE item_id_seq RENAME TO items_documento_id_seq')
    op.execute('ALTER INDEX item_pkey RENAME TO items_documento_pkey')
    op.execute('ALTER INDEX ix_item_product_id RENAME TO ix_items_documento_articulo_id')
    op.execute('ALTER INDEX ix_item_document_id RENAME TO ix_items_documento_documento_id')
    op.execute('ALTER TABLE items_documento RENAME CONSTRAINT item_product_id_fkey TO items_documento_articulo_id_fkey')
    op.execute('ALTER TABLE items_documento RENAME CONSTRAINT item_document_id_fkey TO items_documento_documento_id_fkey')
