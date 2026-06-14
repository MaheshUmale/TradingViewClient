#!/usr/bin/env python3
"""
This example tests indicators that send graphic data such as 'lines', 'labels', 'boxes', 'tables', 'polygons', etc.
"""
import asyncio
import os
from pprint import pprint

from ...tradingview import Client, get_indicator

async def main():
    """Main function"""
    # Check environment variables
    session = os.environ.get('TV_SESSION')
    signature = os.environ.get('TV_SIGNATURE')

    if not session or not signature:
        raise ValueError('Please set TV_SESSION and TV_SIGNATURE environment variables')

    # Create client
    client = Client(
        token=session,
        signature=signature
    )

    # Connect to TradingView
    await client.connect()

    # Create chart session
    chart = client.Session.Chart()

    # Set market
    chart.set_market('BINANCE:BTCEUR', {
        'timeframe': '5',
        'range': 10000,
    })

    # Load indicator - built-in Zig_Zag or a custom indicator
    # Custom indicator examples:
    # indicator = await get_indicator('USER;01efac32df544348810bc843a7515f36')
    # indicator = await get_indicator('PUB;5xi4DbWeuIQrU0Fx6ZKiI2odDvIW9q2j')

    # Use built-in Zig_Zag indicator
    indicator = await get_indicator('STD;Zig_Zag')

    # Create indicator study
    std = chart.Study(indicator)

    # Error handling
    def on_error(*err):
        print('Indicator error:', *err)

    std.on_error(on_error)

    # Callback when indicator is ready
    def on_ready():
        print(f"Indicator '{std.instance.description}' loaded!")

    std.on_ready(on_ready)

    # Callback when indicator data updates
    def on_update():
        print('Graphic data:')
        pprint(std.graphic)

        # Show table info if available
        if hasattr(std.graphic, 'tables') and std.graphic.tables:
            print('Tables:')
            pprint(std.graphic.tables)

            # Show cell info if available
            if hasattr(std.graphic.tables[0], 'cells') and callable(std.graphic.tables[0].cells):
                print('Cells:')
                pprint(std.graphic.tables[0].cells())

        # Task complete, shutdown connection
        asyncio.create_task(client.end())

    std.on_update(on_update)

    # Prevent infinite wait with a timeout
    try:
        await asyncio.wait_for(asyncio.sleep(30), timeout=30)
    except asyncio.TimeoutError:
        print("Operation timed out, closing connection")
        await client.end()

if __name__ == '__main__':
    asyncio.run(main())
