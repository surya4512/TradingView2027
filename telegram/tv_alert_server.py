"""
TradingView webhook receiver -> Telegram notification.
# pip install flask requests

Setup:
    pip install flask requests
    export TELEGRAM_BOT_TOKEN="123456:ABC..."   # from @BotFather
    export TELEGRAM_CHAT_ID="your_chat_id"      # from @userinfobot
    export WEBHOOK_SECRET="choose-a-long-random-string"
    python tv_alert_server.py

TradingView alert settings:
    - Condition: your "Open Levels" indicator -> pick an alert (e.g. "Cross above Open")
    - Webhook URL: https://YOUR_PUBLIC_URL/webhook   (use ngrok or a server; must be public)
    - Message (JSON):
        {"secret": "choose-a-long-random-string",
         "symbol": "{{ticker}}", "price": "{{close}}",
         "time": "{{timenow}}", "alert": "Cross above Open"}
"""

import os
import logging

import requests
from flask import Flask, request, jsonify

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
SECRET = os.environ.get("WEBHOOK_SECRET", "")

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def send_telegram(text: str) -> None:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=10)
    r.raise_for_status()


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)
    if data is None:
        # TradingView sends plain text if the message is not valid JSON
        data = {"alert": request.get_data(as_text=True)}

    if SECRET and data.get("secret") != SECRET:
        logging.warning("Rejected request with bad secret")
        return jsonify({"status": "forbidden"}), 403

    msg = (
        f"🚨 {data.get('alert', 'Alert')}\n"
        f"Symbol: {data.get('symbol', '-')}\n"
        f"Price: {data.get('price', '-')}\n"
        f"Time: {data.get('time', '-')}"
    )
    logging.info(msg.replace("\n", " | "))

    try:
        send_telegram(msg)
    except Exception as exc:
        logging.error("Telegram send failed: %s", exc)
        return jsonify({"status": "error", "detail": str(exc)}), 500

    return jsonify({"status": "ok"}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "running"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
