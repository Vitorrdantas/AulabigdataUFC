# Resultados das análises (gerado por analises.py)

Taxa = fraudes ÷ transações do grupo. Lift = taxa do grupo ÷ taxa geral (1,00 = igual à média).


## A0_visao_geral — KPIs gerais

|   transacoes |   fraudes |   taxa_fraude_pct |   valor_total |   valor_fraude |   pct_valor_fraudado |   ticket_medio_fraude |   ticket_medio_geral |   recusadas |   recusas_legitimas |   pct_recusas_que_eram_legitimas |   pct_legitimas_recusadas |
|-------------:|----------:|------------------:|--------------:|---------------:|---------------------:|----------------------:|---------------------:|------------:|--------------------:|---------------------------------:|--------------------------:|
|        30000 |       751 |               2.5 |   5.20784e+06 |         119368 |                 2.29 |                158.95 |               173.59 |        3052 |                2301 |                             75.4 |                      7.87 |


## A1a_segmento — Fraude por segmento

| segment   |   transacoes |   pct_volume |   fraudes |   pct_fraudes |   taxa_fraude_pct |   lift |   valor_fraude |
|:----------|-------------:|-------------:|----------:|--------------:|------------------:|-------:|---------------:|
| High-Risk |         2915 |          9.7 |       282 |          37.5 |              9.67 |   3.86 |        42156   |
| Standard  |        10645 |         35.5 |       312 |          41.5 |              2.93 |   1.17 |        50874.9 |
| Premium   |        16440 |         54.8 |       157 |          20.9 |              0.95 |   0.38 |        26337   |


## A1b_credit_score — Fraude por faixa de credit score

| faixa_credit_score   |   transacoes |   pct_volume |   fraudes |   pct_fraudes |   taxa_fraude_pct |   lift |   valor_fraude |
|:---------------------|-------------:|-------------:|----------:|--------------:|------------------:|-------:|---------------:|
| 1_baixo (300-499)    |         4718 |         15.7 |        93 |          12.4 |              1.97 |   0.79 |        11918.5 |
| 2_medio (500-699)    |        15252 |         50.8 |       377 |          50.2 |              2.47 |   0.99 |        62807.3 |
| 3_alto (700-900)     |        10030 |         33.4 |       281 |          37.4 |              2.8  |   1.12 |        44642.2 |


## A1c_segmento_credit_medio — Credit score médio por segmento

| segment   |   credit_score_medio |
|:----------|---------------------:|
| High-Risk |                  635 |
| Premium   |                  638 |
| Standard  |                  640 |


## A1d_segmento_x_canal — Segmento x canal

| segment   | channel   |   transacoes |   pct_volume |   fraudes |   pct_fraudes |   taxa_fraude_pct |   lift |   valor_fraude |
|:----------|:----------|-------------:|-------------:|----------:|--------------:|------------------:|-------:|---------------:|
| High-Risk | app       |         1176 |          3.9 |       162 |          21.6 |             13.78 |   5.5  |       22917.1  |
| High-Risk | web       |          860 |          2.9 |        64 |           8.5 |              7.44 |   2.97 |        9607.73 |
| High-Risk | atm       |          273 |          0.9 |        20 |           2.7 |              7.33 |   2.93 |        4016.06 |
| High-Risk | pos       |          606 |          2   |        36 |           4.8 |              5.94 |   2.37 |        5615.15 |
| Standard  | app       |         4296 |         14.3 |       195 |          26   |              4.54 |   1.81 |       27890.6  |
| Standard  | atm       |         1019 |          3.4 |        23 |           3.1 |              2.26 |   0.9  |        4822.87 |
| Standard  | web       |         3258 |         10.9 |        60 |           8   |              1.84 |   0.74 |       14740.5  |
| Standard  | pos       |         2072 |          6.9 |        34 |           4.5 |              1.64 |   0.66 |        3420.93 |
| Premium   | app       |         6549 |         21.8 |        98 |          13   |              1.5  |   0.6  |       13102.2  |
| Premium   | web       |         4886 |         16.3 |        33 |           4.4 |              0.68 |   0.27 |        7230.95 |
| Premium   | atm       |         1715 |          5.7 |        11 |           1.5 |              0.64 |   0.26 |        3556.37 |
| Premium   | pos       |         3290 |         11   |        15 |           2   |              0.46 |   0.18 |        2447.42 |


## A2_canal — Fraude por canal

| channel   |   transacoes |   pct_volume |   fraudes |   pct_fraudes |   taxa_fraude_pct |   lift |   valor_fraude |
|:----------|-------------:|-------------:|----------:|--------------:|------------------:|-------:|---------------:|
| app       |        12021 |         40.1 |       455 |          60.6 |              3.79 |   1.51 |        63909.9 |
| atm       |         3007 |         10   |        54 |           7.2 |              1.8  |   0.72 |        12395.3 |
| web       |         9004 |         30   |       157 |          20.9 |              1.74 |   0.7  |        31579.2 |
| pos       |         5968 |         19.9 |        85 |          11.3 |              1.42 |   0.57 |        11483.5 |


## A3a_categoria — Fraude por categoria de estabelecimento

| merchant_category   |   transacoes |   pct_volume |   fraudes |   pct_fraudes |   taxa_fraude_pct |   lift |   valor_fraude |
|:--------------------|-------------:|-------------:|----------:|--------------:|------------------:|-------:|---------------:|
| viagem              |         3010 |         10   |       160 |          21.3 |              5.32 |   2.12 |        25966.4 |
| saude               |         2951 |          9.8 |        73 |           9.7 |              2.47 |   0.99 |        11141.5 |
| alimentacao         |         5976 |         19.9 |       138 |          18.4 |              2.31 |   0.92 |        21017   |
| varejo              |         9047 |         30.2 |       203 |          27   |              2.24 |   0.9  |        34870.5 |
| servicos            |         4576 |         15.3 |        90 |          12   |              1.97 |   0.79 |        14197.2 |
| eletronico          |         4440 |         14.8 |        87 |          11.6 |              1.96 |   0.78 |        12175.3 |


## A3b_canal_x_categoria — Canal x categoria (top 10 por taxa)

| channel   | merchant_category   |   transacoes |   pct_volume |   fraudes |   pct_fraudes |   taxa_fraude_pct |   lift |   valor_fraude |
|:----------|:--------------------|-------------:|-------------:|----------:|--------------:|------------------:|-------:|---------------:|
| app       | viagem              |         1237 |          4.1 |        99 |          13.2 |              8    |   3.2  |       15578.7  |
| app       | alimentacao         |         2409 |          8   |        92 |          12.3 |              3.82 |   1.53 |       12514.8  |
| pos       | viagem              |          612 |          2   |        23 |           3.1 |              3.76 |   1.5  |        1947.62 |
| atm       | viagem              |          269 |          0.9 |        10 |           1.3 |              3.72 |   1.49 |        2207.66 |
| app       | saude               |         1189 |          4   |        41 |           5.5 |              3.45 |   1.38 |        4803.04 |
| app       | varejo              |         3600 |         12   |       117 |          15.6 |              3.25 |   1.3  |       15924.6  |
| web       | viagem              |          892 |          3   |        28 |           3.7 |              3.14 |   1.25 |        6232.45 |
| app       | eletronico          |         1777 |          5.9 |        55 |           7.3 |              3.1  |   1.24 |        7829.57 |
| app       | servicos            |         1809 |          6   |        51 |           6.8 |              2.82 |   1.13 |        7259.23 |
| web       | saude               |          849 |          2.8 |        21 |           2.8 |              2.47 |   0.99 |        3629.63 |


## A4a_periodo — Fraude por período do dia

| periodo_dia   |   transacoes |   pct_volume |   fraudes |   pct_fraudes |   taxa_fraude_pct |   lift |   valor_fraude |
|:--------------|-------------:|-------------:|----------:|--------------:|------------------:|-------:|---------------:|
| madrugada     |         7553 |         25.2 |       247 |          32.9 |              3.27 |   1.31 |        38375.6 |
| manha         |         7514 |         25   |       172 |          22.9 |              2.29 |   0.91 |        28718.2 |
| noite         |         7466 |         24.9 |       170 |          22.6 |              2.28 |   0.91 |        25348.5 |
| tarde         |         7467 |         24.9 |       162 |          21.6 |              2.17 |   0.87 |        26925.7 |


## A4b_hora — Fraude por hora

|   hora |   transacoes |   fraudes |   taxa_fraude_pct |
|-------:|-------------:|----------:|------------------:|
|      0 |         1288 |        40 |              3.11 |
|      1 |         1233 |        55 |              4.46 |
|      2 |         1259 |        39 |              3.1  |
|      3 |         1234 |        41 |              3.32 |
|      4 |         1277 |        43 |              3.37 |
|      5 |         1262 |        29 |              2.3  |
|      6 |         1192 |        32 |              2.68 |
|      7 |         1284 |        39 |              3.04 |
|      8 |         1231 |        27 |              2.19 |
|      9 |         1248 |        22 |              1.76 |
|     10 |         1291 |        29 |              2.25 |
|     11 |         1268 |        23 |              1.81 |
|     12 |         1238 |        26 |              2.1  |
|     13 |         1246 |        29 |              2.33 |
|     14 |         1249 |        28 |              2.24 |
|     15 |         1322 |        31 |              2.34 |
|     16 |         1171 |        33 |              2.82 |
|     17 |         1241 |        15 |              1.21 |
|     18 |         1169 |        17 |              1.45 |
|     19 |         1280 |        26 |              2.03 |
|     20 |         1194 |        35 |              2.93 |
|     21 |         1250 |        39 |              3.12 |
|     22 |         1301 |        24 |              1.84 |
|     23 |         1272 |        29 |              2.28 |


## A4c_dia_semana — Fraude por dia da semana

|   dia_semana_num | dia_semana   |   transacoes |   fraudes |   taxa_fraude_pct |
|-----------------:|:-------------|-------------:|----------:|------------------:|
|                1 | seg          |         4350 |       101 |              2.32 |
|                2 | ter          |         4207 |       104 |              2.47 |
|                3 | qua          |         4355 |       107 |              2.46 |
|                4 | qui          |         4293 |       116 |              2.7  |
|                5 | sex          |         4248 |       102 |              2.4  |
|                6 | sab          |         4319 |       105 |              2.43 |
|                7 | dom          |         4228 |       116 |              2.74 |


## A4d_mes — Fraude por mês

|   month |   transacoes |   fraudes |   taxa_fraude_pct |   valor_fraude |
|--------:|-------------:|----------:|------------------:|---------------:|
|       1 |         2625 |        68 |              2.59 |       14740    |
|       2 |         2317 |        62 |              2.68 |        8706.6  |
|       3 |         2511 |        60 |              2.39 |        8842.4  |
|       4 |         2458 |        60 |              2.44 |        8257.61 |
|       5 |         2499 |        58 |              2.32 |        9554.79 |
|       6 |         2525 |        66 |              2.61 |        8441.12 |
|       7 |         2530 |        62 |              2.45 |       10847.9  |
|       8 |         2472 |        67 |              2.71 |       11654.6  |
|       9 |         2451 |        51 |              2.08 |        5882.48 |
|      10 |         2585 |        62 |              2.4  |        9441.86 |
|      11 |         2451 |        63 |              2.57 |       13879.7  |
|      12 |         2576 |        72 |              2.8  |        9118.81 |


## A4e_app_viagem_madrugada — Interação app+viagem x madrugada

| app_viagem   | madrugada   |   transacoes |   pct_volume |   fraudes |   pct_fraudes |   taxa_fraude_pct |   lift |   valor_fraude |
|:-------------|:------------|-------------:|-------------:|----------:|--------------:|------------------:|-------:|---------------:|
| False        | False       |        21523 |         71.7 |       434 |          57.8 |              2.02 |   0.81 |       68618.5  |
| False        | True        |         7240 |         24.1 |       218 |          29   |              3.01 |   1.2  |       35170.8  |
| True         | False       |          924 |          3.1 |        70 |           9.3 |              7.58 |   3.03 |       12373.8  |
| True         | True        |          313 |          1   |        29 |           3.9 |              9.27 |   3.7  |        3204.84 |


## A5a_faixa_risk_score — Fraude por faixa do risk_score atual

| faixa_risk_score   |   transacoes |   pct_volume |   fraudes |   pct_fraudes |   taxa_fraude_pct |   lift |   valor_fraude |
|:-------------------|-------------:|-------------:|----------:|--------------:|------------------:|-------:|---------------:|
| 1_baixo (<60)      |        17965 |         59.9 |       426 |          56.7 |              2.37 |   0.95 |        65244.6 |
| 2_medio (60-79)    |         6002 |         20   |       125 |          16.6 |              2.08 |   0.83 |        22599.1 |
| 3_alto (>=80)      |         6033 |         20.1 |       200 |          26.6 |              3.32 |   1.32 |        31524.2 |


## A5b — Poder de separação de cada variável numérica isolada (AUC; 0,50 = aleatório)

| variável | AUC |
|---|---|
| risk_score | 0.535 |
| credit_score | 0.529 |
| amount | 0.496 |

Teste qui-quadrado fraude x faixa de credit score: p = 0.010


## A5c_simulacao_regras — Simulação de regras de autenticação extra

| regra                                            |   alertas |   pct_volume_alertado |   fraudes_capturadas |   pct_fraudes_capturadas |   precisao_pct |   legitimas_incomodadas |
|:-------------------------------------------------|----------:|----------------------:|---------------------:|-------------------------:|---------------:|------------------------:|
| R1 · risk_score >= 80 (motor atual)              |      6033 |                  20.1 |                  200 |                     26.6 |           3.32 |                    5833 |
| R2 · app + viagem                                |      1237 |                   4.1 |                   99 |                     13.2 |           8    |                    1138 |
| R3 · High-Risk no app                            |      1176 |                   3.9 |                  162 |                     21.6 |          13.78 |                    1014 |
| R4 · todo High-Risk                              |      2915 |                   9.7 |                  282 |                     37.5 |           9.67 |                    2633 |
| R5 · High-Risk OU app+viagem                     |      4024 |                  13.4 |                  349 |                     46.5 |           8.67 |                    3675 |
| R6 · High-Risk OU app+viagem OU app na madrugada |      6501 |                  21.7 |                  426 |                     56.7 |           6.55 |                    6075 |

