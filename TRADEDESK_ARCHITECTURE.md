
# TRADEDESK_ARCHITECTURE.md - High-Throughput Real-Time TradeDesk & WebSocket Engine
This file defines the technical specifications, architectural constraints, and pipeline design patterns for the real-time, widget-driven Intraday TradeDesk Proxy system.
## 🎯 Architecture Design & Low-Latency Pipeline### Core PositioningThe TradeDesk Architecture acts as a bidirectional, sub-millisecond proxy layer. It replaces traditional polling/webhook workflows with a continuous streaming network. It ingests raw tick data from Indian brokers or data vendors via upstream WebSockets (WSS), manages data normalization, and broadcasts state to a modular UI terminal.
### Low-Latency Broadcast Pipeline
```text
┌───────────────────────┐
│ Upstream WSS Datafeed │ (NSE / BSE Tick-by-Tick Feed)
└───────────┬───────────┘
            │ (Raw Binary / JSON Ticks)
            ▼
┌───────────────────────┐
│ Async Ingestion Loop │ (Python uvloop + WebSockets Client)
└───────────┬───────────┘
            │ (Normalized Dict Object)
            ▼
┌───────────────────────┐
│ Redis Pub/Sub Matrix │ (Topic Isolation per Ticker/Token)
└───────────┬───────────┘
            │ (Fanned Out Stream)
            ▼
┌───────────────────────┐
│ Local Fanout Workers │ (FastAPI WebSocket Endpoints)
└───────────┬───────────┘
            │ (JSON Streams via WebSockets)
            ▼
┌───────────────────────┐
│ Atomic State Engine │ (Frontend Store - e.g., Zustand/Signals)
└───────────┬───────────┘
            │ (Batch Render Updates)
            ▼
┌───────────────────────┐
│ Modular Canvas UI │ (Lightweight Charts, SVG Matrix Layout)
└───────────────────────┘


---
```
## ⚡ Real-Time WSS Pipeline Specifications

### 1. Concurrency & High Availability Ingestion
* **Engine Core**: Built on Python `asyncio` combined with `uvloop` to drop thread overhead and manage high network concurrency.
* **Backpressure Throttle**: During peak market hours (e.g., 09:15 AM openings), the backend drops older intermediate ticks if the network buffer exceeds a budget of 50ms. It guarantees that the client always receives the absolute latest Last Traded Price (LTP).
* **Connection Lifecycle**: Employs non-blocking heartbeat tracking (ping/pong every 5 seconds). If a drop occurs, it drops the old handler and triggers an exponential backoff reconnect policy within 500ms.

### 2. High-Performance Client Fanout
* **Decoupling**: The ingestion loop does not write to databases or serve clients directly. It publishes strictly to an in-memory Redis Pub/Sub instance.
* **Token Isolation**: Clients subscribe to isolated, dynamic channel rooms based on active instruments (e.g., `ticker:NSE:NIFTY26JUNFUT`), minimizing browser processing load.

---

## 🖥️ Modular TradeDesk UI & Widgets

The TradeDesk frontend uses a flexible dashboard grid framework (e.g., `react-grid-layout`) to let intraday traders dynamically add, size, and remove analytical nodes without hard reloads.

### 📊 Advanced Analytical Widget Specifications

#### 🟢 Widget A: Put-Call Ratio (PCR) vs. Spot Chart
* **Data Processing Logic**: 
  1. The backend parses real-time Options Chain updates from the WebSocket pipeline.
  2. For a targeted index/underlying (e.g., NIFTY / BANKNIFTY), it aggregates total Open Interest for all active Puts and all active Calls.
  3. Formulates the ratio: `PCR = Total Put OI / Total Call OI`.
* **Rendering Component**: A synchronized, dual-axis line graph. The primary Y-axis tracks the spot underlying asset price, and the secondary Y-axis tracks the shifting intraday PCR value, plotted across time.

#### 🔵 Widget B: Candlestick Chart with Horizontal Open Interest (OI) Overlay
* **Data Processing Logic**: 
  1. Captures total accumulated Open Interest (OI) and Change in OI for every individual strike price across the active expiry series.
  2. Maps these values to static strike clusters on the backend.
* **Rendering Component**: A real-time Candlestick visualization engine (utilizing TradingView Lightweight Charts or Canvas). Overlaid on the right side of the canvas is a horizontal bar graph extending along the price coordinate (Y-axis), instantly illuminating areas of massive option writing (Support/Resistance walls).

#### 🟡 Widget C: Custom Pine Indicator Stream Mapper
* **Data Processing Logic**: 
  1. Streams pre-computed historical or live derived calculation arrays (e.g., custom VWAP bands, momentum cross lines) forwarded through the data engine.
  2. Standardizes data into an object array containing a Unix timestamp and float point metrics: `[{ "time": 1718364000, "value": 23450.50 }]`.
* **Rendering Component**: Dynamic secondary line series or sub-charts painted inside the primary canvas panel, maintaining pixel-perfect timestamp synchronization with the real-time price feed.

---

## 🗄️ In-Memory State & Token Mapping Schema

### Dynamic Instrument Cache
To eliminate sluggish lookups during fast execution, the engine keeps an optimized, in-memory dictionary caching TradingView parameters against broker tokens:

```json
{
  "NSE:RELIANCE": {
    "broker_token": "2885",
    "exchange": "NSE",
    "segment": "EQUITY",
    "tick_size": 0.05
  },
  "NSE:NIFTY26JUN2423500CE": {
    "broker_token": "84321",
    "exchange": "NFO",
    "segment": "DERIVATIVES",
    "tick_size": 0.05
  }
}
```

### Front-End Store Thread Optimization
* **Atomic Mutations**: Frontend updates must skip general component state trees to prevent UI freeze frames. 
* **Throttled DOM Refreshes**: The browser WebSocket interface updates an internal atomic data store on every packet, but triggers UI re-renders on a strict throttled clock loop capped at 60 Frames Per Second (every ~16.6ms).

---

## 🚀 Execution & Risk Proxy Controls

* **Zero-Slippage Routing**: Market orders executed via chart clicks are transformed on the fly into aggressive Limit Orders with a predefined offset protection buffer (e.g., LTP + 0.1% for Buys) to prevent getting hit by bad fills during low liquidity liquidity pockets.
* **Bidirectional Sync**: When an order execution confirmation arrives from the broker's API, a system event intercepts it, validates it against the active state cache, and instantly pushes a flash notification over the client's WSS link to animate open position components in real-time.

------------------------------
## 🔧 Next Steps to Proceed

   1. Save the template block above into a file named TRADEDESK_ARCHITECTURE.md inside your repository.
   2. When you query your AI assistant, pass both your original CLAUDE.md (
   3. TRADINGVIEW_CLAUDE.md) and this new TRADEDESK_ARCHITECTURE.md file.

To help you build out the implementation code for this engine, let me know:

* Which specific Indian Broker SDK you are integrating with (e.g., KiteConnect, FyersModel, AngelOne SmartConnect).
* Your preferred Frontend Javascript UI framework and Charting Library (e.g., React + TradingView Lightweight Charts, or Vue + ECharts).







## Frontend Stack Recommendation
For a high-frequency Indian intraday TradeDesk, the optimal stack for speed, stability, and development ease is React (Vite) combined with TradingView's Lightweight Charts and Zustand.

🏎️ Optimal Frontend Stack
├── Framework: React + Vite (Blazing fast HMR, highly modular component design)
├── Charts: TradingView Lightweight Charts (Canvas-based, handles 60+ FPS ticks smoothly)
├── State: Zustand (Atomic state management, updates values without global DOM re-renders)
└── Styling: Tailwind CSS (Utility-first, rapid dashboard layout adjustments)

Why this matters for your Pine Script data: TradingView's official lightweight-charts library uses the exact same layout and visual architecture as the main platform. Since your custom indicators output raw numerical streams from Pine Script, you can feed them directly into an extra LineSeries or HistogramSeries on top of your main candlestick layer without translation friction.
