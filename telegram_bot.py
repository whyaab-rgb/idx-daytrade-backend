import os
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram(message: str):

    if not BOT_TOKEN or not CHAT_ID:
        return {
            "ok": False,
            "error": "TOKEN / CHAT ID belum diisi"
        }

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        r = requests.post(url, json=payload, timeout=20)

        return {
            "ok": r.status_code == 200,
            "status_code": r.status_code,
            "response": r.json()
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }


def should_send_top10(top_signals):

    if not top_signals:
        return False

    for s in top_signals:

        action = s.get("action", "")
        score = s.get("score", 0)

        if action in [
            "ENTRY NOW",
            "WATCH BREAKOUT",
            "BUY ON PULLBACK"
        ] and score >= 55:

            return True

    return False


def format_top10_message(top_signals):

    if not top_signals:
        return "⚠️ Tidak ada signal potensial."

    text = "🚀 <b>TOP DAY TRADE SIGNAL</b>\n\n"

    medals = ["🥇", "🥈", "🥉"]

    for i, s in enumerate(top_signals):

        medal = medals[i] if i < 3 else "📈"

        text += (
            f"{medal} <b>{s['symbol']}</b>\n"
            f"🔥 {s['action']} | Score: {s['score']}\n"
            f"📊 Momentum: {s['momentum']}\n"
            f"💰 Entry: {s['entry']}\n"
            f"🎯 TP1: {s['tp1']}\n"
            f"🎯 TP2: {s['tp2']}\n"
            f"🛑 SL: {s['sl']}\n"
            f"📈 RSI: {s['rsi']}\n"
            f"📦 Volume: {s['volume_status']}\n"
            f"📝 {s['note']}\n\n"
        )

    return text
