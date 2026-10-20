"""
Template: Classificação de Texto (NLP)
=======================================
Cobre: TF-IDF + ML clássico (baseline), fine-tuning BERT (produção).
Ajuste as seções marcadas com "# AJUSTAR"
"""

import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from pathlib import Path
Path("models").mkdir(exist_ok=True)

# ════════════════════════════════════════════════════════════
# OPÇÃO A: TF-IDF + Classificador (baseline rápido)
# ════════════════════════════════════════════════════════════

def tfidf_baseline(df, text_col="text", target_col="label"):
    """Pipeline completo TF-IDF → classificador → avaliação."""
    from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
    from sklearn.pipeline import Pipeline
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import classification_report, roc_auc_score
    from sklearn.preprocessing import LabelEncoder

    le = LabelEncoder()
    y  = le.fit_transform(df[target_col])
    X  = df[text_col].astype(str)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=50_000,
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.95,
            strip_accents="unicode",
            lowercase=True,
            sublinear_tf=True,   # TF log-scale, reduz impacto de palavras muito frequentes
        )),
        ("clf", LogisticRegression(
            C=5.0,
            max_iter=1000,
            class_weight="balanced",
            solver="saga",
            n_jobs=-1,
            random_state=42,
        )),
    ])

    # Cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_f1 = cross_val_score(pipe, X_train, y_train, cv=cv, scoring="f1_weighted", n_jobs=-1)
    print(f"CV F1: {cv_f1.mean():.4f} ± {cv_f1.std():.4f}")

    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)
    print("\n" + classification_report(y_test, y_pred, target_names=le.classes_))

    import joblib
    joblib.dump(pipe, "models/tfidf_pipeline.pkl")
    joblib.dump(le,   "models/label_encoder.pkl")
    print("✅ Pipeline salvo em models/tfidf_pipeline.pkl")
    return pipe


# ════════════════════════════════════════════════════════════
# OPÇÃO B: Fine-tuning BERT (maior performance)
# ════════════════════════════════════════════════════════════

def bert_finetune(df, text_col="text", target_col="label",
                  model_name="neuralmind/bert-base-portuguese-cased",
                  max_length=128, batch_size=16, epochs=5, lr=2e-5):
    """
    Fine-tuning de BERT para classificação de texto.

    Modelos sugeridos por idioma:
    - Português : neuralmind/bert-base-portuguese-cased
    - Inglês    : bert-base-uncased, roberta-base, distilbert-base-uncased
    - Multilíngue: bert-base-multilingual-cased, xlm-roberta-base
    - Compacto  : distilbert-base-uncased (40% menor, 60% mais rápido)
    """
    from transformers import (
        AutoTokenizer, AutoModelForSequenceClassification,
        TrainingArguments, Trainer, DataCollatorWithPadding,
        EarlyStoppingCallback,
    )
    from datasets import Dataset
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder
    from sklearn.metrics import f1_score, classification_report
    import torch

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    # Encode labels
    le = LabelEncoder()
    df = df.copy()
    df["label_int"] = le.fit_transform(df[target_col])
    n_classes = len(le.classes_)
    print(f"Classes: {le.classes_}")

    # Split
    train_df, test_df = train_test_split(
        df, test_size=0.2, random_state=42, stratify=df["label_int"]
    )

    # Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    def tokenize(batch):
        return tokenizer(
            batch[text_col],
            truncation=True,
            max_length=max_length,
            padding=False,
        )

    # HuggingFace Datasets
    def to_hf(df_):
        ds = Dataset.from_dict({text_col: df_[text_col].tolist(),
                                 "label": df_["label_int"].tolist()})
        return ds.map(tokenize, batched=True, remove_columns=[text_col])

    train_ds = to_hf(train_df)
    test_ds  = to_hf(test_df)

    # Modelo
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=n_classes,
        ignore_mismatched_sizes=True,
    )

    # Class weights para dados desbalanceados
    class_counts = train_df["label_int"].value_counts().sort_index().values
    weights = torch.FloatTensor(len(train_df) / (n_classes * class_counts))

    class WeightedTrainer(Trainer):
        def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
            labels = inputs.pop("labels")
            outputs = model(**inputs)
            logits  = outputs.logits
            loss_fn = torch.nn.CrossEntropyLoss(weight=weights.to(device))
            loss    = loss_fn(logits, labels)
            return (loss, outputs) if return_outputs else loss

    # Métricas
    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        preds = np.argmax(logits, axis=-1)
        return {
            "f1": f1_score(labels, preds, average="weighted"),
            "acc": (preds == labels).mean(),
        }

    # Training arguments
    args = TrainingArguments(
        output_dir=f"models/{model_name.split('/')[-1]}_finetuned",
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size * 2,
        learning_rate=lr,
        weight_decay=0.01,
        warmup_ratio=0.1,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        fp16=torch.cuda.is_available(),
        dataloader_num_workers=2,
        report_to="none",
        seed=42,
        logging_steps=50,
    )

    trainer = WeightedTrainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=test_ds,
        tokenizer=tokenizer,
        data_collator=DataCollatorWithPadding(tokenizer),
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
    )

    print(f"\nIniciando fine-tuning de {model_name}...")
    trainer.train()

    # Avaliação final
    preds_out = trainer.predict(test_ds)
    y_pred    = np.argmax(preds_out.predictions, axis=-1)
    y_true    = test_df["label_int"].values
    print("\n" + classification_report(y_true, y_pred, target_names=le.classes_))

    # Salvar
    save_path = f"models/{model_name.split('/')[-1]}_final"
    trainer.save_model(save_path)
    tokenizer.save_pretrained(save_path)
    import joblib
    joblib.dump(le, f"{save_path}/label_encoder.pkl")
    print(f"✅ Modelo salvo em {save_path}")
    return trainer


# ════════════════════════════════════════════════════════════
# INFERÊNCIA (Produção)
# ════════════════════════════════════════════════════════════

class TextClassifier:
    """Wrapper simples para inferência com modelo fine-tuned."""

    def __init__(self, model_path: str):
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        import joblib, torch

        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model     = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.le        = joblib.load(f"{model_path}/label_encoder.pkl")
        self.device    = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device).eval()

    @torch.no_grad()
    def predict(self, texts: list, batch_size: int = 32) -> pd.DataFrame:
        import torch
        all_probs = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            enc   = self.tokenizer(batch, truncation=True, max_length=128,
                                   padding=True, return_tensors="pt")
            enc   = {k: v.to(self.device) for k, v in enc.items()}
            logits = self.model(**enc).logits
            probs  = torch.softmax(logits, dim=1).cpu().numpy()
            all_probs.append(probs)

        all_probs = np.vstack(all_probs)
        pred_idx  = all_probs.argmax(axis=1)
        return pd.DataFrame({
            "text":       texts,
            "prediction": self.le.inverse_transform(pred_idx),
            "confidence": all_probs.max(axis=1).round(4),
            **{f"prob_{cls}": all_probs[:, i] for i, cls in enumerate(self.le.classes_)},
        })


# Exemplo de uso
if __name__ == "__main__":
    # Dados de exemplo
    df_sample = pd.DataFrame({
        "text":  ["Este produto é excelente!", "Péssimo atendimento", "Entrega rápida e produto ok"],
        "label": ["positivo", "negativo", "neutro"],
    })

    print("=== OPÇÃO A: TF-IDF Baseline ===")
    tfidf_baseline(df_sample, text_col="text", target_col="label")
