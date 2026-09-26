from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    tipo_cuenta = db.Column(db.String(20), nullable=False)  # 'cliente' o 'empresa'
    nit = db.Column(db.String(50))
    numero_identificacion = db.Column(db.String(50))

    # Campos para recuperación de cuenta (código temporal de 6 dígitos)
    codigo_recuperacion = db.Column(db.String(6))
    codigo_expira = db.Column(db.DateTime)

    facturas = db.relationship("Factura", backref="usuario", lazy=True, cascade="all, delete-orphan")
    gastos = db.relationship("Gasto", backref="usuario", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def es_empresa(self):
        return self.tipo_cuenta == "empresa"


class Factura(db.Model):
    __tablename__ = "facturas"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    numero_factura = db.Column(db.String(30), nullable=False)
    fecha = db.Column(db.Date, default=lambda: datetime.now().date())
    hora = db.Column(db.Time, default=lambda: datetime.now().time().replace(microsecond=0))
    nombre_cliente = db.Column(db.String(120), nullable=False)
    cedula_cliente = db.Column(db.String(30), nullable=False)
    empresa = db.Column(db.String(120))
    productos = db.Column(db.Text, nullable=False)  # descripción libre de productos/servicios
    total = db.Column(db.Float, nullable=False, default=0)

    @property
    def total_formateado(self):
        return f"${self.total:,.0f}"


class Gasto(db.Model):
    __tablename__ = "gastos"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    descripcion = db.Column(db.String(200), nullable=False)
    monto = db.Column(db.Float, nullable=False, default=0)
    fecha = db.Column(db.Date, default=lambda: datetime.now().date())

    @property
    def monto_formateado(self):
        return f"${self.monto:,.0f}"


def generar_numero_factura(usuario_id):
    """Genera un número de factura consecutivo simple por usuario, ej: FAC-000001."""
    ultimo = (
        Factura.query.filter_by(usuario_id=usuario_id)
        .order_by(Factura.id.desc())
        .first()
    )
    siguiente = (ultimo.id + 1) if ultimo else 1
    return f"FAC-{siguiente:06d}"
