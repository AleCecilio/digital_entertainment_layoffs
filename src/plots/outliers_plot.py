import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
import seaborn as sns


def radar_chart_outliers(
    df_diagnostico: pd.DataFrame,
    cor_tema: str = '#4A4E69',
    titulo: str = "Impacto de Outliers por Métrica"
) -> None:
    """Gera gráfico de barras horizontais ranqueando a incidência de outliers por coluna."""
    if df_diagnostico.empty:
        print("Nenhum outlier encontrado para exibir.")
        return

    df_plot = df_diagnostico.sort_values(by='Impacto (% Válidos)', ascending=True)
    altura = max(2.2, len(df_plot) * 0.75 + 1.2)
    fig, ax = plt.subplots(figsize=(9.5, altura), dpi=130)

    bars = ax.barh(
        df_plot['Coluna'],
        df_plot['Impacto (% Válidos)'],
        color=cor_tema,
        alpha=0.88,
        height=0.55
    )
    max_val = df_plot['Impacto (% Válidos)'].max()

    for bar in bars:
        val = bar.get_width()
        ax.text(
            val + max_val * 0.015,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.2f}%",
            va='center',
            ha='left',
            fontsize=9.5,
            fontweight='bold',
            color='#2b2d42'
        )

    ax.set_title(titulo, fontsize=12.5, fontweight='bold', pad=12, color='#2b2d42')
    ax.set_xlabel('Incidência sobre Registros Válidos (%)', fontsize=10, fontweight='bold', color='#4A4E69')
    ax.set_xlim(0, max_val * 1.18)
    ax.set_axisbelow(True)
    ax.grid(axis='x', linestyle='--', alpha=0.4, color='#BDBDBD')
    sns.despine(top=True, right=True)
    plt.tight_layout()
    plt.show()


def outlier_plot(
    df_plot: pd.DataFrame,
    coluna: str,
    cerca_superior: float,
    cerca_inferior: float | None = None,
    cor_tema: str = '#4A4E69',
    titulo: str | None = None,
    usar_log: bool = False,
    eh_percentual: bool = False
) -> None:
    """Gera gráfico composto (Boxplot + Stripplot) evidenciando dispersão e fronteiras IQR."""
    serie = df_plot[coluna].dropna()
    if serie.empty:
        print(f"Sem dados válidos para '{coluna}'.")
        return

    fig, ax = plt.subplots(figsize=(9.5, 3.6), dpi=130)
    ax.set_axisbelow(True)
    ax.grid(axis='x', linestyle='--', alpha=0.4, color='#BDBDBD')

    if usar_log:
        serie_plot = serie[serie > 0]
        ax.set_xscale('log')
        ax.xaxis.set_minor_locator(ticker.NullLocator())
    else:
        serie_plot = serie
        fmt = '{x:.0%}' if eh_percentual else '{x:,.0f}'
        ax.xaxis.set_major_formatter(ticker.StrMethodFormatter(fmt))

    sns.boxplot(
        x=serie_plot,
        ax=ax,
        color=cor_tema,
        width=0.45,
        fliersize=0,
        linewidth=1.4,
        boxprops=dict(alpha=0.28)
    )
    sns.stripplot(
        x=serie_plot,
        ax=ax,
        color=cor_tema,
        size=3.2,
        alpha=0.35,
        jitter=0.22
    )

    lbl_sup = f"Cerca Sup. ({cerca_superior:.1%})" if eh_percentual else f"Cerca Sup. ({cerca_superior:,.1f})"
    ax.axvline(cerca_superior, color='#E63946', linestyle='--', linewidth=1.8, label=lbl_sup)

    if cerca_inferior is not None and cerca_inferior > 0:
        lbl_inf = f"Cerca Inf. ({cerca_inferior:.1%})" if eh_percentual else f"Cerca Inf. ({cerca_inferior:,.1f})"
        ax.axvline(cerca_inferior, color='#E63946', linestyle=':', linewidth=1.8, label=lbl_inf)

    nome_limpo = coluna.replace('_', ' ').title()
    ax.set_title(titulo or f"Distribuição de {nome_limpo} e Limites IQR", fontsize=12.5, fontweight='bold', pad=12, color='#2b2d42')
    ax.set_xlabel(f"{nome_limpo} (Escala Log)" if usar_log else nome_limpo, fontsize=10, fontweight='bold', color='#4A4E69')
    ax.legend(loc='upper right', frameon=True, edgecolor='#E0E0E0', facecolor='white', fontsize=9.5)
    sns.despine(left=True)
    ax.yaxis.set_visible(False)
    plt.tight_layout()
    plt.show()


def validation_scatter_plot(
    df: pd.DataFrame,
    coluna_x: str,
    coluna_y: str,
    hue_col: str | None = 'sector_scope',
    titulo: str | None = None,
    usar_log_x: bool = True,
    usar_log_y: bool = True
) -> None:
    """Gera scatter plot para validação cruzada de extremos entre duas métricas numéricas."""
    df_valid = df.dropna(subset=[coluna_x, coluna_y])
    if usar_log_x:
        df_valid = df_valid[df_valid[coluna_x] > 0]
    if usar_log_y:
        df_valid = df_valid[df_valid[coluna_y] > 0]

    fig, ax = plt.subplots(figsize=(9.5, 5), dpi=130)
    ax.set_axisbelow(True)
    ax.grid(True, linestyle='--', alpha=0.4, color='#BDBDBD')

    sns.scatterplot(
        data=df_valid,
        x=coluna_x,
        y=coluna_y,
        hue=hue_col if hue_col in df_valid.columns else None,
        palette=['#E63946', '#4A4E69'] if hue_col else None,
        alpha=0.65,
        s=45,
        edgecolor='white',
        linewidth=0.4,
        ax=ax
    )

    if usar_log_x:
        ax.set_xscale('log')
    if usar_log_y:
        ax.set_yscale('log')

    nome_x = coluna_x.replace('_', ' ').title()
    nome_y = coluna_y.replace('_', ' ').title()
    ax.set_title(titulo or f"Validação Cruzada: {nome_x} vs. {nome_y}", fontsize=12.5, fontweight='bold', pad=12, color='#2b2d42')
    ax.set_xlabel(f"{nome_x} {'(Log)' if usar_log_x else ''}", fontsize=10, fontweight='bold', color='#4A4E69')
    ax.set_ylabel(f"{nome_y} {'(Log)' if usar_log_y else ''}", fontsize=10, fontweight='bold', color='#4A4E69')
    sns.despine(top=True, right=True)
    plt.tight_layout()
    plt.show()