-- ============================================================================
-- SCRIPT 02: SEVERIDADE DOS CORTES, ESTÁGIO DAS EMPRESAS E ENCERRAMENTOS
-- Projeto: Digital Entertainment Layoffs (2020–2026)
-- Banco: PostgreSQL
-- ============================================================================

-- 1. Severidade e volume por estágio da empresa (Post-IPO vs. Series A-D vs. Seed)
SELECT
    COALESCE(stage, 'Unknown') AS company_stage,
    COUNT(*) AS total_events,
    COUNT(DISTINCT company) AS unique_companies,
    COALESCE(SUM(total_laid_off), 0) AS total_employees_laid_off,
    ROUND(AVG(total_laid_off), 1) AS avg_headcount_cut,
    ROUND(AVG(percentage_laid_off) * 100, 2) AS avg_pct_cut,
    ROUND(
        (PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY percentage_laid_off) * 100)::NUMERIC,
        2
    ) AS median_pct_cut,
    SUM(CASE WHEN is_company_shutdown THEN 1 ELSE 0 END) AS total_shutdowns,
    ROUND(COALESCE(AVG(funds_raised), 0), 2) AS avg_funds_raised_millions
FROM layoffs
WHERE sector_scope = 'Digital Entertainment'
GROUP BY COALESCE(stage, 'Unknown')
HAVING COUNT(*) >= 3
ORDER BY total_employees_laid_off DESC, total_events DESC;

-- 2. Distribuição por escala do layoff (layoff_scale) e subsegmento
SELECT
    industry AS subsegment,
    COALESCE(layoff_scale, 'Unreported') AS layoff_scale,
    COUNT(*) AS total_events,
    ROUND(
        (COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER (PARTITION BY industry)) * 100,
        2
    ) AS share_within_subsegment_pct,
    COALESCE(SUM(total_laid_off), 0) AS total_employees_laid_off
FROM layoffs
WHERE sector_scope = 'Digital Entertainment'
GROUP BY industry, COALESCE(layoff_scale, 'Unreported')
ORDER BY subsegment ASC, total_events DESC;

-- 3. Auditoria de qualidade: Completude das métricas e lag de registro
SELECT
    metric_completeness,
    COUNT(*) AS total_events,
    ROUND((COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER ()) * 100, 2) AS pct_of_dataset,
    ROUND(AVG(reporting_lag_days), 1) AS avg_reporting_lag_days,
    MIN(reporting_lag_days) AS min_lag_days,
    MAX(reporting_lag_days) AS max_lag_days
FROM layoffs
WHERE sector_scope = 'Digital Entertainment'
GROUP BY metric_completeness
ORDER BY total_events DESC;

/*
================================================================================
OBSERVAÇÕES ANALÍTICAS — SEVERIDADE, ESTÁGIOS E QUALIDADE DOS DADOS
================================================================================

1. Paradoxo Volume vs. Severidade por Estágio: Empresas Post-IPO concentram 
   65,9% do volume total de demitidos (75.056 pessoas em 145 eventos), mas têm 
   a menor severidade relativa (média 13,08%; mediana 10,50%) e zero shutdowns. 
   Em contraste, estágios iniciais sofrem cortes existenciais: Seed (mediana de 
   100,00% e 9 shutdowns em 18 eventos) e Series A (mediana de 90,00% e 4 
   shutdowns em 12 eventos).
   
2. Concentração na cauda longa (Massive Outliers): Em Consumer, apenas 41 
   eventos (>440 demitidos; 12,73% do subsegmento) respondem por 78.530 
   desligamentos (>78% do volume de Consumer). Em Media, predominam cortes 
   pequenos (Small 1–50 representa 33,54% dos eventos).
   
3. Completude e Latência: Apenas 40,74% da base (198 eventos) informa tanto 
   headcount quanto percentual. Cerca de um terço dos eventos em ambos os 
   subsegmentos não divulga o total absoluto de demitidos (Not Reported: 33,85% 
   em Consumer e 32,32% em Media). O lag médio de registro varia entre 6,5 e 
   18,1 dias, com atualizações retroativas pontuais de até 1.155 dias.
================================================================================
*/