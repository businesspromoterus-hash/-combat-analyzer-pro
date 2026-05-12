"""
Inicializa la base de datos creando todas las tablas.
Ejecutar: python -m app.core.init_db
"""
from app.core.database import Base, engine
from app.models import db_models  # noqa: F401 - registra modelos


def init_db():
    print("[init_db] Creando tablas...")
    Base.metadata.create_all(bind=engine)
    print("[init_db] OK. Base de datos lista.")


if __name__ == "__main__":
    init_db()
