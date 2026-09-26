import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "cambia-esta-clave-en-produccion")

    # Por defecto usamos SQLite para que el proyecto funcione "out of the box"
    # sin necesidad de instalar/configurar un servidor MySQL.
    # Si quieres usar MySQL, define la variable de entorno DATABASE_URL, por ejemplo:
    #   mysql+pymysql://usuario:password@localhost/factu_fact_db
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'factu_fact.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
