"""CLI entry point for wax-nft-sniper."""

from __future__ import annotations

import argparse
import sys
import os

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .monitor import NFTMonitor
from .alerts import AlertManager
from .sniper import NFTSniper

console = Console()


def main():
    parser = argparse.ArgumentParser(
        description="wax-nft-sniper — Real-time WAX NFT monitoring and alerts",
    )
    parser.add_argument(
        "command",
        choices=[
            "watch",
            "whales",
            "mints",
            "floor",
            "discounts",
            "setup-telegram",
        ],
        nargs="?",
        help="Command to run",
    )
    parser.add_argument(
        "--collection",
        "-c",
        help="Collection name to monitor",
    )
    parser.add_argument(
        "--min-price",
        "-p",
        type=float,
        default=500,
        help="Minimum WAXP price for whale alerts (default: 500)",
    )
    parser.add_argument(
        "--interval",
        "-i",
        type=int,
        default=30,
        help="Check interval in seconds (default: 30)",
    )
    parser.add_argument(
        "--discount",
        "-d",
        type=float,
        default=0.2,
        help="Minimum discount from floor for sniping (default: 0.2 = 20%%)",
    )
    parser.add_argument(
        "--telegram-token",
        help="Telegram bot token (or set TELEGRAM_BOT_TOKEN env var)",
    )
    parser.add_argument(
        "--telegram-chat",
        help="Telegram chat ID (or set TELEGRAM_CHAT_ID env var)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        console.print(
            Panel(
                "[bold cyan]wax-nft-sniper[/]\n\n"
                "Commands:\n"
                "  watch <collection>     Real-time collection monitor\n"
                "  whales <collection>    Check for whale sales\n"
                "  mints <collection>     Check new mints\n"
                "  floor <collection>     Monitor floor price\n"
                "  discounts <collection> Find underpriced listings\n"
                "  setup-telegram         Configure Telegram alerts\n"
                "\n"
                "Options:\n"
                "  --collection, -c   Collection name\n"
                "  --min-price, -p    Whale threshold (default: 500 WAXP)\n"
                "  --interval, -i     Check interval (default: 30s)\n"
                "  --discount, -d     Discount threshold (default: 20%%)\n"
                "  --telegram-token   Telegram bot token\n"
                "  --telegram-chat    Telegram chat ID",
                title="🔭 WAX NFT Sniper",
            )
        )
        return

    try:
        if args.command == "setup-telegram":
            token = args.telegram_token or input(
                "Telegram Bot Token: "
            )
            chat_id = args.telegram_chat or input(
                "Telegram Chat ID: "
            )

            print(
                f"\nAdd these to your ~/.bashrc or ~/.zshrc:\n"
                f"  export TELEGRAM_BOT_TOKEN='{token}'\n"
                f"  export TELEGRAM_CHAT_ID='{chat_id}'\n"
            )
            print("Or pass them with --telegram-token and --telegram-chat")
            return

        if not args.collection:
            console.print(
                "[red]❌ Please provide --collection name[/]"
            )
            sys.exit(1)

        if args.command == "watch":
            monitor = NFTMonitor(check_interval=args.interval)
            alerts = AlertManager(
                telegram_token=args.telegram_token,
                telegram_chat_id=args.telegram_chat,
            )

            # Connect alerts to monitor
            monitor.on_event(
                lambda e, d: alerts.notify(e, d)
            )

            monitor.watch_collection(
                args.collection,
                min_price=args.min_price,
            )

        elif args.command == "whales":
            monitor = NFTMonitor(check_interval=args.interval)
            whales = monitor.check_for_whales(
                args.collection, min_price=args.min_price, limit=50
            )

            if whales:
                table = Table(
                    title=f"🐋 Whale Sales — {args.collection}"
                )
                table.add_column("Asset", style="cyan")
                table.add_column("Price", justify="right")
                table.add_column("Buyer")
                table.add_column("Seller")

                for w in whales:
                    table.add_row(
                        w["asset"],
                        f"{w['price']:.2f} {w['symbol']}",
                        w["buyer"][:12],
                        w["seller"][:12],
                    )
                console.print(table)
            else:
                console.print(
                    f"[green]✅ No whale sales (>={args.min_price} WAXP) "
                    f"found in '{args.collection}'[/]"
                )

        elif args.command == "mints":
            monitor = NFTMonitor(check_interval=args.interval)
            mints = monitor.check_new_mints(
                args.collection, limit=20
            )

            if mints:
                table = Table(
                    title=f"🆕 New Mints — {args.collection}"
                )
                table.add_column("Asset", style="cyan")
                table.add_column("Template")
                table.add_column("Time")

                for m in mints:
                    table.add_row(
                        m["name"],
                        f"#{m['template']}",
                        m["timestamp"][11:19],
                    )
                console.print(table)
            else:
                console.print(
                    f"[green]✅ No new mints in '{args.collection}'[/]"
                )

        elif args.command == "floor":
            sniper = NFTSniper(check_interval=args.interval)
            sniper.monitor_floor(args.collection)

        elif args.command == "discounts":
            sniper = NFTSniper(check_interval=args.interval)
            discounts = sniper.check_for_discounts(
                args.collection,
                discount_threshold=args.discount,
            )

            if discounts:
                table = Table(
                    title=f"💎 Discounted Listings — {args.collection}"
                )
                table.add_column("Asset", style="cyan")
                table.add_column("Price", justify="right")
                table.add_column("Floor", justify="right")
                table.add_column("Discount", justify="right")
                table.add_column("Seller")

                for d in discounts:
                    table.add_row(
                        d["name"],
                        f"{d['price']:.2f}",
                        f"{d['floor']:.2f}",
                        f"{d['discount_pct']:.1f}%",
                        d["seller"][:12],
                    )
                console.print(table)
            else:
                console.print(
                    f"[green]✅ No discounted listings found "
                    f"in '{args.collection}'[/]"
                )

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/]")
        sys.exit(1)


if __name__ == "__main__":
    main()
