"""
Migraciones idempotentes de esquema.

Railway despliega con el Dockerfile (uvicorn app.main:app) y NO ejecuta un
paso de migración aparte, por lo que estas migraciones corren al arrancar
(desde el lifespan de FastAPI). Añaden columnas que faltan en bases de datos
ya existentes, de forma segura tanto en PostgreSQL como en SQLite.

Para bases nuevas, `Base.metadata.create_all` ya crea las tablas completas y
estas migraciones simplemente no encuentran nada que hacer.
"""
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


# Columnas que deben existir: tabla -> {columna: tipo SQL}
# Se añaden solo si faltan (idempotente).
REQUIRED_COLUMNS: dict[str, dict[str, str]] = {
    "fighters": {
        # Aislamiento por entrenador. La BD de Railway ya existía sin esta
        # columna; se añade aquí para no perder los datos actuales.
        "owner_id": "INTEGER",
        "years_experience_pro": "INTEGER",
        "years_experience_amateur": "INTEGER",
    },
}


def run_migrations(engine: Engine) -> None:
    """Añade columnas faltantes definidas en REQUIRED_COLUMNS."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    for table, columns in REQUIRED_COLUMNS.items():
        if table not in existing_tables:
            # create_all la creará completa; nada que migrar.
            continue
        existing_cols = {c["name"] for c in inspector.get_columns(table)}
        for col, ddl in columns.items():
            if col in existing_cols:
                continue
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}"))
            print(f"[migrations] Columna añadida: {table}.{col}")
