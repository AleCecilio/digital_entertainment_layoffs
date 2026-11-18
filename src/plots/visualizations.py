import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


# ===== Barplot Horizontal de Auditoria de Qualidade de Dados =====


def chart_data_quality(
    df_plot: pd.DataFrame,
    figure_size: tuple[float, float] | None = None,
    dpi: int = 150,
    width: float = 0.6,
    name_df: str | None = None,
    save_path: str | None = None
) -> None:
    """
    Gera um barplot horizontal para auditoria visual da qualidade dos
    dados, exibindo a count absoluta e o percentual de incidência
    das anomalias e dos dados absent identificados por check_data_quality().

    Parâmetros
    ----------
    df_plot : pd.DataFrame
        DataFrame com os resultados da auditoria de qualidade dos dados,
        contendo a coluna 'Incidência (%)' e, opcionalmente, 'Quantidade'.

    figure_size : tuple[float, float] | None, padrão=None
        Dimensões da figura em dpi (largura, altura). Se None,
        a altura é definida dinamicamente conforme a quantidade de barras.

    dpi : int, padrão=150
        Resolução da figura em DPI (dots per inch).

    width : float, padrão=0.6
        Largura relativa das barras no gráfico.

    name_df : str | None, padrão=None
        Nome opcional do DataFrame utilizado para complementar o título.

    save_path : str | None, padrão=None
        Caminho opcional para salvar o gráfico. Se None, a imagem não
        será salva em arquivo.

    Retorno
    -------
    None
        Exibe o gráfico e, opcionalmente, salva a imagem no caminho
        especificado. Se o DataFrame estiver vazio, informa que não
        há anomalias ou dados absent para plotar.
    """

    # Abortar se não houver anomalias ou dados absent para plotar
    if df_plot.empty:
        print("Nenhuma anomalia ou dado ausente encontrado para plotar.")
        return

    qtd_bars = len(df_plot)

    # Definir automaticamente a altura da figura
    if figure_size is None:
        if qtd_bars == 1:
            dynamic_height = 1.8
        elif qtd_bars <= 3:
            dynamic_height = 2.8
        else:
            dynamic_height = (qtd_bars * 0.5) + 2.0

        figure_size = (10, dynamic_height)

    plt.figure(figsize=figure_size, dpi=dpi)

    plt.gca().set_axisbelow(True)
    plt.grid(
        axis='x',
        linestyle='--',
        alpha=0.4,
        color='#9A8C98'
    )

    ax = sns.barplot(
        x='Incidência (%)',
        y=df_plot.index,
        data=df_plot,
        hue=df_plot.index,
        palette='Reds_r',
        legend=False,
        width=width
    )

    # Adicionar rótulos com quantidade absoluta e percentual
    if 'Quantidade' in df_plot.columns:
        labels = [
            f"{int(qtd):,}".replace(",", ".") + f" ({pct:.2f}%)"
            for qtd, pct in zip(
                df_plot['Quantidade'],
                df_plot['Incidência (%)']
            )
        ]

        if len(ax.containers) == 1:
            ax.bar_label(
                ax.containers[0],
                labels=labels,
                padding=6,
                fontsize=9.5,
                fontweight='semibold',
                color='#2B2D42'
            )
        else:
            for container, lbl in zip(ax.containers, labels):
                ax.bar_label(
                    container,
                    labels=[lbl],
                    padding=6,
                    fontsize=9.5,
                    fontweight='semibold',
                    color='#2B2D42'
                )

    # Definir o título conforme o nome do DataFrame
    title = (
        f'Auditoria de Qualidade de Dados — {name_df}'
        if name_df
        else 'Auditoria de Qualidade de Dados'
    )

    plt.title(
        title,
        fontsize=14,
        fontweight='bold',
        color='#2B2D42',
        pad=18
    )

    plt.xlabel(
        'Incidência (%)',
        fontsize=11,
        fontweight='semibold',
        color='#4A4E69'
    )

    plt.ylabel(
        'Atributo / Regra Auditada',
        fontsize=11,
        fontweight='semibold',
        color='#4A4E69'
    )

    # Reservar espaço para os rótulos sem cortar o texto
    plt.xlim(0, df_plot['Incidência (%)'].max() * 1.22)

    sns.despine(left=True, bottom=True)
    plt.tight_layout()

    if save_path:
        plt.savefig(
            save_path,
            dpi=300,
            bbox_inches='tight'
        )

    plt.show()


    

# ===== Barplot Horizontal de Classificação de Duplicidades Parciais =====


def chart_partial_duplicates(
    df_resumo: pd.DataFrame,
    figure_size: tuple[float, float] = (9, 3.0),
    dpi: int = 150,
    name_df: str | None = None,
    save_path: str | None = None
) -> None:
    """
    Gera um barplot horizontal resumindo a classificação dos grupos
    de duplicidade parcial identificados por inspect_partial_duplicates().

    Parâmetros
    ----------
    df_resumo : pd.DataFrame
        DataFrame com os resultados da inspeção de duplicidades parciais,
        contendo a coluna 'diagnostico' com a classificação dos grupos.

    figure_size : tuple[float, float], padrão=(9, 3.0)
        Dimensões da figura em dpi (largura, altura).

    dpi : int, padrão=150
        Resolução da figura em DPI (dots per inch).

    name_df : str | None, padrão=None
        Nome opcional do DataFrame utilizado para complementar o título.

    save_path : str | None, padrão=None
        Caminho opcional para salvar o gráfico. Se None, a imagem não
        será salva em arquivo.

    Retorno
    -------
    None
        Exibe o gráfico e, opcionalmente, salva a imagem no caminho
        especificado. Se o DataFrame estiver vazio, informa que não
        há duplicidades parciais para plotar.
    """

    # Abortar se não houver duplicidades parciais para plotar
    if df_resumo.empty:
        print("Nenhuma duplicidade parcial encontrada para plotar.")
        return

    # Calcular a quantidade e o percentual por classificação
    count = (
        df_resumo['diagnostico']
        .value_counts()
        .reset_index()
    )

    count.columns = ['diagnostico', 'Quantidade']

    count['Incidência (%)'] = (
        count['Quantidade'] / len(df_resumo)
    ) * 100

    # Definir cores conforme a classificação dos grupos
    semantic_palette = {
        'Duplicata exata (Remover)': '#D90429',
        'Mesma cidade / dados divergentes': '#F4A261',
        'Cidades diferentes (Manter)': '#2A9D8F'
    }

    plt.figure(figsize=figure_size, dpi=dpi)

    plt.gca().set_axisbelow(True)
    plt.grid(
        axis='x',
        linestyle='--',
        alpha=0.4,
        color='#9A8C98'
    )

    ax = sns.barplot(
        x='Quantidade',
        y='diagnostico',
        data=count,
        hue='diagnostico',
        palette=semantic_palette,
        legend=False,
        width=0.55
    )

    # Adicionar rótulos com quantidade de grupos e percentual
    labels = [
        f"{int(qtd)} grupos ({pct:.1f}%)"
        for qtd, pct in zip(
            count['Quantidade'],
            count['Incidência (%)']
        )
    ]

    if len(ax.containers) == 1:
        ax.bar_label(
            ax.containers[0],
            labels=labels,
            padding=6,
            fontsize=9.5,
            fontweight='bold',
            color='#2B2D42'
        )
    else:
        for container, lbl in zip(ax.containers, labels):
            ax.bar_label(
                container,
                labels=[lbl],
                padding=6,
                fontsize=9.5,
                fontweight='bold',
                color='#2B2D42'
            )

    # Definir o título conforme o nome do DataFrame
    title = (
        f'Diagnóstico de Duplicidades Parciais — {name_df}'
        if name_df
        else 'Diagnóstico de Duplicidades Parciais (Empresa + Data)'
    )

    plt.title(
        title,
        fontsize=13,
        fontweight='bold',
        color='#2B2D42',
        pad=16
    )

    plt.xlabel(
        'Quantidade de Grupos Suspeitos',
        fontsize=10.5,
        fontweight='bold',
        color='#4A4E69'
    )

    plt.ylabel(
        'Classificação',
        fontsize=10.5,
        fontweight='bold',
        color='#4A4E69'
    )

    # Reservar espaço para os rótulos das barras
    plt.xlim(0, count['Quantidade'].max() * 1.32)

    sns.despine(left=True, bottom=True)
    plt.tight_layout()

    if save_path:
        plt.savefig(
            save_path,
            dpi=300,
            bbox_inches='tight'
        )

    plt.show()




# ===== Barplot Horizontal de Completude das Métricas Por Categoria =====

def chart_completeness_profile(
    df_plot: pd.DataFrame,
    figure_size: tuple[float, float] = (12, 6),
    dpi: int = 150,
    percentage: bool = False,
    dataframe_name: str | None = None,
    save_path: str | None = None
) -> None:
    """
    Gera um gráfico de barras horizontais empilhadas para visualizar
    a completude das métricas de layoff por categoria.

    Parâmetros
    ----------
    df_plot : pd.DataFrame
        Tabela cruzada gerada por cross_tabulation_sector_company(),
        contendo os perfis de completude nas linhas e as categorias
        analisadas nas colunas.

    figure_size : tuple[float, float], padrão=(12, 6)
        Dimensões da figura em polegadas (largura, altura).

    dpi : int, padrão=150
        Resolução da figura em pontos por polegada.

    percentage : bool, padrão=False
        Indica se a tabela contém valores percentuais. Se True,
        remove o símbolo '%' e converte os valores para numéricos.

    dataframe_name : str | None, padrão=None
        Nome opcional do DataFrame utilizado para compor o título.

    save_path : str | None, padrão=None
        Caminho opcional para salvar o gráfico.

    Retorno
    -------
    None
        Exibe o gráfico e, opcionalmente, salva a imagem no caminho
        especificado.
    """

    if df_plot.empty:
        print("Nenhum dado disponível para visualização.")
        return

    # Remover a linha e a coluna de total geral, se presentes
    plot_data = df_plot.drop(
        index='Total Geral',
        errors='ignore'
    ).drop(
        columns='Total Geral',
        errors='ignore'
    ).copy()

    # Converter os valores percentuais para números
    if percentage:
        plot_data = plot_data.map(
            lambda value: (
                float(str(value).replace('%', ''))
                if pd.notna(value) else 0
            )
        )

    # Transpor a tabela para exibir as categorias no eixo vertical
    plot_data = plot_data.T

    # Definir as cores para cada perfil de completude
    semantic_palette = {
        '1. Ambas preenchidas (Total + %)': '#2A9D8F',
        '2. Apenas total_laid_off (% nulo)': '#457B9D',
        '3. Apenas percentage_laid_off (Total nulo)': '#F4A261',
        '4. Ambas nulas (Sem métricas)': '#D90429'
    }

    colors = [
        semantic_palette.get(column, '#9A8C98')
        for column in plot_data.columns
    ]

    fig, ax = plt.subplots(
        figsize=figure_size,
        dpi=dpi
    )

    # Gerar o gráfico de barras horizontais empilhadas
    plot_data.plot(
        kind='barh',
        stacked=True,
        ax=ax,
        color=colors,
        width=0.65
    )

    ax.set_axisbelow(True)
    ax.grid(
        axis='x',
        linestyle='--',
        alpha=0.4,
        color='#9A8C98'
    )

    # Definir o título conforme o nome informado
    title = (
        f'Completude das Métricas de Layoff — {dataframe_name}'
        if dataframe_name
        else 'Completude das Métricas de Layoff'
    )

    ax.set_title(
        title,
        fontsize=13,
        fontweight='bold',
        color='#2B2D42',
        pad=16
    )

    ax.set_xlabel(
        'Percentual (%)' if percentage else 'Quantidade de Registros',
        fontsize=10.5,
        fontweight='bold',
        color='#4A4E69'
    )

    ax.set_ylabel(
        df_plot.columns.name or 'Categoria',
        fontsize=10.5,
        fontweight='bold',
        color='#4A4E69'
    )

    # Limitar o eixo horizontal a 100% quando a tabela for percentual
    if percentage:
        ax.set_xlim(0, 100)

    ax.legend(
        title='Perfil de Completude',
        bbox_to_anchor=(1.02, 1),
        loc='upper left',
        frameon=False
    )

    sns.despine(left=True, bottom=True)
    plt.tight_layout()

    # Salvar o gráfico caso um caminho seja informado
    if save_path:
        plt.savefig(
            save_path,
            dpi=300,
            bbox_inches='tight'
        )

    plt.show()

