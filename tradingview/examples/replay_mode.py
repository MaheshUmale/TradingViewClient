#!/usr/bin/env python3
"""
This example demonstrates how to use replay mode to view historical data.
"""
import asyncio
import os
import json
from datetime import datetime, timezone

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

    # Create chart
    chart = tv.create_chart('BINANCE:BTCUSDT', '1D', 5000)

    # Define callback functions
    def on_error(err):
        """Error handling callback"""
        print("Error:", err)
        tv.close()

    def on_ready():
        """Ready callback"""
        print("Chart ready!")
        print("Enabling replay mode...")

        # Enable replay mode - set to January 1, 2021
        target_time = int(datetime(2021, 1, 1, tzinfo=timezone.utc).timestamp())
        chart.set_replay_mode(True, target_time)

    def on_update(data):
        """Data update callback"""
        # Get candle data
        candles = data.get('candles', [])
        if not candles:
            return

        # Get replay status
        replay_status = data.get('replay')
        if replay_status:
            print(f"\nReplay status: {json.dumps(replay_status, indent=2)}")

            # Check if in replay mode
            is_replay = replay_status.get('active', False)
            if is_replay:
                current_time = replay_status.get('ts')
                if current_time:
                    dt = datetime.fromtimestamp(current_time, tz=timezone.utc)
                    print(f"Current replay time: {dt.strftime('%Y-%m-%d %H:%M:%S')}")

        # Display latest candle data
        print(f"Retrieved {len(candles)} candles")
        print("Latest candle data:")
        latest = candles[-1]
        dt = datetime.fromtimestamp(latest.get('time', 0) / 1000, tz=timezone.utc)
        print(f"Time:  {dt.strftime('%Y-%m-%d')}")
        print(f"Open:  {latest.get('open')}")
        print(f"High:  {latest.get('high')}")
        print(f"Low:   {latest.get('low')}")
        print(f"Close: {latest.get('close')}")
        print(f"Vol:   {latest.get('volume')}")

        # Replay action - step forward every 3 seconds
        # Note: This is for demonstration; actual logic would control replay pace.
        asyncio.create_task(replay_step(chart))

    # Set callbacks
    chart.on_error = on_error
    chart.on_ready = on_ready
    chart.on_update = on_update

    # Create chart
    chart.create()

    # Timeout handling
    await asyncio.sleep(60)
    if tv.connected:
        print("Operation timed out")
        tv.close()

async def replay_step(chart):
    """Execute a replay step"""
    await asyncio.sleep(3)
    if chart.session and chart.session.client.connected:
        print("\nStepping forward to next time point...")
        chart.replay_step()

if __name__ == '__main__':
    asyncio.run(main())
