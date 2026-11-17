import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


# ===== Barplot Horizontal de Auditoria de Qualidade de Dados =====

def chart_data_quality(
    df_plot: pd.DataFrame,
    tamanho_figura: tuple[float, float] | None = None,
    polegadas: int = 150,
    width: float = 0.6,
    nome_dataframe: str | None = None,
    save_path: str | None = None
) -> None:
    """
    Gera um barplot horizontal focado em auditoria visual de qualidade (QA),
    exibindo contagem absoluta e percentual de incidência gerados por check_data_quality().
    """
    # Trava de Segurança: Aborta se não houver anomalias/ausências para plotar
    if df_plot.empty:
        print("Nenhuma anomalia ou dado ausente encontrado para plotar.")
        return

    qtd_barras = len(df_plot)

    # Otimização Automática de Altura
    if tamanho_figura is None:
        if qtd_barras == 1:
            altura_dinamica = 1.8
        elif qtd_barras <= 3:
            altura_dinamica = 2.8
        else:
            altura_dinamica = (qtd_barras * 0.5) + 2.0

        tamanho_figura = (10, altura_dinamica)

    plt.figure(figsize=tamanho_figura, dpi=polegadas)

    plt.gca().set_axisbelow(True)
    plt.grid(axis='x', linestyle='--', alpha=0.4, color='#9A8C98')

    ax = sns.barplot(
        x='Incidência (%)',
        y=df_plot.index,
        data=df_plot,
        hue=df_plot.index,
        palette='Reds_r',
        legend=False,
        width=width
    )

    # Rótulos combinando Quantidade Absoluta e Percentual (se 'Quantidade' existir)
    if 'Quantidade' in df_plot.columns:
        labels = [
            f"{int(qtd):,}".replace(",", ".") + f" ({pct:.2f}%)"
            for qtd, pct in zip(df_plot['Quantidade'], df_plot['Incidência (%)'])
        ]
        # Quando há múltiplas barras com hue, cada container guarda 1 barra (ou todas em 1 container)
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

    # Tratamento dinâmico de Título
    titulo = (
        f'Auditoria de Qualidade de Dados — {nome_dataframe}'
        if nome_dataframe
        else 'Auditoria de Qualidade de Dados'
    )

    plt.title(
        titulo,
        fontsize=14,
        fontweight='bold',
        color='#2B2D42',
        pad=18
    )

    plt.xlabel('Incidência (%)', fontsize=11, fontweight='semibold', color='#4A4E69')
    plt.ylabel('Atributo / Regra Auditada', fontsize=11, fontweight='semibold', color='#4A4E69')

    # Folga de 22% no eixo X para acomodar "Qtd (XX.XX%)" sem cortar
    plt.xlim(0, df_plot['Incidência (%)'].max() * 1.22)

    sns.despine(left=True, bottom=True)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    plt.show()