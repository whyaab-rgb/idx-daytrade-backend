from statistics import mean


def sma(values, length):
    if len(values) < length:
        return None
    return mean(values[-length:])


def ema(values, length):
    if len(values) < length:
        return None

    k = 2 / (length + 1)
    e = values[0]

    for price in values[1:]:
        e = price * k + e * (1 - k)

    return e


def rsi(values, length=14):
    if len(values) < length + 1:
        return None

    gains = []
    losses = []
    recent = values[-(length + 1):]

    for i in range(1, len(recent)):
        diff = recent[i] - recent[i - 1]
        gains.append(max(diff, 0))
        losses.append(abs(min(diff, 0)))

    avg_gain = mean(gains)
    avg_loss = mean(losses)

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calculate_daytrade_signal(symbol: str, candles: list[dict]):
    if len(candles) < 25:
        return {
            "symbol": symbol,
            "action": "SKIP",
            "momentum": "DATA KURANG",
            "score": 0,
            "note": "Data candle tidak cukup",
        }

    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    volumes = [c["volume"] for c in candles]

    last = candles[-1]
    prev = candles[-2]

    close = last["close"]
    open_ = last["open"]
    volume = last["volume"]

    rsi14 = rsi(closes, 14) or 0
    ema20 = ema(closes[-30:], 20) or close
    avg_vol20 = sma(volumes, 20) or volume

    prev_high = max(highs[-6:-1])
    prev_low = min(lows[-6:-1])

    change_pct = (
        ((close - prev["close"]) / prev["close"]) * 100
        if prev["close"]
        else 0
    )

    vol_ratio = volume / avg_vol20 if avg_vol20 else 0

    score = 0
    reasons = []

    # =========================
    # VOLUME
    # =========================
    if vol_ratio >= 2:
        score += 25
        reasons.append("volume spike kuat")
    elif vol_ratio >= 1.3:
        score += 15
        reasons.append("volume naik")
    elif vol_ratio >= 0.8:
        score += 8
        reasons.append("volume mulai naik")

    # =========================
    # PRICE MOMENTUM
    # =========================
    if change_pct >= 2:
        score += 20
        reasons.append("harga naik intraday")
    elif change_pct > 0:
        score += 10
        reasons.append("harga hijau")

    # =========================
    # RSI
    # =========================
    if 45 <= rsi14 <= 75:
        score += 15
        reasons.append("RSI momentum sehat")
    elif 35 <= rsi14 < 45:
        score += 12
        reasons.append("RSI mulai rebound")
    elif 25 <= rsi14 < 35:
        score += 5
        reasons.append("RSI oversold rebound awal")

    # =========================
    # BREAKOUT
    # =========================
    if close > prev_high:
        score += 20
        reasons.append("breakout high pendek")

    # =========================
    # EMA TREND
    # =========================
    if close > ema20:
        score += 15
        reasons.append("di atas EMA20")

    # =========================
    # CANDLE
    # =========================
    if close > open_:
        score += 5
        reasons.append("candle bullish")

    # =========================
    # FINAL ACTION
    # =========================
    if score >= 70:
        action = "ENTRY NOW"
        momentum = "BREAKOUT"
    elif score >= 55:
        action = "WATCH BREAKOUT"
        momentum = "MOMENTUM"
    elif score >= 40:
        action = "BUY ON PULLBACK"
        momentum = "PULLBACK"
    else:
        action = "NO TRADE"
        momentum = "WEAK"

    # =========================
    # RISK MANAGEMENT
    # =========================
    entry = round(close, 2)
    sl = round(min(prev_low, close * 0.97), 2)

    risk = max(entry - sl, entry * 0.01)

    tp1 = round(entry + risk * 1.2, 2)
    tp2 = round(entry + risk * 2.0, 2)

    # =========================
    # VOLUME STATUS
    # =========================
    if vol_ratio >= 2:
        volume_status = "VERY HIGH"
    elif vol_ratio >= 1.3:
        volume_status = "HIGH"
    elif vol_ratio >= 0.8:
        volume_status = "MEDIUM"
    else:
        volume_status = "NORMAL"

    return {
        "symbol": symbol,
        "momentum": momentum,
        "action": action,
        "entry": entry,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
        "rsi": round(rsi14, 2),
        "change_pct": round(change_pct, 2),
        "volume_ratio": round(vol_ratio, 2),
        "volume_status": volume_status,
        "score": int(score),
        "note": ", ".join(reasons) if reasons else "belum ada momentum kuat",
    }
