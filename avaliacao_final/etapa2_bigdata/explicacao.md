# Etapa 2 — Execução do pipeline (relatório)

**Rota declarada:** Rota B (sem admin), a mesma dos Labs 1 a 12. O pipeline roda em DuckDB, gravando Parquet particionado em pasta local, no WSL2/Ubuntu. Não houve tentativa de cluster nesta etapa. A ferramenta muda, mas a lógica de cada camada é a mesma que o Hive executaria.

**Arquivos desta pasta:**

- `generate_avaliacao_dataset.py`: gerador do professor, sem alterações. Produz a base com 30.000 linhas.
- `pipeline.py`: o pipeline completo, das 6 etapas.
- `teste_regras_bronze.py`: teste das regras de limpeza com linhas sujas injetadas numa cópia da base.
- `evidencias/execucao_log.txt`: saída real da execução (schema, contagens, partições, plano de consulta, conferências).
- `evidencias/teste_regras_bronze_log.txt`: resultado do teste de regras.

## Funil de linhas

| Camada | Linhas | Observação |
|---|---|---|
| Arquivo CSV de origem | 30.000 | sem contar o cabeçalho |
| Raw | 30.000 | 0 linhas rejeitadas pelo schema |
| Raw particionada | 30.000 | 12 partições (jan a dez/2025), de 2.317 a 2.625 linhas cada |
| Bronze | 30.000 | 0 linhas em quarentena |
| Silver | 30.000 | nenhuma perda ou duplicação |
| Gold | 4 tabelas | a soma das transações em cada tabela confere com 30.000 |

## As 6 etapas

### 1. Ingestão

**O que fez.** Copiou o arquivo gerado para a pasta de entrada da camada raw, sem mexer em nenhum byte.

**Decisão.** Não basta copiar: o pipeline calcula a assinatura MD5 do arquivo de origem e da cópia e conta as linhas. Assim fica provado que o que entrou no ambiente é idêntico ao que saiu da origem. As duas assinaturas bateram e a contagem deu 30.000 linhas.

**Problema real.** O gerador do professor grava o arquivo numa pasta temporária do sistema. O pipeline recebe o caminho do arquivo como parâmetro e para com uma mensagem clara se o arquivo não existir, em vez de seguir com uma base vazia.

### 2. Tabela raw

**O que fez.** Criou a tabela raw declarando o tipo de cada uma das 12 colunas, sem deixar a ferramenta adivinhar.

**Decisão.** A coluna `is_fraud` ficou deliberadamente como texto nesta camada. Nos Labs 2, 4 e 5 vimos que converter "True"/"False" direto para booleano pode zerar todas as fraudes sem dar erro, então a conversão ficou para a Bronze, onde é feita de forma explícita. Também ativei o registro de linhas rejeitadas: uma linha que não respeita o schema (por exemplo, texto no campo de valor) vai para uma tabela de rejeitos, em vez de derrubar a carga inteira.

**O que foi encontrado.** 0 rejeições. O rótulo chegou como 29.249 "False" e 751 "True".

### 3. Particionamento

**O que fez.** Aplicou a estratégia da Etapa 1: gravou a raw em Parquet, separada em pastas por ano e mês. Resultaram 12 pastas.

**Decisão.** Particionar já nesta camada para que a Bronze e qualquer consulta posterior aproveitem o corte por período. A evidência está no log: uma consulta filtrada em março mostrou no plano de execução que só 1 dos 12 arquivos foi lido. Os volumes mensais ficaram equilibrados (fevereiro é o menor, com 2.317 linhas; janeiro o maior, com 2.625), então não há partição desproporcional.

**Ganho de espaço.** A troca de CSV por Parquet reduziu o armazenamento de 2.678 KB para 743 KB.

### 4. Bronze

**O que fez.** Limpeza sem regra de negócio:

- padronizou texto (espaços nas pontas; minúsculas em canal, categoria, tipo e status);
- converteu o rótulo de fraude aceitando só valores conhecidos;
- aplicou 14 regras de reprovação.

As regras cobrem identificador nulo, duplicata por `transaction_id`, duplicata por conteúdo (a mesma transação com outro id), valor zero, negativo ou acima de R$ 40.000, data fora de 2025, valores fora do domínio esperado em tipo, canal, categoria, status e segmento, risk score fora de 0 a 100, credit score fora de 300 a 900, cliente fora da faixa 1 a 8.000, e rótulo inválido. Na duplicata, fica a primeira ocorrência.

**Decisão 1: quarentena.** Linha reprovada não é apagada em silêncio. Ela vai para uma tabela de quarentena com o motivo, para que alguém possa corrigir na origem.

**Decisão 2: sinalizar sem descartar.** Alguns casos são válidos, mas o analista precisa saber deles. Nesses, a linha fica e recebe uma sinalização.

**O que foi encontrado.** A base oficial é limpa por construção: **nenhuma das 14 regras reprovou linha alguma**. Para mostrar que a Bronze não é uma cópia, rodei o `teste_regras_bronze.py`. Ele injeta 12 linhas sujas numa cópia da base e roda o mesmo pipeline em outra pasta. Resultado:

- 10 linhas foram para a quarentena, cada uma com o motivo certo: a cópia de uma transação existente (a original permaneceu), a duplicata com outro id e as 8 linhas com valor, data, score, canal, rótulo ou cliente inválido;
- a linha com texto no campo de valor foi barrada já na raw, pelo schema;
- a linha com canal " APP " e categoria "Viagem" foi corrigida para "app" e "viagem" e aceita;
- a Bronze do teste terminou com 30.001 linhas, exatamente o esperado.

A base oficial também tem problemas reais que não são motivo de descarte:

- **Valores no piso.** 573 transações têm valor exatamente R$ 5,00. O gerador corta tudo que ficaria abaixo disso, então esses valores não são reais. Ficaram marcados.
- **Credit score nos limites.** 1.222 transações têm credit score exatamente 300 ou 900, pelo mesmo motivo. Também marcadas.
- **Rótulo × status.** 100% das 751 fraudes estão com status "declined", e 2.301 transações legítimas também foram recusadas. Nenhuma fraude aparece como aprovada. Consequência: o status é praticamente uma consequência do rótulo, e usá-lo num modelo seria vazamento de informação. Ele ficou fora do modelo do bônus.
- **Segmento inconsistente por cliente.** Dos 7.803 clientes, 5.887 aparecem com mais de um segmento em transações diferentes. Não há como saber qual é o correto, então tratei o segmento como a classificação do cliente no momento da transação, e não como atributo fixo. Por isso não criei uma tabela de clientes única a partir desta base.
- **Horário só em hora cheia.** Todos os minutos e segundos são 00. Toda análise temporal foi feita no máximo por hora.

### 5. Silver

**O que fez.** Acrescentou as colunas de contexto que as etapas seguintes usam, e só elas:

- data e hora;
- dia da semana (segunda = 1, com o nome abreviado);
- período do dia;
- faixa de credit score (300–499, 500–699, 700–900);
- faixa do risk score atual (abaixo de 60, 60–79, 80 ou mais);
- indicação de recusa (status "declined").

A Silver ficou com 22 colunas: as 12 originais, ano e mês (que vêm das pastas da partição) e as 8 derivadas acima.

**Decisão sobre o que entra.** A regra foi manter na Silver apenas o que alguma tabela Gold, análise ou o modelo realmente utiliza. Colunas cogitadas e deixadas de fora:

- faixa de valor e dia do mês: o valor não separa fraude, e o dia do mês não entrou em nenhuma análise;
- indicação de fim de semana: a análise por dia da semana já cobre;
- combinação canal + categoria: a Gold guarda as duas dimensões separadas, e o cruzamento é feito na agregação;
- colunas de histórico do cliente (quantidade de transações no ano, valor em relação à média dele): seriam calculadas com o ano inteiro, o que usaria informação do futuro em relação a cada transação.

As sinalizações de qualidade (valor no piso, score no limite) ficaram só na Bronze, onde são contadas e diagnosticadas.

**Decisão sobre o período do dia.** Usei uma convenção fixa, definida antes de olhar a fraude: madrugada de 0h a 5h59, manhã de 6h a 11h59, tarde de 12h a 17h59 e noite de 18h a 23h59. Assim o corte não é ajustado aos dados. A análise hora a hora da Etapa 3 mostra que isso tem um custo pequeno: as horas de 0h a 4h ficam todas acima de 3% de fraude, e às 5h a taxa já é 2,30%, o que dilui um pouco a taxa da madrugada.

**Problema real resolvido.** No curso, a Silver fazia um JOIN com a tabela de clientes para trazer segmento e credit score, e perdia cerca de 46 transações de clientes inexistentes. Nesta base, esses campos já vêm na própria transação, então não houve JOIN nem perda: a Silver tem as mesmas 30.000 linhas da Bronze. Com o segmento inconsistente por cliente (item 4), fazer esse JOIN teria sido um erro.

### 6. Gold

**O que fez.** Criou 4 tabelas agregadas, todas com as mesmas medidas: transações, fraudes, recusas, recusas de clientes legítimos, valor total e valor fraudado.

- `gold_cubo_risco` (3.235 linhas): uma linha por mês × canal × categoria × segmento × período do dia.
- `gold_serie_diaria` (1.460 linhas): uma linha por dia × canal.
- `gold_perfil_horario` (168 linhas): hora × dia da semana.
- `gold_segmento_score` (27 linhas): segmento × faixa de credit score × faixa do risk score.

**Decisão.** A Gold guarda **contagens e somas, não taxas**. Uma taxa de fraude não pode ser somada nem tirada a média entre grupos de tamanhos diferentes. Guardando fraudes e transações, o dashboard recalcula a taxa correta para qualquer combinação de filtros.

**Conferência.** Em cada tabela, a soma das transações deu 30.000. Por segmento, a Gold reproduz os números do gerador do professor: High-Risk 9,67%, Standard 2,93%, Premium 0,95%.

## Respostas às perguntas do enunciado

### 1. Quantas linhas sobreviveram da Bronze em diante? Alguma foi descartada?

As 30.000 sobreviveram em todas as camadas; nenhuma foi descartada. Não é falta de limpeza:

- as 14 regras foram aplicadas e contadas uma a uma, e todas deram zero nesta base;
- o teste com linhas sujas prova que elas funcionam;
- os problemas que existem (valores no piso, scores nos limites, segmento inconsistente) foram sinalizados ou tratados na interpretação, porque descartá-los apagaria transações verdadeiras.

### 2. A Silver usa `channel` e `merchant_category`? Por quê?

Sim, as duas, e também a combinação delas. O gerador foi construído para que a fraude dependa desses campos, e a exploração confirmou:

- **canal:** o app tem 3,79% de fraude, contra 1,42% a 1,80% nos outros canais;
- **categoria:** viagem tem 5,32%, contra 1,96% a 2,47% nas demais;
- **combinação:** app + viagem chega a 8,00%.

Sem esses campos, a Silver esconderia justamente onde a fraude se concentra, e a análise ficaria presa ao segmento, como no Lab 12. As duas dimensões seguem juntas até a Gold (no cubo de risco), porque o efeito conjunto é maior que cada um separado, e é lá que o cruzamento é calculado.

### 3. Que agregações foram para a Gold e o que elas respondem?

- **Cubo de risco:** alimenta os KPIs, os gráficos de composição por canal, categoria e segmento, a tabela de detalhe e a curva de captura do dashboard. Responde às análises de segmento, canal, categoria e período.
- **Série diária por canal:** alimenta a média móvel de 7 dias, que mostra se a fraude está subindo ou descendo.
- **Perfil hora × dia da semana:** responde à análise temporal fina (qual hora e qual dia concentram fraude).
- **Segmento × faixa de score:** responde se o credit score e o risk score atual separam fraude, que é a base da pergunta de negócio própria da Etapa 3.
