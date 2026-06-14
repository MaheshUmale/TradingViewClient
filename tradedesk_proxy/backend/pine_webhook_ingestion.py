from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import redis.asyncio as redis
import json
import logging
import asyncio
from datetime import datetime

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TradeDesk Proxy Gateway & Brain Relay")

# Constants
REDIS_HOST = "localhost"
REDIS_PORT = 6379
BRAIN_SIGNAL_CHANNEL = "pubsub:live_ui_state"
TICKER_CHANNEL_PREFIX = "ticker:"

# Redis Client Instance
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

class PineIndicatorPayload(BaseModel):
    ticker: str
    timestamp: str
    indicator_name: str
    values: dict

@app.on_event("startup")
async def startup_event():
    try:
        await redis_client.ping()
        logger.info("Gateway connected to Redis.")
    except Exception as e:
        logger.error(f"Redis Connection Failed: {e}")

@app.post("/webhook/pine")
async def ingest_pine_indicator(payload: PineIndicatorPayload):
    """Ingests TradingView Pine Script alerts and relays them."""
    try:
        broadcast_data = {
            "type": "PINE_INDICATOR",
            "instrument": payload.ticker,
            "time": int(datetime.utcnow().timestamp()),
            "name": payload.indicator_name,
            "values": payload.values
        }
        # Relay through brain's signal channel for unified frontend stream
        await redis_client.publish(BRAIN_SIGNAL_CHANNEL, json.dumps(broadcast_data))
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Webhook Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint that relays live brain signals and
    indicator updates to the frontend.
    """
    await websocket.accept()
    pubsub = redis_client.pubsub()

    try:
        # Subscribe to Brain Signals, Indicators, and Tickers
        await pubsub.subscribe(BRAIN_SIGNAL_CHANNEL)
        # In production, optionally psubscribe to ticker:* for raw data

        logger.info("Client connected to TradeDesk Live Stream.")

        async for message in pubsub.listen():
            if message['type'] == 'message':
                await websocket.send_text(message['data'])

    except WebSocketDisconnect:
        logger.info("Client disconnected.")
    except Exception as e:
        logger.error(f"WebSocket Relay Error: {e}")
    finally:
        await pubsub.unsubscribe()
        await pubsub.close()
        try:
            await websocket.close()
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
