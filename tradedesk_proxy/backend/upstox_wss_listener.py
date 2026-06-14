import asyncio
import json
import logging
import websockets
import redis.asyncio as redis
import upstox_client
from google.protobuf.json_format import MessageToDict
from datetime import datetime
import ssl

try:
    import MarketFeedV2_pb2 as pb
except ImportError:
    pb = None

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
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

    def get_wss_url(self):
        """Retrieve the authorized WebSocket URL using the official Upstox SDK"""
        try:
            configuration = upstox_client.Configuration()
            configuration.access_token = self.access_token
            api_instance = upstox_client.WebsocketApi(upstox_client.ApiClient(configuration))
            api_response = api_instance.get_market_data_feed_authorize('2.0')
            return api_response.data.authorized_redirect_uri
        except Exception as e:
            logger.error(f"Failed to get WSS URL from Upstox SDK: {e}")
            raise

    async def start(self):
        await self.connect_redis()

        # Setup SSL Context for WebSockets
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        reconnect_delay = 1

        while not self.stop_event.is_set():
            try:
                wss_url = self.get_wss_url()
                logger.info(f"Connecting to: {wss_url}")

                async with websockets.connect(wss_url, ssl=ssl_context) as ws:
                    logger.info("Connected to Upstox WSS.")
                    reconnect_delay = 1

                    subscription_payload = {
                        "guid": "tradedesk_proxy_session",
                        "method": "sub",
                        "data": {
                            "instrumentKeys": self.instrument_keys,
                            "mode": "full"
                        }
                    }
                    await ws.send(json.dumps(subscription_payload).encode('utf-8'))

                    async for message in ws:
                        if isinstance(message, bytes):
                            await self.process_binary_message(message)

            except Exception as e:
                logger.error(f"Upstox WSS Error: {e}")
                if not self.stop_event.is_set():
                    logger.info(f"Reconnecting in {reconnect_delay}s...")
                    await asyncio.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, 60)

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
            logger.error(f"Binary Processing Error: {e}")

    def extract_metrics(self, instrument_key, feed_data):
        """Standardizes payload to match Frontend OHLC/Tick expectations"""
        payload = {
            "type": "TICK",
            "instrument": instrument_key,
            "time": int(datetime.utcnow().timestamp()),
        }

        # Priority 1: Full Feed (provides OHLC)
        if "ff" in feed_data:
            ff = feed_data["ff"].get("marketFF") or feed_data["ff"].get("indexFF")
            if ff:
                if "ltpc" in ff:
                    payload["c"] = ff["ltpc"].get("ltp", 0)
                if "marketOHLC" in ff and "ohlc" in ff["marketOHLC"]:
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

        # Priority 2: LTP Only fallback
        elif "ltpc" in feed_data:
            ltp = feed_data["ltpc"].get("ltp", 0)
            payload.update({"o": ltp, "h": ltp, "l": ltp, "c": ltp, "v": 0})

        return payload

    def stop(self):
        self.stop_event.set()

if __name__ == "__main__":
    # Example: python upstox_wss_listener.py
    ACCESS_TOKEN = "YOUR_TOKEN"
    INSTRUMENTS = ["NSE_EQ|INE002A01018", "NSE_INDEX|Nifty_50"]
    asyncio.run(UpstoxWSSListener(ACCESS_TOKEN, INSTRUMENTS).start())
