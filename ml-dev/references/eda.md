# EDA — Análise Exploratória de Dados

## Checklist EDA Completo

### 1. Visão Geral do Dataset

```python
import pandas as pd
import numpy as np

df = pd.read_csv("data/raw/dataset.csv")

print("=" * 50)
print(f"Shape: {df.shape[0]:,} linhas × {df.shape[1]} colunas")
print(f"Memória: {df.memory_usage(deep=True).sum() / 1e6:.1f} MB")
print("=" * 50)
print("\n--- Tipos de dados ---")
print(df.dtypes.value_counts())
print("\n--- Primeiras linhas ---")
print(df.head())
print("\n--- Info detalhado ---")
df.info()
```

### 2. Valores Nulos

```python
# Taxa de nulos por coluna
null_summary = pd.DataFrame({
    "count": df.isnull().sum(),
    "pct": df.isnull().mean() * 100,
}).sort_values("pct", ascending=False)
null_summary = null_summary[null_summary["count"] > 0]
print(null_summary)

# Heatmap de nulos (útil para padrões de missing)
import missingno as msno  # pip install missingno
msno.heatmap(df)
```

**Estratégias por taxa de nulos:**
- **< 5%**: imputar (median/mode/KNN)
- **5-30%**: imputar + criar flag `is_missing`
- **> 30%**: avaliar se dropar a coluna ou usar técnicas avançadas (MICE, IterativeImputer)
- **Nunca imputar o target**

### 3. Distribuições

```python
import matplotlib.pyplot as plt
import seaborn as sns

# Colunas numéricas
num_cols = df.select_dtypes("number").columns.tolist()
fig, axes = plt.subplots(nrows=(len(num_cols) // 4) + 1, ncols=4, figsize=(16, 4 * ((len(num_cols) // 4) + 1)))
for ax, col in zip(axes.flatten(), num_cols):
    df[col].hist(ax=ax, bins=30, edgecolor="black")
    ax.set_title(col)
    ax.set_xlabel("")
plt.suptitle("Distribuições Numéricas")
plt.tight_layout()
plt.savefig("reports/distributions.png", dpi=150)

# Colunas categóricas
cat_cols = df.select_dtypes("object").columns.tolist()
for col in cat_cols:
    print(f"\n--- {col} ---")
    print(df[col].value_counts(normalize=True).head(20))
```

### 4. Outliers

```python
# Método IQR (robusto, não assume normalidade)
def detect_outliers_iqr(series):
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    return series[(series < lower) | (series > upper)]

for col in num_cols:
    outliers = detect_outliers_iqr(df[col].dropna())
    if len(outliers) > 0:
        print(f"{col}: {len(outliers)} outliers ({len(outliers)/len(df)*100:.1f}%)")

# Boxplot visual
df[num_cols].plot(kind="box", figsize=(16, 4), subplots=True, layout=(1, len(num_cols)))
plt.tight_layout()
```

**Decisão sobre outliers:**
- Erros de medição → remover ou corrigir
- Observações legítimas raras → manter (pode ser sinal importante)
- Transformações (log, sqrt, Winsorizing) para reduzir impacto

### 5. Análise do Target

```python
target = "target"  # ajustar

# Classificação: distribuição de classes
print(df[target].value_counts())
print(df[target].value_counts(normalize=True))

ax = df[target].value_counts().plot(kind="bar", figsize=(8, 4))
ax.set_title("Distribuição do Target")
plt.tight_layout()

# Regressão: distribuição da variável resposta
df[target].hist(bins=50)
print(f"Skewness: {df[target].skew():.3f}")  # > |1| → transformar (log/boxcox)
```

### 6. Correlações e Relações com o Target

```python
# Correlação numérica
corr = df[num_cols + [target]].corr()
print(corr[target].sort_values(ascending=False))

# Heatmap
plt.figure(figsize=(12, 8))
sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0,
            mask=np.triu(np.ones_like(corr, dtype=bool)))
plt.title("Correlation Matrix")
plt.tight_layout()
plt.savefig("reports/correlation_heatmap.png", dpi=150)

# Feature vs target (classificação)
for col in num_cols[:6]:
    fig, ax = plt.subplots(1, 1, figsize=(6, 3))
    df.groupby(target)[col].plot(kind="hist", alpha=0.5, ax=ax, legend=True)
    ax.set_title(f"{col} by {target}")
    plt.tight_layout()
```

### 7. Detecção de Duplicatas

```python
n_dup = df.duplicated().sum()
print(f"Duplicatas: {n_dup} ({n_dup/len(df)*100:.2f}%)")
if n_dup > 0:
    df = df.drop_duplicates()
    print(f"Shape após remoção: {df.shape}")
```

### 8. Checklist de Qualidade de Dados

| Check | Código | Ação se problema |
|-------|--------|-----------------|
| Tipos corretos? | `df.dtypes` | Converter com `pd.to_datetime`, `astype` |
| Datas parseadas? | `df["date"].dtype` | `pd.to_datetime(df["date"])` |
| IDs únicos? | `df["id"].nunique() == len(df)` | Investigar duplicatas |
| Ranges plausíveis? | `df.describe()` | Filtrar/clamp valores absurdos |
| Leakage? | Verificar features com timestamp futuro | Remover features com info do futuro |

### 9. EDA para Séries Temporais

```python
df["date"] = pd.to_datetime(df["date"])
df = df.set_index("date").sort_index()

# Decomposição
from statsmodels.tsa.seasonal import seasonal_decompose
result = seasonal_decompose(df["value"], model="additive", period=12)
result.plot()

# Autocorrelação
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
plot_acf(df["value"].dropna(), ax=axes[0], lags=40)
plot_pacf(df["value"].dropna(), ax=axes[1], lags=40)
plt.tight_layout()
```

### 10. EDA para NLP

```python
# Estatísticas de texto
df["text_length"] = df["text"].str.len()
df["word_count"] = df["text"].str.split().str.len()

print(df[["text_length", "word_count"]].describe())

# Palavras mais frequentes
from collections import Counter
import re

words = []
for text in df["text"]:
    words.extend(re.findall(r"\b\w+\b", str(text).lower()))
most_common = Counter(words).most_common(20)
print(most_common)
```
