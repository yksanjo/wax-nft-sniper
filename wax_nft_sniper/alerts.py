"""AlertManager — Send WAX NFT alerts via Telegram, webhook, or console."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

import httpx


class AlertManager:
    """Manages alert delivery channels for NFT events.

    Supports:
    - Telegram bot notifications
    - Webhook callbacks
    - Console output
    - File logging
    """

    def __init__(
        self,
        telegram_token: str | None = None,
        telegram_chat_id: str | None = None,
        webhook_url: str | None = None,
        log_file: str | None = None,
    ):
        self.telegram_token = telegram_token or os.getenv(
            "TELEGRAM_BOT_TOKEN"
        )
        self.telegram_chat_id = telegram_chat_id or os.getenv(
            "TELEGRAM_CHAT_ID"
        )
        self.webhook_url = webhook_url
        self.log_file = log_file
        self._client = httpx.Client(timeout=15)

    def send_telegram(self, message: str) -> bool:
        """Send a message via Telegram bot.

        Returns True if sent successfully.
        """
        if not self.telegram_token or not self.telegram_chat_id:
            return False

        url = (
            f"https://api.telegram.org/bot{self.telegram_token}"
            f"/sendMessage"
        )
        try:
            resp = self._client.post(
                url,
                json={
                    "chat_id": self.telegram_chat_id,
                    "text": message,
                    "parse_mode": "HTML",
                },
            )
            return resp.status_code == 200
        except Exception:
            return False

    def send_webhook(self, data: dict) -> bool:
        """Send event data to a webhook URL."""
        if not self.webhook_url:
            return False

        try:
            resp = self._client.post(
                self.webhook_url,
                json=data,
                headers={"Content-Type": "application/json"},
            )
            return resp.status_code == 200
        except Exception:
            return False

    def log_event(self, event_type: str, data: dict):
        """Log an event to file."""
        if not self.log_file:
            return

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "data": data,
        }

        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    def notify(self, event_type: str, data: dict):
        """Send notification through all configured channels.

        Args:
            event_type: 'whale', 'mint', 'sale', 'floor_change'
            data: Event data dictionary
        """
        # Build message
        if event_type == "whale":
            message = (
                f"🐋 <b>Whale Alert!</b>\n"
                f"Collection: {data.get('collection', '?')}\n"
                f"Asset: {data.get('asset', '?')}\n"
                f"Price: {data.get('price', '?')} "
                f"{data.get('symbol', 'WAXP')}\n"
                f"Buyer: {data.get('buyer', '?')}\n"
                f"Seller: {data.get('seller', '?')}"
            )
        elif event_type == "mint":
            message = (
                f"🆕 <b>New Mint!</b>\n"
                f"Collection: {data.get('collection', '?')}\n"
                f"Asset: {data.get('name', '?')}\n"
                f"Template: #{data.get('template', '?')}"
            )
        elif event_type == "sale":
            message = (
                f"💎 <b>Sale</b>\n"
                f"Collection: {data.get('collection', '?')}\n"
                f"Price: {data.get('price', '?')} "
                f"{data.get('symbol', 'WAXP')}"
            )
        else:
            message = f"<b>{event_type}</b>\n{json.dumps(data, indent=2)}"

        # Send through all channels
        self.send_telegram(message)
        self.send_webhook(data)
        self.log_event(event_type, data)

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
