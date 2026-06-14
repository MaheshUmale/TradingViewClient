import asyncio
import json
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from decision_brain import DecisionBrain

class TestDecisionBrainLogic(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.brain = DecisionBrain()
        self.brain.redis_client = MagicMock()
        self.brain.redis_client.publish = AsyncMock()

    def test_generate_micro_signal_bullish(self):
        # Bullish: Low Vol PCR (<0.7), High COI PCR (>1.2)
        signal = self.brain.generate_micro_signal(coi_pcr=1.5, vol_pcr=0.5)
        self.assertEqual(signal, "BULLISH_DOMINANCE")

    def test_generate_micro_signal_bearish(self):
        # Bearish: High Vol PCR (>1.3), Low COI PCR (<0.8)
        signal = self.brain.generate_micro_signal(coi_pcr=0.5, vol_pcr=1.5)
        self.assertEqual(signal, "BEARISH_DOMINANCE")

    def test_veto_ledger_filter(self):
        # Veto Bullish if PCR is weak (<1.0)
        is_valid = self.brain.verify_veto_ledger("BULLISH_DOMINANCE", coi_pcr=0.9)
        self.assertFalse(is_valid)

        is_valid = self.brain.verify_veto_ledger("BULLISH_DOMINANCE", coi_pcr=1.4)
        self.assertTrue(is_valid)

    @patch("decision_brain.datetime")
    async def test_broadcast_signal(self, mock_datetime):
        mock_datetime.utcnow.return_value.isoformat.return_value = "2026-06-14T12:00:00"
        self.brain.spot_price = 22100

        await self.brain.broadcast_signal("BULLISH_DOMINANCE", 1.5, 0.5)

        self.brain.redis_client.publish.assert_called_once()
        call_args = self.brain.redis_client.publish.call_args
        self.assertEqual(call_args[0][0], "pubsub:live_ui_state")
        payload = json.loads(call_args[0][1])
        self.assertEqual(payload["signal"], "BULLISH_DOMINANCE")
        self.assertEqual(payload["metrics"]["coi_pcr"], 1.5)

if __name__ == "__main__":
    unittest.main()
