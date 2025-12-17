"""
MT5 Trading Client for Sheratan Core
Adapted from GPT Hub trading_tab.py

Provides MT5 integration as a tool handler.
"""

import os
from typing import Optional
from dataclasses import dataclass

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False


@dataclass
class TradeResult:
    success: bool
    ticket: Optional[int] = None
    price: Optional[float] = None
    error: Optional[str] = None


@dataclass
class PriceData:
    symbol: str
    bid: float
    ask: float
    error: Optional[str] = None


def init_mt5() -> bool:
    """Initialize MT5 connection."""
    if not MT5_AVAILABLE:
        return False
    return mt5.initialize()


def get_price(symbol: str) -> PriceData:
    """Get current bid/ask for symbol."""
    if not MT5_AVAILABLE:
        return PriceData(symbol=symbol, bid=0, ask=0, error="MT5 not installed")
    
    if not mt5.initialize():
        return PriceData(symbol=symbol, bid=0, ask=0, error="MT5 not connected")
    
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return PriceData(symbol=symbol, bid=0, ask=0, error=f"Symbol {symbol} not found")
    
    return PriceData(symbol=symbol, bid=tick.bid, ask=tick.ask)


def calculate_crv(entry: float, sl: float, tp: float) -> float:
    """Calculate Chance-Risiko-Verhältnis (reward/risk ratio)."""
    risk = abs(entry - sl)
    reward = abs(tp - entry)
    if risk == 0:
        return 0
    return round(reward / risk, 2)


def execute_order(
    symbol: str,
    direction: str,  # "BUY" or "SELL"
    lot: float,
    sl: float,
    tp: float,
    comment: str = "Sheratan Core"
) -> TradeResult:
    """
    Execute a market order via MT5.
    
    Args:
        symbol: Trading symbol (e.g., "EURUSD")
        direction: "BUY" or "SELL"
        lot: Lot size (e.g., 0.1)
        sl: Stop Loss price
        tp: Take Profit price
        comment: Order comment
        
    Returns:
        TradeResult with success status and ticket/error
    """
    if not MT5_AVAILABLE:
        return TradeResult(success=False, error="MT5 not available")
    
    if not mt5.initialize():
        return TradeResult(success=False, error="MT5 not connected")
    
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        return TradeResult(success=False, error=f"Symbol {symbol} not found")
    
    if not symbol_info.visible:
        mt5.symbol_select(symbol, True)
    
    price = mt5.symbol_info_tick(symbol)
    order_type = mt5.ORDER_TYPE_BUY if direction.upper() == "BUY" else mt5.ORDER_TYPE_SELL
    entry_price = price.ask if direction.upper() == "BUY" else price.bid
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": order_type,
        "price": entry_price,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": 234567,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        return TradeResult(success=True, ticket=result.order, price=entry_price)
    else:
        return TradeResult(success=False, error=f"Order failed: {result.comment}")


# ============================================
# Tool Handler Interface (for worker_loop.py)
# ============================================

def handle_mt5_price(params: dict) -> dict:
    """
    Tool handler for kind: "mt5_price"
    
    params:
        symbol: str
    """
    symbol = params.get("symbol", "EURUSD")
    result = get_price(symbol)
    
    return {
        "ok": result.error is None,
        "symbol": result.symbol,
        "bid": result.bid,
        "ask": result.ask,
        "error": result.error
    }


def handle_mt5_order(params: dict) -> dict:
    """
    Tool handler for kind: "mt5_order"
    
    params:
        symbol: str
        direction: "BUY" | "SELL"
        lot: float
        sl: float
        tp: float
        comment: str (optional)
    """
    result = execute_order(
        symbol=params.get("symbol", "EURUSD"),
        direction=params.get("direction", "BUY"),
        lot=params.get("lot", 0.1),
        sl=params.get("sl", 0),
        tp=params.get("tp", 0),
        comment=params.get("comment", "Sheratan Core")
    )
    
    return {
        "ok": result.success,
        "ticket": result.ticket,
        "price": result.price,
        "error": result.error
    }
