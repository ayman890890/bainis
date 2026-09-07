"""
Binance Read-Only MCP Server
-----------------------------
هذا السيرفر يعرض أدوات قراءة فقط لبيانات Binance (Spot + Futures).
لا يوجد فيه أي أداة تنفيذ صفقات، سحب أموال، أو أي عملية كتابة على الحساب.
"""

import os
import json
from typing import Literal

from binance.client import Client
from mcp.server.fastmcp import FastMCP

API_KEY = os.environ.get("BINANCE_API_KEY", "")
API_SECRET = os.environ.get("BINANCE_API_SECRET", "")

if not API_KEY or not API_SECRET:
    raise RuntimeError(
        "لم يتم العثور على BINANCE_API_KEY أو BINANCE_API_SECRET في متغيرات البيئة."
    )

client = Client(API_KEY, API_SECRET)

mcp = FastMCP("binance-readonly")

MarketType = Literal["spot", "futures"]


@mcp.tool()
def get_current_price(symbol: str, market: MarketType = "futures") -> str:
    """
    يرجع السعر اللحظي الحالي لزوج تداول معيّن.
    """
    symbol = symbol.upper()
    try:
        if market == "futures":
            data = client.futures_symbol_ticker(symbol=symbol)
        else:
            data = client.get_symbol_ticker(symbol=symbol)
        return json.dumps(
            {"symbol": symbol, "market": market, "price": data["price"]},
            ensure_ascii=False,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def get_klines(
    symbol: str,
    interval: str = "1h",
    market: MarketType = "futures",
    limit: int = 100,
) -> str:
    """
    يرجع بيانات الشموع (OHLCV) لزوج تداول وفريم زمني معيّن.
    """
    symbol = symbol.upper()
    try:
        if market == "futures":
            raw = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
        else:
            raw = client.get_klines(symbol=symbol, interval=interval, limit=limit)

        candles = [
            {
                "open_time": c[0],
                "open": c[1],
                "high": c[2],
                "low": c[3],
                "close": c[4],
                "volume": c[5],
                "close_time": c[6],
            }
            for c in raw
        ]
        return json.dumps(
            {
                "symbol": symbol,
                "market": market,
                "interval": interval,
                "count": len(candles),
                "candles": candles,
            },
            ensure_ascii=False,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    mcp.settings.port = port
    mcp.settings.host = "0.0.0.0"
    mcp.run(transport="streamable-http")
