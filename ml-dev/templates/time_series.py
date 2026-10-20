"""
Template: Previsão de Séries Temporais
=======================================
Cobre: EDA temporal, Prophet, XGBoost com features de lag, LSTM.
Ajuste as seções marcadas com "# AJUSTAR"
"""

import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, matplotlib.pyplot as plt
from pathlib import Path
Path("models").mkdir(exist_ok=True); Path("reports").mkdir(exist_ok=True)


# ════════════════════════════════════════════════════════════
# 1. CARREGAR E PREPARAR
# ════════════════════════════════════════════════════════════
df = pd.read_csv("data/raw/timeseries.csv")   # AJUSTAR
DATE_COL  = "date"                             # AJUSTAR
VALUE_COL = "sales"                            # AJUSTAR
HORIZON   = 30                                 # dias a prever

df[DATE_COL] = pd.to_datetime(df[DATE_COL])
df = df.sort_values(DATE_COL).reset_index(drop=True)
df = df.set_index(DATE_COL)

print(f"Período: {df.index.min()} → {df.index.max()}")
print(f"Frequência: {pd.infer_freq(df.index)}")
print(f"Total: {len(df)} observações")
print(f"\nEstatísticas:\n{df[VALUE_COL].describe()}")

# Plot rápido
fig, axes = plt.subplots(2, 1, figsize=(14, 8))
df[VALUE_COL].plot(ax=axes[0], title="Série Temporal Completa")
df[VALUE_COL].rolling(7).mean().plot(ax=axes[0], label="MA-7", alpha=0.8)
df[VALUE_COL].tail(180).plot(ax=axes[1], title="Últimos 180 dias")
plt.tight_layout()
plt.savefig("reports/timeseries_overview.png", dpi=150)
plt.close()


# ════════════════════════════════════════════════════════════
# 2. PROPHET (recomendado para sazonalidade e tendência)
# ════════════════════════════════════════════════════════════

def run_prophet(df, date_col, value_col, horizon, freq="D",
                test_periods=None):
    from prophet import Prophet
    from sklearn.metrics import mean_absolute_error, mean_squared_error

    test_periods = test_periods or horizon

    # Formato Prophet: colunas "ds" e "y"
    df_prophet = df.reset_index().rename(columns={date_col: "ds", value_col: "y"})

    # Split temporal (NUNCA embaralhar séries temporais)
    train = df_prophet.iloc[:-test_periods]
    test  = df_prophet.iloc[-test_periods:]

    model = Prophet(
        seasonality_mode="multiplicative",   # "additive" se y ~ constante
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.05,        # 0.001–0.5, maior = mais flexível
        seasonality_prior_scale=10.0,
        interval_width=0.95,                 # intervalo de confiança 95%
    )

    # Adicionar feriados (opcional)
    # from prophet.make_holidays import make_holidays_df
    # model.add_country_holidays(country_name="BR")

    model.fit(train)

    # Prever período de teste + horizonte futuro
    future = model.make_future_dataframe(periods=test_periods + horizon, freq=freq)
    forecast = model.predict(future)

    # Métricas no período de teste
    y_true = test["y"].values
    y_pred = forecast.tail(test_periods + horizon).head(test_periods)["yhat"].values
    mae    = mean_absolute_error(y_true, y_pred)
    rmse   = np.sqrt(mean_squared_error(y_true, y_pred))
    mape   = np.mean(np.abs((y_true - y_pred) / (np.abs(y_true) + 1e-8))) * 100

    print(f"\nProphet — Test set ({test_periods} períodos):")
    print(f"  MAE  : {mae:,.2f}")
    print(f"  RMSE : {rmse:,.2f}")
    print(f"  MAPE : {mape:.2f}%")

    # Plots
    fig1 = model.plot(forecast)
    fig1.savefig("reports/prophet_forecast.png", dpi=150)
    fig2 = model.plot_components(forecast)
    fig2.savefig("reports/prophet_components.png", dpi=150)
    plt.close("all")

    # Salvar
    import joblib
    joblib.dump(model, "models/prophet_model.pkl")
    forecast.to_csv("reports/prophet_forecast.csv", index=False)

    return model, forecast


# ════════════════════════════════════════════════════════════
# 3. XGBOOST COM FEATURES DE LAG (mais flexível)
# ════════════════════════════════════════════════════════════

def create_lag_features(df, value_col, lags, windows):
    """Cria features de lag e rolling statistics."""
    df = df.copy()

    # Lags
    for lag in lags:
        df[f"lag_{lag}"] = df[value_col].shift(lag)

    # Rolling statistics
    for w in windows:
        df[f"roll_mean_{w}"] = df[value_col].shift(1).rolling(w).mean()
        df[f"roll_std_{w}"]  = df[value_col].shift(1).rolling(w).std()
        df[f"roll_min_{w}"]  = df[value_col].shift(1).rolling(w).min()
        df[f"roll_max_{w}"]  = df[value_col].shift(1).rolling(w).max()

    # Features temporais
    df["month"]       = df.index.month
    df["day_of_week"] = df.index.dayofweek
    df["day_of_year"] = df.index.dayofyear
    df["quarter"]     = df.index.quarter
    df["is_weekend"]  = (df.index.dayofweek >= 5).astype(int)

    # Encoding cíclico
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    df["dow_sin"]   = np.sin(2 * np.pi * df["day_of_week"] / 7)
    df["dow_cos"]   = np.cos(2 * np.pi * df["day_of_week"] / 7)

    return df.dropna()


def run_xgboost_ts(df, value_col, horizon, test_size=90):
    from xgboost import XGBRegressor
    from sklearn.metrics import mean_absolute_error, mean_squared_error

    # Criar features
    df_feat = create_lag_features(
        df, value_col,
        lags=[1, 2, 3, 7, 14, 21, 28],
        windows=[7, 14, 28],
    )

    feature_cols = [c for c in df_feat.columns if c != value_col]
    X = df_feat[feature_cols]
    y = df_feat[value_col]

    # Split temporal (nunca shuffle!)
    X_train, X_test = X.iloc[:-test_size], X.iloc[-test_size:]
    y_train, y_test = y.iloc[:-test_size], y.iloc[-test_size:]

    model = XGBRegressor(
        n_estimators=1000,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=5,
        reg_alpha=0.1,
        reg_lambda=1.0,
        early_stopping_rounds=50,
        random_state=42,
        n_jobs=-1,
    )

    # Validação temporal (usar últimos 20% do treino como val)
    val_size = len(X_train) // 5
    model.fit(
        X_train.iloc[:-val_size], y_train.iloc[:-val_size],
        eval_set=[(X_train.iloc[-val_size:], y_train.iloc[-val_size:])],
        verbose=100,
    )

    y_pred = model.predict(X_test)
    mae    = mean_absolute_error(y_test, y_pred)
    rmse   = np.sqrt(mean_squared_error(y_test, y_pred))
    mape   = np.mean(np.abs((y_test.values - y_pred) / (np.abs(y_test.values) + 1e-8))) * 100

    print(f"\nXGBoost TS — Test set ({test_size} dias):")
    print(f"  MAE  : {mae:,.2f}")
    print(f"  RMSE : {rmse:,.2f}")
    print(f"  MAPE : {mape:.2f}%")

    # Plot comparativo
    plt.figure(figsize=(14, 5))
    plt.plot(y_test.index, y_test.values, label="Real", color="blue")
    plt.plot(y_test.index, y_pred, label="Predito", color="orange", linestyle="--")
    plt.title("XGBoost — Real vs Predito")
    plt.legend(); plt.grid(True)
    plt.tight_layout()
    plt.savefig("reports/xgboost_ts_forecast.png", dpi=150)
    plt.close()

    import joblib
    joblib.dump(model, "models/xgboost_ts.pkl")
    return model


# ════════════════════════════════════════════════════════════
# 4. MÉTRICAS PARA SÉRIES TEMPORAIS
# ════════════════════════════════════════════════════════════

def ts_metrics(y_true, y_pred, naive_pred=None):
    """Calcula métricas completas incluindo MASE (normalizada pelo naive)."""
    mae    = np.mean(np.abs(y_true - y_pred))
    rmse   = np.sqrt(np.mean((y_true - y_pred) ** 2))
    mape   = np.mean(np.abs((y_true - y_pred) / (np.abs(y_true) + 1e-8))) * 100
    smape  = np.mean(2 * np.abs(y_true - y_pred) / (np.abs(y_true) + np.abs(y_pred) + 1e-8)) * 100

    metrics = {"MAE": mae, "RMSE": rmse, "MAPE (%)": mape, "sMAPE (%)": smape}

    if naive_pred is not None:
        mae_naive = np.mean(np.abs(y_true - naive_pred))
        metrics["MASE"] = mae / (mae_naive + 1e-8)

    for k, v in metrics.items():
        print(f"  {k:12s}: {v:.4f}")
    return metrics


# ════════════════════════════════════════════════════════════
# EXECUÇÃO
# ════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=== Prophet ===")
    run_prophet(df, DATE_COL, VALUE_COL, HORIZON)

    print("\n=== XGBoost com Lag Features ===")
    run_xgboost_ts(df, VALUE_COL, HORIZON)
