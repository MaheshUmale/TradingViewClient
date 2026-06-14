#!/usr/bin/env python3
"""
This example demonstrates how to use custom timeframes.
"""
import asyncio
import os
import json
from pprint import pprint

from ...tradingview import Client

async def main():
    """Main function"""
    # Check environment variables
    session = os.environ.get('TV_SESSION')
    signature = os.environ.get('TV_SIGNATURE')

    if not session or not signature:
        raise ValueError('Please set TV_SESSION and TV_SIGNATURE environment variables')

    # Create client
    tv = Client(session, signature)

    # Connect to TradingView
    await tv.connect()

    # Create chart with a custom timeframe: e.g., 10 seconds (S10)
    chart = tv.create_chart(
        'BINANCE:BTCUSDT',
        'S10',
        5000
    )

    # Define callback functions
    def on_error(err):
        """Error handling callback"""
        print("Error:", err)
        tv.close()

    def on_ready():
        """Ready callback"""
        print("Chart ready!")

        # Print examples of custom timeframes
        print("\nAvailable custom timeframe formats:")
        print("- Seconds: S5 (5s), S10 (10s), S15 (15s), etc.")
        print("- Minutes: 1 (1m), 3, 5, 10, 15, 30, 45, etc.")
        print("- Hours: 60 (1h), 120 (2h), 180 (3h), 240 (4h), etc.")
        print("- Days: 1D (1d), 2D, 3D, etc.")
        print("- Weeks: 1W (1w), 2W, etc.")
        print("- Months: 1M (1M), etc.")
        print("- Years: 12M (1Y), etc.")

    def on_update(data):
        """Data update callback"""
        # Retrieve candle data
        candles = data.get('candles', [])
        if candles:
            # Display last 3 candles
            print(f"Retrieved {len(candles)} candles (10-second timeframe)")
            print("Last 3 candles:")
            for candle in candles[-3:]:
                print(json.dumps(candle, indent=2))
            # Close connection
            tv.close()

    # Set callbacks
    chart.on_error = on_error
    chart.on_ready = on_ready
    chart.on_update = on_update

    # Create chart
    chart.create()

    # Timeout handling
    await asyncio.sleep(30)
    if tv.connected:
        print("Operation timed out")
        tv.close()

if __name__ == '__main__':
    asyncio.run(main())
