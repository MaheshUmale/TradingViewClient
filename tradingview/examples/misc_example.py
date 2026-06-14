#!/usr/bin/env python3
"""
Example of using the miscellaneous requests module.
"""
import asyncio
import json
from pprint import pprint

from ..misc import (
    get_ta,
    search_market_v3,
    search_indicator,
    get_indicator
)

async def main():
    """Main function"""
    print("========== Market Search ==========")
    results = await search_market_v3("BINANCE:BTCUSDT")
    if results:
        market = results[0]
        print(f"Found market: {market.id} - {market.description}")

        print("\n========== Technical Analysis ==========")
        ta_data = await get_ta(market.id)
        pprint(ta_data)

    print("\n========== Indicator Search ==========")
    indicators = await search_indicator("RSI")

    if indicators:
        indicator = indicators[0]
        print(f"Found indicator: {indicator.name} Author: {indicator.author['username']}")

        print("\n========== Indicator Details ==========")
        try:
            indicator_detail = await get_indicator(indicator.id, indicator.version)
            print(f"Pine ID: {indicator_detail.pineId}")
            print(f"Version: {indicator_detail.pineVersion}")
            print(f"Description: {indicator_detail.description}")
            print(f"Input Parameters: {len(indicator_detail.inputs)}")
            print(f"Plots: {len(indicator_detail.plots)}")
        except Exception as e:
            print(f"Failed to retrieve indicator details: {e}")

if __name__ == "__main__":
    asyncio.run(main())
