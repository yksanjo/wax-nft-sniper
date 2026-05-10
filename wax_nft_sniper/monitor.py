"""NFTMonitor — Real-time monitoring of WAX NFT collections."""

from __future__ import annotations

import time
import json
from datetime import datetime
from typing import Any, Callable

import httpx
from rich.console import Console
from rich.table import Table
from rich.live import Live


class NFTMonitor:
    """Monitor WAX NFT collections for new mints, sales, and floor changes.

    Features:
    - Track new mints in real-time
    - Alert on sales above configurable thresholds
    - Monitor floor price changes
    - Track whale wallet activity
    """

    def __init__(
        self,
        atomic_endpoint: str = "https://wax.api.atomicassets.io",
        check_interval: int = 30,
    ):
        self.atomic_endpoint = atomic_endpoint.rstrip("/")
        self.check_interval = check_interval
        self._client = httpx.Client(timeout=30)
        self._seen_assets: set[str] = set()
        self._seen_sales: set[str] = set()
        self._callbacks: list[Callable] = []
        self.console = Console()

    def on_event(self, callback: Callable):
        """Register a callback for events.

        Callback receives: (event_type: str, data: dict)
        event_type: 'sale', 'mint', 'whale'
        """
        self._callbacks.append(callback)

    def _notify(self, event_type: str, data: dict):
        """Notify all registered callbacks."""
        for cb in self._callbacks:
            try:
                cb(event_type, data)
            except Exception as e:
                self.console.print(f"[red]Callback error: {e}[/]")

    def get_recent_sales(
        self, collection: str | None = None, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Fetch recent sales from AtomicMarket."""
        params: dict[str, Any] = {
            "limit": limit,
            "order": "desc",
            "sort": "updated_at_time",
        }
        if collection:
            params["collection_name"] = collection

        resp = self._client.get(
            f"{self.atomic_endpoint}/atomicmarket/v1/sales",
            params=params,
        )
        resp.raise_for_status()
        return resp.json().get("data", [])

    def get_recent_mints(
        self, collection: str | None = None, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Fetch recently minted assets."""
        params: dict[str, Any] = {
            "limit": limit,
            "order": "desc",
            "sort": "minted_at_time",
        }
        if collection:
            params["collection_name"] = collection

        resp = self._client.get(
            f"{self.atomic_endpoint}/atomicassets/v1/assets",
            params=params,
        )
        resp.raise_for_status()
        return resp.json().get("data", [])

    def check_for_whales(
        self,
        collection: str,
        min_price: float = 500,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Check for whale-sized sales in a collection."""
        sales = self.get_recent_sales(collection=collection, limit=limit)
        whales = []

        for sale in sales:
            sale_id = str(sale.get("sale_id", ""))
            if sale_id in self._seen_sales:
                continue
            self._seen_sales.add(sale_id)

            sd = sale.get("data", sale)
            price = float(sd.get("price", {}).get("amount", 0))

            if price >= min_price:
                whale_data = {
                    "sale_id": sale_id,
                    "collection": collection,
                    "price": price,
                    "symbol": sd.get("price", {}).get(
                        "token_symbol", "WAXP"
                    ),
                    "buyer": sd.get("buyer", "?"),
                    "seller": sd.get("seller", "?"),
                    "asset": sd.get("assets", [{}])[0].get(
                        "name", "Unknown"
                    ),
                    "timestamp": datetime.now().isoformat(),
                }
                whales.append(whale_data)
                self._notify("whale", whale_data)

        return whales

    def check_new_mints(
        self, collection: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Check for newly minted assets in a collection."""
        mints = self.get_recent_mints(
            collection=collection, limit=limit
        )
        new_mints = []

        for mint in mints:
            asset_id = str(mint.get("asset_id", ""))
            if asset_id in self._seen_assets:
                continue
            self._seen_assets.add(asset_id)

            mint_data = {
                "asset_id": asset_id,
                "collection": collection,
                "name": mint.get("name", "Unknown"),
                "template": mint.get("template", {}).get(
                    "template_id", "?"
                ),
                "mint_time": mint.get("minted_at_time", ""),
                "timestamp": datetime.now().isoformat(),
            }
            new_mints.append(mint_data)
            self._notify("mint", mint_data)

        return new_mints

    def watch_collection(
        self,
        collection: str,
        min_price: float = 500,
        show_mints: bool = True,
        show_sales: bool = True,
    ):
        """Watch a collection in real-time with live display.

        Args:
            collection: Collection name to watch
            min_price: Minimum WAXP price for whale alerts
            show_mints: Show new mints
            show_sales: Show recent sales
        """
        self.console.print(
            f"[bold cyan]🔭 Watching: {collection}[/]\n"
            f"   Whale threshold: {min_price} WAXP\n"
            f"   Check interval: {self.check_interval}s\n"
            f"   Press Ctrl+C to stop\n"
        )

        try:
            with Live(refresh_per_second=1) as live:
                while True:
                    events = []

                    if show_sales:
                        whales = self.check_for_whales(
                            collection, min_price
                        )
                        for w in whales:
                            events.append(
                                f"🐋 [red]WHALE[/] {w['asset']} — "
                                f"{w['price']} {w['symbol']} "
                                f"({w['buyer'][:8]}...)"
                            )

                    if show_mints:
                        mints = self.check_new_mints(collection)
                        for m in mints:
                            events.append(
                                f"🆕 [green]MINT[/] {m['name']} "
                                f"(template #{m['template']})"
                            )

                    # Build display table
                    table = Table(
                        title=f"🔭 {collection} — "
                        f"{datetime.now().strftime('%H:%M:%S')}"
                    )
                    table.add_column("Time", style="dim")
                    table.add_column("Event", style="cyan")
                    table.add_column("Details")

                    # Show recent events
                    for event in events[-10:]:
                        parts = event.split(" ", 2)
                        if len(parts) == 3:
                            table.add_row(
                                datetime.now().strftime("%H:%M:%S"),
                                parts[1],
                                parts[2],
                            )

                    if not events:
                        table.add_row(
                            datetime.now().strftime("%H:%M:%S"),
                            "[dim]⏳[/]",
                            "No new events",
                        )

                    live.update(table)
                    time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.console.print("\n[yellow]👋 Monitor stopped[/]")

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
