#!/usr/bin/env python3
"""
Teste de sanidade das regras da Bronze.

A base oficial (avaliacao_transactions.csv) é limpa por construção, então a Bronze
oficial não reprova nenhuma linha. Para provar que as regras funcionam, este script
cria uma CÓPIA da base com 12 linhas propositalmente sujas, roda o mesmo pipeline.py
num diretório separado (bigdata_teste/) e confere se cada linha suja foi tratada.
Nada aqui altera os números oficiais.
"""
import csv, os, shutil, subprocess, sys
from pathlib import Path
import duckdb

AQUI = Path(__file__).resolve().parent
ORIGEM = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/avaliacao_transactions.csv")
SUJO = Path("/tmp/avaliacao_transactions_SUJO.csv")
BASE_TESTE = Path("bigdata_teste")
LOG = AQUI / "evidencias" / "teste_regras_bronze_log.txt"

linhas = list(csv.DictReader(open(ORIGEM, encoding="utf-8")))
campos = list(linhas[0].keys())
modelo = dict(linhas[0])

def nova(tid, **mud):
    r = dict(modelo); r["transaction_id"] = str(tid)
    r["risk_score"] = f"{tid % 97}.5"  # garante conteúdo distinto entre as linhas injetadas
    r.update(mud); return r

sujas = [
    # (linha, resultado esperado)
    (dict(linhas[10]),                                              "duplicata_id"),
    (nova(900002, **{k: linhas[20][k] for k in campos if k != "transaction_id"}), "duplicata_conteudo"),
    (nova(900003, amount="-150.00"),                                "valor_invalido"),
    (nova(900004, amount="0"),                                      "valor_invalido"),
    (nova(900005, risk_score="150"),                                "risk_score_invalido"),
    (nova(900006, credit_score="1000"),                             "credit_score_invalido"),
    (nova(900007, timestamp="2024-06-10 10:00:00"),                 "timestamp_invalido"),
    (nova(900008, channel="whatsapp"),                              "canal_fora_dominio"),
    (nova(900009, is_fraud="talvez"),                               "rotulo_invalido"),
    (nova(900010, customer_id="0"),                                 "cliente_fora_faixa"),
    (nova(900011, channel=" APP ", merchant_category="Viagem"),     "ACEITA (normalizada p/ app / viagem)"),
    (nova(900012, amount="abc"),                                    "rejeitada no schema da raw"),
]
with open(SUJO, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=campos); w.writeheader()
    w.writerows(linhas); w.writerows(r for r, _ in sujas)

if BASE_TESTE.exists():
    shutil.rmtree(BASE_TESTE)
env = dict(os.environ, BIGDATA_DIR=str(BASE_TESTE), PIPELINE_LOG="/tmp/pipeline_teste_log.txt")
subprocess.run([sys.executable, str(AQUI / "pipeline.py"), str(SUJO)], env=env, check=True,
               stdout=subprocess.DEVNULL)

con = duckdb.connect()
out = []
out.append(f"Linhas no CSV de teste: {len(linhas) + len(sujas):,} ({len(linhas):,} oficiais + {len(sujas)} sujas)")
q = con.sql(f"SELECT transaction_id, motivo FROM read_parquet('{BASE_TESTE}/bronze/quarentena/quarentena.parquet') ORDER BY 1").fetchall()
quar = {}
for tid, motivo in q:
    quar.setdefault(tid, []).append(motivo)
bronze = con.sql(f"SELECT COUNT(*) FROM read_parquet('{BASE_TESTE}/bronze/transactions/**/*.parquet')").fetchone()[0]
norm = con.sql(f"""SELECT channel, merchant_category FROM read_parquet('{BASE_TESTE}/bronze/transactions/**/*.parquet')
                  WHERE transaction_id = 900011""").fetchall()
out.append(f"Bronze: {bronze:,} linhas | quarentena: {len(q)} linhas")
out.append("")
out.append(f"{'linha injetada':<16}{'esperado':<40}{'obtido'}")
for r, esperado in sujas:
    tid = int(r["transaction_id"]) if r["transaction_id"].isdigit() else r["transaction_id"]
    if esperado.startswith("ACEITA"):
        obtido = f"na bronze como {norm[0]}" if norm else "NÃO ENCONTRADA"
    elif esperado.startswith("rejeitada"):
        obtido = "fora da raw (reject_errors)" if tid not in quar else "; ".join(quar[tid])
    elif esperado == "duplicata_id":
        obtido = "; ".join(quar.get(tid, ["não reprovada"])) + " (só a cópia; a original ficou)"
    elif esperado == "duplicata_conteudo":
        obtido = "; ".join(quar.get(tid, ["não reprovada"]))
    else:
        obtido = "; ".join(quar.get(tid, ["não reprovada"]))
    out.append(f"{str(tid):<16}{esperado:<40}{obtido}")
out.append("")
out.append(f"Esperado na bronze: {len(linhas):,} oficiais + 1 normalizada = {len(linhas) + 1:,} -> obtido {bronze:,}")
texto = "\n".join(out)
print(texto)
LOG.write_text(texto + "\n", encoding="utf-8")
shutil.rmtree(BASE_TESTE)
