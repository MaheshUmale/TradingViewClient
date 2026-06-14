#!/usr/bin/env python3
"""
This example demonstrates how to handle various errors in the TradingView API client.
"""
import asyncio
import os
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

    print("=== Example 1: Invalid Trading Symbol ===")

    # Create chart (invalid symbol)
    chart1 = tv.create_chart('INVALID_SYMBOL', '1D', 1000)

    # Define callback functions
    def on_error1(err):
        """Error handling callback"""
        print("Error Example 1:", err)
        print("Successfully captured invalid symbol error")
        # Do not close connection, continue to next example

    def on_ready1():
        """Ready callback"""
        print("Chart 1 ready (this should not happen for an invalid symbol)")

    # Set callback functions
    chart1.on_error = on_error1
    chart1.on_ready = on_ready1

    # Create chart
    chart1.create()

    # Wait for error to occur
    await asyncio.sleep(3)

    print("\n=== Example 2: Invalid Indicator ===")

    # Create chart (valid symbol)
    chart2 = tv.create_chart('BINANCE:BTCUSDT', '1D', 1000)

    # Define callback functions
    def on_error2(err):
        """Error handling callback"""
        print("Error Example 2:", err)
        print("Successfully captured invalid indicator error")
        # Do not close connection, continue to next example

    def on_ready2():
        """Ready callback"""
        print("Chart 2 ready")

        # Try using an invalid indicator
        try:
            chart2.add_indicator("INVALID_INDICATOR")
        except Exception as e:
            print(f"Exception while adding indicator: {e}")

    # Set callback functions
    chart2.on_error = on_error2
    chart2.on_ready = on_ready2

    # Create chart
    chart2.create()

    # Wait for indicator error
    await asyncio.sleep(3)

    print("\n=== Example 3: Authentication Error ===")

    # Create client with invalid credentials
    invalid_client = Client("invalid_session", "invalid_signature")

    try:
        # Connect to TradingView (expected to fail)
        await invalid_client.connect()
        print("Connection successful (this should not happen with invalid credentials)")
    except Exception as e:
        print(f"Authentication error example: {e}")
        print("Successfully captured authentication error")

    # Close all connections
    print("\nClosing connections...")
    tv.close()

if __name__ == '__main__':
    asyncio.run(main())
