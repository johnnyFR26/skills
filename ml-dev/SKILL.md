---
name: ml-dev
description: >
  Skill completa para desenvolvimento de Machine Learning end-to-end. Use esta skill sempre que o
  usuário mencionar ML, machine learning, deep learning, redes neurais, modelos preditivos,
  classificação, regressão, clustering, NLP, visão computacional, séries temporais, feature
  engineering, treinamento de modelos, avaliação de modelos, scikit-learn, PyTorch, TensorFlow,
  Keras, XGBoost, LightGBM, dados de treino/teste, métricas como acurácia/F1/AUC/RMSE,
  overfitting, underfitting, ou qualquer tarefa que envolva aprender padrões de dados.
  Também use para análise exploratória de dados (EDA), pipelines de ML, MLOps básico,
  seleção de algoritmos, tuning de hiperparâmetros, ou quando o usuário quiser "prever",
  "classificar", "detectar anomalias" ou "recomendar" algo com base em dados históricos.
compatibility:
  python: ">=3.9"
  tools: [bash_tool, create_file, present_files]
---

# Machine Learning Development Skill

Skill end-to-end para desenvolvimento de ML: da exploração dos dados ao deploy do modelo.

---

## Índice de Arquivos de Referência

Leia o arquivo relevante conforme a etapa do projeto:

| Etapa | Arquivo | Quando ler |
|-------|---------|-----------|
| Exploração de Dados | `references/eda.md` | Análise inicial, visualizações, entendimento do dataset |
| Pré-processamento | `references/preprocessing.md` | Limpeza, encoding, normalização, feature engineering |
| Seleção de Algoritmos | `references/algorithms.md` | Qual modelo usar para cada problema |
| Frameworks | `references/frameworks.md` | sklearn, PyTorch, TensorFlow, XGBoost — padrões e APIs |
| Avaliação & Métricas | `references/evaluation.md` | Métricas, validação cruzada, diagnóstico de erros |
| Hiperparâmetros | `references/hyperparameter_tuning.md` | Grid/Random/Bayesian search, Optuna, Ray Tune |
| Deploy & MLOps | `references/mlops.md` | Serialização, APIs, monitoramento, drift detection |
| Templates de Código | `templates/` | Boilerplate pronto para copiar e adaptar |

---

## Workflow Padrão de ML

Siga este fluxo em ordem; cada etapa informa a próxima.

```
1. ENTENDER O PROBLEMA
   └─ Tipo de tarefa → Dados disponíveis → Métricas de negócio

2. EDA (Exploração de Dados)
   └─ Shape, tipos, nulos, distribuições, correlações, outliers

3. PRÉ-PROCESSAMENTO
   └─ Limpeza → Encoding → Scaling → Feature Engineering → Split

4. BASELINE MODEL
   └─ Modelo simples primeiro (DummyClassifier / média) → referência

5. MODELAGEM
   └─ Selecionar algoritmos → Treinar → Validação cruzada

6. AVALIAÇÃO
   └─ Métricas no test set → Diagnóstico (bias/variance) → Análise de erros

7. TUNING
   └─ Hiperparâmetros → Feature selection → Ensemble

8. DEPLOY (se necessário)
   └─ Serialização → API → Monitoramento
```

---

## Etapa 1: Entender o Problema

Antes de qualquer código, classifique o problema:

### Tipo de Tarefa

| Pergunta | Tipo | Algoritmos típicos |
|----------|------|-------------------|
| Prever um número | **Regressão** | Linear Reg, XGBoost, SVR, RF |
| Classificar em categorias | **Classificação** | Logistic Reg, RF, XGBoost, SVM |
| Agrupar sem rótulos | **Clustering** | K-Means, DBSCAN, Hierarchical |
| Reduzir dimensões | **Redução dim.** | PCA, UMAP, t-SNE, Autoencoder |
| Gerar/completar texto | **NLP/Generativo** | Transformers, LLMs, fine-tuning |
| Detectar padrões em imagens | **Visão Computacional** | CNNs, YOLO, ViT, SAM |
| Prever valores no tempo | **Série Temporal** | ARIMA, Prophet, LSTM, N-BEATS |
| Detectar anomalias | **Anomaly Detection** | IsolationForest, Autoencoder, LOF |
| Otimizar ações sequenciais | **Reforço** | PPO, DQN, A3C |

### Perguntas de Diagnóstico

Faça estas perguntas ao usuário (ou infira do contexto) antes de sugerir qualquer modelo:

1. **Dados**: Quantos exemplos? Quantas features? Dados estruturados ou não?
2. **Rótulos**: Supervisionado (tem y)? Semi-supervisionado? Não supervisionado?
3. **Balanceamento**: Classes balanceadas? Qual proporção positivo/negativo?
4. **Latência**: Inferência em batch ou real-time? Qual latência aceitável?
5. **Interpretabilidade**: Precisa explicar o modelo? Regulatório?
6. **Recursos**: CPU/GPU disponível? Memória? Restrições de deployment?
7. **Baseline existente**: Já há um modelo? Qual performance atual?

---

## Etapa 2: Setup do Ambiente

### Instalação padrão (copie conforme necessidade)

```bash
# ML clássico
pip install numpy pandas scikit-learn matplotlib seaborn scipy joblib

# Gradient boosting (recomendado para tabular)
pip install xgboost lightgbm catboost

# Deep learning
pip install torch torchvision           # PyTorch
pip install tensorflow keras            # TensorFlow/Keras

# Utilidades
pip install optuna                      # Hyperparameter tuning bayesiano
pip install mlflow                      # Experiment tracking
pip install shap                        # Interpretabilidade
pip install imbalanced-learn            # Dados desbalanceados
pip install yellowbrick                 # Visualizações ML
```

### Estrutura de Projeto Recomendada

```
projeto-ml/
├── data/
│   ├── raw/          # dados originais (nunca modificar)
│   ├── processed/    # dados após preprocessing
│   └── external/     # dados externos/enriquecimento
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_preprocessing.ipynb
│   ├── 03_modeling.ipynb
│   └── 04_evaluation.ipynb
├── src/
│   ├── data.py       # loading e preprocessing
│   ├── features.py   # feature engineering
│   ├── models.py     # definição e treinamento
│   └── evaluate.py   # métricas e visualizações
├── models/           # modelos serializados
├── reports/          # figuras e relatórios
├── requirements.txt
└── README.md
```

---

## Etapa 3: EDA Rápida (Template)

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv("data/raw/dataset.csv")

# --- Shape e tipos ---
print(f"Shape: {df.shape}")
print(df.dtypes.value_counts())
print(df.head())

# --- Valores nulos ---
null_pct = (df.isnull().sum() / len(df) * 100).sort_values(ascending=False)
print(null_pct[null_pct > 0])

# --- Estatísticas descritivas ---
print(df.describe())

# --- Distribuição do target ---
target = "target_column"  # <-- ajustar
print(df[target].value_counts(normalize=True))

# --- Correlações (features numéricas) ---
plt.figure(figsize=(12, 8))
sns.heatmap(df.select_dtypes("number").corr(), annot=True, fmt=".2f", cmap="coolwarm")
plt.title("Correlation Matrix")
plt.tight_layout()
plt.savefig("reports/correlation_matrix.png", dpi=150)
```

> **Ver referência completa**: `references/eda.md`

---

## Etapa 4: Pré-processamento (Pipeline Sklearn)

```python
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelEncoder
from sklearn.impute import SimpleImputer

# Identificar tipos de colunas
num_cols = df.select_dtypes("number").columns.drop(target).tolist()
cat_cols = df.select_dtypes("object").columns.tolist()

# Pipeline numérico
num_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler()),
])

# Pipeline categórico
cat_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
])

# Preprocessor combinado
preprocessor = ColumnTransformer([
    ("num", num_pipeline, num_cols),
    ("cat", cat_pipeline, cat_cols),
])
```

> **Ver referência completa**: `references/preprocessing.md`

---

## Etapa 5: Treinamento e Validação

```python
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report
import numpy as np

# Split
X = df.drop(columns=[target])
y = df[target]
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y  # stratify apenas para classificação
)

# Pipeline completo (preprocessor + modelo)
from sklearn.ensemble import RandomForestClassifier

model_pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("model", RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)),
])

# Validação cruzada estratificada (NÃO use apenas train/val split)
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(model_pipeline, X_train, y_train, cv=cv, scoring="f1_weighted")
print(f"CV F1: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

# Treinar no conjunto completo de treino
model_pipeline.fit(X_train, y_train)

# Avaliar no test set (use apenas UMA VEZ no final)
y_pred = model_pipeline.predict(X_test)
print(classification_report(y_test, y_pred))
```

> **Ver seleção de algoritmos**: `references/algorithms.md`  
> **Ver métricas detalhadas**: `references/evaluation.md`

---

## Etapa 6: Diagnóstico de Overfitting/Underfitting

```
                        Alto Bias (Underfitting)    Alto Variance (Overfitting)
Train score             Baixo                       Alto
Test score              Baixo                       Baixo (muito menor que train)
Gap train-test          Pequeno                     Grande

Solução Underfitting    → Modelo mais complexo, mais features, menos regularização
Solução Overfitting     → Mais dados, regularização, dropout, simplificar modelo,
                          feature selection, early stopping
```

---

## Etapa 7: Serialização e Deploy Básico

```python
import joblib

# Salvar (funciona para qualquer pipeline sklearn)
joblib.dump(model_pipeline, "models/model_v1.pkl")

# Carregar e usar
loaded_model = joblib.load("models/model_v1.pkl")
predictions = loaded_model.predict(new_data)

# Para PyTorch: torch.save(model.state_dict(), "models/model.pt")
# Para TensorFlow: model.save("models/model_tf/")
```

> **Ver guia completo de MLOps**: `references/mlops.md`

---

## Regras Gerais (Nunca Ignore)

1. **Nunca vaze dados do test set no treino** — split ANTES de qualquer preprocessing
2. **Use pipeline sklearn** para evitar data leakage automático
3. **Valide com CV, não com um único val split** — reduz variância da estimativa
4. **Avalie no test set apenas uma vez** — ao final, não durante desenvolvimento
5. **Sempre calcule baseline** (dummy/média) antes de modelos complexos
6. **Documente experimentos** — use MLflow ou um CSV simples com parâmetros/métricas
7. **Salve seeds** (`random_state=42`) para reprodutibilidade
8. **Verifique distribuição de y_train e y_test** — garante representatividade
9. **Analise erros** — não só métricas agregadas; inspecione o que o modelo erra

---

## Seleção Rápida de Modelo por Situação

```
Dado tabular, < 10k exemplos         → Random Forest, XGBoost, LightGBM
Dado tabular, > 100k exemplos        → LightGBM, CatBoost, Redes Neurais
Alta interpretabilidade necessária   → Regressão Logística, Árvore de Decisão, SHAP
Dados muito desbalanceados           → SMOTE + XGBoost, ajuste class_weight, PR-AUC
NLP / Texto                          → TF-IDF + LR (baseline), BERT, sentence-transformers
Imagens                              → CNN (ResNet/EfficientNet), Vision Transformer
Séries temporais                     → Prophet (univariado), N-BEATS, LSTM, TFT
Anomaly detection                    → IsolationForest, Autoencoder, LOF
Poucos dados rotulados               → Transfer learning, semi-supervised, data augmentation
```

---

## Convenções de Output

Ao escrever código ML para o usuário:

- **Sempre use pipelines sklearn** para preprocessamento + modelo juntos
- **Inclua comentários** explicando decisões (por que median vs mean, etc.)
- **Mostre métricas principais** na saída: para classificação → F1, Precision, Recall, AUC; para regressão → RMSE, MAE, R²
- **Salve artefatos** (modelo serializado, figuras) em paths claros
- **Informe o usuário** sobre assunções feitas (e.g., "assumi classificação binária")
- **Sugira próximos passos** ao finalizar cada etapa
- Prefira código **executável e completo** a fragmentos isolados
