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
        # Untuk day trading, gunakan 15m.
        # Jika ingin scalping cepat, bisa ganti ke "5m".
        raw = fetch_chart(symbol, timeframe="15m", range_="7d")

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
        # FAST FILTER DAY TRADING
        # =========================

        if close < 50:
            skipped.append({"symbol": symbol, "reason": "harga di bawah 50"})
            time.sleep(sleep_seconds)
            continue

        if volume < 50_000:
            skipped.append({"symbol": symbol, "reason": "volume intraday kecil"})
            time.sleep(sleep_seconds)
            continue

        if value < 10_000_000:
            skipped.append({"symbol": symbol, "reason": "value intraday kecil"})
            time.sleep(sleep_seconds)
            continue

        # Untuk day trading, jangan terlalu ketat.
        # Saham boleh masuk walau volume_ratio masih 0.5
        if volume_ratio < 0.5:
            skipped.append({"symbol": symbol, "reason": "volume belum cukup kuat"})
            time.sleep(sleep_seconds)
            continue

        # =========================
        # DEEP ANALYSIS
        # =========================

        signal = calculate_daytrade_signal(symbol, candles)

        # Tambahkan klasifikasi entry agar app lebih jelas
        score = signal.get("score", 0)
        action = signal.get("action", "WAIT")

        if score >= 85:
            entry_status = "ENTRY NOW"
        elif score >= 70:
            entry_status = "BUY ON PULLBACK"
        elif score >= 55:
            entry_status = "WATCH BREAKOUT"
        else:
            entry_status = "NO TRADE"

        signal["entry_status"] = entry_status
        signal["last_close"] = close
        signal["last_volume"] = volume
        signal["last_value"] = value
        signal["change_pct"] = round(change_pct, 2)
        signal["volume_ratio"] = round(volume_ratio, 2)
        signal["timeframe"] = "15m"

        print("SYMBOL:", symbol)
        print("TIMEFRAME: 15m")
        print("JUMLAH CANDLES:", len(candles))
        print("CLOSE:", close)
        print("VOLUME:", volume)
        print("VALUE:", value)
        print("CHANGE %:", round(change_pct, 2))
        print("VOLUME RATIO:", round(volume_ratio, 2))
        print("ENTRY STATUS:", entry_status)
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
