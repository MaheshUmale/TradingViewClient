#!/usr/bin/env python3
"""
This example demonstrates how to use a "fake" replay mode by filtering data for custom backtesting.

Unlike the real replay mode, fake replay does not use TradingView's built-in replay feature.
Instead, it filters incoming data to only process candles before a specific date, simulating a past state.
This allows for flexible backtesting without relying on TradingView server-side replay functionality.
"""
import asyncio
import os
import json
from datetime import datetime, timezone

from ...tradingview import Client

# Replay filter date - January 1, 2022
FILTER_DATE = datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000

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
    chart = tv.create_chart('BINANCE:BTCUSDT', '1D', 10000)

    # Define callback functions
    def on_error(err):
        """Error handling callback"""
        print("Error:", err)
        tv.close()

    def on_ready():
        """Ready callback"""
        print("Chart ready!")
        print(f"Using fake replay mode, filter date: {datetime.fromtimestamp(FILTER_DATE/1000, tz=timezone.utc).strftime('%Y-%m-%d')}")

    def on_update(data):
        """Data update callback"""
        # Retrieve candle data
        candles = data.get('candles', [])
        if not candles:
            return

        # Filter data - only keep candles up to the filter date
        filtered_candles = [
            candle for candle in candles
            if candle.get('time', 0) <= FILTER_DATE
        ]

        if not filtered_candles:
            print("No data found before the filter date")
            return

        print(f"Original records: {len(candles)}, Filtered records: {len(filtered_candles)}")

        # Display the latest candle in the filtered series
        latest = filtered_candles[-1]
        dt = datetime.fromtimestamp(latest.get('time', 0) / 1000, tz=timezone.utc)

        print(f"\nFake Replay Latest Data ({dt.strftime('%Y-%m-%d')}):")
        print(f"Open:   {latest.get('open')}")
        print(f"High:   {latest.get('high')}")
        print(f"Low:    {latest.get('low')}")
        print(f"Close:  {latest.get('close')}")
        print(f"Volume: {latest.get('volume')}")

        # Strategy logic can be added here
        if len(filtered_candles) >= 20:
            # Simple MA crossover example
            short_ma = sum(c.get('close', 0) for c in filtered_candles[-10:]) / 10
            long_ma = sum(c.get('close', 0) for c in filtered_candles[-20:]) / 20

            print(f"10-period MA: {short_ma:.2f}")
            print(f"20-period MA: {long_ma:.2f}")

            # Signal logic
            if short_ma > long_ma:
                print("Signal: BUY")
            else:
                print("Signal: SELL")

        # Demo complete, close connection
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
