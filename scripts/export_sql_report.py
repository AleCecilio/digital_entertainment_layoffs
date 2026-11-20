"""
Exportador Automatizado de Relatórios SQL (PostgreSQL / TXT -> CSV & Excel)

Execução a partir da raiz do projeto (`digital_entertainment_layoffs/`):
- Lê diretamente das views do PostgreSQL (modo padrão) OU faz fallback para
  `docs/tables/txt/todos_resultados_sql.txt` caso o banco esteja offline.
- Exporta CSVs leves em `docs/tables/csv/` (para versionamento no GitHub).
- Exporta pasta de trabalho Excel limpa e otimizada com 4 abas em
  `docs/tables/excel/` (ignorada no Git para economizar espaço).
"""

import os
import re
from pathlib import Path
from urllib.parse import quote_plus

import openpyxl
import pandas as pd
from dotenv import load_dotenv
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from sqlalchemy import create_engine


# ==============================================================================
# CONFIGURAÇÕES DE CONEXÃO VIA .ENV E CAMINHOS RELATIVOS À RAIZ DO PROJETO
# ==============================================================================
PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
    if Path(__file__).resolve().parent.name in {"scripts", "src"}
    else Path.cwd()
)

load_dotenv(PROJECT_ROOT / ".env")

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = quote_plus(os.getenv("DB_PASSWORD", ""))
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "layoffs")

DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

TXT_INPUT_PATH = PROJECT_ROOT / "docs" / "tables" / "txt" / "todos_resultados_sql.txt"
CSV_DIR = PROJECT_ROOT / "docs" / "tables" / "csv"
EXCEL_DIR = PROJECT_ROOT / "docs" / "tables" / "excel"
EXCEL_PATH = EXCEL_DIR / "digital_entertainment_layoffs_analise_sql.xlsx"


# ==============================================================================
# IDENTIDADE VISUAL DO PROJETO (PALETA PARA EXCEL E DASHBOARD POWER BI)
# ==============================================================================
# Paleta unificada (alinhada ao gráfico de entrega da Etapa 3):
# - Primária (Consumer / Cabeçalhos / Estrutura): Deep Ocean Navy  #1B4965
# - Secundária (Media / Destaques no Dashboard):  Vibrant Amber    #E67E22
# - Neutra Escura (Tipografia principal):         Slate Charcoal   #1E293B
# - Neutra Suave (Zebra / Fundos de cards):       Ice Tint         #F4F7FA
PROJECT_PALETTE = {
    "primary_navy": "1B4965",     # Cor principal do projeto (Consumer / Headers)
    "secondary_amber": "E67E22",  # Cor de contraste para o Dashboard (Media)
    "dark_text": "1E293B",        # Texto principal
    "muted_text": "64748B",       # Subtítulos e rótulos
    "banner_bg": "E8EEF3",        # Fundo suave derivado do azul primário
    "zebra_bg": "F8FAFC",         # Linhas alternadas sutis
    "total_bg": "E2E8F0",         # Linha de total
    "border_light": "CBD5E1",     # Bordas internas discretas
}

FONT_FAMILY = "Calibri"
PRIMARY_HEADER = PatternFill(
    start_color=PROJECT_PALETTE["primary_navy"],
    end_color=PROJECT_PALETTE["primary_navy"],
    fill_type="solid",
)
SECTION_BANNER = PatternFill(
    start_color=PROJECT_PALETTE["banner_bg"],
    end_color=PROJECT_PALETTE["banner_bg"],
    fill_type="solid",
)
ZEBRA_FILL = PatternFill(
    start_color=PROJECT_PALETTE["zebra_bg"],
    end_color=PROJECT_PALETTE["zebra_bg"],
    fill_type="solid",
)
TOTAL_FILL = PatternFill(
    start_color=PROJECT_PALETTE["total_bg"],
    end_color=PROJECT_PALETTE["total_bg"],
    fill_type="solid",
)
KPI_BG = PatternFill(
    start_color=PROJECT_PALETTE["zebra_bg"],
    end_color=PROJECT_PALETTE["zebra_bg"],
    fill_type="solid",
)

FONT_TITLE = Font(name=FONT_FAMILY, size=13, bold=True, color=PROJECT_PALETTE["primary_navy"])
FONT_SUBTITLE = Font(name=FONT_FAMILY, size=9, italic=True, color=PROJECT_PALETTE["muted_text"])
FONT_SECTION = Font(name=FONT_FAMILY, size=10, bold=True, color=PROJECT_PALETTE["primary_navy"])
FONT_HEADER = Font(name=FONT_FAMILY, size=10, bold=True, color="FFFFFF")
FONT_DATA = Font(name=FONT_FAMILY, size=10, bold=False, color=PROJECT_PALETTE["dark_text"])
FONT_BOLD = Font(name=FONT_FAMILY, size=10, bold=True, color=PROJECT_PALETTE["dark_text"])
FONT_KPI_LABEL = Font(name=FONT_FAMILY, size=8, bold=True, color=PROJECT_PALETTE["muted_text"])
FONT_KPI_VAL = Font(name=FONT_FAMILY, size=12, bold=True, color=PROJECT_PALETTE["primary_navy"])

THIN_SIDE = Side(border_style="thin", color=PROJECT_PALETTE["border_light"])
PRIMARY_SIDE = Side(border_style="medium", color=PROJECT_PALETTE["primary_navy"])
DOUBLE_BOTTOM = Side(border_style="double", color=PROJECT_PALETTE["primary_navy"])

CELL_BORDER = Border(left=THIN_SIDE, right=THIN_SIDE, top=THIN_SIDE, bottom=THIN_SIDE)
HEADER_BORDER = Border(left=THIN_SIDE, right=THIN_SIDE, top=PRIMARY_SIDE, bottom=PRIMARY_SIDE)
TOTAL_BORDER = Border(top=THIN_SIDE, bottom=DOUBLE_BOTTOM, left=THIN_SIDE, right=THIN_SIDE)

COL_LABELS = {
    "year": "Ano",
    "quarter": "Trimestre",
    "subsegment": "Subsegmento",
    "total_events": "Total Eventos",
    "events_with_headcount": "Eventos c/ Headcount",
    "total_laid_off": "Total Demitidos",
    "avg_laid_off": "Média Demitidos",
    "median_laid_off": "Mediana Demitidos",
    "avg_percentage_cut": "Corte Médio (%)",
    "median_percentage_cut": "Corte Mediano (%)",
    "shutdown_events": "Encerramentos",
    "total_shutdowns": "Encerramentos",
    "unique_companies": "Empresas Únicas",
    "avg_funds_raised_millions": "Captação Média (US$ Mi)",
    "median_funds_raised_millions": "Captação Mediana (US$ Mi)",
    "country": "País",
    "location": "Polo Urbano / Cidade",
    "stage": "Estágio Corporativo",
    "rank_position": "Rank",
    "company": "Empresa",
    "layoff_rounds": "Rodadas",
    "is_shutdown": "Encerrou?",
}


def get_num_format(col_name: str) -> str:
    if col_name in {"year", "rank_position"}:
        return "0"
    if "pct" in col_name or "percentage" in col_name:
        return "0.00"
    if "avg" in col_name or "median" in col_name or "funds" in col_name:
        return "#,##0.0"
    if any(k in col_name for k in ["events", "laid_off", "shutdown", "companies", "rounds"]):
        return "#,##0"
    return "@"


def parse_psql_txt(txt_path: Path) -> list[pd.DataFrame]:
    """Lê tabelas ASCII exportadas pelo PSQL em docs/tables/txt/todos_resultados_sql.txt."""
    text = txt_path.read_text(encoding="utf-8", errors="ignore")
    tables = []
    lines = text.splitlines()
    i = 0
    str_cols = {
        "subsegment", "quarter", "year_month", "company_stage", "layoff_scale",
        "metric_completeness", "primary_subsegment", "country", "latest_stage",
        "company", "location", "stage", "ever_shutdown", "is_shutdown",
    }

    while i < len(lines):
        line = lines[i]
        if i + 1 < len(lines) and re.match(r"^[-+]+$", lines[i + 1].strip()) and "|" in line:
            headers = [h.strip() for h in line.split("|")]
            i += 2
            rows = []
            while i < len(lines) and "|" in lines[i] and not re.match(r"^\(\d+ rows?\)", lines[i].strip()):
                vals = [v.strip() for v in lines[i].split("|")]
                if len(vals) == len(headers):
                    rows.append(vals)
                i += 1
            df = pd.DataFrame(rows, columns=headers)
            for col in df.columns:
                if col not in str_cols:
                    converted = pd.to_numeric(df[col], errors="coerce")
                    if not converted.isna().all():
                        df[col] = converted
            tables.append(df)
        else:
            i += 1
    return tables


def load_views_data() -> tuple[dict[str, pd.DataFrame], str]:
    """Carrega dados diretamente do PostgreSQL ou usa docs/tables/txt/ como fallback."""
    try:
        engine = create_engine(DB_URL)
        views = {
            "vw_evolucao_temporal": pd.read_sql("SELECT * FROM vw_evolucao_temporal;", engine),
            "vw_comparacao_subsegmentos": pd.read_sql("SELECT * FROM vw_comparacao_subsegmentos;", engine),
            "vw_analise_geografica": pd.read_sql("SELECT * FROM vw_analise_geografica;", engine),
            "vw_perfil_estagio_empresas": pd.read_sql("SELECT * FROM vw_perfil_estagio_empresas;", engine),
            "vw_top15_empresas": pd.read_sql("SELECT * FROM vw_top15_empresas;", engine),
        }
        return views, "PostgreSQL (Views Analíticas)"
    except Exception as exc:
        if not TXT_INPUT_PATH.exists():
            raise RuntimeError(
                f"Falha ao conectar no PostgreSQL ({exc}) e arquivo fallback não encontrado em: "
                f"docs/tables/txt/{TXT_INPUT_PATH.name}"
            ) from exc
        parsed = parse_psql_txt(TXT_INPUT_PATH)
        views = {
            "vw_evolucao_temporal": parsed[9],
            "vw_comparacao_subsegmentos": parsed[10],
            "vw_analise_geografica": parsed[11],
            "vw_perfil_estagio_empresas": parsed[12],
            "vw_top15_empresas": parsed[13],
        }
        return views, "docs/tables/txt/todos_resultados_sql.txt"


def write_kpi_cards(ws, row_idx: int, kpis: list) -> None:
    col = 1
    for label, val, num_fmt in kpis:
        ws.merge_cells(start_row=row_idx, start_column=col, end_row=row_idx, end_column=col + 1)
        ws.merge_cells(start_row=row_idx + 1, start_column=col, end_row=row_idx + 1, end_column=col + 1)
        c_lbl = ws.cell(row=row_idx, column=col, value=label.upper())
        c_val = ws.cell(row=row_idx + 1, column=col, value=val)
        c_lbl.font = FONT_KPI_LABEL
        c_val.font = FONT_KPI_VAL
        c_val.number_format = num_fmt
        c_lbl.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        c_val.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        for r in (row_idx, row_idx + 1):
            for c in range(col, col + 2):
                cell = ws.cell(row=r, column=c)
                cell.fill = KPI_BG
                cell.border = Border(
                    left=PRIMARY_SIDE if c == col else None,
                    right=THIN_SIDE if c == col + 1 else None,
                    top=THIN_SIDE if r == row_idx else None,
                    bottom=THIN_SIDE if r == row_idx + 1 else None,
                )
        col += 2
    ws.row_dimensions[row_idx].height = 17
    ws.row_dimensions[row_idx + 1].height = 23


def write_table(
    ws, df: pd.DataFrame, start_row: int, start_col: int, title: str,
    add_total_row: bool = False, sum_cols: list | None = None
):
    end_col = start_col + len(df.columns) - 1
    ws.merge_cells(start_row=start_row, start_column=start_col, end_row=start_row, end_column=end_col)
    banner = ws.cell(row=start_row, column=start_col, value=title)
    banner.font = FONT_SECTION
    banner.fill = SECTION_BANNER
    banner.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[start_row].height = 22
    for c in range(start_col, end_col + 1):
        ws.cell(row=start_row, column=c).border = Border(
            left=PRIMARY_SIDE if c == start_col else None,
            top=THIN_SIDE,
            bottom=THIN_SIDE,
            right=THIN_SIDE if c == end_col else None,
        )

    header_row = start_row + 1
    ws.row_dimensions[header_row].height = 28
    for idx, col_name in enumerate(df.columns):
        c_idx = start_col + idx
        cell = ws.cell(row=header_row, column=c_idx, value=COL_LABELS.get(col_name, col_name))
        cell.font = FONT_HEADER
        cell.fill = PRIMARY_HEADER
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = HEADER_BORDER

    data_start = header_row + 1
    for r_offset, (_, row_data) in enumerate(df.iterrows()):
        curr_row = data_start + r_offset
        ws.row_dimensions[curr_row].height = 20
        is_even = (r_offset % 2 == 1)
        for c_offset, col_name in enumerate(df.columns):
            c_idx = start_col + c_offset
            val = row_data[col_name]
            if pd.isna(val) or val == "":
                val = None
            elif col_name == "is_shutdown":
                val = "Sim" if str(val).lower() in {"t", "true", "1"} else "Não"
            cell = ws.cell(row=curr_row, column=c_idx, value=val)
            cell.font = FONT_BOLD if c_offset == 0 else FONT_DATA
            if is_even:
                cell.fill = ZEBRA_FILL
            cell.border = CELL_BORDER
            num_fmt = get_num_format(col_name)
            if num_fmt != "@":
                cell.number_format = num_fmt
                cell.alignment = Alignment(horizontal="right", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left" if c_offset <= 1 else "center", vertical="center")

    data_end = data_start + len(df) - 1
    last_row = data_end

    if add_total_row and sum_cols:
        total_row = data_end + 1
        ws.row_dimensions[total_row].height = 22
        for c_offset, col_name in enumerate(df.columns):
            c_idx = start_col + c_offset
            col_letter = get_column_letter(c_idx)
            cell = ws.cell(row=total_row, column=c_idx)
            cell.font = FONT_BOLD
            cell.fill = TOTAL_FILL
            cell.border = TOTAL_BORDER
            if c_offset == 0:
                cell.value = "TOTAL GERAL"
                cell.alignment = Alignment(horizontal="left", vertical="center")
            elif col_name in sum_cols:
                cell.value = f"=SUM({col_letter}{data_start}:{col_letter}{data_end})"
                cell.number_format = get_num_format(col_name)
                cell.alignment = Alignment(horizontal="right", vertical="center")
            else:
                cell.value = "—"
                cell.alignment = Alignment(horizontal="center", vertical="center")
        last_row = total_row

    return header_row, data_start, data_end, last_row


def setup_sheet_layout(ws, max_col_width: int = 34) -> None:
    """Padroniza visualização limpa, congelamento, ajuste de largura e página."""
    ws.views.sheetView[0].showGridLines = True
    ws.freeze_panes = "A4"
    ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0

    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            if cell.row in (1, 2):
                continue
            val_str = str(cell.value or "")
            if val_str.startswith("="):
                val_str = "123,456.00"
            # Considera cabeçalhos quebrados em 2 palavras
            if cell.row in (8, 12, 24) and len(val_str) > 14:
                val_str = max(val_str.split(), key=len) + "   "
            max_len = max(max_len, len(val_str))
        ws.column_dimensions[col_letter].width = max(min(max_len + 4, max_col_width), 12)


def main() -> None:
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    EXCEL_DIR.mkdir(parents=True, exist_ok=True)

    views_data, source_label = load_views_data()
    print(f"[INFO] Fonte de dados carregada: {source_label}")

    # Agregação anual derivada de vw_evolucao_temporal
    df_temp = views_data["vw_evolucao_temporal"]
    df_anual = (
        df_temp.groupby(["year", "subsegment"], as_index=False)
        .agg(
            total_events=("total_events", "sum"),
            events_with_headcount=("events_with_headcount", "sum"),
            total_laid_off=("total_laid_off", "sum"),
            avg_laid_off=("avg_laid_off", "mean"),
            median_laid_off=("median_laid_off", "median"),
            shutdown_events=("shutdown_events", "sum"),
        )
        .sort_values(["year", "subsegment"])
    )
    df_anual["avg_laid_off"] = df_anual["avg_laid_off"].round(1)
    df_anual["median_laid_off"] = df_anual["median_laid_off"].round(1)

    # Agregação por país derivada de vw_analise_geografica
    df_geo = views_data["vw_analise_geografica"]
    df_paises = (
        df_geo.groupby("country", as_index=False)
        .agg(
            total_events=("total_events", "sum"),
            unique_companies=("unique_companies", "sum"),
            total_laid_off=("total_laid_off", "sum"),
            avg_percentage_cut=("avg_percentage_cut", "mean"),
            shutdown_events=("shutdown_events", "sum"),
        )
        .sort_values(["total_laid_off", "total_events"], ascending=False)
        .head(15)
    )
    df_paises["avg_percentage_cut"] = df_paises["avg_percentage_cut"].round(2)

    # 1. Exportação dos CSVs leves para versionamento no GitHub (`docs/tables/csv/`)
    csv_exports = {
        **views_data,
        "resumo_anual_subsegmento": df_anual,
        "top15_paises": df_paises,
    }
    for name, df in csv_exports.items():
        csv_file = CSV_DIR / f"{name}.csv"
        df.to_csv(csv_file, index=False, encoding="utf-8")
        print(f"[CSV]  digital_entertainment_layoffs/docs/tables/csv/{csv_file.name} ({len(df)} linhas)")

    # 2. Construção da Pasta de Trabalho Excel (`docs/tables/excel/`)
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    # --- ABA 1: Tendências Temporais ---
    ws1 = wb.create_sheet(title="01_Tendencias_Temporais")
    ws1["A1"] = "DIGITAL ENTERTAINMENT LAYOFFS (2020–2026) — TENDÊNCIAS TEMPORAIS"
    ws1["A1"].font = FONT_TITLE
    ws1["A2"] = f"Fonte: {source_label} | Recorte: Entretenimento Digital (2020–2026)"
    ws1["A2"].font = FONT_SUBTITLE

    _, _, _, lr_anual = write_table(
        ws1, df_anual, start_row=7, start_col=1,
        title="1.1 Evolução Anual por Subsegmento (Consumer vs. Media)",
        add_total_row=True,
        sum_cols=["total_events", "events_with_headcount", "total_laid_off", "shutdown_events"],
    )
    write_kpi_cards(ws1, 4, [
        ("Total Eventos (2020–2026)", f"=C{lr_anual}", "#,##0"),
        ("Total Demitidos Mapeados", f"=E{lr_anual}", "#,##0"),
        ("Encerramentos Totais", f"=H{lr_anual}", "#,##0"),
    ])

    write_table(
        ws1, df_temp, start_row=lr_anual + 3, start_col=1,
        title="1.2 Detalhamento Trimestral (Ano x Trimestre x Subsegmento)",
        add_total_row=True,
        sum_cols=["total_events", "events_with_headcount", "total_laid_off", "shutdown_events"],
    )

    # --- ABA 2: Subsegmentos & Estágios ---
    ws2 = wb.create_sheet(title="02_Subsegmentos_Estagios")
    ws2["A1"] = "COMPARATIVO ENTRE SUBSEGMENTOS E ESTÁGIO CORPORATIVO"
    ws2["A1"].font = FONT_TITLE
    ws2["A2"] = f"Fonte: {source_label} | vw_comparacao_subsegmentos & vw_perfil_estagio_empresas"
    ws2["A2"].font = FONT_SUBTITLE

    df_sub = views_data["vw_comparacao_subsegmentos"]
    _, ds_sub, de_sub, lr_sub = write_table(
        ws2, df_sub, start_row=7, start_col=1,
        title="2.1 Comparativo Consolidado: Consumer vs. Media",
        add_total_row=True,
        sum_cols=["total_events", "unique_companies", "total_laid_off", "total_shutdowns"],
    )

    df_stg = views_data["vw_perfil_estagio_empresas"]
    _, ds_stg, _, _ = write_table(
        ws2, df_stg, start_row=lr_sub + 3, start_col=1,
        title="2.2 Severidade e Volume por Estágio Corporativo (Stage)",
        add_total_row=True,
        sum_cols=["total_events", "unique_companies", "total_laid_off", "total_shutdowns"],
    )

    write_kpi_cards(ws2, 4, [
        ("Consumer Demitidos", f"=D{ds_sub}", "#,##0"),
        ("Media Demitidos", f"=D{de_sub}", "#,##0"),
        ("Volume Post-IPO", f"=D{ds_stg}", "#,##0"),
    ])

    # --- ABA 3: Top 15 Empresas ---
    ws3 = wb.create_sheet(title="03_Top15_Empresas")
    ws3["A1"] = "CONCENTRAÇÃO CORPORATIVA — TOP 15 EMPRESAS MAIS AFETADAS"
    ws3["A1"].font = FONT_TITLE
    ws3["A2"] = f"Fonte: {source_label} | vw_top15_empresas"
    ws3["A2"].font = FONT_SUBTITLE

    df_top15 = views_data["vw_top15_empresas"]
    _, ds_top, _, lr_top = write_table(
        ws3, df_top15, start_row=7, start_col=1,
        title="3.1 Ranking Top 15 Empresas / Estúdios (Volume Acumulado)",
        add_total_row=True,
        sum_cols=["layoff_rounds", "total_laid_off"],
    )
    write_kpi_cards(ws3, 4, [
        ("Demitidos Top 15", f"=G{lr_top}", "#,##0"),
        ("Rodadas no Top 15", f"=F{lr_top}", "#,##0"),
        ("Líder Setorial (Meta)", f"=G{ds_top}", "#,##0"),
    ])

    # --- ABA 4: Geografia Global ---
    ws4 = wb.create_sheet(title="04_Analise_Geografica")
    ws4["A1"] = "DISTRIBUIÇÃO GEOGRÁFICA POR PAÍS E POLOS URBANOS"
    ws4["A1"].font = FONT_TITLE
    ws4["A2"] = f"Fonte: {source_label} | vw_analise_geografica"
    ws4["A2"].font = FONT_SUBTITLE

    _, ds_pais, _, lr_pais = write_table(
        ws4, df_paises, start_row=7, start_col=1,
        title="4.1 Top 15 Países Mais Afetados",
        add_total_row=True,
        sum_cols=["total_events", "unique_companies", "total_laid_off", "shutdown_events"],
    )
    write_kpi_cards(ws4, 4, [
        ("Demitidos EUA", f"=D{ds_pais}", "#,##0"),
        ("Eventos EUA", f"=B{ds_pais}", "#,##0"),
        ("Total Polos Mapeados", len(df_geo), "#,##0"),
    ])

    write_table(
        ws4, df_geo.head(25), start_row=lr_pais + 3, start_col=1,
        title="4.2 Top 25 Polos Urbanos (País x Cidade)",
        add_total_row=True,
        sum_cols=["total_events", "unique_companies", "total_laid_off", "shutdown_events"],
    )

    for ws in wb.worksheets:
        setup_sheet_layout(ws)

    wb.save(EXCEL_PATH)
    print(f"[XLSX] digital_entertainment_layoffs/docs/tables/excel/{EXCEL_PATH.name} (4 abas)")


if __name__ == "__main__":
    main()