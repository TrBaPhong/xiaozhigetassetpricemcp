import yfinance as yf
import requests
from fastmcp import FastMCP
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    filename="getprice.log",
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)


API_KEY = "3dbcc3e084e04a4ea3db50c579b6eff8"
CMC_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
SWISSQUOTE_URL = "https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/XAU/USD"
SJC_API_URL = "http://api.btmc.vn/api/BTMCAPI/getpricebtmc"
BTMC_API_KEY = "3kd8ub1llcg9t45hnoh8hmn7t5kc2v"

# Create an MCP server
mcp = FastMCP("asset_price")

@mcp.tool()
def cryptocurrency_price(symbol: str, currency: str = "USD") -> dict:
    """
    Fetch current cryptocurrency price from CoinMarketCap API.

    Args:
        symbol: crypto symbol, e.g. 'BTC', 'ETH'
        currency: fiat currency, default 'USD'

    Returns:
        JSON with price and market data.
    """
    try:
        params = {
            "symbol": symbol.upper(),
            "convert": currency.upper()
        }

        headers = {
            "Accepts": "application/json",
            "X-CMC_PRO_API_KEY": API_KEY
        }

        logger.info(f"Requesting CMC: {params}")

        response = requests.get(CMC_URL, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        if "data" not in data or symbol.upper() not in data["data"]:
            return {"success": False, "error": "Invalid symbol or API error", "raw": data}

        quote = data["data"][symbol.upper()]["quote"][currency.upper()]
        info = data["data"][symbol.upper()]

        return {
            "success": True,
            "symbol": symbol.upper(),
            "name": info["name"],
            "price": quote["price"],
            "percent_change_1h": quote.get("percent_change_1h"),
            "percent_change_24h": quote.get("percent_change_24h"),
            "percent_change_7d": quote.get("percent_change_7d"),
            "market_cap": quote.get("market_cap"),
            "volume_24h": quote.get("volume_24h"),
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def stock_price(symbol: str, currency: str = "USD") -> dict:
    """
    Fetch stock price from Yahoo Finance.
    Example symbols: AAPL, TSLA, MSFT, GOOG
    """
    try:
        symbol = symbol.upper().strip()

        logger.info(f"[Yahoo] Fetching stock: {symbol}")

        stock = yf.Ticker(symbol)
        logger.info("get stock successfully")
        info = stock.fast_info  # fast, lightweight
        logger.info(f"stockinfo {info}")

        if not info:
            return {"success": False, "error": "Invalid stock symbol"}
        logger.info(f"last_price {info.get("last_price")}")
        logger.info(f"open {info.get("opens")}")
        logger.info(f"previous_close {info.get("previous_close")}")
        return {
            "success": True,
            "symbol": symbol,
            "last_price": info.get("last_price") or info.get("previous_close"),
            "open": info.get("open"),
            "day_high": info.get("day_high"),
            "day_low": info.get("day_low"),
            "previous_close": info.get("previous_close"),
            "volume": info.get("volume"),
            "market_cap": info.get("market_cap"),
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def gold_price() -> dict:
    """
    Fetch current gold price (XAU/USD) from Swissquote public API.
    Returns bid, ask, spread, and timestamp.
    """
    try:
        logger.info(f"Requesting Swissquote gold price: {SWISSQUOTE_URL}")
        response = requests.get(SWISSQUOTE_URL, timeout=8)
        response.raise_for_status()
        data = response.json()

        if not data or "spreadProfilePrices" not in data[0]:
            return {"success": False, "error": "Invalid response", "raw": data}

        # Chọn spread profile "premium" làm mặc định
        spread_data = next((s for s in data[0]["spreadProfilePrices"] if s["spreadProfile"]=="premium"), data[0]["spreadProfilePrices"][0])

        bid = spread_data.get("bid")
        ask = spread_data.get("ask")
        bidSpread = spread_data.get("bidSpread")
        askSpread = spread_data.get("askSpread")
        ts = data[0].get("ts")

        # Convert timestamp nếu cần
        dt = datetime.fromtimestamp(ts / 1000.0) if ts else None

        return {
            "success": True,
            "bid": bid,
            "ask": ask,
            "bidSpread": bidSpread,
            "askSpread": askSpread,
            "timestamp": ts,
            "datetime": dt.isoformat() if dt else None
        }

    except requests.Timeout:
        return {"success": False, "error": "Timeout while connecting to Swissquote"}

    except Exception as e:
        logger.error(f"Error fetching gold price: {e}")
        return {"success": False, "error": str(e)}

@mcp.tool()
def gold_sjc_price() -> dict:
    """
    Fetch current SJC gold price from BTMC API.
    Returns buy_price, sell_price, and timestamp.
    """
    try:
        params = {"key": BTMC_API_KEY}
        logger.info(f"Requesting SJC gold price: {SJC_API_URL} with key={API_KEY}")

        response = requests.get(SJC_API_URL, params=params, timeout=8)
        response.raise_for_status()
        data = response.json()

        # Kiểm tra cấu trúc dữ liệu
        if not data or "SJC" not in data:
            return {"success": False, "error": "Invalid response", "raw": data}

        sjc_data = data["SJC"]

        buy_price = sjc_data.get("buy") or sjc_data.get("mua")
        sell_price = sjc_data.get("sell") or sjc_data.get("ban")
        ts = sjc_data.get("timestamp")  # nếu API có trường timestamp

        # Convert timestamp nếu có
        dt = datetime.fromtimestamp(ts) if ts else None

        return {
            "success": True,
            "buy_price": buy_price,
            "sell_price": sell_price,
            "timestamp": ts,
            "datetime": dt.isoformat() if dt else None
        }

    except requests.Timeout:
        return {"success": False, "error": "Timeout while connecting to BTMC API"}

    except Exception as e:
        logger.error(f"Error fetching SJC gold price: {e}")
        return {"success": False, "error": str(e)}

# Start the server
if __name__ == "__main__":
    mcp.run(transport="stdio")