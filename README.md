
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
------------------------------
## Upstox Architecture Extensions
To anchor these choices into your architecture, here is a supplementary markdown file. It maps out your raw Upstox V2 API WebSocket (Protobuf/Binary) pipeline and handles your custom Pine Script indicator data overlays.
Save the file below in your workspace to provide direct, actionable code paths for your implementation engine.
------------------------------

# UPSTOX_ENGINE.md - Upstox V2 WebSocket Pipeline & Pine Indicator Stream Spec
This document details the configuration for streaming raw market feeds from Upstox via binary WebSockets, and overlaying custom external Pine Script indicator streams onto the TradeDesk UI.
## ⚡ Upstox V2 WebSocket & Protobuf Pipeline
Upstox V2 utilizes **Protocol Buffers (Protobuf)** over binary WebSockets for market data feeds. This requires a decoding layer on the backend proxy before broadcasting JSON matrices to the frontend.
### 🐍 Backend Processing Pipeline (Python Asyncio)1. **Authentication**: Upstox requires a daily OAuth2 access token. The session daemon automated login must retrieve this token before 09:15 AM IST.
2. **Binary Decoding**: Ingest incoming raw binary frames using `websockets` or `aiohttp` and compile the `.proto` schema file supplied by Upstox (`MarketFeedV2.proto`).
3. **Data Parsing Example**:
```python
import asyncio
import websockets
import MarketFeedV2_pb2 as UpstoxProtobuf  # Compiled protoc file

async def upstox_wss_handler(access_token):
    uri = f"wss://://upstox.com"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    async with websockets.connect(uri, extra_headers=headers) as ws:
        # Subscribe to required instruments (e.g., Nifty Spot, Options Strikes)
        subscription_payload = {
            "guid": "intraday_desk_request",
            "method": "sub",
            "data": {"instrumentKeys": ["NSE_EQ|INE002A01018", "NSE_INDEX|Nifty_50"], "mode": "full"}
        }
        await ws.send(json.dumps(subscription_payload))
        
        async for message in ws:
            # Parse Upstox's incoming binary buffer
            feed_response = UpstoxProtobuf.FeedResponse()
            feed_response.ParseFromString(message)
            
            # Extract Tick metrics, Open Interest (OI), and Market Depth
            # Forward parsed dictionary payload instantly to Redis Pub/Sub Matrix
```
---## 📈 Pine Script Indicator Data Ingestion
Because Pine Script runs inside TradingView servers, you must bridge your custom alert metrics into the proxy pipeline. This is accomplished using a **Hybrid Webhook-to-Stream Ingestion Gateway**.

```text
    ┌───────────────────────────┐
    │ TradingView Pine Alert    │ (Triggered on-bar or tick-close)
    └─────────────┬─────────────┘
                  │ (HTTP POST Payload with calculated Indicator values)
                  ▼
  ┌───────────────────────────┐
  │ Ingestion Gateway API     │ (FastAPI Endpoint under 10ms processing)
  └─────────────┬─────────────┘
                │ [Publishes to Redis channel: indicator:NSE:RELIANCE]
                ▼
  ┌───────────────────────────┐
  │ Frontend UI WebSocket     │ (Pushes delta update packet to browser)
  └─────────────┬─────────────┘
                │
                ▼
  ┌───────────────────────────┐
  │ Lightweight Charts Canvas │ (Appends point to secondary line series)
  └───────────────────────────┘
```

### 📋 Standardized Pine Webhook Schema
Configure your TradingView Alert message body to send a compact JSON block matching your dashboard ticker index keys:

```json
{
  "ticker": "NSE_EQ|INE002A01018",
  "timestamp": "{{time}}",
  "indicator_name": "CUSTOM_VWAP_BANDS",
  "values": {
    "basis": 2450.25,
    "upper_band": 2465.00,
    "lower_band": 2435.50
  }
}
```

---

## 🖥️ Frontend Render Optimization (Zustand + Canvas)

To prevent your UI from dropping frames under heavy market volatility, decouple the incoming WebSocket stream from standard React re-render loops.

### ⚛️ Atomic State Hub Template (`useTradeDeskStore.js`)
```javascript
import create from 'zustand';

export const useTradeDeskStore = create((set, get) => ({
  prices: {},
  indicators: {},
  
  // High-performance atomic updater called on every single WSS message frame
  updateTick: (instrumentKey, ltp, totalOI) => set((state) => ({
    prices: {
      ...state.prices,
      [instrumentKey]: { ltp, totalOI, timestamp: Date.now() }
    }
  })),

  updateIndicator: (instrumentKey, name, values) => set((state) => ({
    indicators: {
      ...state.indicators,
      [`${instrumentKey}:${name}`]: values
    }
  }))
}));
```

### 📊 Plotting Pine Data to Lightweight Charts
```javascript
import { createChart } from 'lightweight-charts';

// Initialize core candlestick series
const chart = createChart(chartContainerRef.current, { width: 800, height: 400 });
const candlestickSeries = chart.addCandlestickSeries();

// Add custom overlay for your streamed Pine Script Indicator data
const indicatorLineSeries = chart.addLineSeries({
  color: '#2196F3',
  lineWidth: 2,
  title: 'Pine Custom Indicator Line',
});

// Real-time listener appending new live points to the chart layer
const subscribeToDataStream = (instrumentKey) => {
  webSocket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'TICK') {
      candlestickSeries.update({
        time: data.time, open: data.o, high: data.h, low: data.l, close: data.c
      });
    } else if (data.type === 'PINE_INDICATOR') {
      indicatorLineSeries.update({
        time: data.time,
        value: data.values.basis
      });
    }
  };
};
```

------------------------------
## 💡 Pro-Tips for Upstox Integration:

* Protobuf Compilation: You can download Upstox's formal .proto profile definition files directly from the [Upstox Developer Documentation](https://upstox.com/developer/api-documentation). Use protoc --python_out=. MarketFeedV2.proto to generate your Python decoder bindings instantly.
* Order Placement Protection: Since Upstox API limits order requests per second, ensure your front-end Chart Trading click buttons are instantly disabled for 300ms after a click to prevent accidental double-execution fat-finger trades during fast market run-ups.

Would you like to build out the Upstox order execution model next, or start drafting the layout grid skeleton for your React frontend panels?

