"""Rename cache table fields

Revision ID: c71e7fd6a9b7
Revises: 7a699b427893
Create Date: 2018-05-31 02:39:45.793583

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c71e7fd6a9b7'
down_revision = '7a699b427893'
branch_labels = None
depends_on = None


def rename_column(batch_op, old_name, new_name):
    batch_op.alter_column(old_name, new_column_name=new_name)


def upgrade():

    with op.batch_alter_table('cache') as ca:
        rename_column(ca, 'vendedor', 'salesman')
        rename_column(ca, 'descuento', 'discount')
        rename_column(ca, 'cliente_id', 'customer_id')

    op.execute('ALTER INDEX cache_vendedor_key RENAME TO cache_salesman_key')
    op.execute('ALTER INDEX ix_cache_cliente_id RENAME TO ix_cache_customer_id')
    op.execute('ALTER TABLE cache RENAME CONSTRAINT cache_cliente_id_fkey TO cache_customer_id_fkey')


def downgrade():

    with op.batch_alter_table('cache') as ca:
        rename_column(ca, 'salesman', 'vendedor')
        rename_column(ca, 'discount', 'descuento')
        rename_column(ca, 'customer_id', 'cliente_id')

    op.execute('ALTER INDEX cache_salesman_key RENAME TO cache_vendedor_key')
    op.execute('ALTER INDEX ix_cache_customer_id RENAME TO ix_cache_cliente_id')
    op.execute('ALTER TABLE cache RENAME CONSTRAINT cache_customer_id_fkey TO cache_cliente_id_fkey')
