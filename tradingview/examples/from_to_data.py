#!/usr/bin/env python3
"""
This example demonstrates how to retrieve K-line data for a specific time range.
"""
import asyncio
import os
import json
from datetime import datetime, timezone, timedelta

from tradingview import Client


async def main():
    """Main function"""
    # Check environment variables
    session = os.environ.get('TV_SESSION')
    signature = os.environ.get('TV_SIGNATURE')

    if not session or not signature:
        raise ValueError('Please set TV_SESSION and TV_SIGNATURE environment variables')

    # Create client
    client = Client(token=session, signature=signature)

    # Connect to TradingView
    await client.connect()

    # Define time range - January 1, 2022 to January 31, 2022
    # Timestamps in seconds
    from_date = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp())
    to_date = int(datetime(2022, 1, 31, tzinfo=timezone.utc).timestamp())

    print(f"Retrieving data range:")
    print(f"  From: {datetime.fromtimestamp(from_date, tz=timezone.utc).strftime('%Y-%m-%d')}")
    print(f"  To:   {datetime.fromtimestamp(to_date, tz=timezone.utc).strftime('%Y-%m-%d')}")

    # Create chart session
    chart = client.Session.Chart()

    # Set market and parameters
    chart.set_market('BINANCE:BTCUSDT', {
        'timeframe': '1D',
        'range': 5000,
        'from': from_date,
        'to': to_date
    })

    # Flag for data completion
    data_loaded = False

    # Define callback functions
    def on_error(*err):
        """Error handling callback"""
        print("Error:", *err)
        asyncio.create_task(client.end())

    def on_symbol_loaded():
        """Ready callback"""
        print("Chart ready!")
        print(f"Symbol: {chart.infos.description}")

    def on_update():
        """Data update callback"""
        nonlocal data_loaded
        if data_loaded or not chart.periods:
            return

        candles = chart.periods
        print(f"Retrieved {len(candles)} K-line records")

        # Check data time range
        if candles:
            first_candle = candles[0]
            last_candle = candles[-1]

            first_time = datetime.fromtimestamp(first_candle.time, tz=timezone.utc)
            last_time = datetime.fromtimestamp(last_candle.time, tz=timezone.utc)

            print(f"\nData time range:")
            print(f"  First K-line: {first_time.strftime('%Y-%m-%d')}")
            print(f"  Last K-line:  {last_time.strftime('%Y-%m-%d')}")

            # Verify if data is within requested range
            is_in_range = (
                first_candle.time >= from_date and
                last_candle.time <= to_date
            )

            if is_in_range:
                print("Data is within requested range")
            else:
                print("Warning: Data is not entirely within the requested range")

        # Example data processing - Calculate high/low for the period
        if candles:
            highs = [candle.high for candle in candles]
            lows = [candle.low for candle in candles]

            max_price = max(highs) if highs else 0
            min_price = min(lows) if lows else 0

            print(f"\nPeriod high: {max_price}")
            print(f"Period low:  {min_price}")
            print(f"Price range: {max_price - min_price}")
            print(f"Volatility:  {((max_price - min_price) / min_price * 100):.2f}%")

        # Mark as loaded
        data_loaded = True

        # Close connection
        asyncio.create_task(client.end())

    # Set callbacks
    chart.on_error(on_error)
    chart.on_symbol_loaded(on_symbol_loaded)
    chart.on_update(on_update)

    # Timeout handling
    try:
        await asyncio.wait_for(asyncio.sleep(30), timeout=30)
        if not data_loaded:
            print("Operation timed out")
            await client.end()
    except asyncio.TimeoutError:
        print("Operation timed out")
        await client.end()

if __name__ == '__main__':
    asyncio.run(main())
