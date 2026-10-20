"""
Template completo: Projeto de Regressão
========================================
Ajuste as seções marcadas com "# AJUSTAR"
"""

import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import seaborn as sns, joblib, json
from pathlib import Path
from datetime import datetime

from sklearn.model_selection import train_test_split, KFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder, PowerTransformer
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import lightgbm as lgb
import optuna
import shap

optuna.logging.set_verbosity(optuna.logging.WARNING)
Path("models").mkdir(exist_ok=True); Path("reports").mkdir(exist_ok=True)
sns.set_theme(style="whitegrid")

# ════════════════════════════════════════════════════════════
# 1. CARREGAR E INSPECIONAR
# ════════════════════════════════════════════════════════════
df     = pd.read_csv("data/raw/dataset.csv")   # AJUSTAR
TARGET = "price"                                # AJUSTAR

print(f"Shape: {df.shape}")
print(f"\nTarget ({TARGET}):\n{df[TARGET].describe().round(2)}")
print(f"\nSkewness: {df[TARGET].skew():.3f}  (|>1| → considerar log-transform)")

# Verificar se log-transform ajuda
USE_LOG_TARGET = abs(df[TARGET].skew()) > 1
if USE_LOG_TARGET:
    print("\n⚠️  Target assimétrico — aplicando log1p transform")
    df[f"log_{TARGET}"] = np.log1p(df[TARGET])
    TARGET_MODEL = f"log_{TARGET}"
else:
    TARGET_MODEL = TARGET


# ════════════════════════════════════════════════════════════
# 2. SPLIT
# ════════════════════════════════════════════════════════════
num_cols = df.select_dtypes("number").columns.drop([TARGET, TARGET_MODEL] if USE_LOG_TARGET else [TARGET]).tolist()
cat_cols = df.select_dtypes("object").columns.tolist()

X = df[num_cols + cat_cols]
y = df[TARGET_MODEL]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42  # sem stratify em regressão
)


# ════════════════════════════════════════════════════════════
# 3. PIPELINE
# ════════════════════════════════════════════════════════════
num_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("power",   PowerTransformer(method="yeo-johnson")),  # normaliza features assimétricas
    ("scaler",  StandardScaler()),
])

cat_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="constant", fill_value="MISSING")),
    ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
])

preprocessor = ColumnTransformer([
    ("num", num_pipeline, num_cols),
    ("cat", cat_pipeline, cat_cols),
])


# ════════════════════════════════════════════════════════════
# 4. OPTUNA
# ════════════════════════════════════════════════════════════
def objective(trial):
    params = {
        "n_estimators":      trial.suggest_int("n_estimators", 200, 1500, step=50),
        "num_leaves":        trial.suggest_int("num_leaves", 15, 200),
        "learning_rate":     trial.suggest_float("learning_rate", 0.005, 0.2, log=True),
        "feature_fraction":  trial.suggest_float("feature_fraction", 0.5, 1.0),
        "bagging_fraction":  trial.suggest_float("bagging_fraction", 0.5, 1.0),
        "bagging_freq":      trial.suggest_int("bagging_freq", 1, 10),
        "min_child_samples": trial.suggest_int("min_child_samples", 5, 100),
        "lambda_l1":         trial.suggest_float("lambda_l1", 1e-8, 5.0, log=True),
        "lambda_l2":         trial.suggest_float("lambda_l2", 1e-8, 5.0, log=True),
    }
    pipe = Pipeline([
        ("pre", preprocessor),
        ("rgr", lgb.LGBMRegressor(
            **params, objective="regression",
            random_state=42, verbose=-1, n_jobs=-1,
        )),
    ])
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_validate(pipe, X_train, y_train, cv=cv,
                            scoring="neg_root_mean_squared_error", n_jobs=-1)
    return -scores["test_score"].mean()   # minimizar RMSE

study = optuna.create_study(direction="minimize",
                            sampler=optuna.samplers.TPESampler(seed=42))
study.optimize(objective, n_trials=60, show_progress_bar=True)
print(f"\nMelhor RMSE (CV): {study.best_value:.4f}")


# ════════════════════════════════════════════════════════════
# 5. MODELO FINAL
# ════════════════════════════════════════════════════════════
best_pipeline = Pipeline([
    ("pre", preprocessor),
    ("rgr", lgb.LGBMRegressor(
        **study.best_params,
        objective="regression", random_state=42, verbose=-1, n_jobs=-1,
    )),
])
best_pipeline.fit(X_train, y_train)


# ════════════════════════════════════════════════════════════
# 6. AVALIAÇÃO
# ════════════════════════════════════════════════════════════
y_pred_log = best_pipeline.predict(X_test)

# Reverter transform se necessário
if USE_LOG_TARGET:
    y_pred = np.expm1(y_pred_log)
    y_true = np.expm1(y_test.values)
else:
    y_pred = y_pred_log
    y_true = y_test.values

rmse = np.sqrt(mean_squared_error(y_true, y_pred))
mae  = mean_absolute_error(y_true, y_pred)
r2   = r2_score(y_true, y_pred)
mape = np.mean(np.abs((y_true - y_pred) / (np.abs(y_true) + 1e-8))) * 100

print(f"\nRMSE : {rmse:,.2f}")
print(f"MAE  : {mae:,.2f}")
print(f"R²   : {r2:.4f}")
print(f"MAPE : {mape:.2f}%")

# Gráficos
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

axes[0].scatter(y_true, y_pred, alpha=0.3, s=10, color="steelblue")
mn, mx = min(y_true.min(), y_pred.min()), max(y_true.max(), y_pred.max())
axes[0].plot([mn, mx], [mn, mx], "r--", lw=2)
axes[0].set_xlabel("Real"); axes[0].set_ylabel("Predito")
axes[0].set_title(f"Real vs Predito  (R²={r2:.3f})")

residuals = y_true - y_pred
axes[1].hist(residuals, bins=60, color="steelblue", edgecolor="white")
axes[1].axvline(0, color="red", lw=2)
axes[1].set_xlabel("Resíduo (Real − Predito)"); axes[1].set_title("Distribuição dos Resíduos")

plt.tight_layout()
plt.savefig("reports/regression_evaluation.png", dpi=150, bbox_inches="tight")
plt.close()


# ════════════════════════════════════════════════════════════
# 7. SHAP
# ════════════════════════════════════════════════════════════
lgbm_model  = best_pipeline.named_steps["rgr"]
X_test_proc = best_pipeline.named_steps["pre"].transform(X_test)
ohe_names   = list(best_pipeline.named_steps["pre"]
                   .named_transformers_["cat"]
                   .named_steps["encoder"]
                   .get_feature_names_out(cat_cols))
all_names = num_cols + ohe_names

explainer = shap.TreeExplainer(lgbm_model)
sv = explainer.shap_values(X_test_proc)

plt.figure(figsize=(10, 6))
shap.summary_plot(sv, X_test_proc, feature_names=all_names, show=False, max_display=15)
plt.tight_layout()
plt.savefig("reports/shap_summary.png", dpi=150, bbox_inches="tight")
plt.close()


# ════════════════════════════════════════════════════════════
# 8. SALVAR
# ════════════════════════════════════════════════════════════
joblib.dump(best_pipeline, "models/regression_pipeline_v1.pkl", compress=3)
with open("models/regression_metadata_v1.json", "w") as f:
    json.dump({
        "version": "1.0.0",
        "trained_at": datetime.now().isoformat(),
        "target": TARGET,
        "log_transform": USE_LOG_TARGET,
        "metrics": {"rmse": round(rmse, 4), "mae": round(mae, 4),
                    "r2": round(r2, 4), "mape": round(mape, 2)},
        "best_params": study.best_params,
    }, f, indent=2)
print("\n✅ Modelo e metadados salvos")
