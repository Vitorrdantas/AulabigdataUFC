# Etapa 1 — Arquitetura de Big Data (TechPay)

**Diagrama:** `diagrama.png` (fonte editável em `diagrama.svg`). Cada caixa indica a ferramenta de cluster (Rota A) e a equivalente usada na execução (Rota B: DuckDB, PySpark local e Plotly, no WSL2/Ubuntu, a mesma rota dos Labs 1 a 12).

## Fluxo e formatos

As transações nascem nos canais da TechPay (app, web, POS, ATM) e são gravadas no banco transacional, que também guarda segmento e credit score do cliente. O rótulo de fraude chega depois, quando o time de risco conclui a análise, por isso o desenho o trata como atualização tardia.

Uma vez por dia, a ingestão copia as transações do dia anterior para a camada **raw**, em **CSV**, exatamente como chegaram. Isso permite reprocessar tudo se uma regra de limpeza estiver errada. A partir daí, tudo é **Parquet**: o formato é colunar, comprimido (2.678 KB viraram 743 KB) e guarda o tipo de cada coluna, evitando o problema dos Labs 2, 4 e 5 em que o `is_fraud` em texto era convertido errado.

A cadeia Medallion é: raw particionada (schema explícito) → Bronze (limpeza e quarentena) → Silver (colunas de análise) → Gold (4 tabelas de contagens, sem partição, porque a maior tem 3.235 linhas). Só a Gold vai para o BI; o Spark lê a Silver para exploração e para o modelo. O dashboard alimenta o comitê semanal de risco.

## 1. Ferramenta de ingestão e alternativa

A origem é um banco relacional e a necessidade é analítica, com visão do dia anterior. O **Sqoop** resolve com poucos parâmetros: lê via JDBC, divide a leitura em mappers paralelos, grava no HDFS e, no modo incremental, traz só o que mudou desde a última carga. Na Rota B, o equivalente foi copiar o arquivo e conferir assinatura MD5 e contagem de linhas.

A alternativa seria **Kafka** (ou Flume/NiFi), recebendo cada transação no momento em que ocorre. Não usei porque o pedido é batch: streaming traria brokers, tópicos e consumidores para operar, sem ganho numa análise olhada semanalmente. Ressalva: o Sqoop foi descontinuado pela Apache em 2021; em produção, eu faria a mesma leitura incremental com o próprio Spark.

## 2. Estratégia de particionamento

Partições por **ano e mês** da transação. A consulta mais frequente da área de risco é recortada no tempo ("como fechou a fraude do mês e como compara com o anterior?") e, com essa partição, abre 2 das 12 pastas. A execução confirmou: uma consulta filtrada em março leu 1 de 12 arquivos.

Partição por **dia** foi descartada: com 30 mil transações no ano, seriam 365 pastas com cerca de 80 linhas cada, o clássico problema de arquivos pequenos. Partição por **canal** também: quase nenhuma consulta filtra só o canal sem recortar o período, e esse filtro acontece no dashboard, sobre a Gold. Com 100 vezes mais volume, cada mês teria cerca de 250 mil linhas, ainda saudável; acima disso, o próximo passo seria particionar por dia.

## 3. O que quebra primeiro com 100 vezes o volume

1. **Carga na origem.** Ler a tabela inteira todo dia pesaria no banco que atende os clientes. Mitigação: importação incremental, leitura numa réplica e janela noturna.
2. **Máquina única da Rota B.** O DuckDB está limitado a um computador e não tem tolerância a falha. O mesmo pipeline passaria a rodar em Spark ou Hive no cluster.
3. **Reprocessamento completo.** Recriar todas as camadas a cada carga deixa de ser viável; o certo é reprocessar só a partição do mês com dados novos.
4. **Arquivos pequenos e desbalanceamento.** Cargas diárias multiplicam arquivos por partição, e o app concentra 40% do volume. Mitigação: compactação periódica e atenção à distribuição nas agregações.
5. **Metastore e NameNode.** O metastore Derby, que deu problema no curso, não aceita vários usuários; em produção seria MySQL ou PostgreSQL, com NameNode em alta disponibilidade.
6. **Rótulo atrasado.** Fraudes confirmadas semanas depois exigem reprocessar meses anteriores, o que só é possível porque a raw é imutável e particionada.

O que não piora: a tabela principal da Gold cresce com o número de combinações de mês, canal, categoria, segmento e período, não com o número de transações, então o dashboard continua leve.

## 4. Detecção de fraude em tempo real

A decisão passaria a acontecer enquanto o cliente espera a aprovação. A faixa tracejada do diagrama mostra o caminho adicional: o autorizador publica cada transação no **Kafka**; o **Spark Structured Streaming** calcula características recentes do cliente em janelas de minutos (por exemplo, compras de viagem pelo app na última hora); elas ficam num armazenamento de baixa latência (**Redis** ou HBase); uma **API de scoring** aplica o modelo treinado no batch e responde em menos de 100 ms: aprovar, pedir segundo fator ou negar.

O batch continua existindo: os eventos também caem na raw, de onde saem o histórico, o BI e o retreino. As mudanças principais são a ingestão por eventos, uma camada de serving de baixa latência, o monitoramento contínuo do modelo e o tempo de resposta tratado como requisito de negócio.
