from sqlalchemy import *
from migrate import *
from _utils import get_prev_meta

meta = get_prev_meta(__file__)
documentos = meta.tables['documentos']
items_documento = meta.tables['items_documento']
tasas = meta.tables['tasas']
cache = meta.tables['cache']

icach = Index('ix_cache_cliente_id', cache.c.cliente_id)
idoc = Index('ix_documentos_cliente_id', documentos.c.cliente_id)
iidoc_art = Index('ix_items_documento_articulo_id', items_documento.c.articulo_id)
iidoc_doc = Index('ix_items_documento_documento_id', items_documento.c.documento_id)
itas = Index('ix_tasas_documento_id', tasas.c.documento_id)

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind migrate_engine
    # to your metadata
    meta.bind = migrate_engine

    icach.create()
    idoc.create()
    iidoc_art.create()
    iidoc_doc.create()
    itas.create()

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine

    icach.drop()
    idoc.drop()
    iidoc_art.drop()
    iidoc_doc.drop()
    itas.drop()
