# Hub Integration Module

Wertvolle Komponenten aus GPT Hub für Sheratan Core.

## Enthaltene Module

| Modul | Zweck | Original |
|-------|-------|----------|
| `mt5_client.py` | MetaTrader5 Trading | `trading_tab.py` |
| `ml_predictor.py` | XGBoost/LightGBM Prediction | `ml_training_tab.py` |
| `llm_fallback.py` | Multi-LLM Fallback Pattern | `gpt_core.py` |

## Geplante Tool-Handler

```yaml
# Für worker_loop.py
kind: "mt5_order"      # Trade ausführen
kind: "mt5_price"      # Preis abrufen
kind: "ml_predict"     # ML Vorhersage
kind: "ml_train"       # Modell trainieren
```

## Integration in Core

1. Module in `core/sheratan_core_v2/` verschieben
2. Tool-Handler in `worker/worker_loop.py` registrieren
3. LCP Actions für Trading erweitern

## Status

- [ ] MT5 Client adaptiert
- [ ] ML Predictor adaptiert
- [ ] LLM Fallback adaptiert
- [ ] In Worker integriert
- [ ] Tests geschrieben
