#!/usr/bin/env python3
"""
This example demonstrates how to use custom chart types.
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

    # Create chart session
    chart = tv.create_chart('BINANCE:BTCUSDT', '1D', 5000)
    # Set custom chart type: Heikin Ashi
    chart.chart_type = "BarSetHeikenAshi@tv-basicstudies-152!"

    # Define callback functions
    def on_error(err):
        """Error handling callback"""
        print("Error:", err)
        tv.close()

    def on_ready():
        """Ready callback"""
        print("Chart ready!")

    def on_update(data):
        """Data update callback"""
        # Retrieve candle data
        candles = data.get('candles', [])
        if candles:
            # Display last 3 candles
            print(f"Retrieved {len(candles)} candles")
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
