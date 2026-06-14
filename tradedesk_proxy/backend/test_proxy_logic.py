import asyncio
import json
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from upstox_wss_listener import UpstoxWSSListener

class TestTradeDeskProxyLogic(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.access_token = "test_token"
        self.instruments = ["NSE_EQ|INE002A01018"]
        self.listener = UpstoxWSSListener(self.access_token, self.instruments)

    @patch("redis.asyncio.Redis")
    async def test_redis_connection(self, mock_redis):
        mock_instance = mock_redis.return_value
        mock_instance.ping = AsyncMock(return_value=True)
        await self.listener.connect_redis()
        mock_instance.ping.assert_called_once()

    @patch("upstox_client.WebsocketApi.get_market_data_feed_authorize")
    def test_get_wss_url(self, mock_authorize):
        mock_response = MagicMock()
        mock_response.data.authorized_redirect_uri = "wss://test-url.com"
        mock_authorize.return_value = mock_response

        url = self.listener.get_wss_url()
        self.assertEqual(url, "wss://test-url.com")

    def test_extract_metrics_full_feed(self):
        feed_data = {
            "ff": {
                "marketFF": {
                    "ltpc": {"ltp": 2510.0},
                    "marketOHLC": {
                        "ohlc": [{"open": 2500, "high": 2520, "low": 2490, "close": 2510, "volume": 5000}]
                    },
                    "eFeedDetails": {"oi": 1000000.0}
                }
            }
        }
        payload = self.listener.extract_metrics("NSE_EQ|INE002A01018", feed_data)
        self.assertEqual(payload["o"], 2500)
        self.assertEqual(payload["h"], 2520)
        self.assertEqual(payload["l"], 2490)
        self.assertEqual(payload["c"], 2510)
        self.assertEqual(payload["v"], 5000)

    @patch("MarketFeedV2_pb2.FeedResponse")
    @patch("redis.asyncio.Redis")
    async def test_process_binary_message_integration(self, mock_redis, mock_pb):
        self.listener.redis_client = mock_redis.return_value
        self.listener.redis_client.publish = AsyncMock()

        with patch("upstox_wss_listener.MessageToDict") as mock_m2d:
            mock_m2d.return_value = {
                "feeds": {
                    "NSE_EQ|INE002A01018": {
                        "ltpc": {"ltp": 2520.0}
                    }
                }
            }

            await self.listener.process_binary_message(b"fake_data")

            call_args = self.listener.redis_client.publish.call_args
            payload = json.loads(call_args[0][1])
            self.assertEqual(payload["type"], "TICK")
            self.assertEqual(payload["c"], 2520.0)

if __name__ == "__main__":
    unittest.main()
