import pandas as pd

# =====================================================================
# FUNÇÕES AUXILIARES — cada uma retorna uma Série com sufixo no índice
# =====================================================================

def _data_missing_nan(df: pd.DataFrame) -> pd.Series:
    """Conta a quantidade de valores nulos (NaN/None) reais no DataFrame."""
    n = df.isna().sum()
    n.index = n.index + ' (Nulos/NaN)'
    return n


def _data_missing_numeric(df: pd.DataFrame) -> pd.Series:
    """Identifica e conta valores iguais a zero numéricos (int/float)."""
    n = (df.select_dtypes(include='number') == 0).sum()
    n.index = n.index + ' (Valores Zero)'
    return n


def _data_missing_numeric_obj(df: pd.DataFrame) -> pd.Series:
    """Identifica e conta valores iguais a '0' armazenados como texto."""
    str_cols = df.select_dtypes(include=['object', 'string']).columns
    if len(str_cols) == 0:
        return pd.Series(dtype='int64')
    n = df[str_cols].apply(lambda x: x.dropna().astype(str).str.strip() == '0').sum()
    n.index = n.index + ' (Zeros em Texto)'
    return n


def _data_missing_datetime(df: pd.DataFrame) -> pd.Series:
    """Verifica valores nulos (NaT) especificamente em colunas de data e hora."""
    dt_cols = df.select_dtypes(include=['datetime', 'datetime64']).columns
    if len(dt_cols) == 0:
        return pd.Series(dtype='int64')
    n = df[dt_cols].isna().sum()
    n.index = n.index + ' (Datas Inválidas/NaT)'
    return n


def _data_missing_empty_strings(df: pd.DataFrame) -> pd.Series:
    """Procura por strings vazias ou compostas apenas por espaços em branco."""
    str_cols = df.select_dtypes(include=['object', 'string']).columns
    if len(str_cols) == 0:
        return pd.Series(dtype='int64')
    n = df[str_cols].apply(lambda x: x.dropna().astype(str).str.strip() == '').sum()
    n.index = n.index + ' (Strings Vazias/Espaços)'
    return n


def _data_negative_numeric(df: pd.DataFrame) -> pd.Series:
    """Busca valores negativos inválidos (ex: demissões ou capital < 0)."""
    n = (df.select_dtypes(include='number') < 0).sum()
    n.index = n.index + ' (Valores Negativos)'
    return n


def _data_duplicates(df: pd.DataFrame) -> pd.Series:
    """Busca linhas 100% idênticas na tabela."""
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        return pd.Series([dup_count], index=['Linhas Duplicadas (100% Idênticas)'])
    return pd.Series(dtype='int64')


def _data_partial_duplicates(df: pd.DataFrame) -> pd.Series:
    """Verifica eventos duplicados para a mesma empresa na mesma data."""
    if all(c in df.columns for c in ['company', 'date']):
        partial_dup = df.duplicated(subset=['company', 'date']).sum()
        if partial_dup > 0:
            return pd.Series([partial_dup], index=['Duplicidade Parcial (Mesma Empresa + Data)'])
    return pd.Series(dtype='int64')


def _data_invalid_percentage(df: pd.DataFrame) -> pd.Series:
    """Valida se percentage_laid_off está fora do intervalo lógico [0.0, 1.0]."""
    if 'percentage_laid_off' in df.columns:
        invalid_pct = (
            (df['percentage_laid_off'] < 0) | (df['percentage_laid_off'] > 1.0)
        ).sum()
        if invalid_pct > 0:
            return pd.Series([invalid_pct], index=['percentage_laid_off Fora de [0, 1]'])
    return pd.Series(dtype='int64')


def _data_inconsistent_dates(df: pd.DataFrame) -> pd.Series:
    """Verifica se a data do layoff é posterior à data de registro (date > date_added)."""
    if all(c in df.columns for c in ['date', 'date_added']):
        if pd.api.types.is_datetime64_any_dtype(df['date']) and pd.api.types.is_datetime64_any_dtype(df['date_added']):
            inconsistent = (df['date'] > df['date_added']).sum()
            if inconsistent > 0:
                return pd.Series([inconsistent], index=['Data do Evento > Data de Cadastro'])
    return pd.Series(dtype='int64')


# =====================================================================
# MAPA: tipo (string) -> função correspondente
# =====================================================================
_TIPOS_MISSING = {
    'nan':                _data_missing_nan,
    'numeric':            _data_missing_numeric,
    'numeric_obj':        _data_missing_numeric_obj,
    'datetime':           _data_missing_datetime,
    'empty_str':          _data_missing_empty_strings,
    'negatives':          _data_negative_numeric,
    'duplicates':         _data_duplicates,
    'partial_duplicates': _data_partial_duplicates,
    'invalid_pct':        _data_invalid_percentage,
    'inconsistent_dates': _data_inconsistent_dates,
}

_TIPOS_DEFAULT = [
    'nan', 'numeric', 'numeric_obj', 'datetime', 'empty_str',
    'negatives', 'duplicates', 'partial_duplicates',
    'invalid_pct', 'inconsistent_dates'
]


# =====================================================================
# FUNÇÃO PRINCIPAL — DATA QUALITY
# =====================================================================

def check_data_quality(
    df: pd.DataFrame,
    tipos: list[str] | None = None,
    ignorar_zeros_em: list[str] | None = None
) -> pd.DataFrame:
    """
    Gera um DataFrame de diagnóstico de qualidade destacando valores nulos,
    incidência de zeros, duplicatas exatas/parciais e anomalias de domínio (Layoffs.fyi).
    """
    if tipos is None:
        tipos = _TIPOS_DEFAULT
    if ignorar_zeros_em is None:
        ignorar_zeros_em = []

    tipos_invalidos = [t for t in tipos if t not in _TIPOS_MISSING]
    if tipos_invalidos:
        raise ValueError(f"Tipos inválidos: {tipos_invalidos}. Use: {list(_TIPOS_MISSING.keys())}")

    series_list = []

    for t in tipos:
        s = _TIPOS_MISSING[t](df)

        if t == 'numeric' and ignorar_zeros_em and not s.empty:
            indices_para_remover = [col + ' (Valores Zero)' for col in ignorar_zeros_em]
            s = s[~s.index.isin(indices_para_remover)]

        series_list.append(s)

    series_list = [s for s in series_list if not s.empty]

    if not series_list:
        return pd.DataFrame(columns=['Quantidade', 'Incidência (%)'])

    resumo_bruto = pd.concat(series_list)
    resumo_filtrado = resumo_bruto[resumo_bruto > 0]

    if resumo_filtrado.empty:
        return pd.DataFrame(columns=['Quantidade', 'Incidência (%)'])

    return (
        pd.DataFrame({
            'Quantidade':     resumo_filtrado,
            'Incidência (%)': (resumo_filtrado / len(df)) * 100
        })
        .sort_values('Incidência (%)', ascending=False)
        .round(2)
    )


# =====================================================================
# AUDITORIA DE DUPLICIDADES PARCIAIS (MESMA EMPRESA + DATA)
# =====================================================================

def inspect_partial_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrupa registros com mesma empresa e mesma data em 1 linha comparativa
    e classifica o tipo de conflito para decisão de limpeza.
    """
    required = {
        'company', 
        'date', 
        'location', 
        'total_laid_off', 
        'percentage_laid_off', 
        'industry'
    }

    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"Colunas obrigatórias ausentes para auditoria: {missing}")

    dup_mask = df.duplicated(subset=['company', 'date'], keep=False)

    if not dup_mask.any():
        return pd.DataFrame(columns=[
            'company', 'date', 'qtd_linhas', 'cidades',
            'demitidos', 'percentual', 'setor', 'diagnostico', 'status'
        ])

    resumo = (
        df[dup_mask]
        .groupby(['company', 'date'], as_index=False)
        .agg(
            qtd_linhas=('company', 'count'),
            cidades=('location', lambda s: ' vs '.join(s.fillna('NaN').unique())),
            demitidos=(
                'total_laid_off',
                lambda s: ' vs '
                .join(
                    s.fillna(-1)
                    .astype(int)
                    .astype(str)
                    .unique()
                )
                .replace('-1', 'NaN')
            ),
            percentual=(
                'percentage_laid_off',
                lambda s: ' vs '
                .join(
                    s.round(4)
                    .fillna(-1)
                    .astype(str)
                    .unique()
                )
                .replace('-1.0', 'NaN')
            ),
            setor=('industry', 'first')
        )
    )

    def _classificar(row: pd.Series) -> tuple[str, str]:

        if ' vs ' in row['cidades']:
            return (
                'Cidades diferentes (Manter)', 
                '🟢 Cidades diferentes (Manter)'
            )
        
        if ' vs ' not in row['demitidos'] and ' vs ' not in row['percentual']:
            return (
                'Duplicata exata (Remover)', 
                '🔴 Duplicata exata (Remover)'
            )
        
        return (
            'Mesma cidade / dados divergentes', 
            '🟡 Mesma cidade / dados divergentes'
        )

    classificacoes = resumo.apply(_classificar, axis=1)
    resumo['diagnostico'] = [c[0] for c in classificacoes]
    resumo['status'] = [c[1] for c in classificacoes]

    return resumo.sort_values('status').reset_index(drop=True)