# Seleção de Algoritmos

## Mapa de Decisão Rápida

```
Dado tabular estruturado?
├── SIM
│   ├── Supervisionado
│   │   ├── Classificação
│   │   │   ├── Alta interpretabilidade → Regressão Logística, Árvore de Decisão
│   │   │   ├── Melhor performance → XGBoost, LightGBM, CatBoost
│   │   │   ├── Dados pequenos (<5k) → SVM, KNN, RF
│   │   │   └── Dados grandes (>1M) → LightGBM, Redes Neurais
│   │   └── Regressão
│   │       ├── Linear → Ridge, Lasso, ElasticNet
│   │       ├── Não-linear → XGBoost, LightGBM, SVR, RF
│   │       └── Quantílica → QuantileRegressor, LightGBM quantile
│   └── Não supervisionado
│       ├── Clustering → K-Means, DBSCAN, Gaussian Mixture
│       └── Redução dim. → PCA, UMAP, t-SNE
└── NÃO (texto, imagem, áudio, vídeo)
    ├── Texto/NLP → Transformers (BERT, GPT, T5)
    ├── Imagem → CNN (ResNet, EfficientNet, ViT)
    ├── Série Temporal → Prophet, N-BEATS, LSTM, TFT
    └── Áudio → Wav2Vec, Whisper
```

---

## Algoritmos de Classificação

### Regressão Logística
```python
from sklearn.linear_model import LogisticRegression

model = LogisticRegression(
    C=1.0,                    # inverso da regularização (menor C = mais regularização)
    penalty="l2",             # "l1" para sparsity, "elasticnet" para ambos
    solver="lbfgs",           # "saga" para L1/ElasticNet em grandes datasets
    max_iter=1000,
    class_weight="balanced",  # para dados desbalanceados
    random_state=42,
    n_jobs=-1,
)
```
**Use quando**: baseline interpretável, features já bem engenheiradas, relação linear esperada, necessidade de probabilidades calibradas.

---

### Random Forest
```python
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(
    n_estimators=200,         # mais árvores = mais estável, diminishing returns após ~200
    max_depth=None,           # None = expandir até folhas puras (pode overfittar)
    min_samples_leaf=4,       # regularização: aumentar reduz overfitting
    max_features="sqrt",      # "sqrt" para classificação, "log2" ou float para regressão
    class_weight="balanced",
    n_jobs=-1,
    random_state=42,
    oob_score=True,           # out-of-bag score como validação gratuita
)
```
**Use quando**: dados tabulares médios, boa performance out-of-the-box, interpretabilidade via feature importance, robusto a outliers e sem necessidade de scaling.

---

### XGBoost (recomendado para tabular)
```python
from xgboost import XGBClassifier

model = XGBClassifier(
    n_estimators=500,
    max_depth=6,
    learning_rate=0.05,       # lr baixo + mais árvores geralmente supera lr alto
    subsample=0.8,            # fração de linhas por árvore
    colsample_bytree=0.8,     # fração de features por árvore
    min_child_weight=5,       # regularização contra overfitting
    gamma=0.1,                # mínimo de ganho para split
    reg_alpha=0.1,            # L1 regularização
    reg_lambda=1.0,           # L2 regularização
    scale_pos_weight=neg/pos, # desbalanceamento: razão negativo/positivo
    use_label_encoder=False,
    eval_metric="logloss",
    early_stopping_rounds=50, # parar se não melhorar em 50 rounds
    random_state=42,
    n_jobs=-1,
)

# Treino com early stopping
model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    verbose=100,
)
```
**Use quando**: melhor performance em dados tabulares, tolerante a outliers e diferentes escalas, handle nativo de valores faltantes.

---

### LightGBM (mais rápido que XGBoost)
```python
import lightgbm as lgb

model = lgb.LGBMClassifier(
    n_estimators=1000,
    num_leaves=63,            # controle principal de complexidade (max_depth ~ log2(num_leaves))
    learning_rate=0.05,
    feature_fraction=0.8,
    bagging_fraction=0.8,
    bagging_freq=5,
    min_child_samples=20,
    lambda_l1=0.1,
    lambda_l2=0.1,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1,
    verbose=-1,
)

# Com early stopping via callbacks
callbacks = [lgb.early_stopping(50), lgb.log_evaluation(100)]
model.fit(X_train, y_train, eval_set=[(X_val, y_val)], callbacks=callbacks)
```
**Use quando**: datasets grandes (>100k), velocidade importante, bom para features categóricas com alta cardinalidade.

---

### CatBoost (melhor para categoricals)
```python
from catboost import CatBoostClassifier

model = CatBoostClassifier(
    iterations=500,
    depth=6,
    learning_rate=0.05,
    l2_leaf_reg=3.0,
    cat_features=cat_col_indices,  # índices das colunas categóricas
    auto_class_weights="Balanced",
    random_seed=42,
    verbose=100,
    early_stopping_rounds=50,
)
model.fit(X_train, y_train, eval_set=(X_val, y_val))
```
**Use quando**: muitas features categóricas, sem necessidade de encoding manual, datasets médios.

---

### SVM
```python
from sklearn.svm import SVC, LinearSVC

# Kernel RBF — bom para não-linearidades, lento em grandes datasets
model = SVC(C=1.0, kernel="rbf", gamma="scale", probability=True, class_weight="balanced")

# Linear — rápido, bom para texto (TF-IDF)
model = LinearSVC(C=1.0, class_weight="balanced", max_iter=2000)
```
**Use quando**: dados pequenos (<10k), alta dimensionalidade (texto), separação não-linear clara.

---

## Algoritmos de Regressão

### Ridge / Lasso / ElasticNet
```python
from sklearn.linear_model import Ridge, Lasso, ElasticNet, RidgeCV

# Ridge — L2, todos os coeficientes pequenos
model = Ridge(alpha=1.0)

# Lasso — L1, feature selection automático (coeficientes zerados)
model = Lasso(alpha=0.1)

# ElasticNet — combina L1 e L2
model = ElasticNet(alpha=0.1, l1_ratio=0.5)

# RidgeCV — escolhe alpha automaticamente por CV
model = RidgeCV(alphas=[0.1, 1.0, 10.0, 100.0], cv=5)
```

### XGBoost para Regressão
```python
from xgboost import XGBRegressor

model = XGBRegressor(
    n_estimators=500,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="reg:squarederror",  # "reg:absoluteerror" para MAE, "reg:tweedie" para contagem
    random_state=42,
    n_jobs=-1,
)
```

### Regressão Quantílica (predizer intervalos)
```python
from sklearn.linear_model import QuantileRegressor

# Mediana (q=0.5) — robusta a outliers
model_median = QuantileRegressor(quantile=0.5, alpha=0.1)

# Intervalo de confiança 90%
model_lower = QuantileRegressor(quantile=0.05, alpha=0.1)
model_upper = QuantileRegressor(quantile=0.95, alpha=0.1)
```

---

## Algoritmos Não Supervisionados

### K-Means
```python
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# Encontrar K ótimo (método do cotovelo + silhouette)
inertias, silhouettes = [], []
K_range = range(2, 11)
for k in K_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)
    inertias.append(km.inertia_)
    silhouettes.append(silhouette_score(X_scaled, labels))

# Modelo final
km = KMeans(n_clusters=4, random_state=42, n_init=10)
df["cluster"] = km.fit_predict(X_scaled)
```

### DBSCAN (clusters de formato arbitrário)
```python
from sklearn.cluster import DBSCAN

dbscan = DBSCAN(
    eps=0.5,            # raio de vizinhança — ajustar com NearestNeighbors
    min_samples=5,      # mínimo de pontos para core point
    metric="euclidean",
    n_jobs=-1,
)
labels = dbscan.fit_predict(X_scaled)
n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
n_noise = list(labels).count(-1)
print(f"Clusters: {n_clusters}, Ruído: {n_noise}")
```

### PCA (Redução de Dimensionalidade)
```python
from sklearn.decomposition import PCA

# Quanto de variância explicar?
pca = PCA()
pca.fit(X_scaled)
cumvar = pca.explained_variance_ratio_.cumsum()
n_components = (cumvar < 0.95).sum() + 1  # 95% de variância explicada
print(f"Componentes para 95% variância: {n_components}")

# Reduzir
pca = PCA(n_components=n_components)
X_reduced = pca.fit_transform(X_scaled)
```

### UMAP (preserva estrutura local e global)
```python
import umap  # pip install umap-learn

reducer = umap.UMAP(
    n_components=2,     # 2 para visualização
    n_neighbors=15,     # balance local-global: menor = mais local
    min_dist=0.1,       # compactação dos clusters
    metric="euclidean",
    random_state=42,
)
X_2d = reducer.fit_transform(X_scaled)
```

---

## Séries Temporais

### Prophet (Facebook/Meta)
```python
from prophet import Prophet  # pip install prophet

# Formato obrigatório: colunas "ds" (data) e "y" (valor)
df_prophet = df.rename(columns={"date": "ds", "value": "y"})

model = Prophet(
    seasonality_mode="multiplicative",  # ou "additive"
    yearly_seasonality=True,
    weekly_seasonality=True,
    daily_seasonality=False,
    changepoint_prior_scale=0.05,       # sensibilidade a mudanças de tendência
)
model.fit(df_prophet[df_prophet["ds"] < "2024-01-01"])

future = model.make_future_dataframe(periods=90, freq="D")
forecast = model.predict(future)
model.plot(forecast)
model.plot_components(forecast)
```

### LSTM para Séries Temporais
```python
import numpy as np
import torch
import torch.nn as nn

def create_sequences(data, seq_len=30, horizon=7):
    X, y = [], []
    for i in range(len(data) - seq_len - horizon + 1):
        X.append(data[i : i + seq_len])
        y.append(data[i + seq_len : i + seq_len + horizon])
    return np.array(X), np.array(y)

class LSTMForecaster(nn.Module):
    def __init__(self, input_size=1, hidden_size=64, num_layers=2, horizon=7):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=0.2)
        self.fc = nn.Linear(hidden_size, horizon)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])
```

---

## Anomaly Detection

```python
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM

# Isolation Forest (rápido, boa performance)
iso = IsolationForest(
    n_estimators=200,
    contamination=0.05,   # fração esperada de anomalias
    random_state=42,
    n_jobs=-1,
)
df["anomaly"] = iso.fit_predict(X)  # -1 = anomalia, 1 = normal

# Local Outlier Factor (bom para anomalias locais)
lof = LocalOutlierFactor(n_neighbors=20, contamination=0.05, n_jobs=-1)
df["anomaly"] = lof.fit_predict(X)

# One-Class SVM (lento, bom para alta dimensionalidade)
oc_svm = OneClassSVM(kernel="rbf", gamma="scale", nu=0.05)
df["anomaly"] = oc_svm.fit_predict(X)
```

---

## Ensemble Methods

### Voting
```python
from sklearn.ensemble import VotingClassifier

ensemble = VotingClassifier(
    estimators=[
        ("lr", LogisticRegression(random_state=42)),
        ("rf", RandomForestClassifier(n_estimators=100, random_state=42)),
        ("xgb", XGBClassifier(random_state=42)),
    ],
    voting="soft",   # usa probabilidades (melhor); "hard" usa classe majoritária
    n_jobs=-1,
)
```

### Stacking
```python
from sklearn.ensemble import StackingClassifier

stacking = StackingClassifier(
    estimators=[
        ("rf", RandomForestClassifier(n_estimators=200, random_state=42)),
        ("xgb", XGBClassifier(n_estimators=200, random_state=42)),
        ("lgb", LGBMClassifier(n_estimators=200, random_state=42)),
    ],
    final_estimator=LogisticRegression(C=0.1),  # meta-learner
    cv=5,
    n_jobs=-1,
)
```
