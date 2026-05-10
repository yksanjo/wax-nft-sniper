"""NFTSniper — Automated NFT sniping and quick-buy monitoring."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

import httpx
from rich.console import Console


class NFTSniper:
    """Monitor for underpriced NFTs and sniping opportunities.

    Features:
    - Detect newly listed NFTs below market price
    - Monitor specific collections for cheap listings
    - Track floor price movements
    - Alert on potential sniping opportunities
    """

    def __init__(
        self,
        atomic_endpoint: str = "https://wax.api.atomicassets.io",
        check_interval: int = 15,
    ):
        self.atomic_endpoint = atomic_endpoint.rstrip("/")
        self.check_interval = check_interval
        self._client = httpx.Client(timeout=30)
        self._known_floors: dict[str, float] = {}
        self.console = Console()

    def get_collection_floor(
        self, collection: str
    ) -> tuple[float, str | None]:
        """Get the current floor price for a collection.

        Returns:
            Tuple of (floor_price, lowest_price_asset_name)
        """
        # Get cheapest assets for sale
        params = {
            "collection_name": collection,
            "limit": 5,
            "order": "asc",
            "sort": "price",
        }

        try:
            resp = self._client.get(
                f"{self.atomic_endpoint}/atomicmarket/v1/assets",
                params=params,
            )
            resp.raise_for_status()
            data = resp.json().get("data", [])

            if not data:
                return 0.0, None

            cheapest = data[0]
            price_data = cheapest.get("price", {})
            floor = float(price_data.get("amount", 0))
            asset_name = cheapest.get("name", "Unknown")

            return floor, asset_name

        except Exception as e:
            self.console.print(f"[red]Floor check error: {e}[/]")
            return 0.0, None

    def check_for_discounts(
        self,
        collection: str,
        discount_threshold: float = 0.2,
    ) -> list[dict[str, Any]]:
        """Check for listings significantly below floor price.

        Args:
            collection: Collection to check
            discount_threshold: Minimum discount from floor (e.g., 0.2 = 20% off)

        Returns:
            List of discounted listings found.
        """
        current_floor, _ = self.get_collection_floor(collection)
        if current_floor <= 0:
            return []

        # Get recent listings
        params = {
            "collection_name": collection,
            "limit": 20,
            "order": "asc",
            "sort": "price",
        }

        resp = self._client.get(
            f"{self.atomic_endpoint}/atomicmarket/v1/assets",
            params=params,
        )
        resp.raise_for_status()
        listings = resp.json().get("data", [])

        discounts = []
        for listing in listings:
            price_data = listing.get("price", {})
            price = float(price_data.get("amount", 0))

            if price <= 0:
                continue

            discount = (current_floor - price) / current_floor
            if discount >= discount_threshold:
                discounts.append(
                    {
                        "asset_id": listing.get("asset_id", ""),
                        "name": listing.get("name", "Unknown"),
                        "price": price,
                        "floor": current_floor,
                        "discount_pct": round(discount * 100, 1),
                        "seller": listing.get("seller", "?"),
                        "collection": collection,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        return discounts

    def monitor_floor(
        self, collection: str, drop_threshold: float = 0.05
    ):
        """Monitor floor price for significant drops.

        Args:
            collection: Collection to monitor
            drop_threshold: Minimum % drop to alert on (e.g., 0.05 = 5%)
        """
        self.console.print(
            f"[bold cyan]📊 Monitoring floor: {collection}[/]\n"
            f"   Drop threshold: {drop_threshold * 100}%\n"
            f"   Press Ctrl+C to stop\n"
        )

        try:
            while True:
                current_floor, cheapest = self.get_collection_floor(
                    collection
                )

                if collection in self._known_floors:
                    prev_floor = self._known_floors[collection]
                    if prev_floor > 0 and current_floor > 0:
                        change = (
                            current_floor - prev_floor
                        ) / prev_floor

                        if abs(change) >= drop_threshold:
                            direction = (
                                "📈 UP" if change > 0 else "📉 DOWN"
                            )
                            self.console.print(
                                f"[yellow]{direction}[/] "
                                f"{collection}: "
                                f"{prev_floor:.2f} → "
                                f"{current_floor:.2f} WAXP "
                                f"({change * 100:+.1f}%)"
                            )

                            if change < 0:
                                self.console.print(
                                    f"   Cheapest: {cheapest} "
                                    f"at {current_floor:.2f} WAXP "
                                    f"[green]🟢 SNIPE OPPORTUNITY[/]"
                                )

                self._known_floors[collection] = current_floor
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.console.print("\n[yellow]👋 Floor monitor stopped[/]")

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
