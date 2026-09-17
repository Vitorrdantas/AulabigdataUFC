#!/usr/bin/env python3
"""
GERADOR — BASE DE DADOS DA AVALIAÇÃO
Curso: Big Data para Negócios | Avaliação Final (baseada no Lab 12)

Diferente do dataset do curso (transactions_synthetic.csv):
- Novo seed (123) — valores não batem com o que o aluno já viu
- 2 colunas novas: channel (app/web/pos/atm) e merchant_category
- Fraude correlacionada com CHANNEL + MERCHANT_CATEGORY, não só segmento
  (obriga o aluno a explorar de novo, não reciclar a lógica do Lab 12)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

RANDOM_SEED = 123
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

N = 30_000
START_DATE = datetime(2025, 1, 1)
END_DATE = datetime(2025, 12, 31)

print("Gerando base de dados da avaliação...")

# ----------------------------------------------------------------------
# Segmento e score (mesma lógica conceitual do curso, valores diferentes)
# ----------------------------------------------------------------------
segments = np.random.choice(['Premium', 'Standard', 'High-Risk'], size=N, p=[0.55, 0.35, 0.10])
credit_score = np.clip(np.random.normal(640, 140, N).astype(int), 300, 900)

# ----------------------------------------------------------------------
# Novas dimensões — não existiam no dataset do curso
# ----------------------------------------------------------------------
channel = np.random.choice(['app', 'web', 'pos', 'atm'], size=N, p=[0.40, 0.30, 0.20, 0.10])
merchant_category = np.random.choice(
    ['varejo', 'viagem', 'eletronico', 'alimentacao', 'servicos', 'saude'],
    size=N, p=[0.30, 0.10, 0.15, 0.20, 0.15, 0.10]
)
transaction_type = np.random.choice(['compra', 'saque', 'transferencia', 'pagamento'], size=N, p=[0.55, 0.15, 0.20, 0.10])

# ----------------------------------------------------------------------
# Valores e datas
# ----------------------------------------------------------------------
amount = np.clip(np.random.lognormal(4.3, 1.3, N), 5, 40_000)
dates = [START_DATE + timedelta(days=random.randint(0, (END_DATE-START_DATE).days),
                                  hours=random.randint(0, 23)) for _ in range(N)]
risk_score = np.random.uniform(0, 100, N)

# ----------------------------------------------------------------------
# Fraude: NOVA lógica — depende de channel + merchant_category + hora
# (padrão real: fraude em apps costuma concentrar em compras de viagem
#  feitas de madrugada — o aluno precisa DESCOBRIR isso na EDA)
# ----------------------------------------------------------------------
is_fraud = []
for i in range(N):
    base = {'Premium': 0.004, 'Standard': 0.012, 'High-Risk': 0.045}[segments[i]]
    if channel[i] == 'app':
        base *= 2.2
    if merchant_category[i] == 'viagem':
        base *= 2.8
    if dates[i].hour < 5:  # madrugada
        base *= 1.8
    if risk_score[i] > 80:
        base *= 1.5
    is_fraud.append(random.random() < min(base, 0.35))

status = ['declined' if f or random.random() < 0.08 else 'approved' for f in is_fraud]

df = pd.DataFrame({
    'transaction_id': range(1, N+1),
    'customer_id': np.random.randint(1, 8000, N),
    'amount': amount.round(2),
    'transaction_type': transaction_type,
    'channel': channel,
    'merchant_category': merchant_category,
    'timestamp': dates,
    'status': status,
    'risk_score': risk_score.round(2),
    'segment': segments,
    'credit_score': credit_score,
    'is_fraud': is_fraud,
})
df = df.sort_values('timestamp').reset_index(drop=True)

df.to_csv('/tmp/avaliacao_transactions.csv', index=False)

print(f"✓ {len(df)} linhas geradas")
print(f"  Taxa de fraude geral: {df['is_fraud'].mean():.2%}")
print(f"  Fraude por channel:")
print(df.groupby('channel')['is_fraud'].mean().sort_values(ascending=False).apply(lambda x: f"{x:.2%}"))
print(f"  Fraude por merchant_category:")
print(df.groupby('merchant_category')['is_fraud'].mean().sort_values(ascending=False).apply(lambda x: f"{x:.2%}"))
print(f"  Fraude por segmento:")
print(df.groupby('segment')['is_fraud'].mean().sort_values(ascending=False).apply(lambda x: f"{x:.2%}"))
