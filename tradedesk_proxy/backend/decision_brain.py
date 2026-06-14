import asyncio
import json
import logging
import redis.asyncio as redis
import numpy as np
from datetime import datetime

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DecisionBrain:
    def __init__(self):
        self.redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
        self.active_zone_metrics = {} # Stores last known metrics for ATM +/- 5
        self.spot_price = 0
        self.pcr_history = []

    async def start(self):
        logger.info("Starting Decision Brain Module...")
        # Start Micro-Tape Consumer
        asyncio.create_task(self.consume_micro_tape())

    async def consume_micro_tape(self):
        """Processes the Fast Lane (Execution Tape) Stream"""
        while True:
            try:
                # Read from stream
                messages = await self.redis_client.xread({"stream:micro_tape": "0-0"}, count=10, block=1000)
                for stream, msgs in messages:
                    for msg_id, data in msgs:
                        payload = json.loads(data["data"])
                        await self.process_tick(payload)
                        # Delete after processing
                        await self.redis_client.xdel("stream:micro_tape", msg_id)
            except Exception as e:
                logger.error(f"Brain Consumption Error: {e}")
                await asyncio.sleep(1)

    async def process_tick(self, payload):
        instrument = payload["instrument"]
        # Update Spot Price
        if "INDEX" in instrument:
            self.spot_price = payload["ltp"]
            return

        # Update Option Metrics
        self.active_zone_metrics[instrument] = payload

        # Periodic Calculation (e.g., every 1 min or significant tick)
        await self.calculate_active_zone_matrix()

    async def calculate_active_zone_matrix(self):
        """Calculates COI PCR, Vol PCR and Flow Imbalance for Active Zone"""
        if not self.spot_price or len(self.active_zone_metrics) < 5:
            return

        ce_doi, pe_doi = 0, 0
        ce_vol, pe_vol = 0, 0

        for inst, data in self.active_zone_metrics.items():
            # Basic logic to distinguish CE/PE from instrument key (NSE_FO|ID_CE/PE)
            if "CE" in inst:
                ce_doi += data.get("doi", 0)
                ce_vol += data.get("vol", 0)
            elif "PE" in inst:
                pe_doi += data.get("doi", 0)
                pe_vol += data.get("vol", 0)

        coi_pcr = pe_doi / ce_doi if ce_doi != 0 else 1.0
        vol_pcr = pe_vol / ce_vol if ce_vol != 0 else 1.0

        signal = self.generate_micro_signal(coi_pcr, vol_pcr)

        # Veto Ledger Check
        if signal and self.verify_veto_ledger(signal, coi_pcr):
            await self.broadcast_signal(signal, coi_pcr, vol_pcr)

    def generate_micro_signal(self, coi_pcr, vol_pcr):
        """Micro-Signal State Machine Logic"""
        if vol_pcr < 0.7 and coi_pcr > 1.2:
            return "BULLISH_DOMINANCE"
        elif vol_pcr > 1.3 and coi_pcr < 0.8:
            return "BEARISH_DOMINANCE"
        return None

    def verify_veto_ledger(self, signal, coi_pcr):
        """Institutional Trap Filters"""
        # Example: Veto Bullish if PCR is trending down despite signal
        if signal == "BULLISH_DOMINANCE" and coi_pcr < 1.0:
            return False
        return True

    async def broadcast_signal(self, signal, coi_pcr, vol_pcr):
        payload = {
            "type": "BRAIN_SIGNAL",
            "signal": signal,
            "metrics": {
                "coi_pcr": round(coi_pcr, 2),
                "vol_pcr": round(vol_pcr, 2),
                "spot": self.spot_price
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.redis_client.publish("pubsub:live_ui_state", json.dumps(payload))
        logger.info(f"Signal Broadcasted: {signal} | PCR: {coi_pcr}")

if __name__ == "__main__":
    brain = DecisionBrain()
    asyncio.run(brain.start())
