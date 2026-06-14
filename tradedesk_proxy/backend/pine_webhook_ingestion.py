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

app = FastAPI(title="TradeDesk Proxy Gateway")

# Constants
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_TICKER_PREFIX = "ticker:"
REDIS_INDICATOR_PREFIX = "indicator:"

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
        logger.info("Connected to Redis successfully.")
    except Exception as e:
        logger.error(f"Redis Connection Failed: {e}")

@app.post("/webhook/pine")
async def ingest_pine_indicator(payload: PineIndicatorPayload):
    """Ingests TradingView Pine Script alerts and fanned out via Redis."""
    try:
        broadcast_data = {
            "type": "PINE_INDICATOR",
            "instrument": payload.ticker,
            "time": int(datetime.utcnow().timestamp()),
            "name": payload.indicator_name,
            "values": payload.values
        }
        channel = f"{REDIS_INDICATOR_PREFIX}{payload.ticker}"
        await redis_client.publish(channel, json.dumps(broadcast_data))
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Webhook Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint that subscribes to Redis channels and
    streams data to the frontend in real-time.
    """
    await websocket.accept()
    pubsub = redis_client.pubsub()

    # Subscribe to all tickers and indicators (In production, filter based on client needs)
    await pubsub.psubscribe(f"{REDIS_TICKER_PREFIX}*", f"{REDIS_INDICATOR_PREFIX}*")

    logger.info("Client connected to broadcast stream.")

    try:
        async for message in pubsub.listen():
            if message['type'] == 'pmessage':
                # Forward the Redis message payload directly to the WebSocket client
                await websocket.send_text(message['data'])
    except WebSocketDisconnect:
        logger.info("Client disconnected from broadcast stream.")
    except Exception as e:
        logger.error(f"WebSocket Streaming Error: {e}")
    finally:
        await pubsub.punsubscribe()
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
