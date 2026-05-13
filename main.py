import os
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from cache import get_cache, set_cache
from scanner import scan_daytrade
from telegram_bot import send_telegram, format_top10_message, should_send_top10

load_dotenv()

app = FastAPI(title="IDX Day Trading Scanner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SCAN_COOLDOWN_SECONDS = int(os.getenv("SCAN_COOLDOWN_SECONDS", "300"))

@app.get("/")
def home():
    return {
        "app": "IDX Day Trading Scanner",
        "status": "active",
        "endpoints": ["/top-signal", "/scan-and-alert", "/telegram-test"],
    }

@app.get("/top-signal")
def top_signal(
    limit_symbols: int = Query(default=30, ge=1, le=800),
    top: int = Query(default=10, ge=1, le=50),
    force: bool = False,
):
    cache_key = f"top_signal_{limit_symbols}_{top}"

    if not force:
        cached = get_cache(cache_key, SCAN_COOLDOWN_SECONDS)
        if cached:
            cached["cached"] = True
            return cached

    scanned = scan_daytrade(limit_symbols=limit_symbols)
    results = scanned["results"][:top]

    payload = {
        "cached": False,
        "top": results,
        "errors": scanned["errors"],
    }

    set_cache(cache_key, payload)
    return payload

@app.post("/scan-and-alert")
def scan_and_alert(
    limit_symbols: int = Query(default=30, ge=1, le=800),
    top: int = Query(default=10, ge=1, le=10),
):
    scanned = scan_daytrade(limit_symbols=limit_symbols)
    top_signals = scanned["results"][:top]

    if should_send_top10(top_signals):
        message = format_top10_message(top_signals)
        tg = send_telegram(message)
    else:
        tg = {"ok": False, "info": "Tidak ada sinyal >=75 atau masih cooldown Telegram"}

    return {
        "sent": tg,
        "top": top_signals,
        "errors": scanned["errors"],
    }

@app.get("/telegram-test")
def telegram_test():
    message = "✅ <b>Telegram IDX Day Trading Scanner aktif</b>\nBot berhasil terhubung."
    return send_telegram(message)
