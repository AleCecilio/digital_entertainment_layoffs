import pandas as pd
import psycopg2
from sqlalchemy import text
from sqlalchemy.engine import Engine
from src.io.data_load import get_project_root, get_db_config, get_postgres_engine


def save_csv(df: pd.DataFrame, filename: str, folder: str = "processed", index: bool = False) -> str:
    """Salva o DataFrame em data/processed e retorna o caminho absoluto do arquivo."""
    output_dir = get_project_root() / "data" / folder
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / filename
    df.to_csv(file_path, index=index, encoding="utf-8")
    print(f"CSV salvo com sucesso em: {file_path}")
    return str(file_path.resolve())


def save_excel(
    sheets: dict[str, pd.DataFrame] | pd.DataFrame,
    filename: str,
    folder: str = "processed",
    index: bool = False,
) -> str:
    """Salva um DataFrame único ou um dicionário {'Aba': df} em Excel (.xlsx)."""
    output_dir = get_project_root() / "data" / folder
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / filename

    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        if isinstance(sheets, dict):
            for sheet_name, df in sheets.items():
                df.to_excel(writer, sheet_name=sheet_name[:31], index=index)
        else:
            sheets.to_excel(writer, sheet_name="Dados", index=index)

    print(f"Planilha Excel salva com sucesso em: {file_path}")
    return str(file_path.resolve())


def load_layoffs_to_postgres(
    csv_filename: str = "layoffs_clean.csv",
    table_name: str = "layoffs",
    truncate_before_load: bool = False,
    engine: Engine | None = None,
) -> None:
    """
    Cria a tabela tipada no PostgreSQL (se não existir) e realiza carga em lote
    via COPY FROM STDIN a partir do CSV processado.
    """
    if engine is None:
        engine = get_postgres_engine(ensure_db=True)

    csv_path = get_project_root() / "data" / "processed" / csv_filename
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV processado não encontrado: {csv_path}")

    # 1. DDL com tipagem estrita para o schema do projeto
    ddl = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        company VARCHAR(150) NOT NULL,
        location VARCHAR(150),
        total_laid_off INTEGER,
        date DATE NOT NULL,
        percentage_laid_off NUMERIC(6, 4),
        industry VARCHAR(80) NOT NULL,
        sector_scope VARCHAR(30) NOT NULL,
        source TEXT,
        stage VARCHAR(60),
        stage_group VARCHAR(40),
        funds_raised NUMERIC(12, 2),
        country VARCHAR(100),
        date_added DATE,
        year SMALLINT,
        quarter VARCHAR(10),
        year_quarter VARCHAR(10)
    );
    """

    with engine.begin() as conn:
        conn.execute(text(ddl))
        if truncate_before_load:
            conn.execute(text(f"TRUNCATE TABLE {table_name};"))
            print(f"Tabela '{table_name}' limpa (TRUNCATE) antes da recarga.")

        total_registros = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()

    # 2. Carga idempotente via psycopg2 COPY FROM STDIN
    if total_registros == 0:
        cfg = get_db_config()
        raw_conn = psycopg2.connect(
            host=cfg["host"],
            port=cfg["port"],
            user=cfg["user"],
            password=cfg["password"],
            dbname=cfg["dbname"],
        )
        try:
            # Lê apenas o cabeçalho do CSV para mapear as colunas automaticamente na ordem exata
            header_cols = pd.read_csv(csv_path, nrows=0).columns.tolist()
            cols_sql = ", ".join(header_cols)

            with raw_conn.cursor() as cursor, open(csv_path, "r", encoding="utf-8") as f:
                cursor.copy_expert(
                    f"""
                    COPY {table_name} ({cols_sql})
                    FROM STDIN
                    WITH (
                        FORMAT CSV,
                        HEADER TRUE,
                        DELIMITER ',',
                        QUOTE '"',
                        NULL ''
                    )
                    """,
                    f,
                )
            raw_conn.commit()
            print("Carga dos dados concluída via COPY FROM STDIN.")
        except Exception:
            raw_conn.rollback()
            raise
        finally:
            raw_conn.close()
    else:
        print(
            f"A tabela '{table_name}' já possui {total_registros:,} registros. "
            "Carga ignorada (use truncate_before_load=True para recarregar)."
        )

    # 3. Auditoria pós-carga
    with engine.connect() as conn:
        total_final = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
        print(f"Total de registros confirmados em '{table_name}': {total_final:,}".replace(",", "."))