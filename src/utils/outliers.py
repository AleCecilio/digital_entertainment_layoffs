import pandas as pd
from IPython.display import display


def calculate_limits_iqr(
    df: pd.DataFrame,
    coluna: str,
    multiplicador: float = 1.5
) -> tuple[float, float]:
    """Calcula os limites estatísticos (Cerca Inferior e Superior) via método IQR."""
    if coluna not in df.columns or not pd.api.types.is_numeric_dtype(df[coluna]):
        raise ValueError(f"A coluna '{coluna}' não existe ou não é numérica.")

    q1 = df[coluna].quantile(0.25)
    q3 = df[coluna].quantile(0.75)
    iqr = q3 - q1

    return float(q1 - multiplicador * iqr), float(q3 + multiplicador * iqr)


def batch_outlier_diagnosis(
    df: pd.DataFrame,
    colunas_ignorar: list[str] | None = None
) -> pd.DataFrame:
    """Varre as colunas numéricas e retorna um relatório ranqueado de outliers."""
    if colunas_ignorar is None:
        colunas_ignorar = ['year']

    cols_numericas = df.select_dtypes(include='number').columns
    cols_analise = [c for c in cols_numericas if c not in colunas_ignorar]
    resultados = []

    for col in cols_analise:
        serie_valida = df[col].dropna()
        if serie_valida.empty:
            continue

        limite_inf, limite_sup = calculate_limits_iqr(df, col)
        total_outliers = ((serie_valida > limite_sup) | (serie_valida < limite_inf)).sum()

        if total_outliers > 0:
            resultados.append({
                'Coluna': col,
                'Registros Válidos': len(serie_valida),
                'Qtd Outliers': total_outliers,
                'Impacto (% Válidos)': round((total_outliers / len(serie_valida)) * 100, 2),
                'Cerca Inf': round(limite_inf, 2),
                'Cerca Sup': round(limite_sup, 2)
            })

    if not resultados:
        return pd.DataFrame(columns=['Coluna', 'Qtd Outliers', 'Impacto (% Válidos)', 'Cerca Inf', 'Cerca Sup'])

    return pd.DataFrame(resultados).sort_values(by='Impacto (% Válidos)', ascending=False).reset_index(drop=True)


def outliers_summary(
    df: pd.DataFrame,
    coluna: str,
    limite_sup: float,
    limite_inf: float | None = None,
    group_by: str = 'company',
    colunas_analise: list[str] | None = None
) -> None:
    """Exibe métricas de impacto, recorrência por empresa e Top 10 registros extremos."""
    if coluna not in df.columns:
        print(f"A coluna '{coluna}' não existe no DataFrame.")
        return

    condicao = (
        (df[coluna] > limite_sup) | (df[coluna] < limite_inf)
        if limite_inf is not None
        else (df[coluna] > limite_sup)
    )
    outliers = df[condicao.fillna(False)]
    validos = df[coluna].notna().sum()
    pct = (len(outliers) / validos) * 100 if validos > 0 else 0

    print("=" * 62)
    print(f"   RESUMO DE OUTLIERS: {coluna.upper()}")
    print("=" * 62)
    print(f"• Cerca Superior (IQR): {limite_sup:,.2f}")
    if limite_inf is not None:
        print(f"• Cerca Inferior (IQR): {limite_inf:,.2f}")
    print(f"• Outliers encontrados: {len(outliers)} de {validos} registros válidos ({pct:.2f}%)")

    if outliers.empty:
        print("Nenhum registro ultrapassou os limites calculados.\n")
        return

    print(f"• Amplitude entre outliers: {outliers[coluna].min():,.2f} até {outliers[coluna].max():,.2f}\n")

    if group_by in df.columns:
        top_entidades = (
            outliers[group_by]
            .value_counts()
            .head(5)
            .reset_index()
            .rename(columns={'count': 'eventos_outlier', group_by: group_by.title()})
        )
        print(f"Top 5 {group_by.title()} com maior recorrência de outliers:")
        display(top_entidades)

    if colunas_analise is None:
        colunas_analise = ['company', 'date', 'industry', 'sector_scope', 'stage', 'country']

    cols_exibir = list(dict.fromkeys([c for c in [coluna] + colunas_analise if c in df.columns]))
    print(f"\nTop 10 registros mais extremos em '{coluna}':")
    display(outliers[cols_exibir].sort_values(by=coluna, ascending=False).head(10))