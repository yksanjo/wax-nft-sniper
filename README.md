# 🔭 WAX NFT Sniper

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen.svg)](https://github.com/yksanjo/wax-nft-sniper/pulls)

**Real-time WAX NFT monitoring, whale alerts, and sniping opportunities.** Track collections, catch big sales, and find underpriced NFTs — all from your terminal or Telegram.

> **Free tier**: CLI monitoring. **Pro tier**: Telegram alerts + multi-collection watch (coming soon).

---

## ✨ Features

| Feature | What It Does |
|---------|-------------|
| **🐋 Whale Alerts** | Detect sales above configurable WAXP thresholds |
| **🆕 Mint Tracker** | See new NFTs as they're minted |
| **📊 Floor Monitor** | Track floor price changes in real-time |
| **💎 Discount Finder** | Find NFTs listed below market price |
| **📱 Telegram Alerts** | Get notifications on your phone (Pro) |
| **🔭 Live Dashboard** | Terminal UI with real-time updates |

---

## 🚀 Quick Start

### Install

```bash
pip install wax-nft-sniper
```

Or from source:

```bash
git clone https://github.com/yksanjo/wax-nft-sniper.git
cd wax-nft-sniper
pip install -e .
```

### Usage

```bash
# Watch a collection in real-time
wax-sniper watch --collection alienworlds --min-price 500

# Check for whale sales
wax-sniper whales --collection alienworlds --min-price 1000

# See new mints
wax-sniper mints --collection alienworlds

# Monitor floor price
wax-sniper floor --collection alienworlds

# Find discounted listings
wax-sniper discounts --collection alienworlds --discount 0.3

# Setup Telegram alerts
wax-sniper setup-telegram
```

### With Telegram Alerts

```bash
# Set your bot credentials
export TELEGRAM_BOT_TOKEN='your_bot_token'
export TELEGRAM_CHAT_ID='your_chat_id'

# Watch with alerts
wax-sniper watch --collection alienworlds --min-price 500
```

---

## 🎯 Example: Whale Monitor with Telegram

```bash
# Terminal 1: Watch alienworlds for sales over 1000 WAXP
wax-sniper watch --collection alienworlds --min-price 1000 --interval 30

# You'll see:
# 🐋 WHALE: Golden Dragon Egg — 2,500 WAXP (buyer: yksanjo...)
# 🆕 MINT: Rare Sword #42 (template #1337)
# 📉 FLOOR DROP: 1,200 → 950 WAXP (-20.8%)
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│              wax-nft-sniper                   │
│                                               │
│  ┌──────────────┐  ┌──────────┐  ┌────────┐  │
│  │  NFTMonitor   │  │NFTSniper │  │  Alert │  │
│  │  • whales     │  │• floor   │  │Manager │  │
│  │  • mints      │  │• discounts│  │• Telegram│
│  │  • live watch │  │• sniping │  │• Webhook│  │
│  └──────┬───────┘  └────┬─────┘  └────┬───┘  │
│         │               │              │       │
└─────────┼───────────────┼──────────────┼───────┘
          │               │              │
          ▼               ▼              ▼
    AtomicAssets     AtomicMarket    Telegram API
    (NFT data)       (sales/price)   (alerts)
```

---

## 💰 Pricing

| Tier | Price | Features |
|------|-------|----------|
| **Free** | $0 | CLI monitoring, single collection, console output |
| **Pro** | $19/mo | Telegram alerts, multi-collection, floor alerts, discount scanner |
| **Enterprise** | $99/mo | Custom webhooks, API access, priority support |

> **Coming soon**: Pro tier with Stripe integration.

---

## 🔗 Related Projects

- [**wax-mcp-server**](https://github.com/yksanjo/wax-mcp-server) — MCP server for WAX (AI agent interface)
- [**wax-agent-toolkit**](https://github.com/yksanjo/wax-agent-toolkit) — Python SDK for WAX AI agents

---

## 📄 License

MIT

---

<div align="center">
  <strong>⭐ Star if you snipe on WAX — happy hunting!</strong>
  <br>
  <em>Built by <a href="https://github.com/yksanjo">Yoshi Kondo</a> · Music Ai Lab</em>
</div>
