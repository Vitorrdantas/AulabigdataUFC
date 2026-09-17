# Bônus — Modelo preditivo de fraude (Regressão Logística)

**Arquivos:**

- `modelo_fraude.py`: treino e avaliação em PySpark local (Rota B), lendo a Silver da Etapa 2.
- `resultados/metricas_log.txt`: saída real da execução.
- `resultados/coeficientes.csv`: coeficientes, razões de chance, intervalos de confiança e p-valores.
- `resultados/captura_top.csv`: fraudes alcançadas nas transações mais suspeitas.
- `resultados/odds_ratios.png`: gráfico dos efeitos.

## O que foi feito

Treinei uma Regressão Logística, o mesmo tipo de modelo do Lab 12, para estimar a probabilidade de cada transação ser fraude.

**Variáveis de entrada.** Todas estavam disponíveis no momento da transação:

- segmento, canal, categoria do estabelecimento e tipo de transação;
- se a transação foi de madrugada;
- risk score atual, credit score e valor.

**Divisão dos dados.** 80% para treino e 20% para teste, com semente fixa (42) para o resultado ser reproduzível. Ficaram 24.032 transações de treino (602 fraudes) e 5.968 de teste (149 fraudes). Todas as métricas abaixo são do teste, ou seja, de transações que o modelo não viu no treino.

## Decisões e por quê

1. **O status ficou de fora.** Na Bronze (Etapa 2), constatei que 100% das fraudes estão como "declined". O status é, na prática, uma consequência do rótulo. Com ele, o modelo "acertaria" copiando a resposta, e a métrica pareceria excelente sem servir para nada: no momento de decidir se a transação é suspeita, o status ainda não existe.
2. **Categorias com referência explícita.** No Lab 12, o segmento virou um número único (0, 1, 2), o que obriga o modelo a supor que o risco cresce em degraus iguais. Aqui, cada categoria virou uma variável de sim ou não, comparada a uma referência escolhida: Premium, POS, varejo, compra e fora da madrugada. Assim cada coeficiente responde "quanto o risco muda em relação à referência". A madrugada segue a convenção da Silver (0h a 5h59).
3. **Escalas legíveis.** O risk score entra em blocos de 10 pontos e o credit score em blocos de 100. O valor entra em logaritmo, porque a distribuição é muito assimétrica.
4. **Sem regularização.** Deixei o modelo sem penalização para os coeficientes poderem ser interpretados diretamente. Para obter os p-valores, ajustei o mesmo modelo como GLM binomial no Spark; os coeficientes das duas versões são idênticos (diferença máxima de 0,0000).
5. **Métricas adequadas a evento raro.** Com 2,5% de fraude, um modelo que diz "nunca é fraude" acerta 97,5% das vezes. Por isso não usei acurácia. Usei:
   - a **AUC-ROC**, que mede se as fraudes recebem probabilidade maior que as legítimas;
   - a **AUC-PR**, mais exigente em eventos raros;
   - a **captura no topo**: quantas fraudes aparecem entre as X% transações com maior probabilidade.

## Resultado

| Métrica (teste) | Modelo | Só o risk_score atual | Sorteio |
|---|---|---|---|
| AUC-ROC | **0,782** | 0,546 | 0,500 |
| AUC-PR | **0,096** | 0,031 | 0,025 |

| Transações revisadas (maiores probabilidades) | Fraudes alcançadas pelo modelo | Fraudes alcançadas pelo risk_score |
|---|---|---|
| 5% (298) | 36, ou 24,2% (fraude no grupo: 12,08%) | 12, ou 8,1% (4,03%) |
| 10% (597) | 58, ou 38,9% (9,72%) | 29, ou 19,5% (4,86%) |
| 20% (1.194) | 82, ou **55,0%** (6,87%) | 40, ou 26,8% (3,35%) |

Revisando 20% das transações, o modelo alcança o dobro das fraudes do score atual. Esse resultado, obtido fora da amostra de treino, é próximo ao da regra R6 da Etapa 3 (56,7% com 21,7% do volume). Isso confirma que o ganho das regras não foi um acaso da escolha feita sobre a própria base.

## Interpretação dos coeficientes

A razão de chances (odds ratio) é o exponencial do coeficiente. Valor 1 significa sem efeito, 2 significa o dobro da chance de fraude em relação à referência. Todos os valores são do treino, com intervalo de confiança de 95%.

**Efeitos fortes e claros (p < 0,001):**

- **Segmento High-Risk: 11,4** (IC 9,1 a 14,2). Com canal, categoria e horário iguais, um cliente High-Risk tem cerca de 11 vezes a chance de fraude de um Premium. É o maior efeito do modelo, coerente com a análise 1.
- **Segmento Standard: 2,9** (IC 2,3 a 3,6) em relação ao Premium.
- **Canal app: 2,9** (IC 2,2 a 3,8) em relação ao POS. Web (1,37) e ATM (1,47) ficam pouco acima do POS, com p entre 0,04 e 0,05. O app é o único canal com efeito expressivo, como na análise 2.
- **Categoria viagem: 2,6** (IC 2,0 a 3,3) em relação ao varejo.
- **Madrugada: 1,6** (IC 1,3 a 1,9).

As outras categorias (saúde, alimentação, serviços, eletrônico) têm intervalos que cruzam o 1: não diferem do varejo. O mesmo vale para o tipo de transação (saque, transferência, pagamento).

**Efeitos pequenos:**

- **Risk score: 1,04 a cada 10 pontos** (p = 0,013). Estatisticamente existe, mas é mínimo: de 0 a 100 pontos, a chance aumenta cerca de 45%, enquanto o segmento sozinho multiplica por 11. A análise 5 mostra que esse efeito se concentra acima de 80 pontos, e uma reta não captura bem esse comportamento.
- **Credit score: 1,10 a cada 100 pontos** (p = 0,004). O sinal vai no sentido oposto ao intuitivo (score maior, um pouco mais de fraude) e o tamanho é pequeno. Com 17 variáveis testadas, é esperado que algum efeito pequeno apareça por acaso. A variável foi **mantida** no modelo: retirá-la só porque o resultado contraria a intuição seria ajustar o modelo ao resultado desejado. A conclusão prática, somada à análise 1, é não usar o credit score como critério de fraude.
- **Valor: 0,98 por unidade do logaritmo, ou 0,99 ao dobrar o valor** (p = 0,64). Sem efeito: fraudes e transações legítimas têm valores parecidos.

**Leitura de negócio.** O modelo confirma, com os efeitos separados uns dos outros, o que as análises descritivas mostraram: **quem** (segmento), **por onde** (app), **em quê** (viagem) e **quando** (madrugada). Esses quatro fatores explicam a fraude muito melhor que o score atual, o valor ou o credit score.

## Limitações

- **Dados sintéticos.** Os efeitos recuperados ficam próximos dos multiplicadores do gerador do professor. O exercício valida o método, não a realidade de uma fintech.
- **Efeitos independentes.** O modelo assume que cada fator se soma aos outros. Interações como "app e viagem juntos" não foram incluídas como termo próprio.
- **Uma única divisão treino/teste.** Com 149 fraudes no teste, as métricas têm margem de erro relevante. Uma validação cruzada daria uma estimativa mais estável.
- **Probabilidades não calibradas para decisão.** O limite de corte deve ser escolhido pelo comitê pelo volume aceitável de transações revisadas, como na curva do dashboard, e não pelo limite padrão de 0,5: num evento de 2,5%, as probabilidades raramente passam desse valor, e praticamente nenhuma transação seria marcada.
