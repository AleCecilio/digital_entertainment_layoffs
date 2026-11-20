-- ============================================================================
-- SCRIPT 03: CONCENTRAÇÃO CORPORATIVA (TOP EMPRESAS) E GEOGRÁFICA
-- Projeto: Digital Entertainment Layoffs (2020–2026)
-- Banco: PostgreSQL
-- ============================================================================

-- 1. Top 15 empresas com maior volume acumulado de demissões no Entretenimento Digital
WITH company_ranking AS (
    SELECT
        company,
        MAX(industry) AS primary_subsegment,
        MAX(country) AS country,
        MAX(stage) AS latest_stage,
        COUNT(*) AS layoff_rounds,
        COALESCE(SUM(total_laid_off), 0) AS total_employees_laid_off,
        ROUND(AVG(percentage_laid_off) * 100, 2) AS avg_pct_cut,
        BOOL_OR(is_company_shutdown) AS ever_shutdown,
        MIN(date) AS first_event_date,
        MAX(date) AS last_event_date
    FROM layoffs
    WHERE sector_scope = 'Digital Entertainment'
      AND total_laid_off IS NOT NULL
    GROUP BY company
)
SELECT
    RANK() OVER (ORDER BY total_employees_laid_off DESC) AS rank_position,
    company,
    primary_subsegment,
    country,
    latest_stage,
    layoff_rounds,
    total_employees_laid_off,
    ROUND(
        (total_employees_laid_off::NUMERIC / SUM(total_employees_laid_off) OVER ()) * 100,
        2
    ) AS share_of_sector_headcount_pct,
    ROUND(
        (SUM(total_employees_laid_off) OVER (
            ORDER BY total_employees_laid_off DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        )::NUMERIC / SUM(total_employees_laid_off) OVER ()) * 100,
        2
    ) AS cumulative_pareto_pct,
    avg_pct_cut,
    ever_shutdown
FROM company_ranking
ORDER BY total_employees_laid_off DESC
LIMIT 15;

-- 2. Distribuição geográfica por País (Eventos vs. Volume de Desligados)
SELECT
    country,
    COUNT(*) AS total_events,
    COUNT(DISTINCT company) AS unique_companies,
    COALESCE(SUM(total_laid_off), 0) AS total_employees_laid_off,
    ROUND(
        (COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER ()) * 100,
        2
    ) AS share_of_events_pct,
    ROUND(
        (COALESCE(SUM(total_laid_off), 0)::NUMERIC /
         NULLIF(SUM(COALESCE(SUM(total_laid_off), 0)) OVER (), 0)) * 100,
        2
    ) AS share_of_headcount_pct,
    SUM(CASE WHEN is_company_shutdown THEN 1 ELSE 0 END) AS shutdown_count
FROM layoffs
WHERE sector_scope = 'Digital Entertainment'
GROUP BY country
ORDER BY total_employees_laid_off DESC, total_events DESC
LIMIT 15;

-- 3. Top 10 polos urbanos (Location + Country)
SELECT
    location,
    country,
    COUNT(*) AS total_events,
    COALESCE(SUM(total_laid_off), 0) AS total_employees_laid_off
FROM layoffs
WHERE sector_scope = 'Digital Entertainment'
GROUP BY location, country
ORDER BY total_employees_laid_off DESC, total_events DESC
LIMIT 10;

/*
================================================================================
OBSERVAÇÕES ANALÍTICAS — CONCENTRAÇÃO CORPORATIVA E GEOGRÁFICA
================================================================================
1. Concentração de Pareto nas Big Techs: As Top 15 empresas acumulam 70,53% de 
   todos os demitidos do setor (80.278 de 113.822). Somente Meta (35.700 em 9 
   rodadas; 31,36%) e Google (13.749 em 11 rodadas; 12,08%) concentram 43,44% 
   de toda a força de trabalho desligada, apesar de cortes percentuais médios 
   baixos (6,20% e 6,00%).
   
2. Reincidência de rodadas: Nenhuma empresa do Top 15 encerrou operações, mas 
   quase todas passaram por múltiplos ciclos de corte (Google: 11 rodadas; 
   Meta: 9; TikTok: 7; Bytedance, Playtika e Spotify: 6 cada).
   
3. Hegemonia dos EUA e da SF Bay Area: Os Estados Unidos concentram 65,64% dos 
   eventos (319) e 77,71% dos demitidos (88.448), além de 25 dos 36 shutdowns 
   totais. Na escala urbana, apenas a SF Bay Area responde por 69.203 demitidos 
   (>60% do setor), seguida por Los Angeles (5.589), New York City (4.088), 
   Bengaluru (3.991) e Stockholm (3.570).
================================================================================
*/