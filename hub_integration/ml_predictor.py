"""
ML Predictor for Sheratan Core
Adapted from GPT Hub ml_training_tab.py

Provides ML prediction as a tool handler.
"""

import os
import pickle
from typing import Optional, Dict, Any
from dataclasses import dataclass

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False


@dataclass
class PredictionResult:
    symbol: str
    timeframe: str
    prediction: str  # "BUY", "SELL", "NEUTRAL"
    confidence: float
    model_type: str
    error: Optional[str] = None


def fetch_mt5_data(symbol: str, timeframe: int, bars: int = 100) -> Optional[pd.DataFrame]:
    """Fetch OHLCV data from MT5."""
    if not MT5_AVAILABLE or not PANDAS_AVAILABLE:
        return None
    
    if not mt5.initialize():
        return None
    
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    if rates is None:
        return None
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df


def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create trading features from OHLCV data."""
    if df is None or df.empty:
        return df
    
    # Basic features
    df = df.copy()
    df['return'] = df['close'].pct_change()
    
    # Moving averages
    df['sma_10'] = df['close'].rolling(window=10).mean()
    df['sma_20'] = df['close'].rolling(window=20).mean()
    df['ema_10'] = df['close'].ewm(span=10).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # Target: Next period return direction
    df['target'] = (df['return'].shift(-1) > 0).astype(int)
    
    return df.dropna()


def load_model(model_path: str) -> Optional[Any]:
    """Load a trained model from disk."""
    if not os.path.exists(model_path):
        return None
    
    with open(model_path, 'rb') as f:
        return pickle.load(f)


def predict(model, features: pd.DataFrame) -> tuple:
    """Make prediction using trained model."""
    try:
        feature_cols = ['return', 'sma_10', 'sma_20', 'ema_10', 'rsi']
        X = features[feature_cols].iloc[-1:].values
        
        proba = model.predict_proba(X)[0]
        pred = model.predict(X)[0]
        
        direction = "BUY" if pred == 1 else "SELL"
        confidence = max(proba) * 100
        
        return direction, confidence
    except Exception as e:
        return "NEUTRAL", 50


def get_timeframe_const(tf_label: str) -> int:
    """Convert timeframe label to MT5 constant."""
    mapping = {
        "M1": 1, "M5": 5, "M15": 15,
        "H1": 60, "H4": 240, "D1": 1440
    }
    return mapping.get(tf_label, 60)


# ============================================
# Tool Handler Interface (for worker_loop.py)
# ============================================

def handle_ml_predict(params: dict) -> dict:
    """
    Tool handler for kind: "ml_predict"
    
    params:
        symbol: str (e.g., "EURUSD")
        timeframe: str (e.g., "H1")
        model_path: str (path to .pkl model)
    """
    symbol = params.get("symbol", "EURUSD")
    timeframe = params.get("timeframe", "H1")
    model_path = params.get("model_path")
    
    if not model_path:
        model_path = f"models/{symbol}_{timeframe}_xgboost.pkl"
    
    # Load model
    model = load_model(model_path)
    if model is None:
        return {
            "ok": False,
            "error": f"Model not found: {model_path}"
        }
    
    # Fetch data
    tf_const = get_timeframe_const(timeframe)
    df = fetch_mt5_data(symbol, tf_const, bars=100)
    if df is None:
        return {
            "ok": False,
            "error": "Could not fetch MT5 data"
        }
    
    # Create features & predict
    df_feat = create_features(df)
    direction, confidence = predict(model, df_feat)
    
    return {
        "ok": True,
        "symbol": symbol,
        "timeframe": timeframe,
        "prediction": direction,
        "confidence": round(confidence, 1),
        "model_path": model_path
    }


def handle_ml_train(params: dict) -> dict:
    """
    Tool handler for kind: "ml_train"
    
    params:
        symbol: str
        timeframe: str
        model_type: "xgboost" | "lightgbm"
        bars: int (default 3000)
    """
    try:
        symbol = params.get("symbol", "EURUSD")
        timeframe = params.get("timeframe", "H1")
        model_type = params.get("model_type", "xgboost")
        bars = params.get("bars", 3000)
        
        # Fetch data
        tf_const = get_timeframe_const(timeframe)
        df = fetch_mt5_data(symbol, tf_const, bars=bars)
        if df is None:
            return {"ok": False, "error": "Could not fetch MT5 data"}
        
        # Create features
        df_feat = create_features(df)
        
        # Train model
        feature_cols = ['return', 'sma_10', 'sma_20', 'ema_10', 'rsi']
        X = df_feat[feature_cols].values
        y = df_feat['target'].values
        
        if model_type == "xgboost":
            from xgboost import XGBClassifier
            model = XGBClassifier(n_estimators=100, max_depth=3)
        else:
            from lightgbm import LGBMClassifier
            model = LGBMClassifier(n_estimators=100, max_depth=3)
        
        model.fit(X, y)
        
        # Save model
        os.makedirs("models", exist_ok=True)
        model_path = f"models/{symbol}_{timeframe}_{model_type}.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        return {
            "ok": True,
            "symbol": symbol,
            "timeframe": timeframe,
            "model_type": model_type,
            "model_path": model_path,
            "samples": len(df_feat)
        }
        
    except Exception as e:
        return {"ok": False, "error": str(e)}
