# Etapa 3 — Ideia do BI: o painel de risco de fraude da TechPay

**Arquivo:** `dashboard.html`. Abre com duplo clique, funciona sem internet e sem servidor, porque a biblioteca de gráficos e os dados da Gold vão embutidos no arquivo. É gerado por `dashboard.py` a partir de `bigdata_aval/gold/`. A captura `dashboard_print.png` mostra a versão entregue.

**Rota declarada:** sem admin (Plotly em HTML), no lugar do Metabase, que exige Docker com privilégio de administrador.

## O painel como produto

O painel não foi pensado como um conjunto de gráficos sobre fraude. Ele foi pensado para responder a uma pergunta operacional: **em quais transações a TechPay deve pedir uma confirmação extra ao cliente, e quanto isso custa em atrito?** Tudo na tela serve a essa decisão.

Estrutura, de cima para baixo, seguindo a anatomia de 4 blocos da aula:

1. **Filtros** de canal, categoria, segmento, período do dia e mês. Valem para todos os blocos, exceto dois gráficos que indicam isso na própria legenda.
2. **KPIs.** São quatro números:
   - transações;
   - taxa de fraude, comparada com a taxa geral quando há filtro;
   - valor fraudado, com o ticket médio da fraude;
   - clientes legítimos recusados, com o percentual das recusas que eram legítimas.
3. **Tendência.** Taxa de fraude mês a mês sobre o volume, e a média móvel de 7 dias, com a taxa geral como linha de referência.
4. **Composição.** Taxa por canal, por categoria e por segmento, com cores que indicam acima ou abaixo da média; mapa canal × categoria; mapa hora × dia da semana.
5. **Detalhe navegável: "Onde aplicar autenticação extra".** As combinações de canal, categoria, segmento e período aparecem ordenadas da maior para a menor taxa. Um controle deslizante escolhe quanto do volume passaria pela etapa extra. O painel mostra, para essa escolha:
   - quantas fraudes seriam alcançadas;
   - qual a taxa de fraude dentro do grupo;
   - quantas transações legítimas passariam pela etapa extra;
   - no gráfico, onde está o motor atual (risk_score ≥ 80), para comparação.

   Combinações com menos de 50 transações (valor ajustável) são reunidas num grupo mais amplo: primeiro juntando os períodos, depois as categorias, depois os canais. Assim o painel não premia grupos pequenos por acaso, e toda linha continua sendo uma regra que dá para aplicar (por exemplo, "App, Viagem, High-Risk, demais períodos").

## 1. Para quem é o painel?

Para o **comitê semanal de prevenção a fraudes**, conduzido pelo gerente de prevenção a fraudes e com os analistas de risco. O analista usa os filtros e a tabela de detalhe para preparar a reunião; o gerente usa os KPIs, a curva e o texto-resumo para decidir.

Não foi desenhado para a diretoria nem para o atendimento:

- a diretoria precisa de um resumo mensal de perdas, que cabe nos KPIs do topo, mas não de uma ferramenta de calibração de regras;
- o atendimento precisa consultar uma transação específica de um cliente, o que exige dados por transação, e a Gold não guarda isso de propósito.

## 2. Que decisão ele ajuda a tomar?

**Quais combinações de canal, categoria, segmento e horário entram (ou saem) da regra de autenticação extra na próxima semana, e com que abrangência.**

Um exemplo de uso com os dados de 2025: com o controle em 20%, os 51 grupos do topo somam 20,7% do volume e alcançam 63,1% das fraudes, enquanto o motor atual, com 20,1% do volume, alcança 26,6%. Esse número é calculado sobre a própria base e tende a ser otimista; o modelo da Etapa 4, avaliado fora da amostra, alcança 55,0% com 20% do volume. Ao mover o controle para 5% ou 10%, o comitê vê na hora quantas fraudes deixa de alcançar e quantos clientes legítimos deixa de incomodar. A escolha é negociada ali, com o número na tela.

Uma segunda decisão, mais lenta: **se o motor de risco atual precisa ser recalibrado**. O ponto verde do motor atual, muito abaixo da curva, é a evidência visual para isso.

## 3. Por que esses KPIs, e o que foi descartado?

**Os que ficaram:**

- **Taxa de fraude**, e não a quantidade de fraudes sozinha. A quantidade sobe e desce com o volume; a taxa permite comparar canais e segmentos de tamanhos muito diferentes (o app tem 4 vezes o volume do ATM).
- **Valor fraudado.** É a perda que o comitê precisa justificar, e mostra que a fraude pesa 2,29% do valor transacionado.
- **Clientes legítimos recusados.** É o custo do outro lado da balança. Nesta base, 75,4% das recusas foram de clientes legítimos. Sem esse número, o painel empurraria o comitê a apertar as regras indefinidamente.
- **Transações.** Dá a escala do recorte filtrado e evita conclusões sobre grupos pequenos.

**Os que foram descartados, e por quê:**

- **Ticket médio geral e faixa de valor.** O valor não separa fraude (AUC 0,496, igual a um sorteio), e o ticket médio da fraude (R$ 159) é parecido com o geral (R$ 174). O ticket da fraude aparece só como contexto no KPI de valor.
- **Credit score médio.** Não diferencia fraude nesta base (análise 1). Mostrá-lo induziria a regras erradas.
- **Risk score médio.** Separa fraude muito pouco (AUC 0,535). Em vez de um KPI, virou o ponto de comparação na curva.
- **Taxa por dia da semana e ranking de "piores dias do mês".** Planos nesta base (de 2,32% a 2,74%). O mapa hora × dia já mostra essa ausência de padrão sem ocupar um KPI.
- **Valor total transacionado como número principal.** É indicador comercial, não de risco. Ficou como linha de contexto sob o KPI de transações.
- **Total de fraudes por tipo de transação.** A diferença entre compra, saque, transferência e pagamento é pequena (2,38% a 2,72%). Entraria como ruído.

## 4. Quem é o dono do painel?

- **Dono do negócio: o gerente de prevenção a fraudes.** Ele abre o painel toda segunda-feira, antes do comitê, e responde por duas perguntas: a regra de autenticação extra está alcançando as fraudes do recorte? O percentual de clientes legítimos recusados subiu? Quando a taxa de uma combinação que está fora da regra passa a ficar acima da taxa geral por semanas seguidas, é ele quem decide incluí-la.
- **Dono técnico: o analista de dados de risco.** Garante que o pipeline rodou (contagens do log batendo entre as camadas) e que a quarentena da Bronze está vazia ou tratada, antes de o painel ser atualizado.

Sem esses dois nomes definidos, o painel vira o "dashboard bonito que ninguém usa" discutido no dia 3 do curso.
