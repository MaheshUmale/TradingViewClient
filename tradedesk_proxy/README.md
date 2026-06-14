# 🚀 Intraday TradeDesk Proxy - BRAIN Implementation Blueprint

A professional-grade, low-latency implementation for the Indian Algorithmic Trading ecosystem. This system bridges Upstox V2 (Binary WSS/Protobuf) and TradingView (Pine Script Webhooks) into a unified, high-frequency React dashboard.

## 🏗️ System Architecture
- **Ingestion Pipeline:** Python (asyncio + uvloop) + Upstox Python SDK.
- **Data Routing:** Dual-Speed Logic (Fast Lane: Micro-Tape / Slow Lane: Macro-Structural).
- **Strategy Engine:** "The Brain" with 7-Strike Matrix calculation and Veto Ledger filters.
- **Frontend State:** Zustand atomic state management.
- **Visualization:** TradingView Lightweight Charts (Canvas-based).

---

## 🛠️ Setup Guide

### 1. Prerequisites
- **Python:** 3.14+ (Compatible with `asyncio` and `uvloop`).
- **Redis:** 7.0+ (Required for Streams and Pub/Sub).
- **Node.js:** 18+ (For React/Vite frontend).
- **Protobuf Compiler:** `protoc` (Optional, schema provided).

### 2. Backend Installation
```bash
# Navigate to backend
cd tradedesk_proxy/backend

# Install dependencies
pip install upstox-python-sdk websockets redis protobuf fastapi uvicorn pydantic aiohttp numpy pandas polars
```

### 3. Frontend Installation
```bash
# Navigate to frontend
cd tradedesk_proxy/frontend

# Install dependencies
npm install zustand lightweight-charts react react-dom
```

---

## 🔐 Environment Variables Setup

Create a `.env` file in the `tradedesk_proxy/backend` directory:

| Variable | Description | Example |
| :--- | :--- | :--- |
| `UPSTOX_ACCESS_TOKEN` | Daily OAuth2 token from Upstox | `your_token_here` |
| `REDIS_HOST` | Host address for Redis instance | `localhost` |
| `REDIS_PORT` | Port for Redis instance | `6379` |
| `GATEWAY_PORT` | Port for FastAPI Gateway | `8000` |
| `STRATEGY_MODE` | Active strategy configuration | `ACTIVE_ZONE_STRIKE_7` |

---

## 🚀 Quickstart Guide

### Step 1: Start Redis
Ensure your Redis server is running locally on port 6379.

### Step 2: Launch the Ingestion Pipeline
```bash
# Start the Upstox WSS Listener
export UPSTOX_ACCESS_TOKEN="your_token"
python3 upstox_wss_listener.py
```

### Step 3: Start the Decision Brain
```bash
# Start the Strategy Matrix Engine
python3 decision_brain.py
```

### Step 4: Start the Gateway API
```bash
# Start the FastAPI Webhook/WebSocket Broadcaster
uvicorn pine_webhook_ingestion:app --host 0.0.0.0 --port 8000
```

### Step 5: Launch the Frontend
```bash
# Start the Vite development server (inside frontend directory)
npm run dev
```

---

## 📊 Core Logical Features
- **ATM ± 5 Strikes Matrix:** Hyper-focused tracking of 11 option contracts to filter noise.
- **Dual-Speed Routing:** Separates execution-critical tape from structural macro walls.
- **Forward-Fill (FFILL) Engine:** Guarantees zero-data gaps in Open Interest ($\Delta$OI) calculations.
- **Institutional Trap Filters:** The "Veto Ledger" blocks low-conviction signals during Price-OI divergence.

---

## 🧪 Running Tests
```bash
cd tradedesk_proxy/backend
export PYTHONPATH=$PYTHONPATH:.
python3 test_brain_logic.py
python3 test_proxy_logic.py
```
