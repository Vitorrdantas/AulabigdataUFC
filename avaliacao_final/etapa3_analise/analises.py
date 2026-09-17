#!/usr/bin/env python3
"""
Avaliação Final — Etapa 3 · Análises sobre a Gold (e Silver, quando precisa do nível transação)

Pré-requisito: etapa2_bigdata/pipeline.py já executado (pasta bigdata_aval/ na raiz do repositório).
Uso: python3 avaliacao_final/etapa3_analise/analises.py

Saídas: resultados/A*.csv (uma tabela por análise) e resultados/resumo_analises.md
"""
import os
from pathlib import Path

import duckdb
from scipy.stats import chi2_contingency
from sklearn.metrics import roc_auc_score

BASE = Path(os.environ.get("BIGDATA_DIR", "bigdata_aval"))
OUT = Path(__file__).resolve().parent / "resultados"
OUT.mkdir(exist_ok=True)

con = duckdb.connect()
for t in ["gold_cubo_risco", "gold_serie_diaria", "gold_perfil_horario", "gold_segmento_score"]:
    con.sql(f"CREATE VIEW {t} AS SELECT * FROM read_parquet('{BASE / 'gold' / (t + '.parquet')}')")
con.sql(f"""CREATE VIEW silver AS SELECT * FROM read_parquet('{BASE}/silver/transactions/**/*.parquet',
            hive_partitioning = true)""")

# taxas SEMPRE recalculadas a partir das contagens (média de taxas estaria errada)
KPI = """
    SUM(transacoes)::INT                                          AS transacoes,
    ROUND(100.0 * SUM(transacoes) / SUM(SUM(transacoes)) OVER (), 1) AS pct_volume,
    SUM(fraudes)::INT                                             AS fraudes,
    ROUND(100.0 * SUM(fraudes) / SUM(SUM(fraudes)) OVER (), 1)    AS pct_fraudes,
    ROUND(100.0 * SUM(fraudes) / SUM(transacoes), 2)              AS taxa_fraude_pct,
    ROUND((SUM(fraudes) / SUM(transacoes)) / (SELECT SUM(fraudes) / SUM(transacoes) FROM gold_cubo_risco), 2) AS lift,
    ROUND(SUM(valor_fraude), 2)                                   AS valor_fraude
"""

md = ["# Resultados das análises (gerado por analises.py)\n",
      "Taxa = fraudes ÷ transações do grupo. Lift = taxa do grupo ÷ taxa geral (1,00 = igual à média).\n"]


def roda(codigo, titulo, sql):
    df = con.sql(sql).df()
    df.to_csv(OUT / f"{codigo}.csv", index=False)
    md.append(f"\n## {codigo} — {titulo}\n")
    md.append(df.to_markdown(index=False))
    md.append("")
    print(f"\n== {codigo} — {titulo}\n{df.to_string(index=False)}")
    return df


# ---------------------------------------------------------------- visão geral
roda("A0_visao_geral", "KPIs gerais", """
SELECT SUM(transacoes)::INT AS transacoes, SUM(fraudes)::INT AS fraudes,
       ROUND(100.0 * SUM(fraudes) / SUM(transacoes), 2) AS taxa_fraude_pct,
       ROUND(SUM(valor_total), 2) AS valor_total, ROUND(SUM(valor_fraude), 2) AS valor_fraude,
       ROUND(100.0 * SUM(valor_fraude) / SUM(valor_total), 2) AS pct_valor_fraudado,
       ROUND(SUM(valor_fraude) / SUM(fraudes), 2) AS ticket_medio_fraude,
       ROUND(SUM(valor_total) / SUM(transacoes), 2) AS ticket_medio_geral,
       SUM(recusadas)::INT AS recusadas, SUM(recusas_legitimas)::INT AS recusas_legitimas,
       ROUND(100.0 * SUM(recusas_legitimas) / SUM(recusadas), 1) AS pct_recusas_que_eram_legitimas,
       ROUND(100.0 * SUM(recusas_legitimas) / (SUM(transacoes) - SUM(fraudes)), 2) AS pct_legitimas_recusadas
FROM gold_cubo_risco""")

# ---------------------------------------------------------------- A1 segmento / score
roda("A1a_segmento", "Fraude por segmento",
     f"SELECT segment, {KPI} FROM gold_cubo_risco GROUP BY 1 ORDER BY taxa_fraude_pct DESC")
roda("A1b_credit_score", "Fraude por faixa de credit score",
     f"SELECT faixa_credit_score, {KPI} FROM gold_segmento_score GROUP BY 1 ORDER BY 1")
roda("A1c_segmento_credit_medio", "Credit score médio por segmento", """
SELECT segment, ROUND(SUM(soma_credit_score) / SUM(transacoes), 0) AS credit_score_medio
FROM gold_segmento_score GROUP BY 1 ORDER BY 1""")
roda("A1d_segmento_x_canal", "Segmento x canal", f"""
SELECT segment, channel, {KPI} FROM gold_cubo_risco GROUP BY 1, 2 ORDER BY taxa_fraude_pct DESC""")

# ---------------------------------------------------------------- A2 canal
roda("A2_canal", "Fraude por canal",
     f"SELECT channel, {KPI} FROM gold_cubo_risco GROUP BY 1 ORDER BY taxa_fraude_pct DESC")

# ---------------------------------------------------------------- A3 categoria
roda("A3a_categoria", "Fraude por categoria de estabelecimento",
     f"SELECT merchant_category, {KPI} FROM gold_cubo_risco GROUP BY 1 ORDER BY taxa_fraude_pct DESC")
roda("A3b_canal_x_categoria", "Canal x categoria (top 10 por taxa)", f"""
SELECT channel, merchant_category, {KPI} FROM gold_cubo_risco GROUP BY 1, 2
ORDER BY taxa_fraude_pct DESC LIMIT 10""")

# ---------------------------------------------------------------- A4 temporal
roda("A4a_periodo", "Fraude por período do dia",
     f"SELECT periodo_dia, {KPI} FROM gold_cubo_risco GROUP BY 1 ORDER BY taxa_fraude_pct DESC")
roda("A4b_hora", "Fraude por hora", f"""
SELECT hora, SUM(transacoes)::INT AS transacoes, SUM(fraudes)::INT AS fraudes,
       ROUND(100.0 * SUM(fraudes) / SUM(transacoes), 2) AS taxa_fraude_pct
FROM gold_perfil_horario GROUP BY 1 ORDER BY 1""")
roda("A4c_dia_semana", "Fraude por dia da semana", f"""
SELECT dia_semana_num, dia_semana, SUM(transacoes)::INT AS transacoes, SUM(fraudes)::INT AS fraudes,
       ROUND(100.0 * SUM(fraudes) / SUM(transacoes), 2) AS taxa_fraude_pct
FROM gold_perfil_horario GROUP BY 1, 2 ORDER BY 1""")
roda("A4d_mes", "Fraude por mês", f"""
SELECT month, SUM(transacoes)::INT AS transacoes, SUM(fraudes)::INT AS fraudes,
       ROUND(100.0 * SUM(fraudes) / SUM(transacoes), 2) AS taxa_fraude_pct,
       ROUND(SUM(valor_fraude), 2) AS valor_fraude
FROM gold_cubo_risco GROUP BY 1 ORDER BY 1""")
roda("A4e_app_viagem_madrugada", "Interação app+viagem x madrugada", f"""
SELECT (channel = 'app' AND merchant_category = 'viagem') AS app_viagem,
       (periodo_dia = 'madrugada') AS madrugada, {KPI}
FROM gold_cubo_risco GROUP BY 1, 2 ORDER BY 1, 2""")

# ---------------------------------------------------------------- A5 pergunta própria
# "O motor de risco atual (risk_score) está apontando para as transações certas?
#  Se a TechPay pedir autenticação extra para 20% das transações, qual critério pega mais fraude?"
roda("A5a_faixa_risk_score", "Fraude por faixa do risk_score atual",
     f"SELECT faixa_risk_score, {KPI} FROM gold_segmento_score GROUP BY 1 ORDER BY 1")

df = con.sql("SELECT is_fraud::INT AS y, risk_score, credit_score, amount FROM silver").df()
aucs = {c: round(roc_auc_score(df.y, df[c]), 3) for c in ["risk_score", "credit_score", "amount"]}
tab = con.sql("SELECT faixa_credit_score, SUM(fraudes), SUM(transacoes) - SUM(fraudes) FROM gold_segmento_score GROUP BY 1").fetchall()
p_credit = chi2_contingency([[a, b] for _, a, b in tab])[1]
md.append("\n## A5b — Poder de separação de cada variável numérica isolada (AUC; 0,50 = aleatório)\n")
md.append("| variável | AUC |\n|---|---|\n" + "\n".join(f"| {k} | {v} |" for k, v in aucs.items()))
md.append(f"\nTeste qui-quadrado fraude x faixa de credit score: p = {p_credit:.3f}\n")
print("\nAUCs:", aucs, "| p credit:", round(p_credit, 3))

REGRAS = {
    "R1 · risk_score >= 80 (motor atual)": "risk_score >= 80",
    "R2 · app + viagem": "channel = 'app' AND merchant_category = 'viagem'",
    "R3 · High-Risk no app": "segment = 'High-Risk' AND channel = 'app'",
    "R4 · todo High-Risk": "segment = 'High-Risk'",
    "R5 · High-Risk OU app+viagem": "segment = 'High-Risk' OR (channel = 'app' AND merchant_category = 'viagem')",
    "R6 · High-Risk OU app+viagem OU app na madrugada":
        "segment = 'High-Risk' OR (channel = 'app' AND merchant_category = 'viagem') "
        "OR (channel = 'app' AND periodo_dia = 'madrugada')",
}
uniao = " UNION ALL ".join(f"""
SELECT '{nome}' AS regra, COUNT(*) AS alertas,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM silver), 1) AS pct_volume_alertado,
       SUM(is_fraud::INT)::INT AS fraudes_capturadas,
       ROUND(100.0 * SUM(is_fraud::INT) / (SELECT SUM(is_fraud::INT) FROM silver), 1) AS pct_fraudes_capturadas,
       ROUND(100.0 * AVG(is_fraud::INT), 2) AS precisao_pct,
       SUM((NOT is_fraud)::INT)::INT AS legitimas_incomodadas
FROM silver WHERE {cond}""" for nome, cond in REGRAS.items())
roda("A5c_simulacao_regras", "Simulação de regras de autenticação extra", uniao + " ORDER BY regra")

(OUT / "resumo_analises.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print(f"\nResultados gravados em {OUT}")
