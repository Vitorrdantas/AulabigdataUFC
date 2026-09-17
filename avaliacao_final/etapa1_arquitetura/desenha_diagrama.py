#!/usr/bin/env python3
"""Gera diagrama.svg e diagrama.png da arquitetura TechPay (Etapa 1)."""
from pathlib import Path
from xml.sax.saxutils import escape

import cairosvg

AQUI = Path(__file__).resolve().parent
NAVY, NAVY2, NAVYS = "#0B2E59", "#1F4E8C", "#E7EDF5"
GOLD, GOLDS = "#B8860B", "#F6EFD9"
GREEN, GREENS = "#1E5631", "#E3EFE6"
INK, INK2, RULE = "#16212E", "#4A5767", "#C9D2DE"
FONT = "DejaVu Sans, Segoe UI, Arial, sans-serif"

W, H = 1700, 1000
el = []


def texto(x, y, s, size=13, cor=INK, peso="normal", anchor="start", italico=False):
    est = ' font-style="italic"' if italico else ""
    el.append(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" fill="{cor}" '
              f'font-weight="{peso}" text-anchor="{anchor}"{est}>{escape(s)}</text>')


def caixa(x, y, w, h, titulo, linhas, fundo="#FFFFFF", borda=NAVY, cor_tit=NAVY, tag=None, tracejado=False):
    dash = ' stroke-dasharray="7 5"' if tracejado else ""
    el.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fundo}" stroke="{borda}" stroke-width="1.8"{dash}/>')
    texto(x + 12, y + 24, titulo, 15, cor_tit, "bold")
    yy = y + 46
    for ln in linhas:
        if ln.startswith("!"):
            texto(x + 12, yy, ln[1:], 12.5, INK2, italico=True)
        else:
            texto(x + 12, yy, ln, 12.5)
        yy += 18
    if tag:
        tw = 8 * len(tag) + 16
        el.append(f'<rect x="{x + w - tw - 8}" y="{y + h - 28}" width="{tw}" height="20" rx="10" fill="{GOLD}"/>')
        texto(x + w - tw / 2 - 8, y + h - 14, tag, 11.5, "#FFFFFF", "bold", "middle")


def seta(x1, y1, x2, y2, rot=None, cor=NAVY2, tracejado=False, rot_dy=-7, rot_dx=0, anchor="middle"):
    dash = ' stroke-dasharray="6 4"' if tracejado else ""
    mk = {GOLD: "setaG", GREEN: "setaV"}.get(cor, "seta")
    el.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{cor}" stroke-width="2.2"{dash} marker-end="url(#{mk})"/>')
    if rot:
        texto((x1 + x2) / 2 + rot_dx, (y1 + y2) / 2 + rot_dy, rot, 11.5, INK2, anchor=anchor)


def faixa(x, y, w, h, titulo, fundo):
    el.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fundo}"/>')
    texto(x + w / 2, y + 26, titulo, 15.5, NAVY, "bold", "middle")


# ------------------------------------------------------------------ cabeçalho
el.append(f'<rect x="0" y="0" width="{W}" height="70" fill="{NAVY}"/>')
texto(30, 44, "TechPay — arquitetura de dados para risco de fraude", 24, "#FFFFFF", "bold")
texto(W - 30, 34, "Batch diário (D-1), arquitetura Medallion", 13.5, "#FFFFFF", anchor="end")
texto(W - 30, 54, "Rota A: cluster Hadoop   |   Rota B (executada): DuckDB + PySpark local + Plotly", 13.5, "#F3E3B5", anchor="end")

# ------------------------------------------------------------------ faixas de camada
Y0, HF = 90, 660
cols = [(20, 230, "1. Origem"), (270, 230, "2. Ingestão"), (520, 230, "3. Armazenamento bruto"),
        (770, 520, "4. Processamento (Medallion)"), (1310, 370, "5. Serving e BI")]
for x, w, t in cols:
    faixa(x, Y0, w, HF, t, "#F3F6FA")

# 1. origem
caixa(35, 140, 200, 190, "Canais TechPay", ["App (40% do volume)", "Web (30%)", "POS (20%)", "ATM (10%)",
                                             "!eventos de transação"], NAVYS)
caixa(35, 370, 200, 170, "Banco transacional", ["OLTP (MySQL)", "tabela de transações", "+ cadastro do cliente",
                                                  "  (segmento, score)", "!fonte de verdade"])
seta(135, 330, 135, 368, "grava", rot_dy=4, rot_dx=8, anchor="start")
caixa(35, 580, 200, 140, "Rótulo de fraude", ["chargeback / análise", "do time de risco", "!chega com atraso",
                                                "!(dias ou semanas)"], GOLDS, GOLD, INK)
seta(135, 578, 135, 542, "atualiza is_fraud", cor=GOLD, rot_dy=4, rot_dx=8, anchor="start")

# 2. ingestão
caixa(285, 300, 200, 250, "Sqoop (batch diário)", ["import JDBC do MySQL", "modo incremental por", "timestamp (lastmodified)",
                                                    "4 mappers em paralelo", "", "Rota B: cópia do CSV",
                                                    "+ checksum MD5", "+ contagem de linhas"], tag="CSV")
seta(237, 450, 283, 450, "D-1", rot_dy=-8)

# 3. raw
caixa(535, 300, 200, 250, "Landing / raw", ["HDFS /raw/transactions/", "replicação 3×", "arquivo imutável, como", "chegou da origem",
                                             "", "Rota B:", "bigdata_aval/raw/", "!permite reprocessar tudo"], tag="CSV")
seta(487, 425, 533, 425)

# 4. processamento — cadeia vertical à esquerda, detalhes à direita
PX = 790
caixa(PX, 130, 230, 120, "Raw particionada", ["tabela com schema explícito", "is_fraud mantido como texto", "rejeitadas: reject_errors"],
      tag="Parquet · year/month")
caixa(PX, 285, 230, 135, "Bronze", ["Hive / DuckDB", "tipos, domínios, faixas", "duplicata por id e conteúdo", "reprovadas → quarentena"],
      tag="Parquet · year/month")
caixa(PX, 455, 230, 135, "Silver", ["Hive / DuckDB", "hora, período, dia da semana", "faixas de valor e score", "canal × categoria, contexto"],
      tag="Parquet · year/month")
caixa(PX, 625, 230, 110, "Gold", ["Hive / DuckDB", "4 tabelas agregadas (contagens)"], NAVYS, tag="Parquet")
seta(737, 330, PX - 2, 190)
for y1, y2 in [(250, 283), (420, 453), (590, 623)]:
    seta(PX + 115, y1, PX + 115, y2)

caixa(1045, 285, 230, 135, "Quarentena", ["linhas reprovadas + motivo", "revisão pelo dono da origem", "não somem em silêncio"], GOLDS, GOLD, INK)
seta(PX + 232, 352, 1043, 352, cor=GOLD)
caixa(1045, 455, 230, 135, "Spark (PySpark)", ["EDA interativa em memória", "Regressão Logística", "lê a Silver"], GREENS, GREEN, GREEN)
seta(PX + 232, 522, 1043, 522, cor=GREEN)
caixa(1045, 625, 230, 110, "Gold · tabelas", ["cubo_risco", "serie_diaria", "perfil_horario", "segmento_score"], "#FFFFFF")
seta(PX + 232, 680, 1043, 680)
caixa(1045, 130, 230, 120, "Particionamento", ["colunas: year / month", "12 partições por ano", "filtro por mês lê 1/12", "!Gold pequena: sem partição"],
      GOLDS, GOLD, INK)

# 5. serving
caixa(1325, 130, 340, 150, "Export da Gold (Lab 9)", ["Rota A: Sqoop export → MySQL de BI", "Rota B: leitura direta dos Parquet",
                                                        "somente agregados saem do lake", "!taxas recalculadas no BI"], tag="Parquet → tabela SQL")
caixa(1325, 320, 340, 150, "Dashboard de risco", ["Rota A: Metabase", "Rota B: HTML Plotly (offline)", "KPIs, tendência, composição,",
                                                    "detalhe e curva de captura"], NAVYS)
caixa(1325, 510, 340, 105, "Score de fraude (bônus)", ["probabilidade por transação", "modelo lido da Silver via Spark"], GREENS, GREEN, GREEN)
caixa(1325, 650, 340, 90, "Decisão", ["comitê de risco, reunião semanal", "regras de autenticação extra"], GOLDS, GOLD, INK)
seta(1277, 680, 1323, 205, "")
seta(1495, 280, 1495, 318)
seta(1277, 522, 1323, 560, cor=GREEN)
seta(1495, 470, 1495, 508, cor=NAVY2, tracejado=True)
seta(1495, 615, 1495, 648)
el.append(f'<path d="M 1325 395 C 1300 400, 1300 690, 1323 695" fill="none" stroke="{NAVY2}" stroke-width="2.2" marker-end="url(#seta)"/>')

# ------------------------------------------------------------------ faixa de tempo real (pergunta 4)
YR = 775
el.append(f'<rect x="20" y="{YR}" width="{W - 40}" height="200" rx="8" fill="#FFFFFF" stroke="{GOLD}" stroke-width="2" stroke-dasharray="9 6"/>')
texto(40, YR + 28, "Se a TechPay pedir detecção em tempo real (pergunta 4 da justificativa): caminho adicional, o batch acima continua para BI e retreino",
      15, GOLD, "bold")
rt = [("Eventos no autorizador", ["cada transação publicada", "no momento da compra"]),
      ("Kafka", ["tópico transacoes", "retenção e replay"]),
      ("Spark Structured Streaming", ["janelas de 1 a 10 min", "features do cliente"]),
      ("Feature store online", ["Redis / HBase", "contagens recentes"]),
      ("API de scoring", ["modelo da Gold/Silver", "resposta < 100 ms"]),
      ("Decisão na hora", ["aprovar, pedir 2º fator", "ou negar"])]
bx, bw, gap = 40, 230, 44
for i, (t, ls) in enumerate(rt):
    x = bx + i * (bw + gap)
    caixa(x, YR + 50, bw, 95, t, ls, "#FFFFFF", GOLD, INK, tracejado=True)
    if i < len(rt) - 1:
        seta(x + bw + 2, YR + 97, x + bw + gap - 2, YR + 97, cor=GOLD, tracejado=True)
texto(40, YR + 175, "Os eventos também caem no HDFS (camada raw) para manter o histórico e retreinar o modelo em batch.", 12.5, INK2, italico=True)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
<marker id="seta" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="{NAVY2}"/></marker>
<marker id="setaG" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="{GOLD}"/></marker>
<marker id="setaV" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="{GREEN}"/></marker>
</defs>
<rect width="{W}" height="{H}" fill="#FFFFFF"/>
{chr(10).join(el)}
</svg>'''
(AQUI / "diagrama.svg").write_text(svg, encoding="utf-8")
cairosvg.svg2png(bytestring=svg.encode(), write_to=str(AQUI / "diagrama.png"), output_width=W * 1.5)
print("diagrama.svg e diagrama.png gerados")
