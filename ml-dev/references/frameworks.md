# Frameworks de Deep Learning

## PyTorch — Estrutura Padrão de Treino

```python
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset, random_split
import numpy as np

# Reprodutibilidade
torch.manual_seed(42)
np.random.seed(42)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Device: {device}")

# ── 1. DATASET ──────────────────────────────────────────────
class TabularDataset(torch.utils.data.Dataset):
    def __init__(self, X, y):
        self.X = torch.FloatTensor(X)
        self.y = torch.LongTensor(y)    # Long para classificação; Float para regressão

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

train_ds = TabularDataset(X_train, y_train)
test_ds  = TabularDataset(X_test, y_test)

train_loader = DataLoader(train_ds, batch_size=64, shuffle=True,  num_workers=0, pin_memory=True)
test_loader  = DataLoader(test_ds,  batch_size=256, shuffle=False, num_workers=0)

# ── 2. MODELO ───────────────────────────────────────────────
class MLP(nn.Module):
    def __init__(self, input_dim, hidden_dims, output_dim, dropout=0.3):
        super().__init__()
        layers = []
        prev_dim = input_dim
        for h in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, h),
                nn.BatchNorm1d(h),
                nn.ReLU(),
                nn.Dropout(dropout),
            ])
            prev_dim = h
        layers.append(nn.Linear(prev_dim, output_dim))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)

model = MLP(
    input_dim=X_train.shape[1],
    hidden_dims=[256, 128, 64],
    output_dim=n_classes,
    dropout=0.3,
).to(device)

# ── 3. LOSS E OPTIMIZER ─────────────────────────────────────
criterion = nn.CrossEntropyLoss(weight=class_weights.to(device))  # desbalanceamento
# criterion = nn.BCEWithLogitsLoss()  # classificação binária
# criterion = nn.MSELoss()            # regressão

optimizer = optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=50, eta_min=1e-6)
# scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)

# ── 4. LOOP DE TREINO ────────────────────────────────────────
def train_epoch(model, loader, criterion, optimizer):
    model.train()
    total_loss, correct, total = 0, 0, 0
    for X_batch, y_batch in loader:
        X_batch, y_batch = X_batch.to(device), y_batch.to(device)
        optimizer.zero_grad()
        logits = model(X_batch)
        loss = criterion(logits, y_batch)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)  # evita gradient explosion
        optimizer.step()
        total_loss += loss.item() * len(y_batch)
        correct += (logits.argmax(1) == y_batch).sum().item()
        total += len(y_batch)
    return total_loss / total, correct / total

@torch.no_grad()
def eval_epoch(model, loader, criterion):
    model.eval()
    total_loss, correct, total = 0, 0, 0
    all_probs, all_labels = [], []
    for X_batch, y_batch in loader:
        X_batch, y_batch = X_batch.to(device), y_batch.to(device)
        logits = model(X_batch)
        loss = criterion(logits, y_batch)
        total_loss += loss.item() * len(y_batch)
        probs = torch.softmax(logits, dim=1)
        correct += (probs.argmax(1) == y_batch).sum().item()
        total += len(y_batch)
        all_probs.append(probs.cpu())
        all_labels.append(y_batch.cpu())
    return total_loss / total, correct / total, torch.cat(all_probs), torch.cat(all_labels)

# ── 5. TREINAMENTO COM EARLY STOPPING ───────────────────────
best_val_loss = float("inf")
patience, patience_counter = 15, 0
history = {"train_loss": [], "val_loss": [], "train_acc": [], "val_acc": []}

for epoch in range(200):
    train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer)
    val_loss, val_acc, _, _ = eval_epoch(model, test_loader, criterion)
    scheduler.step()

    history["train_loss"].append(train_loss)
    history["val_loss"].append(val_loss)
    history["train_acc"].append(train_acc)
    history["val_acc"].append(val_acc)

    if val_loss < best_val_loss:
        best_val_loss = val_loss
        torch.save(model.state_dict(), "models/best_model.pt")
        patience_counter = 0
    else:
        patience_counter += 1
        if patience_counter >= patience:
            print(f"Early stopping na época {epoch+1}")
            break

    if (epoch + 1) % 10 == 0:
        print(f"Ep {epoch+1:3d} | Train: {train_loss:.4f}/{train_acc:.3f} | Val: {val_loss:.4f}/{val_acc:.3f}")

# Carregar melhor modelo
model.load_state_dict(torch.load("models/best_model.pt"))
```

---

## PyTorch — Transfer Learning com Torchvision

```python
import torchvision.models as models
import torchvision.transforms as T

# Transforms de augmentação
train_transform = T.Compose([
    T.Resize((224, 224)),
    T.RandomHorizontalFlip(),
    T.RandomRotation(15),
    T.ColorJitter(brightness=0.2, contrast=0.2),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),  # ImageNet stats
])

val_transform = T.Compose([
    T.Resize((256, 256)),
    T.CenterCrop(224),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# Carregar modelo pré-treinado
backbone = models.efficientnet_b3(weights="IMAGENET1K_V1")

# Estratégia 1: Congelar backbone, treinar só o classificador
for param in backbone.parameters():
    param.requires_grad = False

# Trocar classificador final
in_features = backbone.classifier[1].in_features
backbone.classifier = nn.Sequential(
    nn.Dropout(0.3),
    nn.Linear(in_features, n_classes),
)
backbone = backbone.to(device)

# Estratégia 2: Fine-tuning gradual (descongelar depois de algumas épocas)
def unfreeze_backbone(model, lr_backbone=1e-5):
    for param in model.parameters():
        param.requires_grad = True
    optimizer = optim.AdamW([
        {"params": model.features.parameters(), "lr": lr_backbone},    # backbone: lr baixo
        {"params": model.classifier.parameters(), "lr": lr_backbone * 10},  # head: lr alto
    ], weight_decay=1e-4)
    return optimizer
```

---

## TensorFlow / Keras

```python
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, callbacks, optimizers, regularizers

tf.random.set_seed(42)
print(f"GPU disponível: {len(tf.config.list_physical_devices('GPU')) > 0}")

# ── 1. MODELO (API Funcional) ────────────────────────────────
def build_model(input_dim, n_classes, dropout=0.3):
    inputs = keras.Input(shape=(input_dim,))
    x = layers.Dense(256, kernel_regularizer=regularizers.l2(1e-4))(inputs)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    x = layers.Dropout(dropout)(x)

    x = layers.Dense(128, kernel_regularizer=regularizers.l2(1e-4))(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    x = layers.Dropout(dropout)(x)

    x = layers.Dense(64)(x)
    x = layers.Activation("relu")(x)

    outputs = layers.Dense(n_classes, activation="softmax")(x)
    # Para binária: activation="sigmoid", loss="binary_crossentropy"
    # Para regressão: sem activation, loss="mse"

    return keras.Model(inputs, outputs)

model = build_model(X_train.shape[1], n_classes)
model.summary()

# ── 2. COMPILAR ─────────────────────────────────────────────
model.compile(
    optimizer=optimizers.AdamW(learning_rate=1e-3, weight_decay=1e-4),
    loss="sparse_categorical_crossentropy",  # y como inteiros
    # loss="categorical_crossentropy",       # y como one-hot
    metrics=["accuracy"],
)

# ── 3. CALLBACKS ────────────────────────────────────────────
cb_list = [
    callbacks.EarlyStopping(
        monitor="val_loss", patience=15, restore_best_weights=True, verbose=1
    ),
    callbacks.ReduceLROnPlateau(
        monitor="val_loss", factor=0.5, patience=5, min_lr=1e-7, verbose=1
    ),
    callbacks.ModelCheckpoint(
        filepath="models/best_model.keras",
        monitor="val_loss", save_best_only=True, verbose=1,
    ),
    callbacks.TensorBoard(log_dir="logs/", histogram_freq=1),
]

# ── 4. TREINAR ──────────────────────────────────────────────
history = model.fit(
    X_train, y_train,
    validation_split=0.15,
    epochs=200,
    batch_size=64,
    callbacks=cb_list,
    class_weight=class_weight_dict,   # {0: 1.0, 1: 5.0} para desbalanceamento
    verbose=1,
)

# ── 5. SALVAR ───────────────────────────────────────────────
model.save("models/model_final.keras")       # formato Keras
model.export("models/model_savedmodel")      # SavedModel (para TF Serving)
```

---

## Hugging Face Transformers (NLP)

```python
from transformers import (
    AutoTokenizer, AutoModelForSequenceClassification,
    TrainingArguments, Trainer,
    DataCollatorWithPadding,
)
from datasets import Dataset
import torch

MODEL_NAME = "neuralmind/bert-base-portuguese-cased"  # BERT português
# Outras opções: "bert-base-uncased", "distilbert-base-uncased", "roberta-base"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

def tokenize(batch):
    return tokenizer(
        batch["text"],
        truncation=True,
        max_length=256,
        padding=False,          # padding dinâmico via DataCollator
    )

# Criar dataset HuggingFace
hf_train = Dataset.from_dict({"text": X_train_text, "label": y_train.tolist()})
hf_test  = Dataset.from_dict({"text": X_test_text,  "label": y_test.tolist()})

hf_train = hf_train.map(tokenize, batched=True, remove_columns=["text"])
hf_test  = hf_test.map(tokenize, batched=True, remove_columns=["text"])

# Modelo
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME, num_labels=n_classes, ignore_mismatched_sizes=True
)

# Training Arguments
training_args = TrainingArguments(
    output_dir="models/bert_finetuned",
    num_train_epochs=5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=32,
    learning_rate=2e-5,
    weight_decay=0.01,
    warmup_ratio=0.1,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="f1",
    fp16=torch.cuda.is_available(),
    dataloader_num_workers=4,
    seed=42,
)

# Métricas customizadas
from sklearn.metrics import f1_score
import numpy as np

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return {"f1": f1_score(labels, preds, average="weighted")}

# Treinar
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=hf_train,
    eval_dataset=hf_test,
    tokenizer=tokenizer,
    data_collator=DataCollatorWithPadding(tokenizer),
    compute_metrics=compute_metrics,
)
trainer.train()
trainer.save_model("models/bert_final")
```

---

## Comparativo: Quando Usar Cada Framework

| Critério | Sklearn | XGBoost/LGBM | PyTorch | TensorFlow/Keras |
|----------|---------|--------------|---------|-----------------|
| Dados tabulares | ✅ | ✅✅ | OK | OK |
| Deep learning | ❌ | ❌ | ✅✅ | ✅✅ |
| Produção/deploy | ✅ | ✅ | ✅ | ✅✅ TF Serving |
| Pesquisa/flexibilidade | OK | OK | ✅✅ | OK |
| Curva de aprendizado | Fácil | Médio | Médio | Fácil |
| Community/modelos | Grande | Grande | Enorme | Grande |
| Mobile/edge | ❌ | ❌ | TorchMobile | TFLite ✅ |
| NLP/Vision | Básico | ❌ | HuggingFace | HuggingFace |
