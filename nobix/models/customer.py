# -*- coding: utf-8 -*-

from . import db


class Cliente(db.Model):
    __tablename__ = 'clientes'
    __table_args__ = (db.UniqueConstraint('code', 'relation'),)

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column('code', db.Integer)
    nombre = db.Column('name', db.UnicodeText(35), nullable=False)
    domicilio = db.Column('address', db.UnicodeText(35))
    localidad = db.Column('state', db.UnicodeText(20))
    codigo_postal = db.Column('zip_code', db.UnicodeText(8))
    responsabilidad_iva = db.Column('fiscal_type',
                                    db.Enum('C', 'I', 'R', 'M', 'E',
                                            name="fiscal_type_enum"),
                                    default="C")
    cuit = db.Column(db.UnicodeText(13))
    relacion = db.Column('relation', db.Enum('C', 'P', name="rel_enum"),
                         default="C")

    #: 'documentos' field added by Documento model

    @property
    def direccion(self):
        dir_data = self.domicilio, self.localidad
        if all(dir_data):
            d = " - ".join(dir_data)
        else:
            d = "".join(dir_data)
        if self.codigo_postal:
            d += " (%s)" % self.codigo_postal
        return d
