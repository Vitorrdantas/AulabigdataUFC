#!/usr/bin/env python3
"""
Avaliação Final — Etapa 2 · Pipeline de Big Data (TechPay)
Rota B (sem admin): DuckDB + Parquet particionado, executado no WSL2/Ubuntu.

Etapas:
  1. Ingestão            -> bigdata_aval/raw/transactions/        (CSV imutável)
  2. Tabela raw          -> schema explícito + captura de linhas rejeitadas
  3. Particionamento     -> bigdata_aval/raw_particionada/        (Parquet, year/month)
  4. Bronze              -> bigdata_aval/bronze/transactions/     (Parquet, year/month)
                            bigdata_aval/bronze/quarentena/       (linhas reprovadas + motivo)
  5. Silver              -> bigdata_aval/silver/transactions/     (Parquet, year/month)
  6. Gold                -> bigdata_aval/gold/*.parquet           (4 tabelas agregadas)

Uso:
  python3 generate_avaliacao_dataset.py          # gera /tmp/avaliacao_transactions.csv
  python3 pipeline.py [caminho_do_csv]           # padrão: /tmp/avaliacao_transactions.csv

Toda contagem de linhas é gravada em evidencias/execucao_log.txt.
"""
import hashlib
import os
import shutil
import sys
from pathlib import Path

import duckdb

CSV_ORIGEM = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/avaliacao_transactions.csv")
BASE = Path(os.environ.get("BIGDATA_DIR", "bigdata_aval"))
AQUI = Path(__file__).resolve().parent
LOG = Path(os.environ.get("PIPELINE_LOG", AQUI / "evidencias" / "execucao_log.txt"))

RAW_DIR = BASE / "raw" / "transactions"
RAWP_DIR = BASE / "raw_particionada" / "transactions"
BRONZE_DIR = BASE / "bronze" / "transactions"
QUAR_DIR = BASE / "bronze" / "quarentena"
SILVER_DIR = BASE / "silver" / "transactions"
GOLD_DIR = BASE / "gold"

LOG.parent.mkdir(parents=True, exist_ok=True)
_log = open(LOG, "w", encoding="utf-8")


def log(msg=""):
    print(msg)
    _log.write(str(msg) + "\n")


def mostra(con, sql, titulo=None):
    """Executa uma consulta e grava o resultado tabular no log."""
    if titulo:
        log(f"\n-- {titulo}")
    rel = con.sql(sql)
    df = rel.df()
    log(df.to_string(index=False))
    return df


def recria(path: Path):
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


con = duckdb.connect()
log("=" * 78)
log("PIPELINE TECHPAY — Rota B (DuckDB " + duckdb.__version__ + ")")
log("=" * 78)

# ---------------------------------------------------------------------------
# 1. INGESTÃO — copia o arquivo para a landing zone raw, sem alterar nada
# ---------------------------------------------------------------------------
log("\n[1] INGESTÃO")
if not CSV_ORIGEM.exists():
    sys.exit(f"Arquivo de origem não encontrado: {CSV_ORIGEM}. Rode generate_avaliacao_dataset.py antes.")
recria(RAW_DIR)
destino = RAW_DIR / CSV_ORIGEM.name
shutil.copy2(CSV_ORIGEM, destino)
md5_origem = hashlib.md5(CSV_ORIGEM.read_bytes()).hexdigest()
md5_destino = hashlib.md5(destino.read_bytes()).hexdigest()
linhas_arquivo = sum(1 for _ in open(destino, encoding="utf-8")) - 1  # sem cabeçalho
log(f"origem : {CSV_ORIGEM}  ({CSV_ORIGEM.stat().st_size:,} bytes)")
log(f"destino: {destino}")
log(f"MD5 origem = {md5_origem} | MD5 destino = {md5_destino} | íntegro = {md5_origem == md5_destino}")
log(f"linhas de dados no arquivo (sem cabeçalho): {linhas_arquivo:,}")

# ---------------------------------------------------------------------------
# 2. TABELA RAW — schema explícito; is_fraud fica como texto (lição dos Labs 2/4/5)
#    Linhas que não obedecem ao schema vão para reject_errors, não derrubam a carga.
# ---------------------------------------------------------------------------
log("\n[2] TABELA RAW (schema explícito)")
con.sql(f"""
CREATE OR REPLACE TABLE raw_transactions AS
SELECT * FROM read_csv('{destino}',
    header = true,
    columns = {{
        'transaction_id':    'INTEGER',
        'customer_id':       'INTEGER',
        'amount':            'DOUBLE',
        'transaction_type':  'VARCHAR',
        'channel':           'VARCHAR',
        'merchant_category': 'VARCHAR',
        'timestamp':         'TIMESTAMP',
        'status':            'VARCHAR',
        'risk_score':        'DOUBLE',
        'segment':           'VARCHAR',
        'credit_score':      'INTEGER',
        'is_fraud':          'VARCHAR'
    }},
    store_rejects = true
)
""")
mostra(con, "DESCRIBE raw_transactions", "schema da raw")
n_raw = con.sql("SELECT COUNT(*) FROM raw_transactions").fetchone()[0]
n_rej = con.sql("SELECT COUNT(*) FROM reject_errors").fetchone()[0]
log(f"\nlinhas carregadas na raw: {n_raw:,} | linhas rejeitadas pelo schema: {n_rej:,}")
mostra(con, "SELECT is_fraud, COUNT(*) AS n FROM raw_transactions GROUP BY 1 ORDER BY 1",
       "valores textuais de is_fraud na origem")

# ---------------------------------------------------------------------------
# 3. PARTICIONAMENTO — Parquet particionado por ano/mês do timestamp
# ---------------------------------------------------------------------------
log("\n[3] PARTICIONAMENTO (year / month)")
recria(RAWP_DIR)
con.sql(f"""
COPY (
    SELECT *, YEAR("timestamp") AS year, MONTH("timestamp") AS month
    FROM raw_transactions
) TO '{RAWP_DIR}' (FORMAT PARQUET, PARTITION_BY (year, month), OVERWRITE_OR_IGNORE)
""")
mostra(con, f"""
SELECT year, month, COUNT(*) AS linhas
FROM read_parquet('{RAWP_DIR}/**/*.parquet', hive_partitioning = true)
GROUP BY ALL ORDER BY ALL""", "linhas por partição")
pastas = sorted((p.relative_to(BASE).as_posix() for p in RAWP_DIR.glob("year=*/month=*")),
                key=lambda s: int(s.rsplit("=", 1)[1]))
log(f"\n{len(pastas)} pastas de partição criadas, ex.: {pastas[0]} ... {pastas[-1]}")

# Evidência de partition pruning: um filtro por mês só abre 1 dos 12 diretórios
plano = con.sql(f"""
EXPLAIN SELECT COUNT(*) FROM read_parquet('{RAWP_DIR}/**/*.parquet', hive_partitioning = true)
WHERE year = 2025 AND month = 3""").fetchall()[0][1]
arquivos_lidos = [l for l in plano.splitlines() if "File" in l or "Filters" in l or "Files" in l]
log("plano (trecho) do filtro month=3: " + " | ".join(s.strip(" │") for s in arquivos_lidos))

# ---------------------------------------------------------------------------
# 4. BRONZE — padroniza, tipa, remove duplicatas e reprova valores impossíveis
# ---------------------------------------------------------------------------
log("\n[4] BRONZE (limpeza)")
con.sql(f"""
CREATE OR REPLACE TABLE stg AS
SELECT
    transaction_id,
    customer_id,
    ROUND(amount, 2)                         AS amount,
    LOWER(TRIM(transaction_type))            AS transaction_type,
    LOWER(TRIM(channel))                     AS channel,
    LOWER(TRIM(merchant_category))           AS merchant_category,
    "timestamp"                              AS ts,
    LOWER(TRIM(status))                      AS status,
    ROUND(risk_score, 2)                     AS risk_score,
    TRIM(segment)                            AS segment,
    credit_score,
    CASE WHEN LOWER(TRIM(is_fraud)) IN ('true', '1')  THEN TRUE
         WHEN LOWER(TRIM(is_fraud)) IN ('false', '0') THEN FALSE
         ELSE NULL END                       AS is_fraud,
    year, month,
    -- 4a. duplicata = mesmo transaction_id; mantém a primeira ocorrência cronológica
    ROW_NUMBER() OVER (PARTITION BY transaction_id ORDER BY "timestamp") AS ordem_id,
    -- 4b. duplicata "disfarçada" = mesma transação com outro id (todas as colunas iguais)
    ROW_NUMBER() OVER (PARTITION BY customer_id, amount, transaction_type, channel,
                       merchant_category, "timestamp", status, risk_score
                       ORDER BY transaction_id) AS ordem_conteudo
FROM read_parquet('{RAWP_DIR}/**/*.parquet', hive_partitioning = true)
""")

REGRAS = {
    "id_nulo":               "transaction_id IS NULL OR customer_id IS NULL",
    "duplicata_id":          "ordem_id > 1",
    "duplicata_conteudo":    "ordem_conteudo > 1",
    "valor_invalido":        "amount IS NULL OR amount <= 0 OR amount > 40000",
    "timestamp_invalido":    "ts IS NULL OR ts < TIMESTAMP '2025-01-01' OR ts >= TIMESTAMP '2026-01-01'",
    "tipo_fora_dominio":     "transaction_type NOT IN ('compra','saque','transferencia','pagamento') OR transaction_type IS NULL",
    "canal_fora_dominio":    "channel NOT IN ('app','web','pos','atm') OR channel IS NULL",
    "categoria_fora_dominio":"merchant_category NOT IN ('varejo','viagem','eletronico','alimentacao','servicos','saude') OR merchant_category IS NULL",
    "status_fora_dominio":   "status NOT IN ('approved','declined') OR status IS NULL",
    "segmento_fora_dominio": "segment NOT IN ('Premium','Standard','High-Risk') OR segment IS NULL",
    "risk_score_invalido":   "risk_score IS NULL OR risk_score < 0 OR risk_score > 100",
    "credit_score_invalido": "credit_score IS NULL OR credit_score < 300 OR credit_score > 900",
    "cliente_fora_faixa":    "customer_id < 1 OR customer_id > 8000",
    "rotulo_invalido":       "is_fraud IS NULL",
}
motivo_sql = "CONCAT_WS(';', " + ", ".join(
    f"CASE WHEN {cond} THEN '{nome}' END" for nome, cond in REGRAS.items()) + ")"
con.sql(f"CREATE OR REPLACE TABLE stg_avaliada AS SELECT *, {motivo_sql} AS motivo FROM stg")

log("reprovações por regra (uma linha pode cair em mais de uma):")
for nome, cond in REGRAS.items():
    n = con.sql(f"SELECT COUNT(*) FROM stg WHERE {cond}").fetchone()[0]
    log(f"  {nome:<24} {n:>6,}")

COLUNAS_BRONZE = """transaction_id, customer_id, amount, transaction_type, channel, merchant_category,
    ts, status, risk_score, segment, credit_score, is_fraud"""

con.sql(f"""
CREATE OR REPLACE TABLE bronze_transactions AS
SELECT {COLUNAS_BRONZE},
    -- sinalizações de qualidade: a linha é válida, mas o analista precisa saber
    (amount = 5.00)                                   AS flag_valor_no_piso,
    (credit_score IN (300, 900))                      AS flag_score_no_limite,
    (is_fraud AND status = 'approved')                AS flag_fraude_aprovada,
    year, month
FROM stg_avaliada WHERE motivo = ''
""")
con.sql(f"CREATE OR REPLACE TABLE bronze_quarentena AS SELECT {COLUNAS_BRONZE}, motivo FROM stg_avaliada WHERE motivo <> ''")

recria(BRONZE_DIR)
recria(QUAR_DIR)
con.sql(f"COPY bronze_transactions TO '{BRONZE_DIR}' (FORMAT PARQUET, PARTITION_BY (year, month), OVERWRITE_OR_IGNORE)")
con.sql(f"COPY bronze_quarentena TO '{QUAR_DIR}/quarentena.parquet' (FORMAT PARQUET)")

n_bronze = con.sql("SELECT COUNT(*) FROM bronze_transactions").fetchone()[0]
n_quar = con.sql("SELECT COUNT(*) FROM bronze_quarentena").fetchone()[0]
log(f"\nraw_particionada: {n_raw:,} | bronze: {n_bronze:,} | quarentena: {n_quar:,} | descartadas: {n_raw - n_bronze:,}")
mostra(con, """
SELECT SUM(flag_valor_no_piso::INT)::INT   AS valor_no_piso_R5,
       SUM(flag_score_no_limite::INT)::INT AS credit_score_300_ou_900,
       SUM(flag_fraude_aprovada::INT)::INT AS fraude_com_status_aprovado
FROM bronze_transactions""", "sinalizações de qualidade mantidas na bronze")
mostra(con, """
SELECT is_fraud, status, COUNT(*) AS n FROM bronze_transactions GROUP BY ALL ORDER BY ALL
""", "cruzamento rótulo x status (checa vazamento)")
mostra(con, """
SELECT COUNT(DISTINCT customer_id) AS clientes,
       COUNT(DISTINCT customer_id) FILTER (WHERE n_seg > 1) AS clientes_com_mais_de_um_segmento
FROM (SELECT customer_id, COUNT(DISTINCT segment) AS n_seg FROM bronze_transactions GROUP BY 1)
""", "consistência do segmento por cliente")
mostra(con, """
SELECT COUNT(DISTINCT MINUTE(ts)) AS minutos_distintos, COUNT(DISTINCT SECOND(ts)) AS segundos_distintos
FROM bronze_transactions""", "granularidade do timestamp")

# ---------------------------------------------------------------------------
# 5. SILVER — enriquecimento com colunas de análise
# ---------------------------------------------------------------------------
log("\n[5] SILVER (enriquecimento)")
con.sql("""
CREATE OR REPLACE TABLE silver_transactions AS
SELECT
    b.transaction_id, b.customer_id, b.amount, b.transaction_type,
    b.channel, b.merchant_category, b.ts, b.status, b.risk_score,
    b.segment, b.credit_score, b.is_fraud,
    CAST(b.ts AS DATE)                                   AS data,
    b.year, b.month,
    HOUR(b.ts)                                           AS hora,
    ISODOW(b.ts)                                         AS dia_semana_num,   -- 1 = segunda
    CASE ISODOW(b.ts) WHEN 1 THEN 'seg' WHEN 2 THEN 'ter' WHEN 3 THEN 'qua'
         WHEN 4 THEN 'qui' WHEN 5 THEN 'sex' WHEN 6 THEN 'sab' ELSE 'dom' END AS dia_semana,
    -- convenção fixa, definida antes de olhar a fraude: madrugada = 00:00 a 05:59
    CASE WHEN HOUR(b.ts) < 6  THEN 'madrugada'
         WHEN HOUR(b.ts) < 12 THEN 'manha'
         WHEN HOUR(b.ts) < 18 THEN 'tarde'
         ELSE 'noite' END                                AS periodo_dia,
    CASE WHEN b.credit_score < 500 THEN '1_baixo (300-499)'
         WHEN b.credit_score < 700 THEN '2_medio (500-699)'
         ELSE '3_alto (700-900)' END                     AS faixa_credit_score,
    CASE WHEN b.risk_score < 60 THEN '1_baixo (<60)'
         WHEN b.risk_score < 80 THEN '2_medio (60-79)'
         ELSE '3_alto (>=80)' END                        AS faixa_risk_score,
    b.status = 'declined'                                AS recusada
FROM bronze_transactions b
""")
recria(SILVER_DIR)
con.sql(f"COPY silver_transactions TO '{SILVER_DIR}' (FORMAT PARQUET, PARTITION_BY (year, month), OVERWRITE_OR_IGNORE)")
n_silver = con.sql("SELECT COUNT(*) FROM silver_transactions").fetchone()[0]
log(f"bronze: {n_bronze:,} | silver: {n_silver:,} (nenhum JOIN com perda — a base já traz segment/credit_score)")
mostra(con, "SELECT periodo_dia, COUNT(*) n FROM silver_transactions GROUP BY 1 ORDER BY 1", "distribuição periodo_dia")
log(f"colunas da silver: {len(con.sql('DESCRIBE silver_transactions').fetchall())}")
mostra(con, "SELECT faixa_risk_score, COUNT(*) n FROM silver_transactions GROUP BY 1 ORDER BY 1", "distribuição faixa_risk_score")

# ---------------------------------------------------------------------------
# 6. GOLD — agregados prontos para a Etapa 3 (contagens e somas; taxas são
#    recalculadas no BI a partir das contagens, para poderem ser re-agregadas)
# ---------------------------------------------------------------------------
log("\n[6] GOLD (agregações)")
recria(GOLD_DIR)
METRICAS = """
    COUNT(*)                                          AS transacoes,
    SUM(is_fraud::INT)                                AS fraudes,
    SUM(recusada::INT)                                AS recusadas,
    SUM((recusada AND NOT is_fraud)::INT)             AS recusas_legitimas,
    ROUND(SUM(amount), 2)                             AS valor_total,
    ROUND(SUM(CASE WHEN is_fraud THEN amount ELSE 0 END), 2) AS valor_fraude
"""
GOLD = {
    # cubo principal: alimenta KPIs, composição, filtros e a tabela de detalhe
    "gold_cubo_risco": f"""
        SELECT year, month, channel, merchant_category, segment, periodo_dia, {METRICAS}
        FROM silver_transactions GROUP BY ALL""",
    # tendência: série diária por canal
    "gold_serie_diaria": f"""
        SELECT data, channel, {METRICAS}
        FROM silver_transactions GROUP BY ALL""",
    # padrão temporal fino: hora x dia da semana
    "gold_perfil_horario": f"""
        SELECT hora, dia_semana_num, dia_semana, {METRICAS}
        FROM silver_transactions GROUP BY ALL""",
    # segmentação: segmento x faixa de credit score x faixa do risk score atual
    "gold_segmento_score": f"""
        SELECT segment, faixa_credit_score, faixa_risk_score, {METRICAS},
               ROUND(SUM(credit_score), 0) AS soma_credit_score
        FROM silver_transactions GROUP BY ALL""",
}
for nome, sql in GOLD.items():
    con.sql(f"CREATE OR REPLACE TABLE {nome} AS {sql}")
    con.sql(f"COPY {nome} TO '{GOLD_DIR / (nome + '.parquet')}' (FORMAT PARQUET)")
    linhas, tx = con.sql(f"SELECT COUNT(*), SUM(transacoes) FROM {nome}").fetchone()
    log(f"  {nome:<22} {linhas:>5,} linhas | soma de transacoes = {tx:,} (deve ser {n_silver:,})")

mostra(con, """
SELECT segment, SUM(transacoes)::INT transacoes, SUM(fraudes)::INT fraudes,
       ROUND(100.0 * SUM(fraudes) / SUM(transacoes), 2) AS taxa_fraude_pct,
       SUM(valor_fraude) valor_fraude
FROM gold_cubo_risco GROUP BY 1 ORDER BY taxa_fraude_pct DESC""", "conferência da gold por segmento")

# ---------------------------------------------------------------------------
# Resumo final
# ---------------------------------------------------------------------------
log("\n" + "=" * 78)
log("RESUMO DO FUNIL DE LINHAS")
log(f"  arquivo CSV ............ {linhas_arquivo:,}")
log(f"  raw .................... {n_raw:,}  (rejeitadas pelo schema: {n_rej:,})")
log(f"  raw_particionada ....... {n_raw:,}  em {len(pastas)} partições")
log(f"  bronze ................. {n_bronze:,}  (quarentena: {n_quar:,})")
log(f"  silver ................. {n_silver:,}")
log(f"  gold ................... {len(GOLD)} tabelas")
log("Arquivos gerados:")
for camada in ["raw", "raw_particionada", "bronze/transactions", "bronze/quarentena", "silver", "gold"]:
    arqs = list((BASE / camada).rglob("*.*"))
    tam = sum(a.stat().st_size for a in arqs)
    log(f"  {camada:<20} {len(arqs):>3} arquivo(s)  {tam/1024:>9,.0f} KB")
log("=" * 78)
_log.close()
