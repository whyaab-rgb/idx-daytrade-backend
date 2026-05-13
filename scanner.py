import time
from symbols import IDX_SYMBOLS
from datasector import fetch_chart, normalize_candles
from daytrade_logic import calculate_daytrade_signal


def scan_daytrade(limit_symbols: int | None = None, sleep_seconds: float = 2):
    symbols = IDX_SYMBOLS[:limit_symbols] if limit_symbols else IDX_SYMBOLS

    results = []
    errors = []
    skipped = []

    for symbol in symbols:
        raw = fetch_chart(symbol, timeframe="daily", range_="6mo")

        if not raw.get("ok"):
            errors.append({
                "symbol": symbol,
                "error": raw.get("error")
            })
            time.sleep(sleep_seconds)
            continue

        candles = normalize_candles(raw.get("data"))

        if len(candles) < 20:
            skipped.append({"symbol": symbol, "reason": "data candle kurang"})
            time.sleep(sleep_seconds)
            continue

        # Buang candle hari ini yang volume-nya 0
        valid_candles = [
            c for c in candles
            if c.get("volume", 0) > 0
            and c.get("close", 0) > 0
            and c.get("open", 0) > 0
            and c.get("high", 0) > 0
            and c.get("low", 0) > 0
        ]

        if len(valid_candles) < 20:
            skipped.append({"symbol": symbol, "reason": "candle valid kurang"})
            time.sleep(sleep_seconds)
            continue

        candles = valid_candles

        last = candles[-1]
        prev = candles[-2]

        close = last["close"]
        volume = last["volume"]
        value = close * volume

        prev_close = prev["close"]

        if prev_close <= 0:
            skipped.append({"symbol": symbol, "reason": "prev close tidak valid"})
            time.sleep(sleep_seconds)
            continue

        change_pct = ((close - prev_close) / prev_close) * 100

        volumes = [c["volume"] for c in candles[-20:] if c["volume"] > 0]
        avg_volume = sum(volumes) / len(volumes) if volumes else 0
        volume_ratio = volume / avg_volume if avg_volume > 0 else 0

        # =========================
        # FAST FILTER LONGGAR
        # =========================

        if volume < 100_000:
            skipped.append({"symbol": symbol, "reason": "volume kecil"})
            time.sleep(sleep_seconds)
            continue

        if close < 50:
            skipped.append({"symbol": symbol, "reason": "harga di bawah 50"})
            time.sleep(sleep_seconds)
            continue

        if value < 50_000_000:
            skipped.append({"symbol": symbol, "reason": "value kecil"})
            time.sleep(sleep_seconds)
            continue

        if volume_ratio < 0.1:
            skipped.append({"symbol": symbol, "reason": "volume belum naik"})
            time.sleep(sleep_seconds)
            continue

        # =========================
        # DEEP ANALYSIS
        # =========================

        signal = calculate_daytrade_signal(symbol, candles)

        # Tambahan info agar tampil di app
        signal["last_close"] = close
        signal["last_volume"] = volume
        signal["last_value"] = value
        signal["change_pct"] = round(change_pct, 2)
        signal["volume_ratio"] = round(volume_ratio, 2)

        print("SYMBOL:", symbol)
        print("JUMLAH CANDLES:", len(candles))
        print("CLOSE:", close)
        print("VOLUME:", volume)
        print("VALUE:", value)
        print("CHANGE %:", round(change_pct, 2))
        print("VOLUME RATIO:", round(volume_ratio, 2))
        print("SIGNAL:", signal)

        if signal.get("action") != "SKIP":
            results.append(signal)

        time.sleep(sleep_seconds)

    results = sorted(results, key=lambda x: x.get("score", 0), reverse=True)

    return {
        "count": len(results),
        "results": results,
        "errors": errors[:20],
        "skipped": skipped[:20],
    }
