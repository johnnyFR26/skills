# MLOps — Serialização, Deploy e Monitoramento

## Serialização de Modelos

### Sklearn / XGBoost / LightGBM → joblib

```python
import joblib
from pathlib import Path

Path("models").mkdir(exist_ok=True)

# Salvar pipeline completo (preprocessor + modelo)
joblib.dump(pipeline, "models/pipeline_v1.pkl", compress=3)
print(f"Tamanho: {Path('models/pipeline_v1.pkl').stat().st_size / 1e6:.1f} MB")

# Carregar
pipeline = joblib.load("models/pipeline_v1.pkl")
predictions = pipeline.predict(new_data)
probabilities = pipeline.predict_proba(new_data)

# Versionar com metadados
import json, datetime
metadata = {
    "version": "1.0.0",
    "trained_at": datetime.datetime.now().isoformat(),
    "features": feature_names,
    "target": target_name,
    "metrics": {"roc_auc": 0.923, "f1": 0.841},
    "python": "3.11",
    "framework": "sklearn==1.4.0",
}
with open("models/metadata_v1.json", "w") as f:
    json.dump(metadata, f, indent=2)
```

### PyTorch → state_dict

```python
import torch

# Salvar só pesos (recomendado)
torch.save(model.state_dict(), "models/model_weights.pt")

# Carregar (requer definição da classe)
model = MLP(input_dim=50, hidden_dims=[256, 128], output_dim=2)
model.load_state_dict(torch.load("models/model_weights.pt", map_location="cpu"))
model.eval()

# Salvar modelo completo (pode quebrar entre versões do PyTorch)
torch.save(model, "models/model_full.pt")

# TorchScript (deploy sem Python)
scripted = torch.jit.script(model)
scripted.save("models/model_scripted.pt")
loaded = torch.jit.load("models/model_scripted.pt")
```

### TensorFlow → SavedModel / ONNX

```python
# SavedModel (formato padrão para TF Serving)
model.save("models/saved_model/")

# Carregar
loaded = tf.saved_model.load("models/saved_model/")
infer = loaded.signatures["serving_default"]

# Converter para TFLite (mobile/edge)
converter = tf.lite.TFLiteConverter.from_saved_model("models/saved_model/")
converter.optimizations = [tf.lite.Optimize.DEFAULT]  # quantização int8
tflite_model = converter.convert()
with open("models/model.tflite", "wb") as f:
    f.write(tflite_model)
```

### ONNX (interoperabilidade entre frameworks)

```python
# Sklearn → ONNX
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

initial_type = [("float_input", FloatTensorType([None, X_train.shape[1]]))]
onnx_model = convert_sklearn(pipeline, initial_types=initial_type)
with open("models/model.onnx", "wb") as f:
    f.write(onnx_model.SerializeToString())

# PyTorch → ONNX
dummy_input = torch.randn(1, input_dim)
torch.onnx.export(
    model, dummy_input, "models/model.onnx",
    input_names=["input"], output_names=["output"],
    dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}},
    opset_version=17,
)

# Inferência com ONNX Runtime (muito rápido, agnóstico de framework)
import onnxruntime as ort  # pip install onnxruntime
sess = ort.InferenceSession("models/model.onnx", providers=["CPUExecutionProvider"])
outputs = sess.run(None, {"input": X_test.astype(np.float32)})
```

---

## API de Inferência com FastAPI

```python
# api/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import joblib
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ML Model API",
    description="API de inferência para modelo de classificação",
    version="1.0.0",
)

# Carregar modelo na inicialização (não a cada request)
pipeline = joblib.load("models/pipeline_v1.pkl")
logger.info("Modelo carregado com sucesso")

# Schema de entrada
class PredictRequest(BaseModel):
    age: float = Field(..., ge=0, le=120, description="Idade em anos")
    income: float = Field(..., ge=0, description="Renda mensal")
    product: str = Field(..., description="Produto contratado")
    score: Optional[float] = Field(None, ge=0, le=1000)

class PredictResponse(BaseModel):
    prediction: int
    probability: float
    label: str

LABEL_MAP = {0: "não_churn", 1: "churn"}

@app.get("/health")
def health_check():
    return {"status": "ok", "model_version": "1.0.0"}

@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    try:
        import pandas as pd
        data = pd.DataFrame([request.dict()])
        prediction = int(pipeline.predict(data)[0])
        probability = float(pipeline.predict_proba(data)[0, prediction])
        return PredictResponse(
            prediction=prediction,
            probability=round(probability, 4),
            label=LABEL_MAP[prediction],
        )
    except Exception as e:
        logger.error(f"Erro na predição: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/batch")
def predict_batch(requests: List[PredictRequest]):
    import pandas as pd
    data = pd.DataFrame([r.dict() for r in requests])
    predictions  = pipeline.predict(data).tolist()
    probabilities = pipeline.predict_proba(data).max(axis=1).tolist()
    return [
        {"prediction": p, "probability": round(prob, 4), "label": LABEL_MAP[p]}
        for p, prob in zip(predictions, probabilities)
    ]

# Rodar: uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Docker para Deploy

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libgomp1 && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código e modelo
COPY api/ ./api/
COPY models/ ./models/

# Variáveis de ambiente
ENV MODEL_PATH=models/pipeline_v1.pkl
ENV PORT=8000

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

```bash
# Build e run
docker build -t ml-api:1.0.0 .
docker run -p 8000:8000 --name ml-api ml-api:1.0.0

# Testar
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"age": 35, "income": 5000.0, "product": "premium", "score": 720}'
```

---

## Monitoramento e Data Drift

```python
# pip install evidently
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, ClassificationPreset
from evidently.metrics import *

# Criar relatório de drift
report = Report(metrics=[
    DataDriftPreset(drift_share=0.3),   # alerta se >30% das features driftaram
    ClassificationPreset(),
])

report.run(
    reference_data=df_train,
    current_data=df_production,
    column_mapping=ColumnMapping(
        target="churn",
        prediction="prediction",
        numerical_features=num_cols,
        categorical_features=cat_cols,
    ),
)
report.save_html("reports/drift_report.html")

# Checar drift programaticamente
result = report.as_dict()
drift_detected = result["metrics"][0]["result"]["dataset_drift"]
if drift_detected:
    send_alert("⚠️ Data drift detectado! Retreinar modelo.")
```

### Monitoramento de Métricas em Produção

```python
# monitor.py — executar diariamente via cron
import pandas as pd
import joblib
from sklearn.metrics import roc_auc_score, f1_score
from datetime import datetime, timedelta

def monitor_daily(date=None):
    date = date or datetime.today().strftime("%Y-%m-%d")

    # Carregar dados do dia com labels reais (se disponíveis)
    df_prod = pd.read_parquet(f"data/production/{date}.parquet")

    if "actual_label" not in df_prod.columns:
        print("Labels não disponíveis ainda. Monitorando apenas distribuição.")
        check_feature_drift(df_prod)
        return

    # Calcular métricas
    pipeline = joblib.load("models/pipeline_v1.pkl")
    y_pred   = pipeline.predict(df_prod)
    y_proba  = pipeline.predict_proba(df_prod)[:, 1]
    y_true   = df_prod["actual_label"]

    metrics = {
        "date":    date,
        "n_preds": len(df_prod),
        "roc_auc": roc_auc_score(y_true, y_proba),
        "f1":      f1_score(y_true, y_pred),
        "positive_rate": y_pred.mean(),
    }

    # Salvar histórico
    hist = pd.read_csv("reports/metrics_history.csv") if Path("reports/metrics_history.csv").exists() else pd.DataFrame()
    hist = pd.concat([hist, pd.DataFrame([metrics])], ignore_index=True)
    hist.to_csv("reports/metrics_history.csv", index=False)

    # Alertar se degradação
    baseline_auc = 0.923
    if metrics["roc_auc"] < baseline_auc * 0.95:
        send_alert(f"🚨 ROC-AUC degradou: {metrics['roc_auc']:.3f} (baseline: {baseline_auc})")
```

---

## MLflow — Ciclo Completo de Experimentos

```python
import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature

mlflow.set_tracking_uri("sqlite:///mlruns.db")  # local; usar servidor remoto em prod
mlflow.set_experiment("churn-prediction")

with mlflow.start_run(run_name="lgbm_v3_optuna") as run:
    run_id = run.info.run_id

    # Parâmetros
    mlflow.log_params({
        "model_type": "LightGBM",
        "n_estimators": 500,
        "num_leaves": 63,
        "learning_rate": 0.05,
        "cv_folds": 5,
        "random_state": 42,
    })

    # Treinar
    pipeline.fit(X_train, y_train)
    y_pred  = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    # Métricas
    mlflow.log_metrics({
        "test_roc_auc":  roc_auc_score(y_test, y_proba),
        "test_f1":       f1_score(y_test, y_pred, average="weighted"),
        "test_precision": precision_score(y_test, y_pred, average="weighted"),
        "test_recall":   recall_score(y_test, y_pred, average="weighted"),
        "train_roc_auc": roc_auc_score(y_train, pipeline.predict_proba(X_train)[:, 1]),
    })

    # Modelo com assinatura (schema de input/output)
    signature = infer_signature(X_train, pipeline.predict(X_train))
    mlflow.sklearn.log_model(
        pipeline,
        "model",
        signature=signature,
        input_example=X_train[:3],
        registered_model_name="churn-classifier",  # registra no Model Registry
    )

    # Artefatos
    mlflow.log_artifact("reports/evaluation.png")
    mlflow.log_artifact("reports/drift_report.html")

    print(f"Run ID: {run_id}")
    print(f"UI: mlflow ui --backend-store-uri sqlite:///mlruns.db")

# Carregar modelo do MLflow Registry
model_uri = "models:/churn-classifier/Production"
loaded_pipeline = mlflow.sklearn.load_model(model_uri)
```

---

## CI/CD para ML (GitHub Actions)

```yaml
# .github/workflows/ml-pipeline.yml
name: ML Pipeline

on:
  schedule:
    - cron: "0 2 * * 1"   # toda segunda-feira às 2h
  push:
    paths:
      - "src/**"
      - "data/raw/**"

jobs:
  train-and-evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run preprocessing
        run: python src/data.py

      - name: Train model
        run: python src/train.py --config configs/lgbm_v3.yaml

      - name: Evaluate model
        run: python src/evaluate.py --threshold 0.90  # falha se AUC < 0.90

      - name: Check data drift
        run: python src/monitor.py --fail-on-drift

      - name: Build and push Docker image
        if: success()
        run: |
          docker build -t ${{ secrets.REGISTRY }}/ml-api:${{ github.sha }} .
          docker push ${{ secrets.REGISTRY }}/ml-api:${{ github.sha }}

      - name: Deploy to staging
        if: success()
        run: kubectl set image deployment/ml-api ml-api=${{ secrets.REGISTRY }}/ml-api:${{ github.sha }}
```

---

## Checklist de Deploy

```
□ Modelo salvo com metadados (versão, data, métricas, features)
□ Pipeline completo serializado (preprocessor + modelo juntos)
□ Input validation na API (Pydantic schemas)
□ Testes de unidade para pipeline (pytest)
□ Teste de carga (locust / k6) antes de ir para produção
□ Healthcheck endpoint funcionando
□ Logging estruturado (JSON) em produção
□ Rollback plan documentado
□ Baseline de métricas salva para comparação futura
□ Alertas configurados para degradação de performance
□ Limites de taxa (rate limiting) na API
□ Documentação do endpoint (FastAPI gera /docs automaticamente)
```
