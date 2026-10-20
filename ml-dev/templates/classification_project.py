"""
Template completo: Projeto de Classificação Binária
====================================================
Copie este arquivo, ajuste as seções marcadas com "# AJUSTAR"
e execute seção por seção em um notebook ou script.
"""

# ── IMPORTS ─────────────────────────────────────────────────
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import joblib
import json
from datetime import datetime

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.metrics import (
    classification_report, roc_auc_score, average_precision_score,
    f1_score, RocCurveDisplay, PrecisionRecallDisplay, ConfusionMatrixDisplay,
)
import lightgbm as lgb
import optuna
import shap

optuna.logging.set_verbosity(optuna.logging.WARNING)
Path("models").mkdir(exist_ok=True)
Path("reports").mkdir(exist_ok=True)
sns.set_theme(style="whitegrid")


# ════════════════════════════════════════════════════════════
# 1. CARREGAR DADOS                          # AJUSTAR
# ════════════════════════════════════════════════════════════
df = pd.read_csv("data/raw/dataset.csv")     # AJUSTAR: path do arquivo
TARGET = "churn"                              # AJUSTAR: nome da coluna target

print(f"Shape: {df.shape}")
print(f"\nTarget:\n{df[TARGET].value_counts(normalize=True).round(3)}")
print(f"\nNulos (%):\n{(df.isnull().mean() * 100).sort_values(ascending=False).head(10)}")


# ════════════════════════════════════════════════════════════
# 2. EDA RÁPIDA
# ════════════════════════════════════════════════════════════
# Distribuições numéricas
num_cols = df.select_dtypes("number").columns.drop(TARGET).tolist()
cat_cols = df.select_dtypes("object").columns.tolist()

fig, axes = plt.subplots(1, min(len(num_cols), 4), figsize=(16, 4))
for ax, col in zip(axes if len(num_cols) > 1 else [axes], num_cols[:4]):
    df.groupby(TARGET)[col].plot(kind="hist", ax=ax, alpha=0.6, legend=True, bins=30)
    ax.set_title(col)
plt.suptitle("Features por Target")
plt.tight_layout()
plt.savefig("reports/eda_features.png", dpi=150)
plt.close()


# ════════════════════════════════════════════════════════════
# 3. SPLIT (SEMPRE ANTES DO PREPROCESSING)
# ════════════════════════════════════════════════════════════
X = df.drop(columns=[TARGET])
y = df[TARGET]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"\nTreino: {X_train.shape[0]:,} | Teste: {X_test.shape[0]:,}")
print(f"Positivos treino: {y_train.mean():.3f} | Positivos teste: {y_test.mean():.3f}")


# ════════════════════════════════════════════════════════════
# 4. PREPROCESSAMENTO
# ════════════════════════════════════════════════════════════
num_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler",  StandardScaler()),
])

cat_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="constant", fill_value="MISSING")),
    ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
])

preprocessor = ColumnTransformer([
    ("num", num_pipeline, num_cols),
    ("cat", cat_pipeline, cat_cols),
], remainder="drop")


# ════════════════════════════════════════════════════════════
# 5. BASELINE (DummyClassifier)
# ════════════════════════════════════════════════════════════
from sklearn.dummy import DummyClassifier
dummy = DummyClassifier(strategy="most_frequent")
dummy.fit(X_train[num_cols + cat_cols], y_train)
dummy_f1 = f1_score(y_test, dummy.predict(X_test[num_cols + cat_cols]), average="weighted")
print(f"\nBaseline F1 (most_frequent): {dummy_f1:.4f}")


# ════════════════════════════════════════════════════════════
# 6. OTIMIZAÇÃO COM OPTUNA
# ════════════════════════════════════════════════════════════
pos = (y_train == 1).sum()
neg = (y_train == 0).sum()
scale_pos_weight = neg / pos

def objective(trial):
    params = {
        "n_estimators":      trial.suggest_int("n_estimators", 200, 1000, step=50),
        "num_leaves":        trial.suggest_int("num_leaves", 20, 150),
        "learning_rate":     trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
        "feature_fraction":  trial.suggest_float("feature_fraction", 0.5, 1.0),
        "bagging_fraction":  trial.suggest_float("bagging_fraction", 0.5, 1.0),
        "bagging_freq":      trial.suggest_int("bagging_freq", 1, 10),
        "min_child_samples": trial.suggest_int("min_child_samples", 5, 100),
        "lambda_l1":         trial.suggest_float("lambda_l1", 1e-8, 5.0, log=True),
        "lambda_l2":         trial.suggest_float("lambda_l2", 1e-8, 5.0, log=True),
    }
    pipe = Pipeline([
        ("pre", preprocessor),
        ("clf", lgb.LGBMClassifier(
            **params,
            scale_pos_weight=scale_pos_weight,
            random_state=42, verbose=-1, n_jobs=-1,
        )),
    ])
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_validate(pipe, X_train, y_train, cv=cv,
                            scoring="roc_auc", n_jobs=-1)
    return scores["test_score"].mean()

study = optuna.create_study(direction="maximize",
                            sampler=optuna.samplers.TPESampler(seed=42))
study.optimize(objective, n_trials=60, show_progress_bar=True)

print(f"\nMelhor ROC-AUC (CV): {study.best_value:.4f}")
print("Melhores parâmetros:", study.best_params)


# ════════════════════════════════════════════════════════════
# 7. MODELO FINAL
# ════════════════════════════════════════════════════════════
best_pipeline = Pipeline([
    ("pre", preprocessor),
    ("clf", lgb.LGBMClassifier(
        **study.best_params,
        scale_pos_weight=scale_pos_weight,
        random_state=42, verbose=-1, n_jobs=-1,
    )),
])
best_pipeline.fit(X_train, y_train)


# ════════════════════════════════════════════════════════════
# 8. AVALIAÇÃO NO TEST SET (executar apenas uma vez)
# ════════════════════════════════════════════════════════════
y_pred  = best_pipeline.predict(X_test)
y_proba = best_pipeline.predict_proba(X_test)[:, 1]

print("\n" + "=" * 55)
print("AVALIAÇÃO FINAL — TEST SET")
print("=" * 55)
print(classification_report(y_test, y_pred))
print(f"ROC-AUC  : {roc_auc_score(y_test, y_proba):.4f}")
print(f"PR-AUC   : {average_precision_score(y_test, y_proba):.4f}")
print(f"F1       : {f1_score(y_test, y_pred, average='weighted'):.4f}")
print("=" * 55)

# Figuras de avaliação
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
ConfusionMatrixDisplay.from_predictions(y_test, y_pred, ax=axes[0])
axes[0].set_title("Confusion Matrix")
RocCurveDisplay.from_predictions(y_test, y_proba, ax=axes[1])
axes[1].set_title(f"ROC Curve (AUC={roc_auc_score(y_test, y_proba):.3f})")
PrecisionRecallDisplay.from_predictions(y_test, y_proba, ax=axes[2])
axes[2].set_title("Precision-Recall Curve")
plt.suptitle("Avaliação do Modelo Final")
plt.tight_layout()
plt.savefig("reports/model_evaluation.png", dpi=150, bbox_inches="tight")
plt.close()
print("Gráficos salvos em reports/model_evaluation.png")


# ════════════════════════════════════════════════════════════
# 9. INTERPRETABILIDADE (SHAP)
# ════════════════════════════════════════════════════════════
lgbm_model = best_pipeline.named_steps["clf"]
X_test_proc = best_pipeline.named_steps["pre"].transform(X_test)

# Nomes das features após encoding
ohe_features = list(best_pipeline.named_steps["pre"]
                    .named_transformers_["cat"]
                    .named_steps["encoder"]
                    .get_feature_names_out(cat_cols))
all_feature_names = num_cols + ohe_features

explainer   = shap.TreeExplainer(lgbm_model)
shap_values = explainer.shap_values(X_test_proc)
sv = shap_values[1] if isinstance(shap_values, list) else shap_values

plt.figure(figsize=(10, 6))
shap.summary_plot(sv, X_test_proc, feature_names=all_feature_names,
                  show=False, max_display=15)
plt.tight_layout()
plt.savefig("reports/shap_summary.png", dpi=150, bbox_inches="tight")
plt.close()
print("SHAP summary salvo em reports/shap_summary.png")


# ════════════════════════════════════════════════════════════
# 10. SALVAR MODELO E METADADOS
# ════════════════════════════════════════════════════════════
MODEL_VERSION = "1.0.0"
model_path    = f"models/pipeline_v{MODEL_VERSION}.pkl"

joblib.dump(best_pipeline, model_path, compress=3)

metadata = {
    "version":    MODEL_VERSION,
    "trained_at": datetime.now().isoformat(),
    "model_type": "LightGBM",
    "features":   {"numerical": num_cols, "categorical": cat_cols},
    "target":     TARGET,
    "train_rows": int(X_train.shape[0]),
    "test_rows":  int(X_test.shape[0]),
    "metrics": {
        "roc_auc": round(roc_auc_score(y_test, y_proba), 4),
        "pr_auc":  round(average_precision_score(y_test, y_proba), 4),
        "f1":      round(f1_score(y_test, y_pred, average="weighted"), 4),
    },
    "best_params": study.best_params,
}

meta_path = f"models/metadata_v{MODEL_VERSION}.json"
with open(meta_path, "w") as f:
    json.dump(metadata, f, indent=2)

print(f"\n✅ Modelo salvo em: {model_path}")
print(f"✅ Metadados em:    {meta_path}")
print(f"✅ Relatórios em:   reports/")


# ════════════════════════════════════════════════════════════
# 11. TESTE DE SANIDADE (smoke test)
# ════════════════════════════════════════════════════════════
loaded = joblib.load(model_path)
assert loaded.predict(X_test.head(5)).shape == (5,), "Erro: shape inesperado"
assert all(0 <= p <= 1 for p in loaded.predict_proba(X_test.head(5))[:, 1]), "Proba fora de [0,1]"
print("\n✅ Smoke test passou — modelo carrega e prediz corretamente")
