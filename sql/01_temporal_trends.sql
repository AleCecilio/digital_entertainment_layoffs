-- ============================================================================
-- SCRIPT 01: TENDÊNCIAS TEMPORAIS E COMPARATIVO ENTRE SUBSEGMENTOS
-- Projeto: Digital Entertainment Layoffs (2020–2026)
-- Banco: PostgreSQL
-- ============================================================================

-- 1. Evolução anual consolidada: Frequência de Eventos vs. Volume de Demitidos
WITH yearly_metrics AS (
    SELECT
        year,
        industry AS subsegment,
        COUNT(*) AS total_events,
        COUNT(total_laid_off) AS events_with_headcount,
        COALESCE(SUM(total_laid_off), 0) AS total_employees_laid_off,
        ROUND(AVG(total_laid_off), 1) AS avg_laid_off_per_event,
        ROUND(
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_laid_off)::NUMERIC,
            1
        ) AS median_laid_off,
        SUM(CASE WHEN is_company_shutdown THEN 1 ELSE 0 END) AS shutdown_events
    FROM layoffs
    WHERE sector_scope = 'Digital Entertainment'
    GROUP BY year, industry
)
SELECT
    year,
    subsegment,
    total_events,
    events_with_headcount,
    ROUND((events_with_headcount::NUMERIC / NULLIF(total_events, 0)) * 100, 1) AS headcount_coverage_pct,
    total_employees_laid_off,
    avg_laid_off_per_event,
    median_laid_off,
    shutdown_events,
    total_employees_laid_off - LAG(total_employees_laid_off) OVER (
        PARTITION BY subsegment
        ORDER BY year
    ) AS yoy_headcount_diff
FROM yearly_metrics
ORDER BY year ASC, subsegment ASC;

-- 2. Série trimestral (Quarter) para detecção de ondas de demissão
SELECT
    quarter,
    year,
    COUNT(*) AS total_events,
    COALESCE(SUM(total_laid_off), 0) AS total_employees_laid_off,
    ROUND(AVG(percentage_laid_off) * 100, 2) AS avg_percentage_cut,
    SUM(CASE WHEN industry = 'Consumer' THEN 1 ELSE 0 END) AS consumer_events,
    SUM(CASE WHEN industry = 'Media' THEN 1 ELSE 0 END) AS media_events
FROM layoffs
WHERE sector_scope = 'Digital Entertainment'
GROUP BY quarter, year
ORDER BY year ASC, quarter ASC;

-- 3. Série mensal (Year-Month) para granularidade fina de picos
SELECT
    year_month,
    COUNT(*) AS total_events,
    COALESCE(SUM(total_laid_off), 0) AS total_employees_laid_off,
    SUM(CASE WHEN is_company_shutdown THEN 1 ELSE 0 END) AS shutdown_events
FROM layoffs
WHERE sector_scope = 'Digital Entertainment'
GROUP BY year_month
ORDER BY year_month ASC;

/*
================================================================================
OBSERVAÇÕES ANALÍTICAS — TENDÊNCIAS TEMPORAIS (2020–2026)
================================================================================
1. Onda principal (2022Q4–2023Q1): O pico agudo do setor ocorreu na virada de 
   2022Q4 (17.244 demitidos) para 2023Q1 (29.242 demitidos em 58 eventos). Apenas 
   nov/2022 (16.020), jan/2023 (13.754) e mar/2023 (11.944) somam 41.718 cortes.
   
2. Assimetria Consumer vs. Media: Em 2023, Consumer registrou 81 eventos (30.403 
   demitidos; média 691,0 vs. mediana 87,5), evidenciando forte distorção por 
   mega-layoffs. Media teve 47 eventos (5.641 demitidos; média 170,9 vs. 
   mediana 60,0), caracterizando cortes mais pulverizados.
   
3. Arrefecimento e repique em 2026: Após recuar em 2024 (13.184) e 2025 (10.359), 
   o volume voltou a acelerar em 2026 (21.623 demitidos até novembro), puxado 
   por Consumer (19.715 demitidos, com pico em maio/2026 de 8.520 pessoas).
   
4. Anomalia de 2021: Apenas 9 eventos totais no ano, com média e mediana 
   infladas em Consumer (1.800,0) devido à baixa cobertura de divulgação (50%).
================================================================================
*/