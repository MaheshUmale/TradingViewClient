import asyncio
import json
import logging
import websockets
import redis.asyncio as redis
from google.protobuf.json_format import MessageToDict
from datetime import datetime
try:
    import MarketFeedV2_pb2 as pb
except ImportError:
    pb = None

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
UPSTOX_WSS_URL = "wss://api.upstox.com/v2/feed/market-data-feed"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_TICKER_PREFIX = "ticker:"

class UpstoxWSSListener:
    def __init__(self, access_token, instrument_keys):
        self.access_token = access_token
        self.instrument_keys = instrument_keys
        self.redis_client = None
        self.stop_event = asyncio.Event()

    async def connect_redis(self):
        self.redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        await self.redis_client.ping()
        logger.info("Connected to Redis successfully.")

    async def start(self):
        await self.connect_redis()
        headers = {"Authorization": f"Bearer {self.access_token}"}

        while not self.stop_event.is_set():
            try:
                async with websockets.connect(UPSTOX_WSS_URL, extra_headers=headers) as ws:
                    logger.info("Connected to Upstox WSS.")
                    subscription_payload = {
                        "guid": "tradedesk_proxy",
                        "method": "sub",
                        "data": {"instrumentKeys": self.instrument_keys, "mode": "full"}
                    }
                    await ws.send(json.dumps(subscription_payload))

                    async for message in ws:
                        if isinstance(message, bytes):
                            await self.process_binary_message(message)
            except Exception as e:
                logger.error(f"WSS Error: {e}")
                await asyncio.sleep(5)

    async def process_binary_message(self, message):
        if not pb: return
        try:
            feed_response = pb.FeedResponse()
            feed_response.ParseFromString(message)
            data_dict = MessageToDict(feed_response, preserving_proto_field_name=True)

            if "feeds" in data_dict:
                for instrument_key, feed_data in data_dict["feeds"].items():
                    payload = self.extract_metrics(instrument_key, feed_data)
                    if payload:
                        await self.redis_client.publish(f"{REDIS_TICKER_PREFIX}{instrument_key}", json.dumps(payload))
        except Exception as e:
            logger.error(f"Processing Error: {e}")

    def extract_metrics(self, instrument_key, feed_data):
        """Standardizes payload to match Frontend OHLC/Tick expectations"""
        payload = {
            "type": "TICK",
            "instrument": instrument_key,
            "time": int(datetime.utcnow().timestamp()),
        }

        # Case 1: Full Feed (provides OHLC)
        if "ff" in feed_data:
            ff = feed_data["ff"].get("marketFF") or feed_data["ff"].get("indexFF")
            if ff:
                if "ltpc" in ff:
                    payload["c"] = ff["ltpc"].get("ltp", 0)
                if "marketOHLC" in ff and "ohlc" in ff["marketOHLC"]:
                    # Take the first OHLC entry (usually 1 minute or daily depending on subscription)
                    ohlc = ff["marketOHLC"]["ohlc"][0]
                    payload.update({
                        "o": ohlc.get("open", 0),
                        "h": ohlc.get("high", 0),
                        "l": ohlc.get("low", 0),
                        "c": ohlc.get("close", payload.get("c", 0)),
                        "v": ohlc.get("volume", 0)
                    })
                if "eFeedDetails" in ff:
                    payload["oi"] = ff["eFeedDetails"].get("oi", 0)

        # Case 2: LTP Only Feed
        elif "ltpc" in feed_data:
            ltp = feed_data["ltpc"].get("ltp", 0)
            payload.update({"o": ltp, "h": ltp, "l": ltp, "c": ltp, "v": 0})

        return payload

    def stop(self):
        self.stop_event.set()

if __name__ == "__main__":
    asyncio.run(UpstoxWSSListener("TOKEN", ["NSE_EQ|INE002A01018"]).start())
