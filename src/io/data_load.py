import os
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def get_project_root() -> Path:
    """Retorna a raiz do projeto independente de onde o kernel foi iniciado."""
    cwd = Path.cwd()
    return cwd.parent if cwd.name == "notebooks" else cwd


def get_db_config() -> dict[str, str]:
    """Carrega e valida as credenciais do PostgreSQL a partir do arquivo .env."""
    load_dotenv(get_project_root() / ".env")
    config = {
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "dbname": os.getenv("DB_NAME", "layoffs_entertainment"),
    }
    missing = [k for k, v in config.items() if not v]
    if missing:
        raise EnvironmentError(f"Variáveis ausentes no .env: {missing}")
    return config


def get_postgres_engine(ensure_db: bool = True) -> Engine:
    """
    Cria a engine SQLAlchemy conectada ao banco do projeto.
    Se ensure_db=True, verifica no servidor e cria o banco caso ainda não exista.
    """
    cfg = get_db_config()

    if ensure_db:
        server_url = f"postgresql+psycopg2://{cfg['user']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/postgres"
        engine_server = create_engine(server_url, isolation_level="AUTOCOMMIT")
        with engine_server.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db"),
                {"db": cfg["dbname"]},
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{cfg["dbname"]}"'))
                print(f"Banco de dados '{cfg['dbname']}' criado.")
            else:
                print(f"Banco de dados '{cfg['dbname']}' já existe.")
        engine_server.dispose()

    db_url = f"postgresql+psycopg2://{cfg['user']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['dbname']}"
    return create_engine(db_url)


def load_csv(filename: str, folder: str = "raw", **kwargs) -> pd.DataFrame:
    """Carrega um CSV de data/raw ou data/processed."""
    file_path = get_project_root() / "data" / folder / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
    return pd.read_csv(file_path, **kwargs)


def load_from_postgres(query: str, engine: Engine | None = None) -> pd.DataFrame:
    """Executa uma consulta SQL no PostgreSQL e retorna um DataFrame."""
    if engine is None:
        engine = get_postgres_engine(ensure_db=False)
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn)