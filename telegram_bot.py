import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TELEGRAM_COOLDOWN_SECONDS = int(os.getenv("TELEGRAM_COOLDOWN_SECONDS", "900"))

_last_sent = {}

def status_emoji(score: int):
    if score >= 85:
        return "🟢"
    if score >= 75:
        return "🟡"
    return "🔴"

def action_emoji(action: str):
    return {
        "BUY FAST": "🚀",
        "BUY PULLBACK": "⚡",
        "WATCH": "👀",
        "WAIT": "⏳",
        "AVOID": "🔻",
    }.get(action, "📊")

def should_send_top10(signals: list[dict]):
    key = "TOP10_DAYTRADE"
    now = time.time()

    if key in _last_sent and now - _last_sent[key] < TELEGRAM_COOLDOWN_SECONDS:
        return False

    qualified = [s for s in signals if s.get("score", 0) >= 75]
    if not qualified:
        return False

    _last_sent[key] = now
    return True

def format_top10_message(signals: list[dict]):
    top10 = signals[:10]

    lines = [
        "🚨 <b>TOP 10 IDX DAY TRADE SIGNAL</b> 🚨",
        "━━━━━━━━━━━━━━━━━━",
    ]

    for i, row in enumerate(top10, start=1):
        score = int(row.get("score", 0))
        action = row.get("action", "-")
        symbol = row.get("symbol", "-")

        lines += [
            f"{status_emoji(score)} <b>#{i} {symbol}</b>",
            f"{action_emoji(action)} <b>{action}</b> | {row.get('momentum', '-')}",
            f"💰 Entry : <b>{row.get('entry', '-')}</b>",
            f"🎯 TP1   : <b>{row.get('tp1', '-')}</b>",
            f"🎯 TP2   : <b>{row.get('tp2', '-')}</b>",
            f"🛑 SL    : <b>{row.get('sl', '-')}</b>",
            f"📈 RSI   : <b>{row.get('rsi', '-')}</b>",
            f"🔥 Vol   : <b>{row.get('volume_status', '-')}</b> x{row.get('volume_ratio', '-')}",
            f"⭐ Score : <b>{score}</b>",
            f"📝 {row.get('note', '-')}",
            "━━━━━━━━━━━━━━━━━━",
        ]

    lines.append("⚠️ Bukan rekomendasi beli/jual. Tetap pakai money management tetap sabar jika merah dan selalu tp saat hijau.")
    return "\n".join(lines)

def send_telegram(message: str):
    if not BOT_TOKEN or not CHAT_ID:
        return {"ok": False, "error": "BOT_TOKEN / CHAT_ID belum diisi"}

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    r = requests.post(url, data=payload, timeout=15)
    try:
        data = r.json()
    except Exception:
        data = {"text": r.text}

    return {"ok": r.ok, "status_code": r.status_code, "response": data}
