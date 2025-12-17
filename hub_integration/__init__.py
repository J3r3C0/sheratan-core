"""
Hub Integration Package

Valuable components from GPT Hub adapted for Sheratan Core.
"""

from .mt5_client import (
    init_mt5,
    get_price,
    execute_order,
    calculate_crv,
    handle_mt5_price,
    handle_mt5_order
)

from .ml_predictor import (
    fetch_mt5_data,
    create_features,
    load_model,
    predict,
    handle_ml_predict,
    handle_ml_train
)

from .llm_fallback import (
    LLMFallbackClient,
    ask_llm,
    get_client,
    handle_llm_call_fallback
)

__all__ = [
    # MT5
    "init_mt5", "get_price", "execute_order", "calculate_crv",
    "handle_mt5_price", "handle_mt5_order",
    # ML
    "fetch_mt5_data", "create_features", "load_model", "predict",
    "handle_ml_predict", "handle_ml_train",
    # LLM
    "LLMFallbackClient", "ask_llm", "get_client", "handle_llm_call_fallback"
]
