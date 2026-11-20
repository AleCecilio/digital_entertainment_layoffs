-- ============================================================================
-- SCRIPT 04: CAMADA ANALÍTICA DE VIEWS (POSTGRESQL -> PYTHON / POWER BI)
-- Projeto: Digital Entertainment Layoffs (2020–2026)
-- ============================================================================

-- 1. Evolução Temporal por Ano, Trimestre e Subsegmento (Consumer vs. Media)
CREATE OR REPLACE VIEW vw_evolucao_temporal AS
SELECT
    year,
    quarter,
    industry AS subsegment,
    COUNT(*) AS total_events,
    COUNT(total_laid_off) AS events_with_headcount,
    COALESCE(SUM(total_laid_off), 0) AS total_laid_off,
    ROUND(AVG(total_laid_off), 1) AS avg_laid_off,
    ROUND(
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_laid_off)::NUMERIC,
        1
    ) AS median_laid_off,
    ROUND(AVG(percentage_laid_off) * 100, 2) AS avg_percentage_cut,
    SUM(CASE WHEN is_company_shutdown THEN 1 ELSE 0 END) AS shutdown_events
FROM layoffs
WHERE sector_scope = 'Digital Entertainment'
GROUP BY year, quarter, industry
ORDER BY year ASC, quarter ASC, industry ASC;


-- 2. Comparação Consolidada entre Subsegmentos (Consumer vs. Media)
CREATE OR REPLACE VIEW vw_comparacao_subsegmentos AS
SELECT
    industry AS subsegment,
    COUNT(*) AS total_events,
    COUNT(DISTINCT company) AS unique_companies,
    COALESCE(SUM(total_laid_off), 0) AS total_laid_off,
    ROUND(AVG(total_laid_off), 1) AS avg_laid_off,
    ROUND(
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_laid_off)::NUMERIC,
        1
    ) AS median_laid_off,
    ROUND(AVG(percentage_laid_off) * 100, 2) AS avg_percentage_cut,
    ROUND(
        (PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY percentage_laid_off) * 100)::NUMERIC,
        2
    ) AS median_percentage_cut,
    ROUND(AVG(funds_raised), 2) AS avg_funds_raised_millions,
    ROUND(
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY funds_raised)::NUMERIC,
        2
    ) AS median_funds_raised_millions,
    SUM(CASE WHEN is_company_shutdown THEN 1 ELSE 0 END) AS total_shutdowns
FROM layoffs
WHERE sector_scope = 'Digital Entertainment'
GROUP BY industry
ORDER BY total_laid_off DESC;


-- 3. Análise Geográfica por País e Polo Urbano (Location)
CREATE OR REPLACE VIEW vw_analise_geografica AS
SELECT
    COALESCE(country, 'Unknown') AS country,
    COALESCE(location, 'Unknown') AS location,
    COUNT(*) AS total_events,
    COUNT(DISTINCT company) AS unique_companies,
    COALESCE(SUM(total_laid_off), 0) AS total_laid_off,
    ROUND(AVG(total_laid_off), 1) AS avg_laid_off,
    ROUND(AVG(percentage_laid_off) * 100, 2) AS avg_percentage_cut,
    SUM(CASE WHEN is_company_shutdown THEN 1 ELSE 0 END) AS shutdown_events
FROM layoffs
WHERE sector_scope = 'Digital Entertainment'
GROUP BY COALESCE(country, 'Unknown'), COALESCE(location, 'Unknown')
ORDER BY total_laid_off DESC, total_events DESC;


-- 4. Perfil por Estágio Corporativo (Stage)
CREATE OR REPLACE VIEW vw_perfil_estagio_empresas AS
SELECT
    COALESCE(stage, 'Unknown') AS stage,
    COUNT(*) AS total_events,
    COUNT(DISTINCT company) AS unique_companies,
    COALESCE(SUM(total_laid_off), 0) AS total_laid_off,
    ROUND(AVG(total_laid_off), 1) AS avg_laid_off,
    ROUND(
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_laid_off)::NUMERIC,
        1
    ) AS median_laid_off,
    ROUND(AVG(percentage_laid_off) * 100, 2) AS avg_percentage_cut,
    ROUND(
        (PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY percentage_laid_off) * 100)::NUMERIC,
        2
    ) AS median_percentage_cut,
    ROUND(COALESCE(AVG(funds_raised), 0), 2) AS avg_funds_raised_millions,
    SUM(CASE WHEN is_company_shutdown THEN 1 ELSE 0 END) AS total_shutdowns
FROM layoffs
WHERE sector_scope = 'Digital Entertainment'
GROUP BY COALESCE(stage, 'Unknown')
ORDER BY total_laid_off DESC, total_events DESC;


-- 5. Ranking das Top 15 Empresas / Estúdios Mais Afetados
CREATE OR REPLACE VIEW vw_top15_empresas AS
SELECT
    RANK() OVER (ORDER BY COALESCE(SUM(total_laid_off), 0) DESC) AS rank_position,
    company,
    MAX(industry) AS subsegment,
    MAX(country) AS country,
    MAX(stage) AS stage,
    COUNT(*) AS layoff_rounds,
    COALESCE(SUM(total_laid_off), 0) AS total_laid_off,
    ROUND(AVG(percentage_laid_off) * 100, 2) AS avg_percentage_cut,
    BOOL_OR(is_company_shutdown) AS is_shutdown
FROM layoffs
WHERE sector_scope = 'Digital Entertainment'
  AND total_laid_off IS NOT NULL
GROUP BY company
ORDER BY total_laid_off DESC
LIMIT 15;

/*
================================================================================
OBSERVAÇÕES ANALÍTICAS — CONSOLIDAÇÃO DAS VIEWS (CONSUMER VS. MEDIA)
================================================================================
1. Contraste estrutural entre subsegmentos: Consumer possui quase o dobro de 
   eventos de Media (322 contra 164), mas 7,6 vezes mais demitidos (100.625 
   contra 13.197). A mediana de demitidos por evento em Consumer (130,0) é mais 
   de 2,5 vezes superior à de Media (51,0), embora a severidade percentual 
   mediana seja próxima (17,00% contra 15,00%).
   
2. Consumo analítico: As 5 views criadas (vw_evolucao_temporal, 
   vw_comparacao_subsegmentos, vw_analise_geografica, vw_perfil_estagio_empresas 
   e vw_top15_empresas) encapsulam tendência central (média/mediana), severidade 
   e concentração para alimentação direta do notebook 02_eda_analysis.ipynb e 
   dos dashboards em Power BI.
================================================================================
*/