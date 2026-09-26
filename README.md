# Factu Fact

Aplicación web de facturación electrónica para Colombia (Flask + SQLAlchemy + Jinja2).

## Cómo ejecutarla

```bash
python -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Abre http://127.0.0.1:5000 en tu navegador. La base de datos SQLite se crea automáticamente
en `instance/factu_fact.db` la primera vez que ejecutas la app.

### Usar MySQL en vez de SQLite (opcional)

1. Ejecuta `factu_fact_db.sql` en tu servidor MySQL.
2. Define la variable de entorno antes de arrancar la app:
   ```bash
   export DATABASE_URL="mysql+pymysql://usuario:password@localhost/factu_fact_db"
   ```

### Reemplazar el logo

Se incluyó un logo temporal en `static/img/logo.svg`. Reemplázalo por tu `Logo.png` real
(o cambia la referencia en `templates/base.html`).

## Qué se corrigió/terminó respecto a los HTML originales

- Se convirtieron los 13 archivos HTML estáticos en plantillas Jinja2 dentro de `templates/`,
  conectadas a rutas reales de Flask (antes los `<form action="#">` no enviaban datos a ningún lado).
- Se eliminaron los espacios en nombres de archivo (causaban enlaces `href`/`action` rotos).
- Se consolidaron `Factura 1.html` a `Factura 5.html` en una sola plantilla dinámica
  (`factura_detalle.html`) que muestra cualquier factura según su ID.
- `Recuperacion_de_cuenta.html`: se corrigió el `<footer>` que estaba mal anidado dentro del
  `<form>` y el `</form>` duplicado al final del archivo.
- `Recuperacion_de_cuenta(ingresar_codigo).html`: los `<input>` tenían atributos inválidos con
  espacios (`new password="new password"`, etc.); se corrigieron a `name`/`id` válidos y ahora
  el formulario realmente valida el código y guarda la nueva contraseña.
- Se agregaron las funcionalidades que faltaban para que el flujo fuera completo:
  registro/login real con contraseñas cifradas (Werkzeug), creación y eliminación de facturas,
  generación de PDF (ReportLab, en memoria con `BytesIO`), registro y listado de gastos, y
  recuperación de cuenta de dos pasos con código temporal de 6 dígitos.
- Botones "Descargar Factura" y "Eliminar Factura" ahora funcionan (antes eran botones sin acción).
- Se agregó el decorador `empresa_required`: solo las cuentas tipo "Empresa" pueden crear facturas;
  las cuentas "Cliente" pueden registrar y ver gastos.
- Se usa `db.session.flush()` antes de `db.session.commit()` al crear una factura, para poder
  generar el número de factura (`FAC-000001`, etc.) usando el ID recién asignado.
- Se amplió `styles.css` con variables CSS, tarjetas, botones tipo "pill" y mensajes de error/éxito,
  manteniendo la paleta azul-blanco Material Design.

## Nota sobre el envío de correos

El envío real de correos para la recuperación de cuenta no está integrado (requeriría
Flask-Mail y credenciales SMTP). Por ahora, el código de verificación se muestra directamente
en pantalla como mensaje flash para poder probar el flujo completo end-to-end.
