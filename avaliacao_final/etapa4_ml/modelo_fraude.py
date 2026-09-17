#!/usr/bin/env python3
"""
Avaliação Final — Bônus · Regressão Logística para is_fraud (PySpark local, Rota B)

Pré-requisito: etapa2_bigdata/pipeline.py executado (bigdata_aval/silver/ na raiz do repositório).
Uso: python3 avaliacao_final/etapa4_ml/modelo_fraude.py

Decisões:
  - status NÃO entra como variável: 100% das fraudes estão 'declined' (vazamento do rótulo).
  - Variáveis categóricas viram dummies com categoria de referência explícita, para que
    cada coeficiente se leia como "risco em relação à referência".
  - regParam = 0 (sem regularização) para os coeficientes serem interpretáveis; os p-valores
    vêm do GLM binomial (mesmo modelo, com erros-padrão).
"""
import math
import os
from pathlib import Path

import matplotlib
import matplotlib.ticker
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pyspark.ml import Pipeline
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.evaluation import BinaryClassificationEvaluator
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.functions import vector_to_array
from pyspark.ml.regression import GeneralizedLinearRegression
from pyspark.sql import SparkSession, functions as F

BASE = Path(os.environ.get("BIGDATA_DIR", "bigdata_aval")).resolve()
OUT = Path(__file__).resolve().parent / "resultados"
OUT.mkdir(exist_ok=True)
linhas_log = []


def log(msg=""):
    print(msg)
    linhas_log.append(str(msg))


spark = (SparkSession.builder.appName("avaliacao_ml").master("local[*]")
         .config("spark.sql.shuffle.partitions", "8").getOrCreate())
spark.sparkContext.setLogLevel("ERROR")

df = spark.read.option("basePath", str(BASE / "silver/transactions")) \
          .parquet(str(BASE / "silver/transactions"))
log(f"Linhas lidas da Silver: {df.count():,}")

# ------------------------------------------------------------------ features
# referência: segment=Premium, channel=pos, merchant_category=varejo,
#             transaction_type=compra, fora da madrugada
DUMMIES = {
    "seg_high_risk": F.col("segment") == "High-Risk",
    "seg_standard": F.col("segment") == "Standard",
    "canal_app": F.col("channel") == "app",
    "canal_web": F.col("channel") == "web",
    "canal_atm": F.col("channel") == "atm",
    "cat_viagem": F.col("merchant_category") == "viagem",
    "cat_saude": F.col("merchant_category") == "saude",
    "cat_alimentacao": F.col("merchant_category") == "alimentacao",
    "cat_servicos": F.col("merchant_category") == "servicos",
    "cat_eletronico": F.col("merchant_category") == "eletronico",
    "tipo_saque": F.col("transaction_type") == "saque",
    "tipo_transferencia": F.col("transaction_type") == "transferencia",
    "tipo_pagamento": F.col("transaction_type") == "pagamento",
    "madrugada": F.col("periodo_dia") == "madrugada",
}
NUMERICAS = {
    "risk_score_10pts": F.col("risk_score") / 10,       # efeito de +10 pontos
    "credit_score_100pts": F.col("credit_score") / 100,  # efeito de +100 pontos
    "log_valor": F.log(F.col("amount")),                 # efeito de dobrar o valor = coef * ln(2)
}
for nome, expr in {**DUMMIES, **NUMERICAS}.items():
    df = df.withColumn(nome, expr.cast("double"))
df = df.withColumn("label", F.col("is_fraud").cast("double"))
FEATURES = list(DUMMIES) + list(NUMERICAS)

train, test = df.randomSplit([0.8, 0.2], seed=42)
n_tr, n_te = train.count(), test.count()
f_tr = train.agg(F.sum("label")).first()[0]
f_te = test.agg(F.sum("label")).first()[0]
log(f"Treino: {n_tr:,} linhas ({int(f_tr)} fraudes) | Teste: {n_te:,} linhas ({int(f_te)} fraudes)")

assembler = VectorAssembler(inputCols=FEATURES, outputCol="features")
lr = LogisticRegression(featuresCol="features", labelCol="label", regParam=0.0, maxIter=200)
modelo = Pipeline(stages=[assembler, lr]).fit(train)

# ------------------------------------------------------------------ avaliação
pred = modelo.transform(test).withColumn("p_fraude", vector_to_array("probability")[1])
roc = BinaryClassificationEvaluator(labelCol="label", rawPredictionCol="p_fraude", metricName="areaUnderROC")
pr = BinaryClassificationEvaluator(labelCol="label", rawPredictionCol="p_fraude", metricName="areaUnderPR")
auc_modelo, aupr_modelo = roc.evaluate(pred), pr.evaluate(pred)
roc_rs = BinaryClassificationEvaluator(labelCol="label", rawPredictionCol="risk_score", metricName="areaUnderROC")
pr_rs = BinaryClassificationEvaluator(labelCol="label", rawPredictionCol="risk_score", metricName="areaUnderPR")
auc_rs, aupr_rs = roc_rs.evaluate(pred), pr_rs.evaluate(pred)
taxa_base = f_te / n_te
log("\nDesempenho no TESTE (dados que o modelo não viu)")
log(f"  AUC-ROC  modelo = {auc_modelo:.3f} | só risk_score atual = {auc_rs:.3f} | aleatório = 0.500")
log(f"  AUC-PR   modelo = {aupr_modelo:.3f} | só risk_score atual = {aupr_rs:.3f} | aleatório = {taxa_base:.3f}")


def captura_top(col, frac):
    k = int(round(n_te * frac))
    fr = pred.orderBy(F.col(col).desc(), F.col("transaction_id")).limit(k).agg(F.sum("label")).first()[0]
    return k, int(fr), 100 * fr / f_te, 100 * fr / k


log("\nSe a TechPay revisar só as X% transações mais suspeitas do teste:")
log(f"  {'fatia':>6} | {'modelo: fraudes (recall / precisão)':<38} | risk_score atual: fraudes (recall / precisão)")
tabela_captura = []
for frac in [0.05, 0.10, 0.20]:
    k, fm, rm, pm = captura_top("p_fraude", frac)
    _, fr, rr, prr = captura_top("risk_score", frac)
    tabela_captura.append((frac, k, fm, rm, pm, fr, rr, prr))
    log(f"  {frac:>5.0%}  | {fm:>4} ({rm:5.1f}% / {pm:5.2f}%){'':<17} | {fr:>4} ({rr:5.1f}% / {prr:5.2f}%)   [{k} transações]")

# ------------------------------------------------------------------ coeficientes
lr_model = modelo.stages[-1]
glm = GeneralizedLinearRegression(family="binomial", link="logit", featuresCol="features",
                                  labelCol="label", maxIter=50).fit(assembler.transform(train))
resumo = glm.summary
pvals, eps = resumo.pValues, resumo.coefficientStandardErrors

log("\nCoeficientes (treino) — odds ratio = exp(coef); referência: Premium, pos, varejo, compra, fora da madrugada")
log(f"  {'variável':<22}{'coef':>9}{'odds ratio':>12}{'IC95% OR':>20}{'p-valor':>10}")
linhas_coef = []
for nome, c_lr, c_glm, se, p in zip(FEATURES, lr_model.coefficients, glm.coefficients, eps, pvals):
    orr = math.exp(c_glm)
    ic = (math.exp(c_glm - 1.96 * se), math.exp(c_glm + 1.96 * se))
    linhas_coef.append((nome, c_glm, orr, ic[0], ic[1], p, c_lr))
    log(f"  {nome:<22}{c_glm:>9.3f}{orr:>12.2f}{f'[{ic[0]:.2f} ; {ic[1]:.2f}]':>20}{p:>10.4f}")
log(f"  {'intercepto':<22}{glm.intercept:>9.3f}")
dif = max(abs(r[1] - r[6]) for r in linhas_coef)
log(f"(maior diferença entre coeficientes do LogisticRegression e do GLM: {dif:.4f} — mesmo modelo)")

with open(OUT / "coeficientes.csv", "w", encoding="utf-8") as f:
    f.write("variavel,coeficiente,odds_ratio,ic95_inf,ic95_sup,p_valor\n")
    for nome, c, orr, a, b, p, _ in linhas_coef:
        f.write(f"{nome},{c:.4f},{orr:.4f},{a:.4f},{b:.4f},{p:.6f}\n")
with open(OUT / "captura_top.csv", "w", encoding="utf-8") as f:
    f.write("fatia,transacoes_revisadas,fraudes_modelo,recall_modelo_pct,precisao_modelo_pct,"
            "fraudes_risk_score,recall_risk_score_pct,precisao_risk_score_pct\n")
    for r in tabela_captura:
        f.write(",".join(f"{x:.4f}" if isinstance(x, float) else str(x) for x in r) + "\n")

# gráfico dos odds ratios (paleta: azul escuro = aumenta risco significativo, verde escuro = reduz, cinza = n.s.)
ordem = sorted(linhas_coef, key=lambda r: r[2])
fig, ax = plt.subplots(figsize=(8, 6.5), dpi=150)
for i, (nome, c, orr, a, b, p, _) in enumerate(ordem):
    cor = "#9AA5B1" if p >= 0.05 else ("#0B2E59" if orr > 1 else "#1E5631")
    ax.plot([a, b], [i, i], color=cor, lw=2)
    ax.plot(orr, i, "o", color=cor, ms=7)
ax.axvline(1, color="#B8860B", ls="--", lw=1.2)
ax.set_xscale("log")
ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
ax.set_xticks([0.5, 1, 2, 3, 5, 10, 15], ["0,5", "1", "2", "3", "5", "10", "15"])
from matplotlib.lines import Line2D
ax.legend(handles=[Line2D([], [], color="#0B2E59", marker="o", label="aumenta a chance (p < 0,05)"),
                   Line2D([], [], color="#1E5631", marker="o", label="reduz a chance (p < 0,05)"),
                   Line2D([], [], color="#9AA5B1", marker="o", label="sem efeito significativo"),
                   Line2D([], [], color="#B8860B", ls="--", label="1 = sem efeito")],
          loc="lower right", fontsize=8.5, frameon=False)
ax.set_yticks(range(len(ordem)), [r[0] for r in ordem])
ax.set_xlabel("Odds ratio (escala log) — IC 95%")
ax.set_title("Regressão logística — efeito de cada variável na chance de fraude", fontsize=11)
ax.grid(axis="x", alpha=.3)
for s in ["top", "right"]:
    ax.spines[s].set_visible(False)
plt.tight_layout()
plt.savefig(OUT / "odds_ratios.png")

(OUT / "metricas_log.txt").write_text("\n".join(linhas_log) + "\n", encoding="utf-8")
spark.stop()
