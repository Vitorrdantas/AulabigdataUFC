#!/usr/bin/env bash
# Reproduz toda a Avaliação Final (Rota B) a partir da raiz do repositório:
#   bash avaliacao_final/rodar_tudo.sh
set -euo pipefail
cd "$(dirname "$0")/.."

echo ">> 0. Gerando a base (script do professor, seed 123)"
python3 avaliacao_final/etapa2_bigdata/generate_avaliacao_dataset.py

echo ">> Etapa 1. Diagrama"
python3 avaliacao_final/etapa1_arquitetura/desenha_diagrama.py

echo ">> Etapa 2. Pipeline raw -> particionada -> bronze -> silver -> gold"
python3 avaliacao_final/etapa2_bigdata/pipeline.py /tmp/avaliacao_transactions.csv
python3 avaliacao_final/etapa2_bigdata/teste_regras_bronze.py /tmp/avaliacao_transactions.csv

echo ">> Etapa 3. Análises e dashboard"
python3 avaliacao_final/etapa3_analise/analises.py
python3 avaliacao_final/etapa3_analise/dashboard.py

echo ">> Bônus. Modelo de fraude (PySpark local)"
python3 avaliacao_final/etapa4_ml/modelo_fraude.py

echo ">> Concluído. Abra avaliacao_final/etapa3_analise/dashboard.html no navegador."
