# Avaliação de Modelos e Métricas

## Métricas por Tipo de Tarefa

### Classificação Binária

```python
from sklearn.metrics import (
    classification_report, confusion_matrix,
    roc_auc_score, average_precision_score,
    f1_score, precision_score, recall_score,
    RocCurveDisplay, PrecisionRecallDisplay,
    ConfusionMatrixDisplay,
)
import matplotlib.pyplot as plt

y_pred      = model.predict(X_test)
y_proba     = model.predict_proba(X_test)[:, 1]

print("=" * 50)
print(classification_report(y_test, y_pred))
print(f"ROC-AUC  : {roc_auc_score(y_test, y_proba):.4f}")
print(f"PR-AUC   : {average_precision_score(y_test, y_proba):.4f}")
print(f"F1 (0.5) : {f1_score(y_test, y_pred):.4f}")

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Confusion Matrix
ConfusionMatrixDisplay.from_predictions(y_test, y_pred, ax=axes[0])
axes[0].set_title("Confusion Matrix")

# ROC Curve
RocCurveDisplay.from_predictions(y_test, y_proba, ax=axes[1])
axes[1].set_title("ROC Curve")

# Precision-Recall Curve (mais informativa para dados desbalanceados)
PrecisionRecallDisplay.from_predictions(y_test, y_proba, ax=axes[2])
axes[2].set_title("Precision-Recall Curve")

plt.tight_layout()
plt.savefig("reports/evaluation.png", dpi=150)
```

**Quando usar qual métrica:**
| Situação | Métrica Primária |
|----------|-----------------|
| Classes balanceadas | F1 / Accuracy |
| Classes desbalanceadas | PR-AUC / F1 (macro) |
| Custo de FP ≠ FN | Precision ou Recall (escolher threshold) |
| Ranking/probabilidades | ROC-AUC |
| Regulatório / alto custo FN | Recall (sensibilidade) |
| Spam / baixo custo FP | Precision |

---

### Escolha do Threshold

```python
from sklearn.metrics import precision_recall_curve

precisions, recalls, thresholds = precision_recall_curve(y_test, y_proba)

# F1 por threshold
f1_scores = 2 * (precisions * recalls) / (precisions + recalls + 1e-8)
best_threshold = thresholds[f1_scores[:-1].argmax()]
print(f"Melhor threshold F1: {best_threshold:.3f}")

# Threshold customizado (ex: garantir recall >= 0.90)
min_recall = 0.90
valid = recalls[:-1] >= min_recall
if valid.any():
    threshold_high_recall = thresholds[valid][precisions[:-1][valid].argmax()]
    print(f"Threshold para recall>={min_recall}: {threshold_high_recall:.3f}")

# Aplicar threshold customizado
y_pred_custom = (y_proba >= best_threshold).astype(int)
```

---

### Classificação Multiclasse

```python
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns

print(classification_report(y_test, y_pred, target_names=class_names))

# ROC-AUC multiclasse
roc_auc = roc_auc_score(y_test, model.predict_proba(X_test), multi_class="ovr", average="macro")
print(f"ROC-AUC (macro, OvR): {roc_auc:.4f}")

# Confusion Matrix normalizada
cm = confusion_matrix(y_test, y_pred, normalize="true")
plt.figure(figsize=(10, 8))
sns.heatmap(cm, annot=True, fmt=".2%", xticklabels=class_names, yticklabels=class_names, cmap="Blues")
plt.ylabel("Real")
plt.xlabel("Predito")
plt.title("Confusion Matrix (normalizada por real)")
plt.tight_layout()
```

---

### Regressão

```python
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.metrics import mean_absolute_percentage_error
import numpy as np

y_pred = model.predict(X_test)

rmse  = np.sqrt(mean_squared_error(y_test, y_pred))
mae   = mean_absolute_error(y_test, y_pred)
r2    = r2_score(y_test, y_pred)
mape  = mean_absolute_percentage_error(y_test, y_pred) * 100

print(f"RMSE : {rmse:.4f}")
print(f"MAE  : {mae:.4f}")
print(f"R²   : {r2:.4f}")
print(f"MAPE : {mape:.2f}%")

# Plot: real vs predito
fig, axes = plt.subplots(1, 2, figsize=(12, 4))

axes[0].scatter(y_test, y_pred, alpha=0.4, s=10)
axes[0].plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], "r--")
axes[0].set_xlabel("Real")
axes[0].set_ylabel("Predito")
axes[0].set_title("Real vs Predito")

residuals = y_test - y_pred
axes[1].hist(residuals, bins=50, edgecolor="black")
axes[1].axvline(0, color="r", linestyle="--")
axes[1].set_title("Distribuição dos Resíduos")

plt.tight_layout()
plt.savefig("reports/regression_eval.png", dpi=150)
```

**Quando usar qual métrica:**
| Métrica | Características | Use quando |
|---------|----------------|-----------|
| RMSE | Penaliza erros grandes | Erros grandes são inaceitáveis |
| MAE | Mais robusto a outliers | Outliers presentes, quer interpretabilidade |
| R² | % variância explicada | Comparar modelos na mesma escala |
| MAPE | % relativo | Interpretar em linguagem de negócio |

---

## Validação Cruzada

```python
from sklearn.model_selection import (
    cross_val_score, cross_validate,
    StratifiedKFold, KFold, GroupKFold,
    TimeSeriesSplit,
)
import numpy as np

# Classificação — usar StratifiedKFold (mantém proporção de classes)
cv_strat = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# Regressão — KFold padrão
cv_kfold = KFold(n_splits=5, shuffle=True, random_state=42)

# Séries temporais — TimeSeriesSplit (não embaralha, respeita ordem)
cv_ts = TimeSeriesSplit(n_splits=5, gap=0)

# Dados com grupos (ex: múltiplas medições por paciente)
cv_group = GroupKFold(n_splits=5)

# cross_validate: múltiplas métricas de uma vez
results = cross_validate(
    model, X_train, y_train,
    cv=cv_strat,
    scoring=["f1_weighted", "roc_auc", "precision_weighted", "recall_weighted"],
    n_jobs=-1,
    return_train_score=True,
)

for metric in ["f1_weighted", "roc_auc"]:
    train = results[f"train_{metric}"]
    test  = results[f"test_{metric}"]
    print(f"{metric}:")
    print(f"  Train: {train.mean():.4f} ± {train.std():.4f}")
    print(f"  Val  : {test.mean():.4f} ± {test.std():.4f}")
    print(f"  Gap  : {(train - test).mean():.4f}")
```

**Sinais de Overfitting/Underfitting via CV:**
```
Gap alto (train >> val)   → Overfitting  → regularização, mais dados, simplificar
Ambos baixos              → Underfitting → modelo mais complexo, mais features
Val alta variância        → Instável     → mais folds, mais dados
```

---

## Curvas de Aprendizado

```python
from sklearn.model_selection import learning_curve
import matplotlib.pyplot as plt
import numpy as np

train_sizes, train_scores, val_scores = learning_curve(
    model, X_train, y_train,
    train_sizes=np.linspace(0.1, 1.0, 10),
    cv=5,
    scoring="f1_weighted",
    n_jobs=-1,
    shuffle=True,
    random_state=42,
)

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(train_sizes, train_scores.mean(axis=1), "o-", label="Train", color="blue")
ax.fill_between(train_sizes,
    train_scores.mean(1) - train_scores.std(1),
    train_scores.mean(1) + train_scores.std(1), alpha=0.1, color="blue")
ax.plot(train_sizes, val_scores.mean(axis=1), "o-", label="Validation", color="orange")
ax.fill_between(train_sizes,
    val_scores.mean(1) - val_scores.std(1),
    val_scores.mean(1) + val_scores.std(1), alpha=0.1, color="orange")
ax.set_xlabel("Training set size")
ax.set_ylabel("F1 Score")
ax.set_title("Learning Curve")
ax.legend()
ax.grid(True)
plt.tight_layout()
plt.savefig("reports/learning_curve.png", dpi=150)
```

**Interpretação:**
- Ambas curvas convergem e se estabilizam → bom
- Gap grande que persiste → overfitting (precisa mais dados ou regularização)
- Ambas baixas e convergem → underfitting (modelo precisa de mais capacidade)

---

## Interpretabilidade com SHAP

```python
import shap

# Tree-based models (rápido)
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)

# Para classificação binária
if isinstance(shap_values, list):
    sv = shap_values[1]  # classe positiva
else:
    sv = shap_values

# Summary plot (importância global)
shap.summary_plot(sv, X_test, feature_names=feature_names, show=True)

# Waterfall (explicar uma predição individual)
idx = 0  # índice do exemplo a explicar
shap.waterfall_plot(shap.Explanation(
    values=sv[idx],
    base_values=explainer.expected_value[1] if isinstance(explainer.expected_value, list) else explainer.expected_value,
    data=X_test[idx],
    feature_names=feature_names,
))

# Dependence plot (relação feature vs SHAP)
shap.dependence_plot("feature_name", sv, X_test, feature_names=feature_names)

# Modelo agnóstico (redes neurais, qualquer modelo)
explainer_kp = shap.KernelExplainer(model.predict_proba, shap.sample(X_train, 100))
shap_values_kp = explainer_kp.shap_values(X_test[:50])
```

---

## Análise de Erros

```python
# Criar DataFrame com predições e erros
results_df = X_test.copy()
results_df["y_true"]  = y_test.values
results_df["y_pred"]  = y_pred
results_df["y_proba"] = y_proba
results_df["correct"] = results_df["y_true"] == results_df["y_pred"]

# Falsos Negativos (erros mais caros em muitos problemas)
fn = results_df[(results_df["y_true"] == 1) & (results_df["y_pred"] == 0)]
print(f"\nFalsos Negativos: {len(fn)}")
print(fn.describe())

# Falsos Positivos
fp = results_df[(results_df["y_true"] == 0) & (results_df["y_pred"] == 1)]
print(f"\nFalsos Positivos: {len(fp)}")

# Exemplos com maior incerteza (proba próxima de 0.5)
uncertain = results_df[(results_df["y_proba"] > 0.4) & (results_df["y_proba"] < 0.6)]
print(f"\nPredições incertas: {len(uncertain)}")

# Distribuição de erro por segmento
for col in ["categoria", "região"]:
    if col in results_df.columns:
        print(f"\nAcurácia por {col}:")
        print(results_df.groupby(col)["correct"].mean().sort_values())
```

---

## Calibração de Probabilidades

```python
from sklearn.calibration import calibration_curve, CalibratedClassifierCV
import matplotlib.pyplot as plt

# Checar calibração atual
fraction_of_positives, mean_predicted = calibration_curve(y_test, y_proba, n_bins=10)
plt.plot(mean_predicted, fraction_of_positives, "s-", label="Modelo")
plt.plot([0, 1], [0, 1], "k--", label="Perfeito")
plt.xlabel("Probabilidade Predita")
plt.ylabel("Fração de Positivos")
plt.title("Calibration Curve")
plt.legend()

# Calibrar se necessário (especialmente SVMs, RF, XGBoost)
calibrated = CalibratedClassifierCV(model, method="isotonic", cv=5)  # ou "sigmoid"
calibrated.fit(X_train, y_train)
y_proba_cal = calibrated.predict_proba(X_test)[:, 1]
```
