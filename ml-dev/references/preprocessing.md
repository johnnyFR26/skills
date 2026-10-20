# Pré-processamento e Feature Engineering

## Princípio Fundamental: Evitar Data Leakage

```python
# ✅ CORRETO — split ANTES de qualquer fit
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
preprocessor.fit(X_train)           # fit APENAS no treino
X_train_proc = preprocessor.transform(X_train)
X_test_proc  = preprocessor.transform(X_test)   # aplica parâmetros do treino

# ❌ ERRADO — preprocessar tudo, depois splittar
X_proc = preprocessor.fit_transform(X)  # vaza estatísticas do test no treino!
X_train_proc, X_test_proc = train_test_split(X_proc, ...)
```

**Regra de ouro**: `fit` → apenas no train. `transform` → em todos os sets.

---

## Imputação de Valores Nulos

```python
from sklearn.impute import SimpleImputer, KNNImputer

# Numérico: median é mais robusto que mean
imputer_num = SimpleImputer(strategy="median")

# Categórico: most_frequent ou constante
imputer_cat = SimpleImputer(strategy="most_frequent")
# imputer_cat = SimpleImputer(strategy="constant", fill_value="MISSING")

# KNN (melhor, mas mais lento)
imputer_knn = KNNImputer(n_neighbors=5)

# IterativeImputer (MICE — melhor ainda, experimental)
from sklearn.experimental import enable_iterative_imputer  # noqa
from sklearn.impute import IterativeImputer
imputer_mice = IterativeImputer(max_iter=10, random_state=42)
```

**Dica**: Para features com muitos nulos (>15%), crie uma feature binária indicando ausência:
```python
df["col_missing"] = df["col"].isnull().astype(int)
```

---

## Encoding de Variáveis Categóricas

```python
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, LabelEncoder
from sklearn.preprocessing import TargetEncoder  # sklearn >= 1.3

# OneHotEncoder — nominais, baixa cardinalidade (< 20 valores únicos)
ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False, drop="first")

# OrdinalEncoder — ordinais com ordem conhecida
oe = OrdinalEncoder(categories=[["low", "medium", "high"]])

# TargetEncoder — alta cardinalidade, supervisionado
te = TargetEncoder(target_type="continuous")  # ou "binary", "multiclass"

# LabelEncoder — APENAS para o target (y), não para features X
le = LabelEncoder()

# Hash encoding — altíssima cardinalidade (IDs, URLs)
from sklearn.feature_extraction import FeatureHasher
fh = FeatureHasher(n_features=64, input_type="string")
```

**Quando usar qual:**
| Tipo | Cardinalidade | Encoder |
|------|--------------|---------|
| Nominal | < 10 | OneHot |
| Nominal | 10-100 | Target / Hash |
| Nominal | > 100 | Target / Hash / Embedding |
| Ordinal | Qualquer | Ordinal |
| Target (y) classificação | - | LabelEncoder |

---

## Scaling / Normalização

```python
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler, PowerTransformer

# StandardScaler — z-score, maioria dos casos
scaler = StandardScaler()

# MinMaxScaler — quando precisa de [0, 1], ex: redes neurais
scaler = MinMaxScaler()

# RobustScaler — resistente a outliers (usa IQR)
scaler = RobustScaler()

# PowerTransformer — aproxima distribuição normal (Yeo-Johnson)
pt = PowerTransformer(method="yeo-johnson")
# Box-Cox requer valores positivos
pt = PowerTransformer(method="box-cox")
```

**Quando usar:**
- **StandardScaler**: default para a maioria dos modelos lineares, SVM, KNN, PCA, redes neurais
- **RobustScaler**: quando há outliers relevantes
- **PowerTransformer**: features com distribuição muito assimétrica (skewness > |1|)
- **NÃO é necessário**: árvores de decisão, Random Forest, XGBoost, LightGBM

---

## Feature Engineering

### Variáveis de Data/Tempo

```python
df["date"] = pd.to_datetime(df["date"])

df["year"]          = df["date"].dt.year
df["month"]         = df["date"].dt.month
df["day_of_week"]   = df["date"].dt.dayofweek   # 0=segunda, 6=domingo
df["day_of_year"]   = df["date"].dt.dayofyear
df["quarter"]       = df["date"].dt.quarter
df["is_weekend"]    = df["day_of_week"].isin([5, 6]).astype(int)

# Encoding cíclico (melhor que linear para meses/horas)
import numpy as np
df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
df["hour_sin"]  = np.sin(2 * np.pi * df["hour"] / 24)
df["hour_cos"]  = np.cos(2 * np.pi * df["hour"] / 24)
```

### Interações entre Features

```python
# Produto de duas features
df["feat_A_x_B"] = df["feat_A"] * df["feat_B"]

# Razão (cuidado com divisão por zero)
df["ratio_AB"] = df["feat_A"] / (df["feat_B"] + 1e-6)

# Diferença
df["diff_AB"] = df["feat_A"] - df["feat_B"]

# Polinomiais (use com cuidado, expande muito o espaço)
from sklearn.preprocessing import PolynomialFeatures
poly = PolynomialFeatures(degree=2, include_bias=False)
X_poly = poly.fit_transform(X[["feat_A", "feat_B"]])
```

### Agregações por Grupo (muito poderoso para tabular)

```python
# Estatísticas por grupo
agg = df.groupby("categoria")["valor"].agg(["mean", "std", "max", "min"]).reset_index()
agg.columns = ["categoria", "val_mean", "val_std", "val_max", "val_min"]
df = df.merge(agg, on="categoria", how="left")

# Contagem de ocorrências
df["count_per_categoria"] = df.groupby("categoria")["categoria"].transform("count")
```

### Transformações Matemáticas

```python
# Log (para distribuições assimétricas positivas, ex: preço, renda)
df["log_valor"] = np.log1p(df["valor"])          # log(x+1), evita log(0)

# Raiz quadrada (suaviza menos que log)
df["sqrt_valor"] = np.sqrt(df["valor"])

# Binarização
df["alto_valor"] = (df["valor"] > df["valor"].median()).astype(int)

# Binning / Discretização
df["valor_bin"] = pd.cut(df["valor"], bins=5, labels=["muito_baixo","baixo","medio","alto","muito_alto"])
df["valor_qbin"] = pd.qcut(df["valor"], q=4, labels=["Q1","Q2","Q3","Q4"])  # quantis
```

### Features para NLP (bag-of-words)

```python
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer

# TF-IDF (melhor que CountVectorizer na maioria dos casos)
tfidf = TfidfVectorizer(
    max_features=10_000,
    ngram_range=(1, 2),       # unigramas e bigramas
    min_df=2,                 # ignora termos que aparecem < 2 vezes
    max_df=0.95,              # ignora termos que aparecem em > 95% dos docs
    strip_accents="unicode",
    lowercase=True,
)
X_tfidf = tfidf.fit_transform(df["text"])
```

---

## Feature Selection

### Métodos de Filtro (rápidos, independentes do modelo)

```python
from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif
from sklearn.feature_selection import VarianceThreshold

# Remove features com variância quase zero
vt = VarianceThreshold(threshold=0.01)
X_var = vt.fit_transform(X)

# Seleciona K melhores por teste F (rápido)
selector = SelectKBest(score_func=f_classif, k=20)
X_selected = selector.fit_transform(X_train, y_train)

# Mutual information (captura não-linearidades)
selector_mi = SelectKBest(score_func=mutual_info_classif, k=20)
```

### Importância do Modelo (embedded)

```python
import shap
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Importância de feature (built-in)
importances = pd.Series(model.feature_importances_, index=feature_names)
importances.sort_values(ascending=False).head(20).plot(kind="bar")

# SHAP values (mais interpretável)
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)
shap.summary_plot(shap_values[1], X_test, feature_names=feature_names)
```

### Recursive Feature Elimination

```python
from sklearn.feature_selection import RFECV

rfecv = RFECV(
    estimator=RandomForestClassifier(n_estimators=50, random_state=42),
    step=1,
    cv=5,
    scoring="f1_weighted",
    n_jobs=-1,
)
rfecv.fit(X_train, y_train)
print(f"Features selecionadas: {rfecv.n_features_}")
X_selected = rfecv.transform(X_train)
```

---

## Dados Desbalanceados

```python
# Verificar desbalanceamento
print(y_train.value_counts(normalize=True))

# Opção 1: class_weight (mais simples, direto no modelo)
from sklearn.ensemble import RandomForestClassifier
model = RandomForestClassifier(class_weight="balanced", random_state=42)

# Opção 2: Oversampling (SMOTE)
from imblearn.over_sampling import SMOTE
sm = SMOTE(random_state=42, k_neighbors=5)
X_resampled, y_resampled = sm.fit_resample(X_train_proc, y_train)

# Opção 3: Undersampling
from imblearn.under_sampling import RandomUnderSampler
rus = RandomUnderSampler(random_state=42)
X_resampled, y_resampled = rus.fit_resample(X_train_proc, y_train)

# Opção 4: Combinar (SMOTEENN ou SMOTETomek)
from imblearn.combine import SMOTETomek
smk = SMOTETomek(random_state=42)
X_resampled, y_resampled = smk.fit_resample(X_train_proc, y_train)
```

**Recomendação prática:**
1. Primeiro tente `class_weight="balanced"` — simples e eficaz
2. Se não funcionar, use SMOTE no conjunto de treino (nunca no test)
3. Prefira PR-AUC / F1 como métrica (não acurácia) para dados desbalanceados

---

## Pipeline Completo (Template de Produção)

```python
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from xgboost import XGBClassifier

# Definir colunas
num_cols = ["age", "income", "score"]
cat_cols = ["city", "product", "channel"]

# Sub-pipelines
num_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler()),
])

cat_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="constant", fill_value="MISSING")),
    ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
])

preprocessor = ColumnTransformer([
    ("num", num_pipeline, num_cols),
    ("cat", cat_pipeline, cat_cols),
], remainder="drop")  # drop colunas não especificadas

# Pipeline final
full_pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("model", XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=neg_count / pos_count,  # para desbalanceamento
        random_state=42,
        n_jobs=-1,
    )),
])

# Treinar
full_pipeline.fit(X_train, y_train)

# Salvar tudo (preprocessor + modelo juntos)
import joblib
joblib.dump(full_pipeline, "models/pipeline_v1.pkl")
```
