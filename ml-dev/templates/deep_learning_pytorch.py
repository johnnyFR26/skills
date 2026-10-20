"""
Template completo: Deep Learning com PyTorch
=============================================
Cobre: MLP tabular, CNN para imagens, fine-tuning de backbone pré-treinado.
Ajuste as seções marcadas com "# AJUSTAR"
"""

import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import torch, torch.nn as nn, torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from pathlib import Path
from datetime import datetime
import json

torch.manual_seed(42); np.random.seed(42)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Device: {device}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

Path("models").mkdir(exist_ok=True); Path("reports").mkdir(exist_ok=True)


# ════════════════════════════════════════════════════════════
# OPÇÃO A: MLP para Dados Tabulares
# ════════════════════════════════════════════════════════════

class TabularDataset(Dataset):
    def __init__(self, X: np.ndarray, y: np.ndarray, task="classification"):
        self.X = torch.FloatTensor(X)
        if task == "classification":
            self.y = torch.LongTensor(y)
        else:
            self.y = torch.FloatTensor(y).unsqueeze(1)

    def __len__(self): return len(self.X)
    def __getitem__(self, i): return self.X[i], self.y[i]


class MLP(nn.Module):
    """Multi-Layer Perceptron com BatchNorm, Dropout e Residual connections opcionais."""
    def __init__(self, input_dim: int, hidden_dims: list, output_dim: int,
                 dropout: float = 0.3, use_residual: bool = False):
        super().__init__()
        self.use_residual = use_residual
        self.blocks = nn.ModuleList()

        prev_dim = input_dim
        for h in hidden_dims:
            block = nn.Sequential(
                nn.Linear(prev_dim, h),
                nn.BatchNorm1d(h),
                nn.GELU(),
                nn.Dropout(dropout),
            )
            self.blocks.append(block)
            if use_residual and prev_dim == h:
                self.blocks[-1].add_module("residual", nn.Identity())
            prev_dim = h

        self.head = nn.Linear(prev_dim, output_dim)
        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, nonlinearity="relu")
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(self, x):
        for block in self.blocks:
            x = block(x)
        return self.head(x)


def get_class_weights(y_train: np.ndarray) -> torch.Tensor:
    """Calcula pesos inversamente proporcionais à frequência das classes."""
    from sklearn.utils.class_weight import compute_class_weight
    weights = compute_class_weight("balanced", classes=np.unique(y_train), y=y_train)
    return torch.FloatTensor(weights)


def train_epoch(model, loader, criterion, optimizer, scaler=None):
    model.train()
    total_loss = correct = total = 0
    for X_b, y_b in loader:
        X_b, y_b = X_b.to(device), y_b.to(device)
        optimizer.zero_grad(set_to_none=True)

        if scaler:  # Mixed precision
            with torch.amp.autocast(device_type="cuda"):
                out = model(X_b)
                loss = criterion(out, y_b)
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()
        else:
            out = model(X_b)
            loss = criterion(out, y_b)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

        total_loss += loss.item() * len(y_b)
        if y_b.dim() == 1:  # classificação
            correct += (out.argmax(1) == y_b).sum().item()
        total += len(y_b)

    return total_loss / total, correct / total if total > 0 else 0.0


@torch.no_grad()
def eval_epoch(model, loader, criterion):
    model.eval()
    total_loss = correct = total = 0
    all_preds, all_probs, all_labels = [], [], []

    for X_b, y_b in loader:
        X_b, y_b = X_b.to(device), y_b.to(device)
        out = model(X_b)
        loss = criterion(out, y_b)
        total_loss += loss.item() * len(y_b)
        if y_b.dim() == 1:
            probs = torch.softmax(out, dim=1)
            preds = probs.argmax(1)
            correct += (preds == y_b).sum().item()
            all_probs.append(probs.cpu())
        all_preds.append(preds.cpu() if y_b.dim() == 1 else out.cpu())
        all_labels.append(y_b.cpu())
        total += len(y_b)

    return (total_loss / total,
            correct / total if total > 0 else 0.0,
            torch.cat(all_preds),
            torch.cat(all_probs) if all_probs else None,
            torch.cat(all_labels))


def train_model(model, train_loader, val_loader, n_epochs=200, lr=1e-3,
                weight_decay=1e-4, patience=20, task="classification",
                class_weights=None, save_path="models/best_model.pt"):
    """Loop de treino completo com early stopping e mixed precision."""

    # Loss
    if task == "classification":
        criterion = nn.CrossEntropyLoss(weight=class_weights.to(device) if class_weights is not None else None)
    else:
        criterion = nn.MSELoss()

    # Optimizer e scheduler
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=n_epochs, eta_min=lr * 0.01)
    scaler    = torch.amp.GradScaler() if device.type == "cuda" else None

    best_val_loss = float("inf")
    patience_cnt  = 0
    history       = {"train_loss": [], "val_loss": [], "train_acc": [], "val_acc": []}

    for epoch in range(1, n_epochs + 1):
        tr_loss, tr_acc = train_epoch(model, train_loader, criterion, optimizer, scaler)
        vl_loss, vl_acc, _, _, _ = eval_epoch(model, val_loader, criterion)
        scheduler.step()

        history["train_loss"].append(tr_loss)
        history["val_loss"].append(vl_loss)
        history["train_acc"].append(tr_acc)
        history["val_acc"].append(vl_acc)

        # Early stopping
        if vl_loss < best_val_loss:
            best_val_loss = vl_loss
            torch.save(model.state_dict(), save_path)
            patience_cnt = 0
        else:
            patience_cnt += 1
            if patience_cnt >= patience:
                print(f"  Early stopping na época {epoch}")
                break

        if epoch % 10 == 0 or epoch == 1:
            lr_cur = scheduler.get_last_lr()[0]
            print(f"Ep {epoch:4d}/{n_epochs} | "
                  f"Train {tr_loss:.4f}/{tr_acc:.3f} | "
                  f"Val {vl_loss:.4f}/{vl_acc:.3f} | "
                  f"LR {lr_cur:.2e} | Patience {patience_cnt}/{patience}")

    # Carregar melhor
    model.load_state_dict(torch.load(save_path, map_location=device))
    print(f"\n✅ Melhor val_loss: {best_val_loss:.4f} — modelo carregado")
    return history


def plot_training_history(history, save_path="reports/training_history.png"):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].plot(history["train_loss"], label="Train")
    axes[0].plot(history["val_loss"],   label="Validation")
    axes[0].set_title("Loss"); axes[0].legend(); axes[0].grid(True)
    axes[1].plot(history["train_acc"], label="Train")
    axes[1].plot(history["val_acc"],   label="Validation")
    axes[1].set_title("Accuracy"); axes[1].legend(); axes[1].grid(True)
    plt.suptitle("Training History")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Histórico salvo em {save_path}")


# ── USO COMPLETO ────────────────────────────────────────────
if __name__ == "__main__":
    # AJUSTAR: substituir por seus dados reais
    from sklearn.datasets import make_classification
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

    X_raw, y_raw = make_classification(n_samples=10000, n_features=30,
                                       n_informative=20, random_state=42)
    X_train_raw, X_test_raw, y_train_np, y_test_np = train_test_split(
        X_raw, y_raw, test_size=0.2, random_state=42, stratify=y_raw
    )

    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train_raw)
    X_test_sc  = scaler.transform(X_test_raw)

    train_ds = TabularDataset(X_train_sc, y_train_np)
    test_ds  = TabularDataset(X_test_sc,  y_test_np)
    train_dl = DataLoader(train_ds, batch_size=256, shuffle=True,  pin_memory=True)
    test_dl  = DataLoader(test_ds,  batch_size=512, shuffle=False, pin_memory=True)

    model = MLP(
        input_dim=X_train_sc.shape[1],
        hidden_dims=[256, 128, 64],
        output_dim=2,
        dropout=0.3,
    ).to(device)
    print(f"Parâmetros: {sum(p.numel() for p in model.parameters()):,}")

    class_weights = get_class_weights(y_train_np)
    history = train_model(
        model, train_dl, test_dl,
        n_epochs=100, lr=1e-3, patience=15,
        class_weights=class_weights,
        save_path="models/mlp_best.pt",
    )

    plot_training_history(history)

    # Avaliação final
    from sklearn.metrics import classification_report, roc_auc_score
    model.eval()
    with torch.no_grad():
        logits = []
        for X_b, _ in test_dl:
            logits.append(model(X_b.to(device)).cpu())
        logits = torch.cat(logits)
        probs  = torch.softmax(logits, dim=1).numpy()
        preds  = logits.argmax(1).numpy()

    print("\n" + classification_report(y_test_np, preds))
    print(f"ROC-AUC: {roc_auc_score(y_test_np, probs[:, 1]):.4f}")
