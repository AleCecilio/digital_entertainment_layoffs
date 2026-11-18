
import numpy as np
import pandas as pd


# =====================================================================
# FUNÇÕES AUXILIARES — DIAGNÓSTICO DE QUALIDADE DOS DADOS
# =====================================================================

def _data_missing_nan(df: pd.DataFrame) -> pd.Series:
    """
    Conta os valores nulos reais do DataFrame.

    Parâmetros:
        df: DataFrame que será analisado.

    Retorno:
        Série com a quantidade de valores nulos por coluna.
    """
    counts = df.isna().sum()
    counts.index = counts.index + ' (Nulos/NaN)'
    return counts


def _data_missing_numeric(df: pd.DataFrame) -> pd.Series:
    """
    Conta os valores numéricos iguais a zero.

    Parâmetros:
        df: DataFrame que será analisado.

    Retorno:
        Série com a quantidade de zeros numéricos por coluna.
    """
    numeric_columns = df.select_dtypes(include='number')
    counts = (numeric_columns == 0).sum()
    counts.index = counts.index + ' (Valores Zero)'
    return counts


def _data_missing_numeric_obj(df: pd.DataFrame) -> pd.Series:
    """
    Conta os valores iguais a '0' armazenados como texto.

    Parâmetros:
        df: DataFrame que será analisado.

    Retorno:
        Série com a quantidade de zeros textuais por coluna.
    """
    string_columns = df.select_dtypes(
        include=['object', 'string']
    ).columns

    if len(string_columns) == 0:
        return pd.Series(dtype='int64')

    counts = df[string_columns].apply(
        lambda series: (
            series.dropna().astype(str).str.strip() == '0'
        ).sum()
    )

    counts.index = counts.index + ' (Zeros em Texto)'
    return counts


def _data_missing_datetime(df: pd.DataFrame) -> pd.Series:
    """
    Conta os valores ausentes em colunas de data e hora.

    Parâmetros:
        df: DataFrame que será analisado.

    Retorno:
        Série com a quantidade de valores ausentes por coluna temporal.
    """
    datetime_columns = df.select_dtypes(
        include=['datetime', 'datetime64']
    ).columns

    if len(datetime_columns) == 0:
        return pd.Series(dtype='int64')

    counts = df[datetime_columns].isna().sum()
    counts.index = counts.index + ' (Datas Inválidas/NaT)'
    return counts


def _data_missing_empty_strings(df: pd.DataFrame) -> pd.Series:
    """
    Conta strings vazias ou compostas apenas por espaços em branco.

    Parâmetros:
        df: DataFrame que será analisado.

    Retorno:
        Série com a quantidade de strings vazias por coluna textual.
    """
    string_columns = df.select_dtypes(
        include=['object', 'string']
    ).columns

    if len(string_columns) == 0:
        return pd.Series(dtype='int64')

    counts = df[string_columns].apply(
        lambda series: (
            series.dropna().astype(str).str.strip() == ''
        ).sum()
    )

    counts.index = counts.index + ' (Strings Vazias/Espaços)'
    return counts


def _data_negative_numeric(df: pd.DataFrame) -> pd.Series:
    """
    Conta valores numéricos negativos.

    Parâmetros:
        df: DataFrame que será analisado.

    Retorno:
        Série com a quantidade de valores negativos por coluna.
    """
    numeric_columns = df.select_dtypes(include='number')
    counts = (numeric_columns < 0).sum()
    counts.index = counts.index + ' (Valores Negativos)'
    return counts


def _data_duplicates(df: pd.DataFrame) -> pd.Series:
    """
    Conta linhas integralmente duplicadas.

    Parâmetros:
        df: DataFrame que será analisado.

    Retorno:
        Série com a quantidade de duplicatas exatas, caso existam.
    """
    duplicate_count = df.duplicated().sum()

    if duplicate_count > 0:
        return pd.Series(
            [duplicate_count],
            index=['Linhas Duplicadas (100% Idênticas)']
        )

    return pd.Series(dtype='int64')


def _data_partial_duplicates(df: pd.DataFrame) -> pd.Series:
    """
    Conta registros repetidos para a mesma empresa e data.

    Parâmetros:
        df: DataFrame que será analisado.

    Retorno:
        Série com a quantidade de duplicatas parciais, caso existam.
    """
    required_columns = ['company', 'date']

    if all(column in df.columns for column in required_columns):
        duplicate_count = df.duplicated(
            subset=required_columns
        ).sum()

        if duplicate_count > 0:
            return pd.Series(
                [duplicate_count],
                index=['Duplicidade Parcial (Mesma Empresa + Data)']
            )

    return pd.Series(dtype='int64')


def _data_invalid_percentage(df: pd.DataFrame) -> pd.Series:
    """
    Conta percentuais de demissões fora do intervalo de 0 a 1.

    Parâmetros:
        df: DataFrame que será analisado.

    Retorno:
        Série com a quantidade de percentuais inválidos, caso existam.
    """
    column = 'percentage_laid_off'

    if column in df.columns:
        invalid_mask = (
            (df[column] < 0) | (df[column] > 1.0)
        )
        invalid_count = invalid_mask.sum()

        if invalid_count > 0:
            return pd.Series(
                [invalid_count],
                index=['percentage_laid_off Fora de [0, 1]']
            )

    return pd.Series(dtype='int64')


def _data_inconsistent_dates(df: pd.DataFrame) -> pd.Series:
    """
    Conta datas de eventos posteriores às respectivas datas de cadastro.

    Parâmetros:
        df: DataFrame que será analisado.

    Retorno:
        Série com a quantidade de datas inconsistentes, caso existam.
    """
    required_columns = ['date', 'date_added']

    if not all(column in df.columns for column in required_columns):
        return pd.Series(dtype='int64')

    date_column = df['date']
    registration_column = df['date_added']

    if (
        pd.api.types.is_datetime64_any_dtype(date_column)
        and pd.api.types.is_datetime64_any_dtype(registration_column)
    ):
        invalid_mask = date_column > registration_column
        invalid_count = invalid_mask.sum()

        if invalid_count > 0:
            return pd.Series(
                [invalid_count],
                index=['Data do Evento > Data de Cadastro']
            )

    return pd.Series(dtype='int64')


# =====================================================================
# REGISTRO DAS ROTINAS DE DIAGNÓSTICO
# =====================================================================

_MISSING_CHECKS = {
    'nan': _data_missing_nan,
    'numeric': _data_missing_numeric,
    'numeric_obj': _data_missing_numeric_obj,
    'datetime': _data_missing_datetime,
    'empty_str': _data_missing_empty_strings,
    'negatives': _data_negative_numeric,
    'duplicates': _data_duplicates,
    'partial_duplicates': _data_partial_duplicates,
    'invalid_pct': _data_invalid_percentage,
    'inconsistent_dates': _data_inconsistent_dates,
}

_DEFAULT_CHECKS = [
    'nan',
    'numeric',
    'numeric_obj',
    'datetime',
    'empty_str',
    'negatives',
    'duplicates',
    'partial_duplicates',
    'invalid_pct',
    'inconsistent_dates',
]


# =====================================================================
# FUNÇÃO PRINCIPAL — DIAGNÓSTICO DE QUALIDADE
# =====================================================================

def check_data_quality(
    df: pd.DataFrame,
    types: list[str] | None = None,
    ignore_zeros_in: list[str] | None = None
) -> pd.DataFrame:
    """
    Gera um relatório de qualidade dos dados com as anomalias encontradas.

    Parâmetros:
        df: DataFrame que será auditado.
        types: Lista dos identificadores das verificações desejadas.
            Se None, executa todas as verificações disponíveis.
        ignore_zeros_in: Lista de colunas cujos zeros numéricos devem
            ser desconsiderados no relatório.

    Retorno:
        DataFrame com a quantidade e a incidência percentual de cada
        anomalia encontrada. Se nenhuma for encontrada, retorna uma
        tabela vazia com as colunas esperadas.

    Observações:
        A incidência é calculada em relação ao total de linhas do DataFrame.
        Os percentuais podem somar mais de 100%, pois uma mesma linha pode
        apresentar diferentes tipos de anomalia.
    """
    if types is None:
        types = _DEFAULT_CHECKS.copy()

    if ignore_zeros_in is None:
        ignore_zeros_in = []

    invalid_types = [
        check_type
        for check_type in types
        if check_type not in _MISSING_CHECKS
    ]

    if invalid_types:
        raise ValueError(
            f"Tipos inválidos: {invalid_types}. "
            f"Use: {list(_MISSING_CHECKS.keys())}"
        )

    series_list = []

    for check_type in types:
        result = _MISSING_CHECKS[check_type](df)

        if (
            check_type == 'numeric'
            and ignore_zeros_in
            and not result.empty
        ):
            excluded_indices = [
                f'{column} (Valores Zero)'
                for column in ignore_zeros_in
            ]

            result = result[
                ~result.index.isin(excluded_indices)
            ]

        series_list.append(result)

    series_list = [
        result for result in series_list
        if not result.empty
    ]

    empty_columns = ['Quantidade', 'Incidência (%)']

    if not series_list:
        return pd.DataFrame(columns=empty_columns)

    raw_summary = pd.concat(series_list)
    filtered_summary = raw_summary[raw_summary > 0]

    if filtered_summary.empty:
        return pd.DataFrame(columns=empty_columns)

    return (
        pd.DataFrame({
            'Quantidade': filtered_summary,
            'Incidência (%)': (
                filtered_summary / len(df)
            ) * 100
        })
        .sort_values('Incidência (%)', ascending=False)
        .round(2)
    )


# =====================================================================
# AUDITORIA DE DUPLICIDADES PARCIAIS — EMPRESA + DATA
# =====================================================================

def inspect_partial_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrupa registros da mesma empresa e data e classifica os conflitos.

    Parâmetros:
        df: DataFrame que será auditado. Deve conter as colunas company,
            date, location, total_laid_off, percentage_laid_off e industry.

    Retorno:
        DataFrame com os registros agrupados, os dados comparados,
        o diagnóstico e o status sugerido para a limpeza.

    Observações:
        Registros de uma mesma empresa e data em cidades diferentes
        são classificados como casos a manter. Os demais grupos são
        classificados conforme a igualdade ou divergência das métricas.
    """
    required_columns = {
        'company',
        'date',
        'location',
        'total_laid_off',
        'percentage_laid_off',
        'industry',
    }

    if not required_columns.issubset(df.columns):
        missing_columns = required_columns - set(df.columns)

        raise ValueError(
            'Colunas obrigatórias ausentes para auditoria: '
            f'{sorted(missing_columns)}'
        )

    duplicate_mask = df.duplicated(
        subset=['company', 'date'],
        keep=False
    )

    empty_columns = [
        'company',
        'date',
        'qtd_linhas',
        'cidades',
        'demitidos',
        'percentual',
        'setor',
        'diagnostico',
        'status',
    ]

    if not duplicate_mask.any():
        return pd.DataFrame(columns=empty_columns)

    duplicate_data = df.loc[duplicate_mask]

    def _format_unique_values(
        series: pd.Series,
        decimals: int | None = None
    ) -> str:
        """Formata valores distintos para facilitar a comparação."""
        unique_values = series.drop_duplicates().tolist()
        formatted_values = []

        for value in unique_values:
            if pd.isna(value):
                formatted_values.append('NaN')
            elif decimals is not None:
                formatted_values.append(
                    f'{value:.{decimals}f}'
                )
            elif isinstance(value, (int, np.integer)):
                formatted_values.append(str(value))
            elif isinstance(value, (float, np.floating)) and value.is_integer():
                formatted_values.append(str(int(value)))
            else:
                formatted_values.append(str(value))

        return ' vs '.join(formatted_values)

    summary = (
        duplicate_data
        .groupby(['company', 'date'], as_index=False)
        .agg(
            qtd_linhas=('company', 'count'),
            cidades=(
                'location',
                lambda series: _format_unique_values(series)
            ),
            demitidos=(
                'total_laid_off',
                lambda series: _format_unique_values(series)
            ),
            percentual=(
                'percentage_laid_off',
                lambda series: _format_unique_values(
                    series,
                    decimals=4
                )
            ),
            setor=('industry', 'first'),
        )
    )

    def _classify_group(row: pd.Series) -> tuple[str, str]:
        """Classifica o grupo conforme as diferenças encontradas."""
        if ' vs ' in row['cidades']:
            return (
                'Cidades diferentes (Manter)',
                '🟢 Cidades diferentes (Manter)'
            )

        if (
            ' vs ' not in row['demitidos']
            and ' vs ' not in row['percentual']
        ):
            return (
                'Duplicata exata (Remover)',
                '🔴 Duplicata exata (Remover)'
            )

        return (
            'Mesma cidade / dados divergentes',
            '🟡 Mesma cidade / dados divergentes'
        )

    classifications = summary.apply(
        _classify_group,
        axis=1
    )

    summary['diagnostico'] = [
        classification[0]
        for classification in classifications
    ]

    summary['status'] = [
        classification[1]
        for classification in classifications
    ]

    return (
        summary
        .sort_values('status')
        .reset_index(drop=True)
    )


# =====================================================================
# AUDITORIA DE COMPLETUDE — TABELAS CRUZADAS
# =====================================================================

def cross_tabulation_sector_company(
    df: pd.DataFrame,
    column: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Analisa a completude das métricas de demissões por uma categoria.

    Parâmetros:
        df: DataFrame que contém as métricas de demissões e a categoria
            utilizada para agrupar os registros.
        column: Nome da coluna categórica usada no cruzamento, como
            sector_scope, industry ou stage. Deve existir em df.columns.

    Retorno:
        Tupla contendo duas tabelas:
        - Tabela de contagens absolutas, incluindo totais.
        - Tabela de percentuais por categoria, sem margens de totais.

    Observações:
        A completude é avaliada pelas colunas total_laid_off e
        percentage_laid_off. A tabela percentual contém valores textuais
        formatados com o símbolo de porcentagem.
    """
    required_columns = [
        column,
        'total_laid_off',
        'percentage_laid_off',
    ]

    missing_columns = [
        name
        for name in required_columns
        if name not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f'Colunas obrigatórias ausentes no DataFrame: {missing_columns}. '
            f'Colunas disponíveis: {df.columns.tolist()}'
        )

    total_filled = df['total_laid_off'].notna()
    percentage_filled = df['percentage_laid_off'].notna()

    conditions = [
        total_filled & percentage_filled,
        total_filled & ~percentage_filled,
        ~total_filled & percentage_filled,
        ~total_filled & ~percentage_filled,
    ]

    categories = [
        '1. Ambas preenchidas (Total + %)',
        '2. Apenas total_laid_off (% nulo)',
        '3. Apenas percentage_laid_off (Total nulo)',
        '4. Ambas nulas (Sem métricas)',
    ]

    completeness_profile = pd.Series(
        np.select(
            conditions,
            categories,
            default='Outro'
        ),
        index=df.index,
        name='Perfil de Completude',
    )

    absolute_table = pd.crosstab(
        completeness_profile,
        df[column],
        margins=True,
        margins_name='Total Geral',
    )

    percentage_table = pd.crosstab(
        completeness_profile,
        df[column],
        normalize='columns',
    ) * 100

    percentage_table = (
        percentage_table.round(2).astype(str) + '%'
    )

    return absolute_table, percentage_table