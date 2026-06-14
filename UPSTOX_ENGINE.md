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

