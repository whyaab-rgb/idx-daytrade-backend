import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DATASECTOR_API_KEY", "")
BASE_URL = "https://api.datasectors.com/api"

HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json",
}


from datetime import datetime, timedelta

def fetch_chart(symbol: str, timeframe: str = "daily", range_: str = "6mo"):

    url = f"{BASE_URL}/chart-saham/{symbol}/{timeframe}"

    today = datetime.now()
    from_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    to_date = today.strftime("%Y-%m-%d")

    params = {
        "from": from_date,
        "to": to_date
    }

    try:
        r = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=15
        )

        print("URL:", r.url)
        print("STATUS:", r.status_code)
        print("TEXT:", r.text[:500])

        if r.status_code == 400:
            return {
                "ok": False,
                "symbol": symbol,
                "error": f"400 Bad Request: {r.text[:300]}",
                "data": []
            }

        if r.status_code == 429:
            return {
                "ok": False,
                "symbol": symbol,
                "error": "429 Too Many Requests",
                "data": []
            }

        if r.status_code == 404:
            return {
                "ok": False,
                "symbol": symbol,
                "error": "404 Endpoint / symbol salah",
                "data": []
            }

        if r.status_code >= 500:
            return {
                "ok": False,
                "symbol": symbol,
                "error": f"{r.status_code} Server error",
                "data": []
            }

        r.raise_for_status()

        return {
            "ok": True,
            "symbol": symbol,
            "error": None,
            "data": r.json()
        }

    except Exception as e:
        return {
            "ok": False,
            "symbol": symbol,
            "error": f"Request gagal: {e}",
            "data": []
        }

def normalize_candles(raw_response):
    data = raw_response

    # Format DataSectors chart-saham:
    # raw_response["data"]["data"]["data"]["chartbit"]
    try:
        chartbit = data["data"]["data"]["data"]["chartbit"]
        data = chartbit
    except Exception:
        pass

    if isinstance(data, dict):
        data = (
            data.get("chartbit")
            or data.get("data")
            or data.get("result")
            or data.get("candles")
            or data.get("chart")
            or data.get("values")
            or []
        )

    if isinstance(data, dict):
        for key in ["chartbit", "data", "result", "candles", "chart", "items", "values"]:
            if isinstance(data.get(key), list):
                data = data[key]
                break

    if not isinstance(data, list):
        return []

    candles = []

    # Data dari API terbaru ada dari tanggal terbaru ke lama,
    # jadi nanti kita balik agar urut lama ke terbaru.
    for item in data:
        if not isinstance(item, dict):
            continue

        o = item.get("open") or item.get("o")
        h = item.get("high") or item.get("h")
        l = item.get("low") or item.get("l")
        c = item.get("close") or item.get("c")
        v = item.get("volume") or item.get("v") or 0

        try:
            candles.append({
                "open": float(o),
                "high": float(h),
                "low": float(l),
                "close": float(c),
                "volume": float(v),
            })
        except Exception:
            continue

    candles = list(reversed(candles))

    return candles
