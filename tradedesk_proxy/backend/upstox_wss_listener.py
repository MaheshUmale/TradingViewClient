import asyncio
import json
import logging
import websockets
import redis.asyncio as redis
import upstox_client
from google.protobuf.json_format import MessageToDict
from datetime import datetime
import ssl
import pandas as pd

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
STREAM_MICRO_TAPE = "stream:micro_tape"
STREAM_MACRO_STRUCTURAL = "stream:macro_structural"

class DualSpeedIngestionPipeline:
    def __init__(self, access_token, instrument_keys, spot_instrument="NSE_INDEX|Nifty_50"):
        self.access_token = access_token
        self.instrument_keys = instrument_keys
        self.spot_instrument = spot_instrument
        self.redis_client = None
        self.stop_event = asyncio.Event()
        self.oi_cache = {}  # Store baseline OI for Delta OI calculation

    async def connect_redis(self):
        self.redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        await self.redis_client.ping()
        logger.info("Connected to Redis for Dual-Speed Ingestion.")

    def get_wss_url(self):
        configuration = upstox_client.Configuration()
        configuration.access_token = self.access_token
        api_instance = upstox_client.WebsocketApi(upstox_client.ApiClient(configuration))
        return api_instance.get_market_data_feed_authorize('2.0').data.authorized_redirect_uri

    async def start(self):
        await self.connect_redis()
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        while not self.stop_event.is_set():
            try:
                wss_url = self.get_wss_url()
                async with websockets.connect(wss_url, ssl=ssl_context) as ws:
                    subscription_payload = {
                        "guid": "dualspeed_ingestion",
                        "method": "sub",
                        "data": {"instrumentKeys": self.instrument_keys + [self.spot_instrument], "mode": "full"}
                    }
                    await ws.send(json.dumps(subscription_payload).encode('utf-8'))

                    async for message in ws:
                        if isinstance(message, bytes):
                            await self.process_message(message)
            except Exception as e:
                logger.error(f"Ingestion Pipeline Error: {e}")
                await asyncio.sleep(5)

    async def process_message(self, message):
        if not pb: return
        try:
            feed_response = pb.FeedResponse()
            feed_response.ParseFromString(message)
            data_dict = MessageToDict(feed_response, preserving_proto_field_name=True)

            if "feeds" in data_dict:
                timestamp = int(datetime.utcnow().timestamp())
                for instrument_key, feed_data in data_dict["feeds"].items():
                    payload = self.parse_feed(instrument_key, feed_data)
                    payload["ts"] = timestamp

                    # Routing
                    if instrument_key == self.spot_instrument or "ff" in feed_data:
                        # Macro / Structural Data (Every 3-5 mins or full packets)
                        await self.redis_client.xadd(STREAM_MACRO_STRUCTURAL, {"data": json.dumps(payload)})

                    # Execution Tape (Fast Lane - Every Tick/Min)
                    await self.redis_client.xadd(STREAM_MICRO_TAPE, {"data": json.dumps(payload)})

        except Exception as e:
            logger.error(f"Parsing Error: {e}")

    def parse_feed(self, instrument_key, feed_data):
        """Extracts LTP, Volume, and OI with Forward-Fill Logic"""
        metrics = {"instrument": instrument_key, "ltp": 0, "vol": 0, "oi": 0, "doi": 0}

        # LTPC
        if "ltpc" in feed_data:
            metrics["ltp"] = feed_data["ltpc"].get("ltp", 0)

        # Full Feed
        if "ff" in feed_data:
            ff = feed_data["ff"].get("marketFF") or feed_data["ff"].get("indexFF")
            if ff:
                if "ltpc" in ff: metrics["ltp"] = ff["ltpc"].get("ltp", metrics["ltp"])
                if "eFeedDetails" in ff:
                    metrics["oi"] = ff["eFeedDetails"].get("oi", self.oi_cache.get(instrument_key, 0))
                    metrics["vol"] = ff["eFeedDetails"].get("tv", 0)

                    # Delta OI Calculation
                    if instrument_key not in self.oi_cache:
                        self.oi_cache[instrument_key] = metrics["oi"] # Daily Baseline
                    metrics["doi"] = metrics["oi"] - self.oi_cache[instrument_key]

        # Fallback to cache for OI if missing in packet (Forward Fill)
        if metrics["oi"] == 0:
            metrics["oi"] = self.oi_cache.get(instrument_key, 0)

        return metrics

if __name__ == "__main__":
    # Example Initialization
    # Active Zone: Nifty Spot + 11 Option Strikes (ATM +/- 5)
    pipeline = DualSpeedIngestionPipeline("TOKEN", ["NSE_FO|54321", "NSE_FO|54322"])
    asyncio.run(pipeline.start())
