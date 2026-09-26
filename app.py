import io
import random
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, send_file
)
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from config import Config
from models import db, Usuario, Factura, Gasto, generar_numero_factura

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)


# ---------------------------------------------------------------------------
# Decoradores de autenticación / autorización
# ---------------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Debes iniciar sesión para continuar.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def empresa_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Debes iniciar sesión para continuar.", "error")
            return redirect(url_for("login"))
        usuario = Usuario.query.get(session["usuario_id"])
        if not usuario or not usuario.es_empresa:
            flash("Esta acción solo está disponible para cuentas de tipo Empresa.", "error")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return wrapper


def usuario_actual():
    if "usuario_id" in session:
        return Usuario.query.get(session["usuario_id"])
    return None


@app.context_processor
def inject_usuario():
    return {"usuario_actual": usuario_actual()}


# ---------------------------------------------------------------------------
# Páginas públicas
# ---------------------------------------------------------------------------
@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        tipo_cuenta = request.form.get("tipo_cuenta", "")
        nit = request.form.get("nit", "").strip()
        numero_identificacion = request.form.get("numero_identificacion", "").strip()

        if not nombre or not email or not password or tipo_cuenta not in ("cliente", "empresa"):
            flash("Por favor completa todos los campos obligatorios.", "error")
            return redirect(url_for("registro"))

        if Usuario.query.filter_by(email=email).first():
            flash("Ya existe una cuenta registrada con ese correo.", "error")
            return redirect(url_for("registro"))

        if tipo_cuenta == "empresa" and not nit:
            flash("El NIT de la empresa es obligatorio para cuentas de tipo Empresa.", "error")
            return redirect(url_for("registro"))

        if tipo_cuenta == "cliente" and not numero_identificacion:
            flash("El número de identificación es obligatorio para cuentas de tipo Cliente.", "error")
            return redirect(url_for("registro"))

        usuario = Usuario(
            nombre=nombre,
            email=email,
            tipo_cuenta=tipo_cuenta,
            nit=nit if tipo_cuenta == "empresa" else None,
            numero_identificacion=numero_identificacion if tipo_cuenta == "cliente" else None,
        )
        usuario.set_password(password)
        db.session.add(usuario)
        db.session.commit()

        flash("Cuenta creada exitosamente. Ya puedes iniciar sesión.", "success")
        return redirect(url_for("login"))

    return render_template("registro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and usuario.check_password(password):
            session["usuario_id"] = usuario.id
            flash(f"¡Bienvenido de nuevo, {usuario.nombre}!", "success")
            return redirect(url_for("dashboard"))

        flash("Correo o contraseña incorrectos.", "error")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for("landing"))


# ---------------------------------------------------------------------------
# Recuperación de cuenta (flujo de dos pasos)
# ---------------------------------------------------------------------------
@app.route("/recuperar-cuenta", methods=["GET", "POST"])
def recuperar_cuenta():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        usuario = Usuario.query.filter_by(email=email).first()

        if not usuario:
            flash("No existe ninguna cuenta con ese correo.", "error")
            return redirect(url_for("recuperar_cuenta"))

        codigo = f"{random.randint(0, 999999):06d}"
        usuario.codigo_recuperacion = codigo
        usuario.codigo_expira = datetime.utcnow() + timedelta(minutes=15)
        db.session.commit()

        session["recuperacion_email"] = email

        # NOTA: aquí normalmente se enviaría el código por correo (Flask-Mail).
        # Por ahora se muestra en pantalla para poder probar el flujo completo.
        flash(f"Tu código de recuperación es: {codigo} (válido 15 minutos).", "success")
        return redirect(url_for("recuperar_cuenta_codigo"))

    return render_template("recuperar_paso1.html")


@app.route("/recuperar-cuenta/codigo", methods=["GET", "POST"])
def recuperar_cuenta_codigo():
    email = session.get("recuperacion_email")
    if not email:
        flash("Primero solicita un código de recuperación.", "error")
        return redirect(url_for("recuperar_cuenta"))

    if request.method == "POST":
        codigo = request.form.get("codigo", "").strip()
        nueva_password = request.form.get("nueva_password", "")
        repetir_password = request.form.get("repetir_password", "")

        usuario = Usuario.query.filter_by(email=email).first()

        if not usuario or usuario.codigo_recuperacion != codigo:
            flash("El código ingresado no es correcto.", "error")
            return redirect(url_for("recuperar_cuenta_codigo"))

        if usuario.codigo_expira and usuario.codigo_expira < datetime.utcnow():
            flash("El código ha expirado. Solicita uno nuevo.", "error")
            return redirect(url_for("recuperar_cuenta"))

        if not nueva_password or nueva_password != repetir_password:
            flash("Las contraseñas no coinciden.", "error")
            return redirect(url_for("recuperar_cuenta_codigo"))

        usuario.set_password(nueva_password)
        usuario.codigo_recuperacion = None
        usuario.codigo_expira = None
        db.session.commit()
        session.pop("recuperacion_email", None)

        flash("Contraseña actualizada correctamente. Ya puedes iniciar sesión.", "success")
        return redirect(url_for("login"))

    return render_template("recuperar_paso2.html")


# ---------------------------------------------------------------------------
# Panel principal
# ---------------------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    usuario = usuario_actual()
    facturas = (
        Factura.query.filter_by(usuario_id=usuario.id)
        .order_by(Factura.id.desc())
        .limit(5)
        .all()
    )
    total_facturado = sum(f.total for f in Factura.query.filter_by(usuario_id=usuario.id).all())
    return render_template("dashboard.html", facturas=facturas, total_facturado=total_facturado)


# ---------------------------------------------------------------------------
# Facturas
# ---------------------------------------------------------------------------
@app.route("/facturas")
@login_required
def facturas_historial():
    usuario = usuario_actual()
    facturas = (
        Factura.query.filter_by(usuario_id=usuario.id)
        .order_by(Factura.id.desc())
        .all()
    )
    return render_template("facturas_historial.html", facturas=facturas)


@app.route("/facturas/nueva", methods=["GET", "POST"])
@empresa_required
def factura_nueva():
    if request.method == "POST":
        usuario = usuario_actual()
        nombre_cliente = request.form.get("nombre_cliente", "").strip()
        cedula_cliente = request.form.get("cedula_cliente", "").strip()
        empresa = request.form.get("empresa", "").strip()
        productos = request.form.get("productos", "").strip()
        total_raw = request.form.get("total", "0").replace(",", "").strip()

        try:
            total = float(total_raw)
        except ValueError:
            total = 0

        if not nombre_cliente or not cedula_cliente or not productos:
            flash("Completa todos los campos obligatorios de la factura.", "error")
            return redirect(url_for("factura_nueva"))

        factura = Factura(
            usuario_id=usuario.id,
            numero_factura=generar_numero_factura(usuario.id),
            nombre_cliente=nombre_cliente,
            cedula_cliente=cedula_cliente,
            empresa=empresa or usuario.nombre,
            productos=productos,
            total=total,
        )
        # flush() antes de commit(): garantiza que la factura tenga un ID
        # asignado (y quede visible dentro de la misma transacción) antes
        # de confirmar definitivamente los cambios en la base de datos.
        db.session.add(factura)
        db.session.flush()
        db.session.commit()

        flash(f"Factura {factura.numero_factura} creada exitosamente.", "success")
        return redirect(url_for("factura_detalle", factura_id=factura.id))

    return render_template("factura_nueva.html")


@app.route("/facturas/<int:factura_id>")
@login_required
def factura_detalle(factura_id):
    usuario = usuario_actual()
    factura = Factura.query.filter_by(id=factura_id, usuario_id=usuario.id).first_or_404()
    return render_template("factura_detalle.html", factura=factura)


@app.route("/facturas/<int:factura_id>/eliminar", methods=["POST"])
@login_required
def factura_eliminar(factura_id):
    usuario = usuario_actual()
    factura = Factura.query.filter_by(id=factura_id, usuario_id=usuario.id).first_or_404()
    db.session.delete(factura)
    db.session.commit()
    flash("Factura eliminada correctamente.", "success")
    return redirect(url_for("facturas_historial"))


@app.route("/facturas/<int:factura_id>/pdf")
@login_required
def factura_pdf(factura_id):
    usuario = usuario_actual()
    factura = Factura.query.filter_by(id=factura_id, usuario_id=usuario.id).first_or_404()

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    y = height - 60
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, y, "Factu Fact - Factura Electrónica")
    y -= 30
    c.setFont("Helvetica", 12)

    campos = [
        ("Número de factura", factura.numero_factura),
        ("Fecha", str(factura.fecha)),
        ("Hora", str(factura.hora)),
        ("Empresa", factura.empresa or "-"),
        ("Cliente", factura.nombre_cliente),
        ("Cédula", factura.cedula_cliente),
        ("Productos", factura.productos),
        ("Total", factura.total_formateado),
    ]
    for etiqueta, valor in campos:
        c.drawString(50, y, f"{etiqueta}: {valor}")
        y -= 22

    c.showPage()
    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{factura.numero_factura}.pdf",
    )


# ---------------------------------------------------------------------------
# Gastos
# ---------------------------------------------------------------------------
@app.route("/gastos")
@login_required
def gastos_historial():
    usuario = usuario_actual()
    gastos = Gasto.query.filter_by(usuario_id=usuario.id).order_by(Gasto.id.desc()).all()
    total_gastos = sum(g.monto for g in gastos)
    return render_template("gastos_historial.html", gastos=gastos, total_gastos=total_gastos)


@app.route("/gastos/nuevo", methods=["GET", "POST"])
@login_required
def gasto_nuevo():
    if request.method == "POST":
        usuario = usuario_actual()
        descripcion = request.form.get("descripcion", "").strip()
        monto_raw = request.form.get("monto", "0").replace(",", "").strip()

        try:
            monto = float(monto_raw)
        except ValueError:
            monto = 0

        if not descripcion:
            flash("Escribe una descripción para el gasto.", "error")
            return redirect(url_for("gasto_nuevo"))

        gasto = Gasto(usuario_id=usuario.id, descripcion=descripcion, monto=monto)
        db.session.add(gasto)
        db.session.commit()

        flash("Gasto registrado exitosamente.", "success")
        return redirect(url_for("gastos_historial"))

    return render_template("gasto_nuevo.html")


@app.route("/gastos/<int:gasto_id>/eliminar", methods=["POST"])
@login_required
def gasto_eliminar(gasto_id):
    usuario = usuario_actual()
    gasto = Gasto.query.filter_by(id=gasto_id, usuario_id=usuario.id).first_or_404()
    db.session.delete(gasto)
    db.session.commit()
    flash("Gasto eliminado correctamente.", "success")
    return redirect(url_for("gastos_historial"))


# ---------------------------------------------------------------------------
# Arranque
# ---------------------------------------------------------------------------
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
