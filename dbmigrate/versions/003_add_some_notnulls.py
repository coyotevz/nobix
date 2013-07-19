from sqlalchemy import *
from sqlalchemy import sql
from migrate import *
from _utils import get_prev_meta

meta = get_prev_meta(__file__)

documentos = meta.tables['documentos']
tasas = meta.tables['tasas']

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind migrate_engine
    # to your metadata
    meta.bind = migrate_engine

    # Migrate data
    sql.update(documentos, documentos.c.cliente_id==None,
               values={'cliente_id': 1},
               bind=migrate_engine).execute()

    tasas.c.documento_id.alter(nullable=False)
    documentos.c.cliente_id.alter(nullable=False)

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine

    tasas.c.documento_id.alter(nullable=True)
    documentos.c.cliente_id.alter(nullable=True)

