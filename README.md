# Big Data para Negócios — Vitor Dantas

Repositório com o código dos 12 labs e da Avaliação Final do curso **Big Data para Negócios** (UFC / MPCE, prof. Luiz Alexandre Moreira Barros).

## Estrutura

- `dia1_fundamentos/` a `dia3_insights_bi/`: labs 1 a 12.
- `avaliacao_final/`: projeto final da TechPay.

O relatório completo da avaliação, reunindo as três etapas e o bônus com o diagrama e as telas do dashboard, está em `avaliacao_final/Relatorio_Avaliacao_Final.pdf` (versão editável em `.docx`).

| Pasta | Conteúdo | Relatório (sem código) |
|---|---|---|
| `avaliacao_final/etapa1_arquitetura/` | `diagrama.png` / `diagrama.svg` e o script que os desenha | `justificativa.md` |
| `avaliacao_final/etapa2_bigdata/` | `pipeline.py` (6 etapas), `teste_regras_bronze.py`, gerador da base, `evidencias/` com os logs reais | `explicacao.md` |
| `avaliacao_final/etapa3_analise/` | `analises.py`, `resultados/`, `dashboard.py`, `dashboard.html`, `dashboard_print.png` | `achados.md` e `ideia_bi.md` |
| `avaliacao_final/etapa4_ml/` (bônus) | `modelo_fraude.py`, `resultados/` | `explicacao.md` |

## Ambiente usado

**Rota B (sem admin)** em todos os labs e na avaliação final: WSL2 com Ubuntu no Windows, sem cluster Hadoop administrado.

| Papel no pipeline | Rota A (cluster) | Rota B (usada aqui) |
|---|---|---|
| Armazenamento | HDFS | pastas locais com Parquet particionado (`year=/month=`) |
| Transformação | Hive | DuckDB |
| Exploração e ML | Spark no cluster | PySpark em modo local |
| BI | Metabase | Plotly (HTML que abre offline) |

O motivo da escolha é que não havia cluster disponível e o Metabase exige Docker com privilégio de administrador. A lógica de cada camada (raw → bronze → silver → gold) é a mesma do Hive, e o particionamento é físico, não simulado.

## Como rodar a avaliação final

Requisitos: Python 3.10 ou superior e Java 17 ou superior (para o PySpark).

```bash
pip install -r requirements.txt
bash avaliacao_final/rodar_tudo.sh
```

O script executa, em ordem:

1. gera a base `avaliacao_transactions.csv` com o gerador do professor (seed 123, 30.000 linhas);
2. roda o pipeline, que cria `bigdata_aval/` na raiz;
3. roda o teste das regras da Bronze;
4. roda as análises;
5. gera o dashboard;
6. treina o modelo.

Os CSVs e Parquets não são versionados (ver `.gitignore`): são reproduzíveis pelos scripts. As exceções são as tabelas pequenas de resultado das análises e do modelo.

Para ver o dashboard, abra `avaliacao_final/etapa3_analise/dashboard.html` no navegador.
