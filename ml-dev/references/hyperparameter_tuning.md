# Tuning de Hiperparâmetros

## Estratégias em Ordem de Recomendação

```
1. Optuna (Bayesian)   → melhor custo-benefício, qualquer modelo
2. RandomizedSearchCV  → rápido, quando Optuna não disponível
3. GridSearchCV        → espaço pequeno (<50 combinações)
4. HalvingSearch       → datasets grandes, muitos parâmetros
5. Ray Tune            → distributed / GPU clusters
```

---

## Optuna (Recomendado)

```python
import optuna
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.pipeline import Pipeline
import lightgbm as lgb

optuna.logging.set_verbosity(optuna.logging.WARNING)

def objective(trial):
    params = {
        "n_estimators":      trial.suggest_int("n_estimators", 100, 1000, step=50),
        "num_leaves":        trial.suggest_int("num_leaves", 20, 150),
        "learning_rate":     trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "feature_fraction":  trial.suggest_float("feature_fraction", 0.5, 1.0),
        "bagging_fraction":  trial.suggest_float("bagging_fraction", 0.5, 1.0),
        "bagging_freq":      trial.suggest_int("bagging_freq", 1, 10),
        "min_child_samples": trial.suggest_int("min_child_samples", 5, 100),
        "lambda_l1":         trial.suggest_float("lambda_l1", 1e-8, 10.0, log=True),
        "lambda_l2":         trial.suggest_float("lambda_l2", 1e-8, 10.0, log=True),
    }

    model = Pipeline([
        ("preprocessor", preprocessor),
        ("model", lgb.LGBMClassifier(
            **params,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
            verbose=-1,
        )),
    ])

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="roc_auc", n_jobs=-1)
    return scores.mean()

# Criar estudo e otimizar
study = optuna.create_study(
    direction="maximize",
    sampler=optuna.samplers.TPESampler(seed=42),
    pruner=optuna.pruners.MedianPruner(n_warmup_steps=5),
)
study.optimize(objective, n_trials=100, timeout=3600, show_progress_bar=True)

print(f"\nMelhor ROC-AUC: {study.best_value:.4f}")
print("Melhores parâmetros:")
for k, v in study.best_params.items():
    print(f"  {k}: {v}")

# Visualizações do Optuna
optuna.visualization.plot_optimization_history(study).show()
optuna.visualization.plot_param_importances(study).show()
optuna.visualization.plot_contour(study, params=["learning_rate", "num_leaves"]).show()

# Treinar modelo final com melhores parâmetros
best_model = Pipeline([
    ("preprocessor", preprocessor),
    ("model", lgb.LGBMClassifier(**study.best_params, random_state=42, verbose=-1)),
])
best_model.fit(X_train, y_train)
```

---

## RandomizedSearchCV

```python
from sklearn.model_selection import RandomizedSearchCV
from scipy.stats import randint, uniform, loguniform
from xgboost import XGBClassifier

param_distributions = {
    "model__n_estimators":      randint(100, 800),
    "model__max_depth":         randint(3, 10),
    "model__learning_rate":     loguniform(0.01, 0.3),
    "model__subsample":         uniform(0.6, 0.4),       # [0.6, 1.0]
    "model__colsample_bytree":  uniform(0.5, 0.5),       # [0.5, 1.0]
    "model__min_child_weight":  randint(1, 20),
    "model__gamma":             loguniform(1e-4, 1.0),
    "model__reg_alpha":         loguniform(1e-8, 10.0),
    "model__reg_lambda":        loguniform(1e-8, 10.0),
}

search = RandomizedSearchCV(
    full_pipeline,
    param_distributions,
    n_iter=60,
    cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
    scoring="roc_auc",
    n_jobs=-1,
    random_state=42,
    verbose=2,
    refit=True,   # re-treina com melhores params no dataset completo
)
search.fit(X_train, y_train)

print(f"Melhor ROC-AUC: {search.best_score_:.4f}")
print(search.best_params_)

# Analisar resultados
cv_results = pd.DataFrame(search.cv_results_).sort_values("rank_test_score")
print(cv_results[["params", "mean_test_score", "std_test_score"]].head(10))
```

---

## GridSearchCV (espaço pequeno)

```python
from sklearn.model_selection import GridSearchCV

param_grid = {
    "model__C":     [0.01, 0.1, 1.0, 10.0, 100.0],
    "model__kernel": ["linear", "rbf"],
    "model__gamma": ["scale", "auto"],
}

grid = GridSearchCV(
    pipeline,
    param_grid,
    cv=5,
    scoring="f1_weighted",
    n_jobs=-1,
    refit=True,
    verbose=1,
)
grid.fit(X_train, y_train)
print(grid.best_params_, grid.best_score_)
```

---

## HalvingRandomSearchCV (datasets grandes)

```python
from sklearn.model_selection import HalvingRandomSearchCV

halving = HalvingRandomSearchCV(
    estimator=pipeline,
    param_distributions=param_distributions,
    n_candidates=200,       # começa com 200 configurações
    factor=3,               # a cada round, mantém 1/3 das melhores
    scoring="roc_auc",
    cv=5,
    n_jobs=-1,
    random_state=42,
    verbose=2,
)
halving.fit(X_train, y_train)
print(halving.best_params_)
```

---

## Early Stopping (XGBoost / LightGBM)

```python
# Evitar tuning manual de n_estimators com early stopping
from sklearn.model_selection import train_test_split
import lightgbm as lgb

X_tr, X_val, y_tr, y_val = train_test_split(X_train, y_train, test_size=0.15, random_state=42)

# Converter para Dataset LightGBM nativo (mais rápido)
dtrain = lgb.Dataset(X_tr, label=y_tr)
dval   = lgb.Dataset(X_val, label=y_val, reference=dtrain)

params = {
    "objective": "binary",
    "metric": "auc",
    "num_leaves": 63,
    "learning_rate": 0.05,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 5,
    "verbose": -1,
}

callbacks = [
    lgb.early_stopping(stopping_rounds=50, verbose=True),
    lgb.log_evaluation(period=100),
]

booster = lgb.train(
    params,
    dtrain,
    num_boost_round=2000,
    valid_sets=[dval],
    callbacks=callbacks,
)

print(f"Melhor iteração: {booster.best_iteration}")
print(f"Melhor AUC val: {booster.best_score['valid_0']['auc']:.4f}")
```

---

## Parâmetros Chave por Modelo

### XGBoost
```
n_estimators      → 100–2000 (use early stopping)
max_depth         → 3–8  (menor = mais regularização)
learning_rate     → 0.01–0.3 (menor lr + mais árvores = melhor)
subsample         → 0.6–1.0
colsample_bytree  → 0.5–1.0
min_child_weight  → 1–20 (maior = mais regularização)
gamma             → 0–5  (maior = mais regularização)
reg_alpha         → 0–10 (L1, para sparsity)
reg_lambda        → 0–10 (L2, padrão)
scale_pos_weight  → neg_count / pos_count (desbalanceamento)
```

### LightGBM
```
n_estimators      → 100–3000 (use early stopping)
num_leaves        → 20–300  (PRINCIPAL controle de complexidade)
learning_rate     → 0.01–0.3
feature_fraction  → 0.5–1.0
bagging_fraction  → 0.5–1.0
bagging_freq      → 1–10
min_child_samples → 10–100 (maior = mais regularização)
lambda_l1/l2      → 0–10
max_bin           → 100–500 (mais bins = mais preciso, mais lento)
```

### Random Forest
```
n_estimators      → 100–500 (mais = melhor até platô, depois só mais lento)
max_depth         → None ou 5–30
min_samples_leaf  → 1–20
min_samples_split → 2–20
max_features      → "sqrt", "log2", 0.3–0.8
bootstrap         → True (padrão)
```

### Redes Neurais (PyTorch)
```
learning_rate     → 1e-5 a 1e-1 (log scale)
batch_size        → 16, 32, 64, 128, 256
n_layers          → 1–10
hidden_size       → 32–1024
dropout           → 0.0–0.5
weight_decay      → 1e-6 a 1e-2 (L2 regularização)
optimizer         → Adam (padrão), AdamW (transformers), SGD+momentum
scheduler         → cosine annealing, reduce on plateau, warmup
```

---

## Registro de Experimentos com MLflow

```python
import mlflow
import mlflow.sklearn

mlflow.set_experiment("classificacao-churn")

with mlflow.start_run(run_name="lgbm_optuna_v3"):
    # Logar parâmetros
    mlflow.log_params(study.best_params)
    mlflow.log_param("n_trials", 100)
    mlflow.log_param("cv_folds", 5)

    # Logar métricas
    mlflow.log_metrics({
        "cv_roc_auc": study.best_value,
        "test_roc_auc": roc_auc_score(y_test, y_proba),
        "test_f1": f1_score(y_test, y_pred, average="weighted"),
    })

    # Logar o modelo
    mlflow.sklearn.log_model(best_model, "model")

    # Logar artefatos
    mlflow.log_artifact("reports/evaluation.png")
    mlflow.log_artifact("reports/learning_curve.png")

print("Experimento registrado! Execute: mlflow ui")
```

---

## Dicas para Tuning Eficiente

1. **Comece com parâmetros de regularização** — eles têm maior impacto
2. **Use early stopping** para n_estimators de GBMs — elimina um hiperparâmetro
3. **Fix learning_rate baixo** (0.05) e tune os demais primeiro
4. **Budget de trials**: 30–50 para Optuna (TPE) ≈ 100–150 para Random Search
5. **Nested CV**: se dataset pequeno, use CV externo para estimar generalização
6. **Não faça tuning no test set** — use sempre CV no treino
7. **Registre TODOS os experimentos** no MLflow — você vai se arrepender se não fizer
