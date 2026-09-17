# Etapa 3 — Relatório de achados

**Como os números foram produzidos:** `analises.py` lê a Gold (e a Silver quando precisa do nível da transação). Cada tabela citada está em `resultados/` e todas estão reunidas em `resultados/resumo_analises.md`. O dashboard (`dashboard.html`, gerado por `dashboard.py`) lê as mesmas tabelas Gold, por isso os números batem.

**Convenções:**

- **Taxa de fraude** = fraudes ÷ transações do grupo.
- **Lift** = taxa do grupo ÷ taxa geral; 1,00 significa igual à média.
- A taxa geral da base é **2,50%**: 751 fraudes em 30.000 transações, somando R$ 119.368 fraudados de R$ 5.207.844 transacionados (2,29% do valor).

Foram feitas as cinco análises da lista. Cada uma segue o framework da aula: Finding → Insight → Ação.

---

## Análise 1 — Segmentação por segmento e score

**Finding.**

| Segmento | % do volume | % das fraudes | Taxa |
|---|---|---|---|
| High-Risk | 9,7% | 37,5% | 9,67% |
| Standard | 35,5% | 41,5% | 2,93% |
| Premium | 54,8% | 20,9% | 0,95% |

O High-Risk tem 10 vezes a taxa do Premium. O credit score não acompanha essa diferença:

- o score médio é praticamente igual nos três segmentos (High-Risk 635, Standard 640, Premium 638);
- por faixa de score, a taxa não cai quando o score sobe: 1,97% (300–499), 2,47% (500–699), 2,80% (700–900);
- isolado, o credit score separa fraude quase como um sorteio (AUC 0,529, onde 0,50 é aleatório).

**Insight.** Nesta base, o segmento carrega o sinal de fraude e o credit score não. Faz sentido: credit score mede chance de inadimplência, não de a transação ser fraudulenta. A pequena diferença entre faixas vai no sentido contrário ao intuitivo e não tem uso prático. O segmento também se combina com o canal: High-Risk no app chega a **13,78%** de fraude, com 3,9% do volume e 21,6% de todas as fraudes.

**Ação.** Não usar credit score como filtro de fraude. Usar o segmento como primeira camada das regras, começando pelo High-Risk no app, que tem a maior taxa entre os 12 cruzamentos de segmento e canal.

---

## Análise 2 — Risco por canal

**Finding.**

| Canal | Taxa | Lift | % do volume | % das fraudes |
|---|---|---|---|---|
| App | 3,79% | 1,51 | 40,1% | 60,6% |
| ATM | 1,80% | 0,72 | 10,0% | 7,2% |
| Web | 1,74% | 0,70 | 30,0% | 20,9% |
| POS | 1,42% | 0,57 | 19,9% | 11,3% |

Em valor, o app responde por R$ 63.910, ou 53,5% de todo o valor fraudado.

**Insight.** O app não é arriscado só porque atende mais clientes High-Risk. Dentro de **cada** segmento, ele é o canal com maior taxa:

- Premium: 1,50% no app, contra no máximo 0,68% nos outros canais;
- Standard: 4,54% contra no máximo 2,26%;
- High-Risk: 13,78% contra no máximo 7,44%.

O efeito é do canal. O POS, onde o cartão está presente fisicamente, é o mais seguro.

**Ação.** Concentrar a autenticação extra no app e deixar o POS com o fluxo atual. Para os segmentos Standard e High-Risk no app, que somam 18,2% do volume e 47,5% das fraudes, vale avaliar um segundo fator em transações fora do padrão do cliente.

---

## Análise 3 — Risco por categoria de estabelecimento

**Finding.** Viagem tem 5,32% de fraude (lift 2,12). Com 10,0% do volume, concentra 21,3% das fraudes e R$ 25.966 fraudados. As outras cinco categorias ficam entre 1,96% (eletrônico) e 2,47% (saúde), todas perto ou abaixo da média. Viagem é a categoria mais arriscada em todos os canais:

| Canal | Taxa em viagem |
|---|---|
| App | 8,00% |
| POS | 3,76% |
| ATM | 3,72% |
| Web | 3,14% |

**Insight.** O risco de viagem se soma ao do app. A combinação **app + viagem** tem 8,00% de fraude, acima de cada efeito isolado (3,79% do app e 5,32% de viagem). Com apenas 4,1% do volume (1.237 transações), ela concentra 13,2% das fraudes. Eletrônico, por sua vez, tem a menor taxa da base (1,96%).

**Ação.** Exigir confirmação adicional em compras de viagem pelo app. É a regra com menor atrito entre as que usam só canal e categoria.

---

## Análise 4 — Padrão temporal

**Finding.**

- **Período do dia.** A madrugada (0h a 5h59, convenção fixa definida na Silver) tem 3,27% de fraude (lift 1,31) e concentra 32,9% das fraudes com 25,2% do volume. Manhã, tarde e noite ficam entre 2,17% e 2,29%.
- **Hora a hora.** As horas de 0h a 4h estão todas acima de 3%, com pico à 1h (4,46%). Às 5h a taxa já é 2,30%.
- **Dia da semana.** Não há padrão: todos os dias ficam entre 2,32% (segunda) e 2,74% (domingo).
- **Mês.** Também não: a taxa oscila entre 2,08% (setembro) e 2,80% (dezembro), sem tendência de alta ou de baixa ao longo do ano.
- **Combinação.** App + viagem de madrugada chega a 9,27%, com 313 transações e 29 fraudes.

**Insight.** O sinal temporal está na hora, não no calendário. Isso é diferente da base usada no curso, onde a fraude acompanhava o fim do mês, e mostra por que a exploração precisou ser refeita em vez de reaproveitar as conclusões do Lab 8. O risco concentra-se entre 0h e 4h; a convenção de madrugada até 5h59 inclui uma hora já próxima da média, o que dilui um pouco a taxa, mas evita um corte ajustado aos próprios dados. Como a série mensal é estável, uma alta futura na tendência do dashboard será sinal de mudança real, e não sazonalidade conhecida.

**Ação.** Incluir a madrugada como critério nas regras do app e não criar regras por dia da semana ou por mês, que não têm base nos dados.

---

## Análise 5 — Pergunta própria: o motor de risco atual aponta para as transações certas?

**Pergunta.** A TechPay já tem um `risk_score` (0 a 100) em cada transação. Se a empresa aceitar exigir autenticação extra em cerca de 20% das transações, qual critério alcança mais fraudes: o score atual ou regras construídas a partir das análises 1 a 4?

**Finding.** O score atual quase não separa fraude:

- por faixa, a taxa é 2,37% abaixo de 60, 2,08% entre 60 e 79 e 3,32% a partir de 80;
- a faixa intermediária tem até menos fraude que a mais baixa;
- isolado, o score tem AUC de 0,535.

Simulação das regras sobre as 30.000 transações:

| Regra | % do volume alertado | % das fraudes alcançadas | Fraude dentro do grupo | Transações legítimas afetadas |
|---|---|---|---|---|
| R1: risk_score ≥ 80 (motor atual) | 20,1% | 26,6% | 3,32% | 5.833 |
| R2: app + viagem | 4,1% | 13,2% | 8,00% | 1.138 |
| R3: High-Risk no app | 3,9% | 21,6% | 13,78% | 1.014 |
| R4: todo High-Risk | 9,7% | 37,5% | 9,67% | 2.633 |
| R5: High-Risk ou app + viagem | 13,4% | 46,5% | 8,67% | 3.675 |
| R6: High-Risk ou app + viagem ou app na madrugada | 21,7% | **56,7%** | 6,55% | 6.075 |

**Insight.** Com volume alertado parecido (21,7% contra 20,1%), a regra R6 alcança **mais que o dobro** das fraudes do motor atual (426 contra 200). O preço é pequeno: 242 transações legítimas a mais passam pela etapa extra (6.075 contra 5.833), enquanto a taxa de fraude dentro do grupo alertado quase dobra (6,55% contra 3,32%). O motor atual só tem algum efeito acima de 80 pontos e ignora exatamente os campos onde a fraude se concentra: canal, categoria, segmento e hora.

Há um segundo achado, sobre atrito: das 3.052 transações recusadas no ano, **2.301 (75,4%) eram legítimas**. Isso equivale a 7,87% de todas as transações legítimas. O custo de uma regra mal calibrada não é só a fraude que passa, é também o cliente bom que é barrado.

Limitação: as regras foram escolhidas olhando esta mesma base, então os percentuais tendem a ser otimistas. O modelo do bônus (Etapa 4), avaliado em dados que ele não viu no treino, alcançou 55,0% das fraudes nos 20% mais suspeitos, um resultado próximo ao da R6. Isso indica que o ganho não é artefato da escolha das regras.

**Ação.**

1. Levar ao comitê de risco a comparação R1 × R6.
2. Começar por um piloto de R3 (High-Risk no app), que afeta só 3,9% do volume e já alcança 21,6% das fraudes.
3. Ampliar para R6 depois de medir no piloto quantos clientes legítimos abandonam a transação na etapa extra.
4. Em paralelo, recalibrar o `risk_score` incluindo canal, categoria, segmento e período, que é o que o modelo da Etapa 4 faz.

---

## Onde cada análise aparece no dashboard

| Análise | Bloco do dashboard |
|---|---|
| 1. Segmentação | Gráfico "Taxa de fraude por segmento"; filtro de segmento em todos os blocos |
| 2. Canal | Gráfico "Taxa de fraude por canal"; mapa canal × categoria |
| 3. Categoria | Gráfico "Taxa de fraude por categoria"; mapa canal × categoria |
| 4. Temporal | Tendência mensal; média móvel de 7 dias; mapa hora × dia da semana; filtro de período |
| 5. Pergunta própria | Bloco "Onde aplicar autenticação extra": curva de captura com o ponto do motor atual e tabela acumulada; KPI de clientes legítimos recusados |
